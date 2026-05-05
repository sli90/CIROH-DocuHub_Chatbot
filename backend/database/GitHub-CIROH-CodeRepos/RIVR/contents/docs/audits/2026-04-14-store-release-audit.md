# RIVR App Store Release Audit

**Date:** 2026-04-14
**Version:** 1.0.0+5
**Branch:** `development`
**Audited by:** 6 parallel audit agents (security, Android, iOS, codebase, store requirements, store assets)

---

## Executive Summary

RIVR is **not yet ready** for public release on either store. There are **9 critical issues** that must be resolved, **~25 warnings** that should be addressed, and several recommendations for polish. The most urgent items are:

1. **Security:** Firebase API keys and Mapbox tokens are permanently exposed in the public git history
2. **iOS:** Missing `NSFaceIDUsageDescription` (will crash on Face ID devices) and `ITSAppUsesNonExemptEncryption`
3. **Android:** Dead storage permissions that will raise reviewer flags
4. **Accessibility:** Zero `Semantics` usage across the entire codebase
5. **Store assets:** No screenshots, no feature graphic, app icon has alpha transparency issues

---

## Table of Contents

1. [Security Audit](#1-security-audit)
2. [Android (Google Play) Audit](#2-android-google-play-audit)
3. [iOS (App Store) Audit](#3-ios-app-store-audit)
4. [Codebase Readiness Audit](#4-codebase-readiness-audit)
5. [Store Assets Audit](#5-store-assets-audit)
6. [Store Requirements Checklist](#6-store-requirements-checklist)
7. [Roadmap](#7-roadmap)

---

## 1. Security Audit

### CRITICAL

| # | Issue | Details | Remediation |
|---|-------|---------|-------------|
| S-1 | **Firebase API keys in public git history** | Android key `AIzaSyDmxL...`, iOS key `AIzaSyBbU...`, migration key `AIzaSyABS...`, and a 4th iOS key are all recoverable from commits `47c93d8`, `0e2b450`, `a16f0e9` in the **public** repo `github.com/CIROH-UA/RIVR` | **Immediately** restrict all keys in Google Cloud Console (package name + SHA-1 for Android, bundle ID for iOS). Enable only required APIs per key. Consider rotating keys via FlutterFire CLI. |
| S-2 | **Mapbox tokens in public git history** | 3 distinct Mapbox public tokens (BYU Hydroinformatics production token + 2 jersondevs tokens) are in git history via `AndroidManifest.xml`, `strings.xml`, `GoogleService-Info.plist` | Add app/URL restrictions in Mapbox dashboard. Set monthly usage caps. Rotate personal tokens if still active. |
| S-3 | **Unauthenticated Cloud Function** | `triggerAlertCheck` in `functions/src/index.ts:94` is an `onRequest` endpoint with no auth. Anyone with the URL can trigger alert checks and push notifications to all users. | Add authentication (Authorization header check or switch to `onCall`), or delete before production. |

### WARNING

| # | Issue | Details |
|---|-------|---------|
| S-4 | NWM API key was previously exposed | Rotated 2026-03-27. Verify old key is deactivated by CIROH. |
| S-5 | Development Team ID `2UL5XK6YRM` in Xcode project | Semi-public but could aid targeted social engineering. |
| S-6 | `firebase.json` exposes project ID and app IDs | Low risk alone, but combined with exposed API keys provides full abuse surface. |
| S-7 | Makefile `test` target points to nonexistent dirs | `test/core` and `test/features` don't exist; `make test` silently skips. |

### PASS

- `config.dart` never committed (Mapbox token, NWM API key safe on disk)
- `functions/.env` never committed
- `android/key.properties` never committed
- `ios/Flutter/Secrets.xcconfig` never committed
- All 7 sensitive files properly `.gitignore`d
- Template files contain only placeholders
- CI stub uses `CI_PLACEHOLDER` values
- No hardcoded secrets in current tracked `.dart` files
- Firestore rules are properly restrictive (default deny, user-scoped)
- No binary secrets (`.pem`, `.p12`, `.jks`) tracked

### RECOMMENDATIONS

- **REC-S1:** Rewrite git history with `git-filter-repo` or BFG to remove sensitive commits (requires force push + all collaborators re-clone)
- **REC-S2:** Enable Firebase App Check to ensure only the legitimate app can call Firebase services
- **REC-S3:** Enable GitHub secret scanning on the repo
- **REC-S4:** Add a pre-push git hook scanning for common secret patterns (`AIza`, `pk.`, `sk-`)

---

## 2. Android (Google Play) Audit

### CRITICAL

| # | Issue | Details | Fix |
|---|-------|---------|-----|
| A-1 | **`WRITE_EXTERNAL_STORAGE` permission declared** | Completely non-functional on `minSdk 30` (Android 11+). Will raise reviewer flags. | Remove from `AndroidManifest.xml` |
| A-2 | **`READ_EXTERNAL_STORAGE` permission declared** | Same — dead on API 30+. `gal` and `image_picker` handle scoped storage internally. | Remove from `AndroidManifest.xml` |

### WARNING

| # | Issue | Details |
|---|-------|---------|
| A-3 | `SCHEDULE_EXACT_ALARM` declared | No code references found. Sensitive permission on Android 12+ requiring justification. Remove unless needed. |
| A-4 | `CAMERA` permission explicitly declared | Only used via `image_picker` (optional). Plugin handles this automatically. Explicit declaration means Play Store will list camera as required. |
| A-5 | Adaptive icon foreground is raw launcher PNG | Will be clipped by system masks on modern Android. Create proper foreground with 108dp safe zone. |
| A-6 | No monochrome icon for Android 13+ | Themed icon support missing. Optional but polished. |
| A-7 | Kotlin stdlib version mismatch | Explicit `kotlin-stdlib-jdk8:1.9.10` conflicts with Kotlin plugin 2.1.0. Remove the explicit dep. |
| A-8 | Google Services plugin 4.3.15 | Consider updating to 4.4.x. |
| A-9 | `android.enableJetifier=true` | Likely unnecessary; test removal. |
| A-10 | Default pubspec description | `"A new Flutter project."` — update to real description. |
| A-11 | Makefile `make test` targets wrong dirs | `test/core` and `test/features` don't exist. |
| A-12 | Makefile comment references old config path | `lib/core/config.dart` should be `lib/services/0_config/shared/config.dart`. |

### PASS

- `applicationId` = `com.hydromap.rivr`
- `minSdk` = 30, `targetSdk` = 35, `compileSdk` = 36 (meets Play Store 2025-2026 requirements)
- Release signing properly reads `key.properties` (gitignored)
- R8/ProGuard enabled with correct rules (Flutter, Firebase, Mapbox, Play Core kept)
- Version: 1.0.0+5 (appropriate for first release)
- AGP 8.7.3 / Gradle 8.12 / Kotlin 2.1.0 — all current
- No debug flags in `gradle.properties`
- `make release-android` produces signed AAB with obfuscation + split debug info
- All pubspec dependencies are stable releases
- Launcher icon density buckets present at correct sizes (mdpi through xxxhdpi)
- `usesCleartextTraffic` defaults to `false`
- No `android:debuggable` attribute in main manifest

### RECOMMENDATIONS

- Verify Syncfusion license (community vs. commercial) before publishing
- Confirm versionCode 5 has not been previously uploaded to Play Console
- Consider `android:allowBackup="false"` if sensitive local data
- Add a custom FCM notification icon (default may render as white square on some devices)
- Will need `targetSdk` = 36 by August 31, 2026

---

## 3. iOS (App Store) Audit

### CRITICAL

| # | Issue | Details | Fix |
|---|-------|---------|-----|
| I-1 | **`NSFaceIDUsageDescription` missing** | App uses `local_auth` for biometric auth (10+ source files). On Face ID devices, the app will **crash** or Apple will **reject**. | Add to `Info.plist`: `"RIVR uses Face ID to quickly and securely sign you in."` |
| I-2 | **`ITSAppUsesNonExemptEncryption` missing** | Without this, Apple asks export compliance questions on every submission. App uses only standard HTTPS. | Add `<key>ITSAppUsesNonExemptEncryption</key><false/>` to `Info.plist` |

### WARNING

| # | Issue | Details |
|---|-------|---------|
| I-3 | Project-level deployment target mismatch | Project-level `IPHONEOS_DEPLOYMENT_TARGET` is `13.0`, target-level is `16.6`. Update project-level to `16.6`. |
| I-4 | Missing `LaunchImage.imageset` | `LaunchScreen.storyboard` references `LaunchImage` but the asset doesn't exist. Blank white launch screen. |
| I-5 | Missing `PERMISSION_LOCATION` macros in Podfile | If `permission_handler` is used for location, add `PERMISSION_LOCATION_WHENINUSE=1` and `PERMISSION_LOCATION_ALWAYS=1`. |
| I-6 | `aps-environment` set to `development` | In `Runner.entitlements`. Should auto-switch to `production` during archive, but verify. |

### PASS

- Bundle identifier: `com.hydromap.rivr` (all 3 configs)
- Bundle display name: `RIVR`
- All 15 iOS icon sizes present with correct dimensions including 1024x1024
- Code signing: `DEVELOPMENT_TEAM = 2UL5XK6YRM`, `ENABLE_BITCODE = NO`
- Swift version: 5.0
- Podfile platform: `ios, '16.6'` (matches target)
- Background modes: `remote-notification` for FCM
- App Transport Security: default HTTPS-only policy
- App category: `public.app-category.weather`
- Release build: `wholemodule` compilation, `-O` optimization, dSYM generation
- All 6 privacy permission descriptions present with clear, specific language (Camera, Location Always/WhenInUse, Photo Library, Photo Library Add)
- `FirebaseAppDelegateProxyEnabled = false` (correct for Dart-side init)
- iPhone portrait-only, iPad all orientations
- `LaunchScreen.storyboard` exists and is referenced

### RECOMMENDATIONS

- **REC-I1:** Add `UIRequiredDeviceCapabilities` with `arm64` to Info.plist
- **REC-I2:** Verify iPad UI works properly since app is Universal (`TARGETED_DEVICE_FAMILY = "1,2"`). If not designed for iPad, change to `1` (iPhone only).
- **REC-I3:** Recreate `LaunchScreen.storyboard` in current Xcode (current version is from Xcode 8 era)
- **REC-I4:** Apple requires iOS 26 SDK / Xcode 26 starting April 28, 2026 — plan upgrade path
- **REC-I5:** Ensure `PrivacyInfo.xcprivacy` manifest is included (required for apps using required reason APIs)
- **REC-I6:** If app offers Google Sign-In, must also offer Sign in with Apple (Guideline 4.8)

---

## 4. Codebase Readiness Audit

### CRITICAL

| # | Issue | Details | Fix |
|---|-------|---------|-----|
| C-1 | **Zero accessibility support** | No `Semantics` widgets, no `semanticLabel` on images, no accessibility hints anywhere. VoiceOver/TalkBack users have a severely degraded experience. | Add `semanticLabel` to all images, `Semantics` wrappers to interactive elements, meaningful labels to buttons. |

### WARNING

| # | Issue | Details |
|---|-------|---------|
| C-2 | Default pubspec description | `"A new Flutter project."` — unprofessional. |
| C-3 | 74 outdated dependencies | Key: `syncfusion_flutter_charts` 3 major versions behind, `share_plus` 2 behind, `local_auth`, `flutter_secure_storage`, `csv` need major bumps. |
| C-4 | Unused `flutter_localization` dependency | Declared but never imported. App uses `flutter_localizations` from SDK instead. |
| C-5 | Empty `setState(() {})` calls | Found in `favorites_page.dart`, `horizontal_flow_timeline.dart`, `map_page.dart`. Trigger unnecessary full rebuilds. |
| C-6 | 25 failing integration tests | All from Firebase init issue (`No Firebase App '[DEFAULT]' has been created`). Pre-existing. |
| C-7 | `ErrorService._logError` has commented-out Crashlytics | Minor documentation inconsistency. |
| C-8 | `runZonedGuarded` not used | `PlatformDispatcher.instance.onError` is used (acceptable modern approach), but `runZonedGuarded` adds extra safety. |

### PASS

- **Debug code:** No active `print()` or `debugPrint()` calls in production code
- **TODO/FIXME:** None found in entire codebase
- **kDebugMode:** Used correctly (gates Crashlytics + debug logging)
- **assert():** Only 2, both appropriate construction-time checks in onboarding widgets
- **debugShowCheckedModeBanner:** Set to `false`
- **Crash reporting:** Firebase Crashlytics fully integrated with global error handlers (`FlutterError.onError` + `PlatformDispatcher.instance.onError`)
- **ErrorService:** Comprehensive error mapping (Firebase Auth, Firestore, network), error sanitization (redacts UIDs, emails, tokens), retryable error detection
- **Memory management:** All stream subscriptions and controllers properly disposed
- **Offline handling:** `ConnectivityService` + `ConnectivityProvider` + `OfflineBanner`
- **HTTP timeouts:** Tiered (15s quick, 20s normal, 30s long) with retry logic
- **Flutter analyze:** Zero issues
- **Unit/widget tests:** 573 passing (25 integration failures are pre-existing)
- **Localization:** US English only with proper delegates configured (acceptable for v1.0)
- **Version:** 1.0.0+5 follows semver

### RECOMMENDATIONS

- Clean up ~20 commented-out `print()` statements in `chart_preview_widget.dart`
- Run `flutter pub upgrade` for non-breaking patch updates (Firebase, Mapbox, etc.)
- Fix integration test Firebase initialization for CI confidence

---

## 5. Store Assets Audit

### Status of Required Assets

| Asset | Status | Specification | Priority |
|-------|--------|---------------|----------|
| **Google Play icon (512x512)** | MISSING | PNG, 32-bit, no alpha, sRGB | HIGH |
| **Google Play feature graphic** | MISSING | 1024x500 PNG/JPG, no alpha | HIGH |
| **Google Play phone screenshots** | MISSING | Min 2, max 8, 1080x1920 recommended | HIGH |
| **App Store icon (1024x1024)** | EXISTS (with issue) | Current `1024.png` has alpha channel — Apple rejects this | HIGH |
| **iPhone 6.7" screenshots** | MISSING | 1290x2796 pixels | HIGH |
| **iPhone 6.5" screenshots** | MISSING | 1284x2778 pixels | HIGH |
| **iPhone 5.5" screenshots** | MISSING | 1242x2208 pixels | MEDIUM |
| **iPad 12.9" screenshots** | MISSING | 2048x2732 (required if universal app) | MEDIUM |
| **Google Play tablet screenshots** | MISSING | Optional | LOW |

### Existing Assets

- **Source logo:** `assets/images/rivr_logo.png` (2048x2048, RGB, has alpha) — master for deriving icons
- **Android launcher icons:** All 5 density buckets (mdpi through xxxhdpi) with correct sizes
- **iOS app icons:** All 15 sizes present in `AppIcon.appiconset` including 1024x1024
- **Adaptive icon:** `mipmap-anydpi-v26/rivr.xml` exists (but foreground uses raw icon, not safe-zone version)
- **Launch screens:** Both platforms have launch screen files but reference missing/blank assets

### Created Structure

`release-assets/` directory created at project root with:
- `README.md` — Complete specs for all asset types with dimensions, formats, and generation instructions
- `store-listing-template.md` — Pre-filled metadata templates for both stores
- Organized subdirectories: `google-play/{screenshots/phone,tablet-7,tablet-10,feature-graphic,icon}`, `app-store/{screenshots/iphone-6.7,iphone-6.5,iphone-5.5,ipad-12.9,icon}`, `shared/promotional`

---

## 6. Store Requirements Checklist

### Google Play Store

| Requirement | Status | Notes |
|-------------|--------|-------|
| Developer account ($25) | ? | Verify account exists and is verified |
| App signed with upload key | READY | `rivr-upload-keystore.jks` exists (backed up in Google Drive) |
| Play App Signing enrolled | TODO | Must enroll during first upload |
| AAB format | READY | `make release-android` produces AAB |
| `targetSdkVersion` >= 35 | PASS | Currently 35 (need 36 by Aug 2026) |
| App icon 512x512 no alpha | MISSING | Must generate from source logo |
| Feature graphic 1024x500 | MISSING | Must design |
| Phone screenshots (min 2) | MISSING | Must capture |
| App title (max 30 chars) | TODO | "RIVR" or "RIVR - River Flow Monitor" |
| Short description (max 80 chars) | TODO | Template prepared in `store-listing-template.md` |
| Full description (max 4000 chars) | TODO | Template prepared |
| Privacy policy URL | READY | User confirmed it exists |
| Contact email | TODO | Must provide |
| Content rating (IARC) | TODO | Questionnaire in Play Console |
| Data safety form | TODO | Must declare: location, email, analytics, crash logs, FCM tokens |
| Ads declaration | TODO | Declare "No ads" |
| App access / test credentials | TODO | Must provide Firebase Auth test account |
| Target audience declaration | TODO | General audience (not children) |
| Closed testing (14 days, 12 testers) | ? | Required for new personal accounts (post-Nov 2023) |
| Deobfuscation mapping | TODO | Upload from `build/debug-info/android/` after release build |
| Permissions justification | TODO | Justify location, camera in Play Console |

### Apple App Store

| Requirement | Status | Notes |
|-------------|--------|-------|
| Apple Developer Program ($99/yr) | ? | Verify enrollment |
| Built with Xcode 26 / iOS 26 SDK | TODO | Required starting April 28, 2026 |
| App icon 1024x1024 no alpha | NEEDS FIX | Existing icon has alpha transparency |
| iPhone screenshots (6.7" min) | MISSING | Must capture |
| App name (max 30 chars) | TODO | Must be unique across App Store |
| Subtitle (max 30 chars) | TODO | Template prepared |
| Description (max 4000 chars) | TODO | Template prepared |
| Keywords (max 100 chars) | TODO | Template prepared |
| Privacy policy URL | READY | User confirmed it exists |
| Support URL | TODO | Must provide |
| Copyright text | TODO | e.g., "2026 HydroMap LLC" |
| Contact info for App Review | TODO | Name, phone, email |
| Age rating questionnaire | TODO | Likely 4+ |
| App Privacy labels | TODO | Must declare: location, email, analytics, crash logs, FCM tokens |
| Export compliance (Info.plist) | MISSING | Must add `ITSAppUsesNonExemptEncryption = NO` |
| NSFaceIDUsageDescription | MISSING | Must add to Info.plist |
| Demo account for reviewers | TODO | Must provide Firebase Auth test account |
| Sign in with Apple | ? | Required if Google Sign-In is offered |
| Privacy manifest (.xcprivacy) | ? | Check if included in build |
| iPad screenshots | TODO | Required since app is Universal |
| IPv6 network compatibility | ? | Should work (Flutter/Dart use system networking) |

---

## 7. Roadmap

### Phase 1: Critical Blockers (Must Fix Before Any Submission)

**Priority: IMMEDIATE**

- [ ] **S-1/S-2: Restrict all exposed API keys**
  - Restrict Firebase keys in Google Cloud Console (package name + SHA-1 / bundle ID)
  - Restrict Mapbox token in Mapbox dashboard (app identifiers + usage caps)
  - Consider rotating keys entirely
- [ ] **S-3: Secure `triggerAlertCheck` Cloud Function**
  - Add auth or delete the endpoint
- [ ] **I-1: Add `NSFaceIDUsageDescription` to Info.plist**
  - `"RIVR uses Face ID to quickly and securely sign you in."`
- [ ] **I-2: Add `ITSAppUsesNonExemptEncryption` to Info.plist**
  - Set to `false` (standard HTTPS only)
- [ ] **A-1/A-2: Remove dead Android permissions**
  - Remove `WRITE_EXTERNAL_STORAGE` and `READ_EXTERNAL_STORAGE` from `AndroidManifest.xml`
- [ ] **Fix app icons (alpha transparency)**
  - Re-export iOS 1024.png without alpha channel
  - Generate Google Play 512x512 icon without alpha from source logo

### Phase 2: Store Asset Creation (Required for Submission)

**Priority: HIGH — Blocks submission**

- [ ] Create Google Play feature graphic (1024x500)
- [ ] Capture/design phone screenshots for Google Play (min 2, recommended 4-6)
- [ ] Capture iPhone 6.7" screenshots for App Store
- [ ] Capture iPhone 6.5" screenshots for App Store
- [ ] Decide iPad support: keep Universal or switch to iPhone-only
  - If Universal: capture iPad 12.9" screenshots and verify iPad UI
  - If iPhone-only: change `TARGETED_DEVICE_FAMILY` to `1`
- [ ] Fill out store listing metadata (templates ready in `release-assets/store-listing-template.md`)

### Phase 3: Code Quality & Warnings (Should Fix Before Submission)

**Priority: MEDIUM**

- [ ] **C-1: Add basic accessibility**
  - `semanticLabel` on all `Image.asset()` and `Image.file()` calls
  - `Semantics` wrappers on custom interactive elements
  - Meaningful labels on all buttons
- [ ] **A-3: Remove `SCHEDULE_EXACT_ALARM` permission** (if unused)
- [ ] **A-4: Review `CAMERA` permission** (remove explicit declaration if only used optionally via `image_picker`)
- [ ] **A-5: Create proper adaptive icon foreground** with 108dp safe zone padding
- [ ] **I-3: Fix project-level deployment target** (13.0 -> 16.6)
- [ ] **I-4: Fix LaunchScreen** (add LaunchImage asset or redesign storyboard)
- [ ] **I-5: Add location permission macros to Podfile** (if `permission_handler` handles location)
- [ ] **C-2/A-10: Update pubspec description** from default template text
- [ ] **C-4: Remove unused `flutter_localization`** from pubspec.yaml
- [ ] **A-7: Remove explicit `kotlin-stdlib-jdk8`** dependency
- [ ] Update Makefile `test` target to correct directories

### Phase 4: Store Console Setup (Manual Steps)

**Priority: HIGH — Parallel with Phases 1-3**

- [ ] Verify Google Play Console account (organization + identity verification)
- [ ] Verify Apple Developer Program enrollment
- [ ] Complete Google Play IARC content rating questionnaire
- [ ] Complete Apple age rating questionnaire
- [ ] Complete Google Play Data Safety form
- [ ] Complete Apple App Privacy labels
- [ ] Create test/demo account for store reviewers
- [ ] Prepare reviewer instructions (how to test the app)
- [ ] Declare "No ads" in Google Play Console
- [ ] If offering Google Sign-In, implement Sign in with Apple
- [ ] Check if closed testing is required (personal Google account post-Nov 2023)

### Phase 5: Pre-Submission Verification

**Priority: Before submitting**

- [ ] Run `flutter analyze` — must be zero issues
- [ ] Run `flutter test` — all unit/widget tests must pass
- [ ] Test on real Android device (not just emulator)
- [ ] Test on real iOS device (not just simulator)
- [ ] Verify privacy policy URL is live and accessible
- [ ] Verify support URL is live
- [ ] Test push notifications on both platforms
- [ ] Verify offline behavior gracefully degrades
- [ ] Build release AAB: `make release-android`
- [ ] Build release IPA: `make release-ios`
- [ ] Upload deobfuscation mapping to Play Console
- [ ] Upload dSYM to Firebase Crashlytics (iOS)
- [ ] Final secrets scan: no secrets in staged changes

### Phase 6: Nice-to-Have Improvements

**Priority: LOW — Can ship without these**

- [ ] Add monochrome icon for Android 13+ themed icons
- [ ] Add Firebase App Check
- [ ] Enable GitHub secret scanning
- [ ] Add pre-push git hook for secret detection
- [ ] Consider rewriting git history to remove exposed secrets permanently
- [ ] Fix integration test Firebase initialization
- [ ] Audit empty `setState(() {})` calls
- [ ] Clean up commented-out `print()` in `chart_preview_widget.dart`
- [ ] Update outdated dependencies (non-breaking patches first, then majors)
- [ ] Remove `android.enableJetifier=true` if builds succeed without it
- [ ] Update Google Services plugin to 4.4.x
- [ ] Add `UIRequiredDeviceCapabilities` with `arm64` to Info.plist
- [ ] Recreate LaunchScreen.storyboard in current Xcode
- [ ] Add PrivacyInfo.xcprivacy manifest
- [ ] Add custom FCM notification icon for Android

---

## Appendix A: Remediation Work Completed

The following fixes were applied during this session (not yet committed):

### Phase 1 Critical Fixes (All Done)

| Issue | Status | What was done |
|-------|--------|---------------|
| I-1: NSFaceIDUsageDescription | **FIXED** | Added to `ios/Runner/Info.plist` |
| I-2: ITSAppUsesNonExemptEncryption | **FIXED** | Added `<false/>` to `ios/Runner/Info.plist` |
| A-1: WRITE_EXTERNAL_STORAGE | **FIXED** | Removed from `AndroidManifest.xml` |
| A-2: READ_EXTERNAL_STORAGE | **FIXED** | Removed from `AndroidManifest.xml` |
| A-3: SCHEDULE_EXACT_ALARM | **FIXED** | Removed from `AndroidManifest.xml` |
| S-3: triggerAlertCheck auth | **FIXED** | Added Bearer token auth to `functions/src/index.ts` (also healthCheck) |
| C-1: Accessibility | **FIXED** | Added 62 semantic labels across 38 files (images, icons, interactive elements) |
| Icons alpha transparency | **FIXED** | Flattened all iOS icons (15) + Android mipmap icons (5) onto white background |
| Store icons generated | **DONE** | 512x512 Play Store icon + 1024x1024 App Store icon in `release-assets/` |

### Phase 3 Code Quality Fixes (All Done)

| Issue | Status | What was done |
|-------|--------|---------------|
| pubspec description | **FIXED** | Updated from "A new Flutter project." to proper app description |
| Unused flutter_localization | **FIXED** | Removed from `pubspec.yaml` |
| Kotlin stdlib mismatch | **FIXED** | Removed explicit `kotlin-stdlib-jdk8:1.9.10` from `build.gradle.kts` |
| Makefile test target | **FIXED** | Changed from `test/core test/features test/helpers` to `flutter test` |
| Makefile config path | **FIXED** | Updated comment from `lib/core/config.dart` to correct path |
| iOS deployment target mismatch | **FIXED** | Updated 3 project-level entries from 13.0 to 16.6 in `project.pbxproj` |
| Commented-out prints | **FIXED** | Removed 17 commented-out print statements from `chart_preview_widget.dart` |
| Missing PrivacyInfo.xcprivacy | **FIXED** | Created and added to Xcode project (location, email, crash, device ID, perf data) |

### Verification

- `flutter analyze`: **0 issues**
- `flutter test`: **573 pass / 25 fail** (same as before, all failures are pre-existing integration tests)
- Cloud Functions build: **Clean TypeScript compilation**

### Remaining Work (Requires Manual Action)

| Item | Why it can't be automated |
|------|--------------------------|
| S-1: Restrict Firebase API keys | Requires Google Cloud Console access |
| S-2: Restrict Mapbox tokens | Requires Mapbox dashboard access |
| Store screenshots | Requires running app on device/simulator |
| Feature graphic (1024x500) | Requires graphic design |
| Store listing metadata | Requires business decisions (title, description) |
| Content rating questionnaires | Requires Play Console / App Store Connect |
| Data safety / privacy labels | Requires Play Console / App Store Connect |
| Test account for reviewers | Requires creating a demo Firebase Auth account |
| iPad decision | Requires testing iPad UI or switching to iPhone-only |

---

## Appendix B: Files Changed/Created During This Session

### Source Files Modified:

| File | Changes |
|------|---------|
| `ios/Runner/Info.plist` | Added NSFaceIDUsageDescription, ITSAppUsesNonExemptEncryption |
| `android/app/src/main/AndroidManifest.xml` | Removed 3 dead permissions |
| `pubspec.yaml` | Fixed description, removed unused flutter_localization |
| `android/app/build.gradle.kts` | Removed explicit kotlin-stdlib-jdk8 |
| `Makefile` | Fixed test target + config path comment |
| `ios/Runner.xcodeproj/project.pbxproj` | Fixed deployment target (3 places), added PrivacyInfo.xcprivacy |
| `functions/src/index.ts` | Added auth to triggerAlertCheck + healthCheck |
| `lib/ui/2_presentation/features/forecast/widgets/chart_preview_widget.dart` | Removed 17 commented-out prints |
| 38 files in `lib/ui/` | Added 62 semantic labels for accessibility |

### Asset Files Modified:

| File | Changes |
|------|---------|
| `ios/Runner/Assets.xcassets/AppIcon.appiconset/*.png` (15 files) | Flattened alpha onto white background |
| `android/app/src/main/res/mipmap-*/rivr.png` (5 files) | Flattened alpha onto white background |

### New Files Created:

| File | Purpose |
|------|---------|
| `ios/Runner/PrivacyInfo.xcprivacy` | Apple privacy manifest (location, email, crash data, device ID, perf data) |
| `release-assets/README.md` | Asset specifications and generation instructions |
| `release-assets/store-listing-template.md` | Pre-filled store metadata templates |
| `release-assets/google-play/icon/icon-512x512.png` | Google Play Store icon (512x512, no alpha) |
| `release-assets/app-store/icon/icon-1024x1024.png` | App Store icon (1024x1024, no alpha) |
| `release-assets/google-play/screenshots/phone/.gitkeep` | Directory placeholder |
| `release-assets/google-play/screenshots/tablet-7/.gitkeep` | Directory placeholder |
| `release-assets/google-play/screenshots/tablet-10/.gitkeep` | Directory placeholder |
| `release-assets/google-play/feature-graphic/.gitkeep` | Directory placeholder |
| `release-assets/app-store/screenshots/iphone-6.7/.gitkeep` | Directory placeholder |
| `release-assets/app-store/screenshots/iphone-6.5/.gitkeep` | Directory placeholder |
| `release-assets/app-store/screenshots/iphone-5.5/.gitkeep` | Directory placeholder |
| `release-assets/app-store/screenshots/ipad-12.9/.gitkeep` | Directory placeholder |
| `release-assets/shared/promotional/.gitkeep` | Directory placeholder |
| `docs/audits/2026-04-14-store-release-audit.md` | This audit document |

## Appendix B: Test Results Summary

| Suite | Passed | Failed | Total |
|-------|--------|--------|-------|
| Unit/Widget tests | 573 | 0 | 573 |
| Integration tests | 0 | 25 | 25 |
| **Total** | **573** | **25** | **598** |

- All 25 integration test failures are from missing Firebase initialization (pre-existing issue)
- `flutter analyze`: **0 issues**

## Appendix C: Dependency Health

- **74 upgradable dependencies** detected
- **1 discontinued** transitive dependency (`js` v0.6.7)
- **1 unused** direct dependency (`flutter_localization`)
- **0 known security vulnerabilities** in direct dependencies
- All direct dependencies use stable release versions with caret constraints
