# Apple Privacy Manifest Agent Skill

Agent skill for any AI coding tool that supports the [Agent Skills open format](https://agentskills.io/home). It audits Apple platform `PrivacyInfo.xcprivacy` files and required reason API usage in iOS, iPadOS, macOS, Mac Catalyst, tvOS, visionOS, and watchOS projects.

## Who This Is For

Developers and agents working on Apple platform apps, app extensions, frameworks, or SDKs that need to prepare or review privacy manifests for App Store submission.

The skill helps agents:

- Scan Swift, Objective-C, C, and C++ code for likely required reason API usage.
- Review existing `PrivacyInfo.xcprivacy` manifests.
- Triage App Store Connect errors such as `ITMS-91053` and `ITMS-91055`.
- Identify target membership, app extension, framework, and third-party SDK packaging risks.
- Recommend precise `NSPrivacyAccessedAPITypes` entries with reason-code rationale.

This skill is intended for macOS-based Apple platform development environments.

## How To Verify

After installation, ask your agent to use `apple-privacy-manifest` on an Apple platform project. The agent should reference `apple-privacy-manifest/SKILL.md`, use the bundled scanner when source-code evidence is needed, and consult `references/required-reason-apis.md` before recommending manifest entries.

## Install

Choose one installation method.

### Option A: skills.sh (Recommended)

```bash
npx skills add https://github.com/enoktate/Privacy-Manifest-Agent-Skill --skill apple-privacy-manifest
```

For more information, visit the [skills.sh platform page](https://skills.sh/enoktate/privacy-manifest-agent-skill).

### Option B: Codex Manual Install

Installs the skill for all Codex projects on this Mac.

```bash
git clone https://github.com/enoktate/Privacy-Manifest-Agent-Skill.git
cd Privacy-Manifest-Agent-Skill
mkdir -p ~/.agents/skills
cp -R apple-privacy-manifest ~/.agents/skills/
```

### Option C: Claude Code Manual Install

Installs the skill for all Claude Code projects on this Mac.

```bash
git clone https://github.com/enoktate/Privacy-Manifest-Agent-Skill.git
cd Privacy-Manifest-Agent-Skill
mkdir -p ~/.claude/skills
cp -R apple-privacy-manifest ~/.claude/skills/
```

### Project-Local Install

To install the skill only for one project, copy `apple-privacy-manifest` into that project's skill folder:

- Codex: `.agents/skills/apple-privacy-manifest`
- Claude Code: `.claude/skills/apple-privacy-manifest`

If the skill does not appear after a manual install, restart the agent session.

## Usage

Ask your agent:

```text
Use the apple-privacy-manifest skill to audit this Apple platform project for required reason API usage and PrivacyInfo.xcprivacy coverage.
```

Or:

```text
Audit this app's privacy manifest and explain any missing required reason API declarations.
```

## Bundled Scanner

The skill includes a small Python script that agents can run locally to gather evidence from a project. It uses only the Python standard library, reads source files and `PrivacyInfo.xcprivacy` manifests, and reports likely required reason API usage for the agent to verify against code context and Apple documentation.

## Skill Structure

```text
apple-privacy-manifest/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   └── required-reason-apis.md
└── scripts/
    └── scan_privacy_manifest.py
```

## License

MIT. See [LICENSE](LICENSE).
