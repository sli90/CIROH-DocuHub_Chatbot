# RIVR Release Assets

This directory contains all assets required for publishing RIVR to the Google Play Store and Apple App Store. Each subdirectory corresponds to a specific store and asset type.

## Directory Structure

```
release-assets/
  README.md                          -- This file
  store-listing-template.md          -- Store listing text (descriptions, keywords, etc.)
  google-play/
    screenshots/
      phone/                         -- Phone screenshots (required)
      tablet-7/                      -- 7" tablet screenshots (optional)
      tablet-10/                     -- 10" tablet screenshots (optional)
    feature-graphic/                 -- Feature graphic (required)
    icon/                            -- High-res app icon (required)
  app-store/
    screenshots/
      iphone-6.7/                    -- 6.7" display (required)
      iphone-6.5/                    -- 6.5" display (required)
      iphone-5.5/                    -- 5.5" display (optional, recommended)
      ipad-12.9/                     -- 12.9" iPad Pro (required if supporting iPad)
    icon/                            -- App Store icon (required)
  shared/
    promotional/                     -- Shared promotional images
```

---

## Google Play Store Requirements

### App Icon (`google-play/icon/`)

| Property       | Requirement                           |
|----------------|---------------------------------------|
| Dimensions     | 512 x 512 pixels                      |
| Format         | PNG                                   |
| Color depth    | 32-bit color (RGBA)                   |
| Alpha channel  | No alpha / no transparency            |
| Max file size  | 1024 KB                               |
| Shape          | Full bleed, square; system applies mask|

**File naming:** `icon_512x512.png`

**Notes:**
- Google Play dynamically applies a circular or rounded-square mask depending on device. Design the icon to look good under both masks.
- The icon must fill the entire 512x512 canvas (full bleed). Place important content within the center 384x384 "safe zone" (75% of canvas) to avoid clipping.
- Do not include any transparency or alpha channel. If the source PNG has alpha, flatten it onto a solid background before export.

### Feature Graphic (`google-play/feature-graphic/`)

| Property       | Requirement                           |
|----------------|---------------------------------------|
| Dimensions     | 1024 x 500 pixels                     |
| Format         | PNG or JPEG                           |
| Color depth    | 24-bit (RGB) recommended              |
| Alpha channel  | Not recommended                       |

**File naming:** `feature_graphic_1024x500.png` or `.jpg`

**Notes:**
- **This is required** for Google Play Store listing. The app cannot be published without it.
- This image appears at the top of the store listing page and may appear in promotional placements across Google Play.
- Avoid placing critical text or visuals near the edges; Google may crop or overlay UI elements (e.g., a play button for video previews).
- Design for legibility at small sizes -- it may be shown as a thumbnail.
- Suggested content: app logo/name, representative screenshot or illustration of the map view, NOAA/CIROH branding if appropriate.

### Screenshots (`google-play/screenshots/phone/`)

| Property       | Requirement                           |
|----------------|---------------------------------------|
| Count          | Minimum 2, maximum 8 per device type  |
| Format         | JPEG or PNG (24-bit, no alpha)        |
| Aspect ratio   | 16:9 or 9:16                          |
| Min dimension  | 320 px on shortest side               |
| Max dimension  | 3840 px on longest side               |

**File naming:** `01_favorites_list.png`, `02_map_view.png`, `03_forecast_chart.png`, etc.

**Phone screenshots are required.** Tablet screenshots (7" and 10") are optional but recommended if the app has a tablet-optimized layout.

**Recommended screenshot subjects for RIVR:**
1. Favorites list showing saved rivers with current flow and risk status
2. Interactive map with river reach selection
3. Forecast detail page with flow chart and return period thresholds
4. Short/medium/long range forecast comparison
5. Flood risk indicators and return period visualization
6. Settings or onboarding screen

**Recommended dimensions for phone screenshots:**
- Portrait: 1080 x 1920 (Full HD) or 1440 x 2560 (QHD)
- Landscape: 1920 x 1080 or 2560 x 1440

### Tablet Screenshots (Optional)

| Directory      | Device              | Recommended Dimensions |
|----------------|---------------------|------------------------|
| `tablet-7/`    | 7" tablet           | 1200 x 1920 portrait   |
| `tablet-10/`   | 10" tablet          | 1600 x 2560 portrait   |

---

## Apple App Store Requirements

### App Icon (`app-store/icon/`)

| Property       | Requirement                           |
|----------------|---------------------------------------|
| Dimensions     | 1024 x 1024 pixels                    |
| Format         | PNG                                   |
| Color space    | sRGB or Display P3                    |
| Alpha channel  | No alpha / no transparency            |
| Rounded corners| No -- the system applies rounding     |
| Layers/effects | No layers, no transparency            |
| Max file size  | None specified, but keep reasonable   |

**File naming:** `icon_1024x1024.png`

**Notes:**
- Apple automatically applies rounded corners, so provide a square image with sharp corners.
- The icon must not contain any transparency; the entire canvas must be filled.
- The same 1024x1024 icon is used for both the App Store listing and (since Xcode 14+) can be the single source icon for the app itself.
- This is separate from the in-app icons in `ios/Runner/Assets.xcassets/AppIcon.appiconset/`, which are already in place.

### Screenshots

Screenshots are **required** for at least the 6.7" and 6.5" iPhone display sizes. iPad screenshots are required if the app declares iPad support.

#### iPhone 6.7" Display (`app-store/screenshots/iphone-6.7/`) -- REQUIRED

| Property       | Requirement                                |
|----------------|--------------------------------------------|
| Devices        | iPhone 16 Pro Max, iPhone 15 Pro Max, etc. |
| Dimensions     | 1290 x 2796 (portrait) or 2796 x 1290 (landscape) |
| Format         | PNG or JPEG                                |
| Color space    | sRGB or Display P3                         |
| Count          | Minimum 1, maximum 10                      |

#### iPhone 6.5" Display (`app-store/screenshots/iphone-6.5/`) -- REQUIRED

| Property       | Requirement                                |
|----------------|--------------------------------------------|
| Devices        | iPhone 14 Plus, iPhone 13 Pro Max, etc.    |
| Dimensions     | 1284 x 2778 (portrait) or 2778 x 1284 (landscape) |
| Format         | PNG or JPEG                                |
| Color space    | sRGB or Display P3                         |
| Count          | Minimum 1, maximum 10                      |

#### iPhone 5.5" Display (`app-store/screenshots/iphone-5.5/`) -- Optional, Recommended

| Property       | Requirement                                |
|----------------|--------------------------------------------|
| Devices        | iPhone 8 Plus, iPhone 7 Plus, etc.         |
| Dimensions     | 1242 x 2208 (portrait) or 2208 x 1242 (landscape) |
| Format         | PNG or JPEG                                |
| Color space    | sRGB or Display P3                         |
| Count          | Minimum 1, maximum 10                      |

#### iPad Pro 12.9" (`app-store/screenshots/ipad-12.9/`) -- Required if supporting iPad

| Property       | Requirement                                |
|----------------|--------------------------------------------|
| Devices        | iPad Pro 12.9" (6th gen and later)         |
| Dimensions     | 2048 x 2732 (portrait) or 2732 x 2048 (landscape) |
| Format         | PNG or JPEG                                |
| Color space    | sRGB or Display P3                         |
| Count          | Minimum 1, maximum 10                      |

**File naming:** `01_favorites_list.png`, `02_map_view.png`, `03_forecast_chart.png`, etc.

**Notes:**
- App Store Connect allows you to use 6.7" screenshots for 6.5" if they are similar enough. But for best results, provide separate sets.
- Screenshots can include device frames and marketing text overlays. If using frames, match the frame to the target device class.
- If the app supports both orientations, you can mix portrait and landscape screenshots.

---

## Generating Screenshots

### Option 1: Manual Capture

Run the app on a simulator matching the target device and use the simulator's screenshot function:
- **iOS Simulator:** Cmd+S or File > Save Screen
- **Android Emulator:** Camera icon in the toolbar

Recommended simulators:
- iPhone 15 Pro Max (6.7" -- 1290x2796)
- iPhone 14 Plus (6.5" -- 1284x2778)
- iPhone 8 Plus (5.5" -- 1242x2208)
- iPad Pro 12.9" (2048x2732)
- Pixel 7 Pro or similar (1440x3120 or 1080x2400)

### Option 2: Flutter Integration Test Screenshots

Use `integration_test` with the `IntegrationTestWidgetsFlutterBinding` to capture screenshots programmatically:

```dart
import 'package:integration_test/integration_test.dart';

void main() {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('capture favorites page screenshot', (tester) async {
    // Launch app and navigate to desired screen
    app.main();
    await tester.pumpAndSettle();

    // Capture
    await binding.convertFlutterSurfaceToImage();
    await tester.pumpAndSettle();
    await binding.takeScreenshot('01_favorites_list');
  });
}
```

### Option 3: Fastlane Screengrab / Snapshot

- **Android:** [fastlane screengrab](https://docs.fastlane.tools/actions/screengrab/) -- automated screenshot capture on multiple devices/locales.
- **iOS:** [fastlane snapshot](https://docs.fastlane.tools/actions/snapshot/) -- uses UI tests to capture screenshots.

### Option 4: Third-Party Framing Tools

After capturing raw screenshots, use these tools to add device frames and marketing text:
- [Screenshots.pro](https://screenshots.pro) -- web-based, supports both stores
- [LaunchMatic](https://launchmatic.app) -- macOS app
- [Previewed](https://previewed.app) -- mockup generator
- [AppMockUp](https://app-mockup.com) -- free online tool

---

## File Naming Conventions

Use zero-padded numbers to control ordering, followed by a descriptive name:

```
01_favorites_list.png
02_map_view.png
03_forecast_detail.png
04_risk_assessment.png
05_short_range_forecast.png
06_settings.png
```

- Use lowercase with underscores
- PNG preferred for screenshots with text; JPEG acceptable for photo-heavy content
- Keep file sizes reasonable (under 5 MB each for screenshots)

---

## Current Asset Status

### What Exists

| Asset                              | Status | Location                                       | Notes                     |
|------------------------------------|--------|-------------------------------------------------|---------------------------|
| Android launcher icons (mipmap)    | Done   | `android/app/src/main/res/mipmap-*/rivr.png`   | All 5 densities present   |
| Android adaptive icon XML          | Done   | `android/app/src/main/res/mipmap-anydpi-v26/`  | White background + foreground |
| iOS app icons (all sizes)          | Done   | `ios/Runner/Assets.xcassets/AppIcon.appiconset/`| 15 sizes, 20px to 1024px  |
| iOS 1024px marketing icon          | Done   | Same as above, `1024.png`                       | Has alpha -- needs fix    |
| High-res source logo               | Done   | `assets/images/rivr_logo.png`                   | 2048x2048, has alpha      |
| Old logo                           | Done   | `assets/images/rivr_logo-old.png`               | 1024x1024, deprecated     |
| Onboarding SVGs                    | Done   | `assets/images/onboarding/`                     | 4 illustrations           |
| River background images            | Done   | `assets/images/rivers/`                         | 24 webp images (4 categories) |
| Sponsor logos                      | Done   | `assets/images/sponsors/`                       | NOAA, CIROH, BYU, UA, OWP |
| Risk level videos                  | Done   | `assets/videos/`                                | 6 MP4 risk animations     |
| Android launch screen              | Partial| `android/app/src/main/res/drawable/`            | Default white, no custom image |
| iOS launch screen                  | Partial| `ios/Runner/Base.lproj/LaunchScreen.storyboard` | References LaunchImage but no image asset exists |

### What Is Missing

| Asset                              | Priority | Notes                                        |
|------------------------------------|----------|----------------------------------------------|
| Google Play 512x512 icon (no alpha)| High     | Source logo is 2048x2048 with alpha -- must flatten and resize |
| Google Play feature graphic        | High     | 1024x500, required for Play Store listing    |
| App Store 1024x1024 icon (no alpha)| High     | Existing 1024.png has alpha -- must flatten   |
| Phone screenshots (both stores)    | High     | None exist; need minimum 2 for Play, 1+ for App Store |
| iPhone 6.7" screenshots            | High     | Required for App Store                       |
| iPhone 6.5" screenshots            | High     | Required for App Store                       |
| iPhone 5.5" screenshots            | Medium   | Optional but recommended                    |
| iPad 12.9" screenshots             | Medium   | Required only if iPad is supported           |
| Tablet screenshots                 | Low      | Optional for Play Store                      |
| Promotional images                 | Low      | Nice to have for marketing                   |

### Known Issues

1. **iOS 1024px icon has alpha channel.** Apple will reject this during submission. The icon at `ios/Runner/Assets.xcassets/AppIcon.appiconset/1024.png` must be re-exported without alpha/transparency.
2. **Android icons have alpha channel.** The mipmap PNGs have alpha. Google Play requires the 512x512 store icon to have no alpha. Generate a flattened version for the store.
3. **Source logo has alpha.** `assets/images/rivr_logo.png` (2048x2048) has an alpha channel. Use this as the source but flatten onto the app's background color (white or brand color) when generating store icons.
4. **iOS LaunchScreen references a missing image.** The storyboard references a `LaunchImage` asset, but no `LaunchImage.imageset` exists in `Assets.xcassets`. This means the iOS launch screen shows a blank white view.

---

## Quick-Start Checklist

- [ ] Flatten `assets/images/rivr_logo.png` onto a solid background (remove alpha)
- [ ] Export 512x512 PNG (no alpha) to `google-play/icon/icon_512x512.png`
- [ ] Export 1024x1024 PNG (no alpha) to `app-store/icon/icon_1024x1024.png`
- [ ] Replace `ios/Runner/Assets.xcassets/AppIcon.appiconset/1024.png` with the no-alpha version
- [ ] Design and export feature graphic (1024x500) to `google-play/feature-graphic/`
- [ ] Capture phone screenshots on iPhone 15 Pro Max simulator (1290x2796)
- [ ] Capture phone screenshots on iPhone 14 Plus simulator (1284x2778)
- [ ] Copy/resize phone screenshots for Google Play (1080x1920 or 1440x2560)
- [ ] Fill in `store-listing-template.md` with final copy
- [ ] If supporting iPad, capture iPad Pro 12.9" screenshots (2048x2732)
