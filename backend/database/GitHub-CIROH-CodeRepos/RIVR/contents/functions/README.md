# RIVR Cloud Functions

Firebase Cloud Functions (1st gen) that power the RIVR push notification system. These functions check users' favorite rivers against NOAA flood thresholds and send FCM alerts when return period thresholds are exceeded.

## Architecture

```
functions/
  src/
    index.ts                -- Function entry points (4 scheduled + 2 HTTPS)
    notification-service.ts -- Core alert logic: user queries, threshold checks, FCM delivery
    noaa-client.ts          -- Server-side NOAA API client (forecasts, return periods, river names)
  lib/                      -- Compiled JS output (gitignored)
  package.json              -- Node.js 22, firebase-functions v6, firebase-admin v12
  tsconfig.json             -- TypeScript config
  eslint.config.mjs         -- ESLint config
```

## Functions

### Scheduled (Pub/Sub cron)

| Function | Schedule | Users Checked |
|----------|----------|---------------|
| `checkRiverAlerts6am` | 6:00 AM MT | All (1x, 2x, 3x, 4x daily) |
| `checkRiverAlerts12pm` | 12:00 PM MT | 3x and 4x daily |
| `checkRiverAlerts6pm` | 6:00 PM MT | 2x, 3x, and 4x daily |
| `checkRiverAlerts12am` | 12:00 AM MT | 4x daily only |

### HTTPS Endpoints

| Function | URL | Auth | Purpose |
|----------|-----|------|---------|
| `healthCheck` | `.../healthCheck` | Public | System status |
| `triggerAlertCheck` | `.../triggerAlertCheck` | Authenticated | Manual test trigger (POST `{"slot": 1}`) |

Base URL: `https://us-central1-ciroh-rivr-app.cloudfunctions.net`

## How Alert Checking Works

1. Query Firestore `users` collection for users with `enableNotifications == true` and `notificationFrequency >= minFrequency` for the time slot
2. For each user's `favoriteReachIds`, fetch in parallel:
   - Short-range and medium-range forecasts from NOAA API (values in CFS)
   - Return period thresholds from CIROH NWM API (values in CMS)
3. Find the max forecast flow across short + medium range
4. Convert forecast CFS to CMS and compare against return period thresholds (2, 5, 10, 25, 50, 100-year)
5. If the highest exceeded threshold is found, send an FCM push notification
6. Log sent notifications to `notification_logs` collection to avoid duplicate alerts within 6 hours

## Setup & Development

### Prerequisites

- Node.js 22
- Firebase CLI (`npm install -g firebase-tools`)
- Authenticated with Firebase (`firebase login`)

### Install & Build

```bash
cd functions
npm install
npm run build        # Compile TypeScript
npm run lint         # Run ESLint
```

### Local Development

```bash
npm run serve        # Build + start Firebase emulator
npm run build:watch  # Watch mode for TypeScript
```

### Deploy

```bash
firebase deploy --only functions --force
```

### View Logs

```bash
firebase functions:log
# or
gcloud functions logs read <functionName> --region=us-central1 --project=ciroh-rivr-app
```

### Test Endpoints

```bash
# Health check (public)
curl https://us-central1-ciroh-rivr-app.cloudfunctions.net/healthCheck

# Manual alert trigger (requires authentication)
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"slot": 1}' \
  https://us-central1-ciroh-rivr-app.cloudfunctions.net/triggerAlertCheck
```

## Firestore Dependencies

### Collections

| Collection | Used For |
|------------|----------|
| `users` | Read user settings: `enableNotifications`, `notificationFrequency`, `favoriteReachIds`, `fcmToken`, `preferredFlowUnit` |
| `notification_logs` | Write sent notification records to prevent duplicate alerts (6-hour dedup window) |

### Required Composite Index

The `users` collection requires a composite index for the notification query:

| Collection | Fields | Order |
|------------|--------|-------|
| `users` | `enableNotifications` ASC, `notificationFrequency` ASC | Ascending |

Create manually if needed:
```bash
gcloud firestore indexes composite create \
  --project=ciroh-rivr-app \
  --collection-group=users \
  --field-config field-path=enableNotifications,order=ASCENDING \
  --field-config field-path=notificationFrequency,order=ASCENDING
```

## External APIs

| API | Base URL | Data | Units |
|-----|----------|------|-------|
| NOAA NWPS | `https://api.water.noaa.gov/nwps/v1` | Streamflow forecasts, river names | CFS (ft³/s) |
| CIROH NWM | `https://nwm-api.ciroh.org/return-period` | Return period flood thresholds | CMS (m³/s) |

The CIROH NWM API requires an API key configured in `noaa-client.ts`.

## GCP IAM Requirements

Deployment and runtime require specific IAM roles on two service accounts. **Do not remove these roles** or deployments/functions will break.

### Compute Engine Default Service Account

`359266072243-compute@developer.gserviceaccount.com`

Used by Cloud Build to build and deploy function containers.

| Role | Purpose |
|------|---------|
| `roles/storage.objectViewer` | Read function source code from GCS during build |
| `roles/artifactregistry.writer` | Push built container images to Artifact Registry |
| `roles/logging.logWriter` | Write build logs to Cloud Logging (essential for debugging failed builds) |

### App Engine Default Service Account

`ciroh-rivr-app@appspot.gserviceaccount.com`

Used as the runtime service account for all Cloud Functions.

| Role | Purpose |
|------|---------|
| `roles/datastore.user` | Read/write Firestore (`users`, `notification_logs`) |
| `roles/firebase.sdkAdminServiceAgent` | Firebase Admin SDK operations (FCM push notifications) |

### Deployer Account

The account running `firebase deploy` (e.g., `jersondevs@gmail.com`) needs:

| Role | Purpose |
|------|---------|
| `roles/cloudfunctions.developer` | Deploy and manage Cloud Functions |
| `roles/iam.serviceAccountUser` | Act as service accounts during deployment |

### Granting Roles

```bash
# Example: grant a role to the compute service account
gcloud projects add-iam-policy-binding ciroh-rivr-app \
  --member="serviceAccount:359266072243-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

# Check current roles for a service account
gcloud projects get-iam-policy ciroh-rivr-app \
  --flatten="bindings[].members" \
  --filter="bindings.members:359266072243-compute@developer.gserviceaccount.com" \
  --format="table(bindings.role)"
```

## Troubleshooting

### "Build error details not available"

The Compute Engine service account is missing `roles/logging.logWriter`. Without this role, Cloud Build cannot write logs, making all build failures opaque. Grant the role and redeploy.

### "Build failed" with quick exit (< 1 second build step)

The Compute Engine service account is missing `roles/artifactregistry.writer`. The build completes source fetch but fails immediately when trying to push the container image. Grant the role and redeploy.

### "PERMISSION_DENIED: Missing or insufficient permissions" at runtime

The App Engine service account (`ciroh-rivr-app@appspot.gserviceaccount.com`) is missing Firestore or Firebase Admin access. Grant `roles/datastore.user` and `roles/firebase.sdkAdminServiceAgent`.

### "The query requires an index"

The Firestore composite index on `users` (`enableNotifications` + `notificationFrequency`) hasn't been created. See the [Required Composite Index](#required-composite-index) section above.

### "Access to bucket gcf-sources denied"

The Compute Engine service account is missing `roles/storage.objectViewer`. This prevents Cloud Build from reading the uploaded source code.

### Organization policy blocking all deployments

If all IAM roles are correct but deploys still fail, the GCP organization may have policies restricting Cloud Build. Check organization policies at:
```
https://console.cloud.google.com/iam-admin/orgpolicies?project=ciroh-rivr-app
```
Look for `constraints/iam.allowedPolicyMemberDomains` and related policies. This requires organization admin access to resolve.

## v1 vs v2 (1st Gen vs 2nd Gen)

These functions use **1st generation** (`firebase-functions/v1`). This was chosen because:
- The GCP organization policy was blocking 2nd gen deployments at the time of initial deployment
- 1st gen is fully sufficient for scheduled cron functions and simple HTTPS endpoints
- The same IAM requirements apply to both generations

To upgrade to 2nd gen in the future, change the import to `firebase-functions/v2` and update the function signatures to use `onSchedule` / `onRequest` from `firebase-functions/v2/scheduler` and `firebase-functions/v2/https`.
