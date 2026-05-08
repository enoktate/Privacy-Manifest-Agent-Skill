---
name: apple-privacy-manifest
description: Audit and remediate iOS, iPadOS, macOS, Mac Catalyst, tvOS, visionOS, and watchOS PrivacyInfo.xcprivacy privacy manifests for Apple required reason APIs. Use when asked to add, fix, review, or generate privacy manifests; handle ITMS-91053 or ITMS-91055 App Store errors; inspect Xcode privacy reports; verify third-party SDK manifest coverage; or scan Swift, Objective-C, C, and C++ projects for UserDefaults, file timestamp, system boot time, disk space, or active keyboard API usage.
license: MIT
compatibility: Designed for macOS-based Apple platform development. Uses Python 3 and Apple plist tooling such as plutil when available.
---

# Apple Privacy Manifest

## Workflow

1. Read `references/required-reason-apis.md` before giving manifest guidance or editing a manifest.
2. For submission-sensitive advice, verify Apple Developer documentation because required reason APIs and approved reasons can change.
3. Audit the project before editing:
   - Run the bundled scanner to find likely required reason API usage and existing `PrivacyInfo.xcprivacy` declarations.
   - In Claude Code, use `python "${CLAUDE_SKILL_DIR}/scripts/scan_privacy_manifest.py" <project-root>`.
   - In other agents, resolve `scripts/scan_privacy_manifest.py` relative to this skill directory.
   - Add `--include-dependencies` when the user wants bundled dependency source scanned too.
   - Review scanner findings against code context; scanner hits are evidence, not final compliance decisions.
4. If the user has an App Store rejection, extract the exact ITMS code, named API/category, target/bundle, and SDK from the rejection text before proposing a fix.
5. Identify every bundle that needs its own manifest. The app target, extensions, frameworks, dynamic libraries, and third-party SDKs that use required reason APIs may need separate `PrivacyInfo.xcprivacy` files.
6. Verify placement, not just content. Inspect `.xcodeproj/project.pbxproj`, package manifests, podspecs, framework contents, and resource-copy phases where available. A manifest sitting in the project tree is ineffective unless it is included in the correct target resources or bundled inside the correct framework/SDK.
7. Choose the narrowest accurate reason codes. Do not declare all categories as a hedge, and do not use SDK-only reason codes for app code.
8. Edit manifests as property lists, preferably with `plistlib` or `plutil`. Keep `NSPrivacyAccessedAPITypes` as an array of dictionaries with exactly:
   - `NSPrivacyAccessedAPIType`
   - `NSPrivacyAccessedAPITypeReasons`
9. Validate with `plutil -lint PrivacyInfo.xcprivacy` after edits. If the user asks for build validation, do not run `xcodebuild` unless they explicitly authorize it in the current turn.

## Decision Rules

- If code uses `UserDefaults` or `NSUserDefaults`, expect a `NSPrivacyAccessedAPICategoryUserDefaults` declaration unless the usage is removed or isolated in a third-party SDK manifest.
- If code reads file creation or modification timestamps, expects `URLResourceKey` timestamp values, or calls timestamp-returning file attribute APIs, consider `NSPrivacyAccessedAPICategoryFileTimestamp`.
- If code uses `mach_absolute_time()` or `ProcessInfo.processInfo.systemUptime`, consider `NSPrivacyAccessedAPICategorySystemBootTime`.
- If code checks total, free, or available disk capacity before writes/downloads/cleanup, consider `NSPrivacyAccessedAPICategoryDiskSpace`.
- If code reads active keyboard/input modes, consider `NSPrivacyAccessedAPICategoryActiveKeyboards`.
- For third-party SDKs, first update the SDK and inspect its bundled manifest. Copy SDK declarations into the app manifest only as a last-resort workaround when the packaging format fails to bundle a vendor manifest and the declarations accurately represent bundled code.
- For app extensions, do not consolidate declarations into the app target. Widget, Share, Notification Service, Keyboard, and other extensions need manifests that reflect only their own binary behavior.
- Treat Xcode privacy warnings, Xcode Privacy Report gaps, and TestFlight validation failures as release-blocking until explained. If the agent cannot generate or inspect those artifacts in the environment, report them as explicit remaining validation steps instead of asking the user to do them mid-audit.

## SDK Audit Checklist

For each dependency manager or binary format present:

- Swift Package Manager: inspect the package repository and local checkout for `PrivacyInfo.xcprivacy`.
- CocoaPods: inspect `Pods/<SDKName>/` after install and watch for static pod resource bundling gaps.
- XCFrameworks: inspect inside the `.xcframework`; the manifest should be bundled in the framework itself.
- Binary SDKs on Apple's commonly used SDK list: prefer updating to a vendor release with a manifest and valid signature.
- SDKs with Core ML or heavy file/model pipelines: pay extra attention to disk space and file timestamp API usage.

## Output Expectations

When auditing, return:

- Existing manifest files found.
- Targets/bundles that appear to need separate manifests, including app extensions and bundled SDKs.
- Required reason API evidence with file and line references.
- Missing, extra, or suspicious manifest declarations.
- Recommended `NSPrivacyAccessedAPITypes` entries by target/bundle, with reason-code rationale.
- Target membership or packaging risks that could make an otherwise correct manifest ineffective.
- Xcode Privacy Report, build-log, or TestFlight validation evidence found; if unavailable, list them as remaining manual validation steps.
- Open questions where the correct reason depends on product behavior, off-device transmission, user visibility, or SDK ownership.

When editing, keep changes scoped to privacy manifests or small supporting scripts/docs the user requested.
