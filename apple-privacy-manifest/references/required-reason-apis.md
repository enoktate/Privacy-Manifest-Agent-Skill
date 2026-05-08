# Required Reason APIs Reference

Use this as a compact working reference. For App Store submission decisions, verify against Apple's current documentation:

- Apple: Privacy manifest files, `PrivacyInfo.xcprivacy`
- Apple: Describing use of required reason API
- Apple: TN3183, adding required reason API entries to your privacy manifest

Apple enforces required reason API declarations for apps and third-party SDKs. A privacy manifest is a property list named `PrivacyInfo.xcprivacy`. The key most relevant to required reason APIs is `NSPrivacyAccessedAPITypes`, an array of dictionaries.

## Top-Level Manifest Keys

- `NSPrivacyTracking`: Boolean. Use `true` only when the app tracks under App Tracking Transparency.
- `NSPrivacyTrackingDomains`: Array of domains contacted specifically for tracking.
- `NSPrivacyCollectedDataTypes`: Array describing collected data categories, use, identity linkage, and tracking behavior.
- `NSPrivacyAccessedAPITypes`: Array declaring required reason API categories and reason codes.

Most required reason API audits focus on `NSPrivacyAccessedAPITypes`, but do not ignore tracking accuracy when preparing a submission.

Each dictionary has:

```xml
<dict>
    <key>NSPrivacyAccessedAPIType</key>
    <string>NSPrivacyAccessedAPICategoryUserDefaults</string>
    <key>NSPrivacyAccessedAPITypeReasons</key>
    <array>
        <string>CA92.1</string>
    </array>
</dict>
```

## Categories And Common Reason Codes

### File Timestamp

Category: `NSPrivacyAccessedAPICategoryFileTimestamp`

Common APIs/signals:

- `creationDate`
- `modificationDate`
- `fileModificationDate`
- `contentModificationDateKey`
- `creationDateKey`
- `getattrlist()`
- `getattrlistat()`
- file attributes that expose creation or modification timestamps

Reason codes:

- `DDA9.1`: Display timestamps to the user only; data stays on-device.
- `C617.1`: Read metadata of files in the app container, app group, or CloudKit.
- `3B52.1`: Read timestamps for files the user explicitly grants access to, such as document picker files.
- `0A2A.1`: Third-party SDK wrapper around file timestamp APIs. SDKs only.

### System Boot Time

Category: `NSPrivacyAccessedAPICategorySystemBootTime`

Common APIs/signals:

- `ProcessInfo.processInfo.systemUptime`
- `systemUptime`
- `mach_absolute_time()`

Reason codes:

- `35F9.1`: Measure elapsed time between in-app events; data stays on-device.
- `8FFB.1`: Calculate absolute timestamps that may be sent off-device.
- `3D61.1`: Include boot time in an optional user-submitted bug report.

### Disk Space

Category: `NSPrivacyAccessedAPICategoryDiskSpace`

Common APIs/signals:

- `volumeAvailableCapacityKey`
- `volumeAvailableCapacityForImportantUsageKey`
- `volumeAvailableCapacityForOpportunisticUsageKey`
- `volumeTotalCapacityKey`
- `systemFreeSize`
- `systemSize`
- `statfs()`
- related file system capacity calls

Reason codes:

- `85F4.1`: Display disk space information to the user.
- `E174.1`: Check available space before writing files or trigger cleanup.
- `7D9E.1`: Include disk space information in an optional user-submitted bug report.
- `B728.1`: Health research apps detecting low disk space that affects data collection.

### Active Keyboards

Category: `NSPrivacyAccessedAPICategoryActiveKeyboards`

Common APIs/signals:

- `activeInputModes`
- `UITextInputMode.activeInputModes`

Reason codes:

- `3EC4.1`: Custom keyboard app determines which keyboards are active.
- `54BD.1`: App adapts UI based on active keyboard in a user-visible way.

### User Defaults

Category: `NSPrivacyAccessedAPICategoryUserDefaults`

Common APIs/signals:

- `UserDefaults`
- `NSUserDefaults`
- `UserDefaults.standard`
- `UserDefaults(suiteName:)`

Reason codes:

- `CA92.1`: Access user defaults from within the app itself.
- `1C8F.1`: Access shared defaults from an app group container.
- `C56D.1`: Third-party SDK accesses user defaults only when the app calls the SDK API.
- `AC6B.1`: Health research app records measurements from a health research sensor.

## Manifest Skeleton

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
    "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSPrivacyTracking</key>
    <false/>
    <key>NSPrivacyTrackingDomains</key>
    <array/>
    <key>NSPrivacyCollectedDataTypes</key>
    <array/>
    <key>NSPrivacyAccessedAPITypes</key>
    <array/>
</dict>
</plist>
```

## Rejection Triage

For ITMS-91053 or ITMS-91055:

1. Inspect the exact rejection text if the user supplied it; otherwise state that rejection-specific triage is unavailable.
2. Extract the named APIs, categories, target/bundle, and SDK if Apple identifies one.
3. Confirm whether the usage comes from app code, an extension, a framework, or a third-party SDK.
4. Prefer adding or fixing the manifest in the bundle that owns the code.
5. If the issue is from a third-party SDK, update the SDK first. Add declarations to the app manifest only when the SDK manifest is not packaged correctly and the declarations accurately describe bundled behavior.

## Creating Or Editing A Manifest

Prefer direct file operations. If a target needs a new manifest, create `PrivacyInfo.xcprivacy` as a valid plist and add only the declarations supported by audit evidence and product behavior. Use `plistlib`, `plutil`, or project-native plist tooling rather than Xcode UI steps.

After creating or editing the file:

1. Run `plutil -lint` on every changed `PrivacyInfo.xcprivacy`.
2. Inspect `.xcodeproj/project.pbxproj` or package configuration to verify the file is included in the intended target resources when the project format is available.
3. If target membership cannot be proven from files available to the agent, report it as a packaging risk and a remaining manual validation step.

For extensions, each extension target needs its own manifest if that binary uses required reason APIs. Do not put all extension declarations into the containing app's manifest.

## Third-Party SDK Audit

- Swift Package Manager: inspect the package repository and local checkout for `PrivacyInfo.xcprivacy`, usually at the package root or inside source targets.
- CocoaPods: inspect `Pods/<SDKName>/` after install. Static pods can fail to bundle resources in some configurations, so verify the final Privacy Report.
- XCFrameworks: inspect inside the framework bundle. The manifest should ship inside the framework itself.
- Commonly used SDKs on Apple's list must ship with a privacy manifest and valid signature for binary distributions.
- Inspect an existing Xcode Privacy Report if one is present. If it is not present and the environment cannot generate it, state that Privacy Report review remains outstanding. Missing SDK entries in that report are a red flag.
- Core ML and on-device model SDKs often touch file timestamp or disk space APIs through model loading and cache management; audit them carefully.

## Common Mistakes

- Picking the broadest or most convenient reason code instead of the one that matches actual behavior.
- Copying all five categories from an internet sample.
- Declaring APIs that are not used, which misrepresents the app.
- Forgetting app extension manifests.
- Assuming a third-party SDK manifest is bundled without checking the final report.
- Ignoring Xcode 15+ privacy warnings.
- Treating the first accepted manifest as permanent; Apple can expand required reason APIs in future OS releases.

## Final Pre-Submission Checklist

- `PrivacyInfo.xcprivacy` is included in the correct target resources.
- Every target/bundle that uses required reason APIs has its own manifest.
- Every used category is declared once with one or more accurate reason codes.
- No unused categories are declared.
- SDK-only reason codes are not used for first-party app code.
- Third-party SDKs that require manifests have current releases and bundled manifests.
- `NSPrivacyTracking` and `NSPrivacyTrackingDomains` match the app's actual tracking behavior.
- Xcode Privacy Report has been generated or an existing report has been reviewed when preparing for submission. If unavailable, mark as outstanding.
- TestFlight upload validation has passed when appropriate. If unavailable, mark as outstanding.
