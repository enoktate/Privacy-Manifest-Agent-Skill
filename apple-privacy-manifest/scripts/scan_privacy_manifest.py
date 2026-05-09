#!/usr/bin/env python3
"""Scan an Apple-platform project for required reason API evidence."""

from __future__ import annotations

import argparse
import json
import plistlib
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    ".svn",
    ".hg",
    ".idea",
    ".vscode",
    "DerivedData",
    "build",
    "Build",
    ".build",
    "Carthage",
    "Pods",
    "node_modules",
}

DEPENDENCY_DIRS = {"Pods", "Carthage", ".build", "SourcePackages", "checkouts"}

SOURCE_SUFFIXES = {
    ".swift",
    ".m",
    ".mm",
    ".h",
    ".hpp",
    ".c",
    ".cc",
    ".cpp",
    ".plist",
    ".xcprivacy",
}


PATTERNS = {
    "NSPrivacyAccessedAPICategoryUserDefaults": [
        r"\bUserDefaults\b",
        r"\bNSUserDefaults\b",
    ],
    "NSPrivacyAccessedAPICategorySystemBootTime": [
        r"\bmach_absolute_time\s*\(",
        r"\bsystemUptime\b",
        r"\bProcessInfo\.processInfo\.systemUptime\b",
    ],
    "NSPrivacyAccessedAPICategoryDiskSpace": [
        r"\bNSURLVolumeAvailableCapacity(?:ForImportantUsage|ForOpportunisticUsage)?Key\b",
        r"\bURLResourceKey\.volumeAvailableCapacity(?:ForImportantUsage|ForOpportunisticUsage)?Key\b",
        r"\bvolumeAvailableCapacity(?:ForImportantUsage|ForOpportunisticUsage)?Key\b",
        r"\bNSURLVolumeTotalCapacityKey\b",
        r"\bURLResourceKey\.volumeTotalCapacityKey\b",
        r"\bvolumeTotalCapacityKey\b",
        r"\bsystemFreeSize\b",
        r"\bsystemSize\b",
        r"\bstatfs\s*\(",
        r"\bf_bavail\b",
        r"\bf_bfree\b",
        r"\bf_blocks\b",
        r"\bstatvfs\s*\(",
    ],
    "NSPrivacyAccessedAPICategoryFileTimestamp": [
        r"\bNSFileCreationDate\b",
        r"\bNSFileModificationDate\b",
        r"\bFileAttributeKey\.creationDate\b",
        r"\bFileAttributeKey\.modificationDate\b",
        r"\bURLResourceKey\.contentModificationDateKey\b",
        r"\bURLResourceKey\.creationDateKey\b",
        r"\bcreationDate\b",
        r"\bmodificationDate\b",
        r"\bfileModificationDate\b",
        r"\bcontentModificationDateKey\b",
        r"\bcreationDateKey\b",
        r"\bgetattrlist(?:bulk|at)?\s*\(",
        r"\bfgetattrlist\s*\(",
        r"\bstat\s*\(",
        r"\bfstat\s*\(",
        r"\bfstatat\s*\(",
        r"\blstat\s*\(",
        r"\battributesOfItem\s*\(",
    ],
    "NSPrivacyAccessedAPICategoryActiveKeyboards": [
        r"\bactiveInputModes\b",
        r"\bUITextInputMode\.activeInputModes\b",
    ],
}

DEPENDENCY_MARKERS = {
    "Swift Package Manager": ["Package.swift", "Package.resolved"],
    "CocoaPods": ["Podfile", "Podfile.lock", "Pods"],
    "Carthage": ["Cartfile", "Cartfile.resolved", "Carthage"],
}


REASONS = {
    "NSPrivacyAccessedAPICategoryUserDefaults": ["CA92.1", "1C8F.1", "C56D.1", "AC6B.1"],
    "NSPrivacyAccessedAPICategorySystemBootTime": ["35F9.1", "8FFB.1", "3D61.1"],
    "NSPrivacyAccessedAPICategoryDiskSpace": ["85F4.1", "E174.1", "7D9E.1", "B728.1"],
    "NSPrivacyAccessedAPICategoryFileTimestamp": ["DDA9.1", "C617.1", "3B52.1", "0A2A.1"],
    "NSPrivacyAccessedAPICategoryActiveKeyboards": ["3EC4.1", "54BD.1"],
}


@dataclass
class Finding:
    category: str
    path: str
    line: int
    match: str
    text: str


def iter_files(root: Path, include_dependencies: bool) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = set(path.relative_to(root).parts[:-1])
        skipped = SKIP_DIRS & parts
        if skipped and not (include_dependencies and skipped <= DEPENDENCY_DIRS):
            continue
        if path.suffix in SOURCE_SUFFIXES or path.name == "PrivacyInfo.xcprivacy":
            yield path


def scan_sources(root: Path, include_dependencies: bool) -> list[Finding]:
    compiled = {
        category: [re.compile(pattern) for pattern in patterns]
        for category, patterns in PATTERNS.items()
    }
    findings: list[Finding] = []
    for path in iter_files(root, include_dependencies):
        if path.name == "PrivacyInfo.xcprivacy":
            continue
        try:
            lines = path.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        rel = str(path.relative_to(root))
        for line_number, line in enumerate(lines, start=1):
            for category, patterns in compiled.items():
                for pattern in patterns:
                    match = pattern.search(line)
                    if match:
                        findings.append(
                            Finding(
                                category=category,
                                path=rel,
                                line=line_number,
                                match=match.group(0),
                                text=line.strip()[:240],
                            )
                        )
                        break
    return findings


def read_manifests(root: Path) -> list[dict]:
    manifests = []
    for path in root.rglob("PrivacyInfo.xcprivacy"):
        try:
            with path.open("rb") as handle:
                data = plistlib.load(handle)
        except Exception as exc:  # plistlib reports several parse errors.
            manifests.append(
                {
                    "path": str(path.relative_to(root)),
                    "error": str(exc),
                    "declared": [],
                }
            )
            continue
        declared = []
        for item in data.get("NSPrivacyAccessedAPITypes", []) or []:
            if not isinstance(item, dict):
                continue
            declared.append(
                {
                    "category": item.get("NSPrivacyAccessedAPIType"),
                    "reasons": item.get("NSPrivacyAccessedAPITypeReasons", []),
                }
            )
        manifests.append(
            {
                "path": str(path.relative_to(root)),
                "declared": declared,
            }
        )
    return manifests


def dependency_hints(root: Path) -> list[dict]:
    hints = []
    for manager, markers in DEPENDENCY_MARKERS.items():
        found = []
        for marker in markers:
            path = root / marker
            if path.exists():
                found.append(marker)
        if found:
            hints.append({"manager": manager, "markers": found})
    xcframeworks = [str(path.relative_to(root)) for path in root.rglob("*.xcframework")]
    if xcframeworks:
        hints.append({"manager": "XCFrameworks", "markers": xcframeworks[:50]})
    extensions = [
        str(path.relative_to(root))
        for path in root.rglob("*.appex")
        if path.is_dir()
    ]
    if extensions:
        hints.append({"manager": "App Extensions", "markers": extensions[:50]})
    return hints


def summarize(findings: list[Finding], manifests: list[dict]) -> dict:
    evidence_by_category = sorted({finding.category for finding in findings})
    declared_by_category = sorted(
        {
            entry.get("category")
            for manifest in manifests
            for entry in manifest.get("declared", [])
            if entry.get("category")
        }
    )
    return {
        "evidence_categories": evidence_by_category,
        "declared_categories": declared_by_category,
        "missing_declarations_to_review": [
            category for category in evidence_by_category if category not in declared_by_category
        ],
        "declared_without_scanner_evidence": [
            category for category in declared_by_category if category not in evidence_by_category
        ],
    }


def print_text_report(
    root: Path,
    findings: list[Finding],
    manifests: list[dict],
    dependency_info: list[dict],
) -> None:
    print(f"Project: {root}")
    print()
    print("Dependency and bundle hints:")
    if not dependency_info:
        print("  none found")
    for hint in dependency_info:
        print(f"  {hint['manager']}: {', '.join(hint['markers'])}")
    print()
    print("Privacy manifests:")
    if not manifests:
        print("  none found")
    for manifest in manifests:
        print(f"  {manifest['path']}")
        if manifest.get("error"):
            print(f"    parse error: {manifest['error']}")
            continue
        if not manifest["declared"]:
            print("    no NSPrivacyAccessedAPITypes declarations")
        for entry in manifest["declared"]:
            reasons = ", ".join(entry.get("reasons") or [])
            print(f"    {entry.get('category')}: {reasons or '(no reasons)'}")
    print()
    print("Required reason API evidence:")
    if not findings:
        print("  none found")
    for category in sorted({finding.category for finding in findings}):
        print(f"  {category}")
        print(f"    possible reasons: {', '.join(REASONS.get(category, []))}")
        for finding in [item for item in findings if item.category == category][:25]:
            print(f"    {finding.path}:{finding.line}: {finding.match} | {finding.text}")
        count = len([item for item in findings if item.category == category])
        if count > 25:
            print(f"    ... {count - 25} more")
    print()
    summary = summarize(findings, manifests)
    print("Review summary:")
    for key, value in summary.items():
        print(f"  {key}: {', '.join(value) if value else 'none'}")
    print()
    print("Note: scanner findings are heuristics. Confirm product behavior and Apple docs before submission.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Project root to scan.")
    parser.add_argument(
        "--include-dependencies",
        action="store_true",
        help="Scan dependency directories such as Pods, Carthage, and SwiftPM checkouts.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    findings = scan_sources(root, args.include_dependencies)
    manifests = read_manifests(root)
    dependency_info = dependency_hints(root)

    if args.json:
        print(
            json.dumps(
                {
                    "root": str(root),
                    "dependency_hints": dependency_info,
                    "manifests": manifests,
                    "findings": [asdict(finding) for finding in findings],
                    "summary": summarize(findings, manifests),
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print_text_report(root, findings, manifests, dependency_info)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
