# RIVR Architecture Guide: Models → Services → UI

> A practical guide to RIVR's target architecture using clean architecture with horizontal and vertical organization. Adapted from the Oqupa Flutter Architecture Guide for RIVR's domain: river flow monitoring, NOAA National Water Model data, and flood risk assessment.

---

## Table of Contents

1. [Understanding the Philosophy](#understanding-the-philosophy)
2. [The Complete Structure](#the-complete-structure)
3. [Models Layer: What RIVR Is About](#models-layer-what-rivr-is-about)
4. [Services Layer: How Data Flows](#services-layer-how-data-flows)
5. [UI Layer: How Users Interact](#ui-layer-how-users-interact)
6. [Utilities: Cross-Cutting Helpers](#utilities-cross-cutting-helpers)
7. [Shared vs Features Organization](#shared-vs-features-organization)
8. [Dependency Flow and Import Rules](#dependency-flow-and-import-rules)
9. [Error Handling: The ServiceResult Pattern](#error-handling-the-serviceresult-pattern)
10. [Dependency Injection: Two-Phase Wiring](#dependency-injection-two-phase-wiring)
11. [Cross-Feature Communication](#cross-feature-communication)
12. [Testing Structure](#testing-structure)
13. [Development Order: Horizontal Foundation, Vertical Features](#development-order-horizontal-foundation-vertical-features)
14. [RIVR-Specific Decisions](#rivr-specific-decisions)
15. [When to Break the Rules](#when-to-break-the-rules)

---

## Understanding the Philosophy

This architecture organizes RIVR around three fundamental concerns:

- **Models** — *What* RIVR is about in pure business terms (reaches, forecasts, flow categories, return periods)
- **Services** — *How* data moves in and out of RIVR (NOAA API, Firebase, local cache, Mapbox)
- **UI** — *How* users interact with RIVR (favorites list, forecast charts, interactive map)

Each layer has a single direction of dependency: **Models know nothing about Services or UI. Services know nothing about UI.**

The architecture uses two organizational axes simultaneously:

- **Horizontal (layers):** The numbered folders (`1_domain/`, `2_usecases/`, `1_contracts/`, etc.) that enforce dependency direction
- **Vertical (features):** The `shared/` and `features/` folders within each layer that group code by business capability

This dual-axis approach avoids the false choice between "feature-first" and "layer-first" organization. You get both.

---

## The Complete Structure

```
lib/
├── models/
│   ├── 1_domain/
│   │   ├── shared/
│   │   │   └── entities/           # ReachData, FavoriteRiver, UserSettings, ForecastResponse
│   │   └── features/
│   │       └── forecast/
│   │           └── entities/       # DailyFlowForecast, DailyForecastCollection
│   └── 2_usecases/
│       └── features/
│           ├── auth/               # SignInUseCase, SignUpUseCase, etc.
│           ├── favorites/          # AddFavoriteUseCase, RefreshFavoriteFlowUseCase, etc.
│           ├── forecast/           # LoadForecastOverviewUseCase, RefreshForecastUseCase, etc.
│           ├── map/                # GetReachDetailsForMapUseCase
│           └── settings/           # UpdateFlowUnitUseCase, SyncSettingsAfterLoginUseCase, etc.
│
├── services/
│   ├── 0_config/
│   │   └── shared/                 # API endpoints, environment, Mapbox config
│   ├── 1_contracts/
│   │   └── features/
│   │       ├── auth/               # IAuthRepository
│   │       ├── favorites/          # IFavoritesRepository
│   │       ├── forecast/           # IForecastRepository
│   │       └── settings/           # ISettingsRepository
│   ├── 2_coordinators/
│   │   └── features/
│   │       ├── auth/               # AuthRepositoryImpl
│   │       ├── favorites/          # FavoritesRepositoryImpl
│   │       ├── forecast/           # ForecastRepositoryImpl (caching, phased loading)
│   │       └── settings/           # SettingsRepositoryImpl
│   ├── 3_datasources/
│   │   └── features/
│   │       ├── auth/               # AuthFirebaseDatasource, BiometricDatasource
│   │       ├── favorites/          # FavoritesFirestoreDatasource
│   │       ├── forecast/           # ForecastApiDatasource, ForecastCacheDatasource
│   │       └── settings/           # SettingsFirestoreDatasource, SettingsLocalDatasource
│   ├── 4_infrastructure/
│   │   ├── auth/                   # Firebase Auth wrapper, biometric local_auth
│   │   ├── firebase/               # Firestore client, Cloud Messaging
│   │   ├── http/                   # HTTP client, retry logic, timeout tiers
│   │   ├── local_storage/          # File-based cache, SharedPreferences, secure storage
│   │   ├── map/                    # Mapbox SDK, geocoding, vector tiles
│   │   ├── notifications/          # FCM token management, local notifications
│   │   └── shared/                 # ServiceResult, ServiceException, AppLogger
│   └── 5_injection/
│       ├── dependency_container.dart
│       └── features/
│           ├── auth/               # AuthDependencies
│           ├── favorites/          # FavoritesDependencies
│           ├── forecast/           # ForecastDependencies
│           ├── map/                # MapDependencies
│           └── settings/           # SettingsDependencies
│
├── ui/
│   ├── 1_state/
│   │   ├── shared/
│   │   │   ├── connectivity_provider.dart
│   │   │   └── theme_provider.dart
│   │   └── features/
│   │       ├── auth/               # AuthProvider
│   │       ├── favorites/          # FavoritesProvider
│   │       └── forecast/           # ReachDataProvider
│   └── 2_presentation/
│       ├── shared/
│       │   ├── widgets/            # NavigationButton, shimmer cards, etc.
│       │   ├── dialogs/            # Confirmation dialogs, error dialogs
│       │   └── theme/              # ThemeData, colors, text styles
│       ├── features/
│       │   ├── auth/
│       │   │   ├── pages/          # AuthCoordinator
│       │   │   └── widgets/        # LoginForm, SignUpForm, etc.
│       │   ├── favorites/
│       │   │   ├── pages/          # FavoritesPage
│       │   │   └── widgets/        # FavoriteRiverCard, shimmer, etc.
│       │   ├── forecast/
│       │   │   ├── pages/          # ReachOverviewPage
│       │   │   └── widgets/        # DailyExpandable, ChartPreview, HourlyDisplay, etc.
│       │   ├── map/
│       │   │   ├── pages/          # MapPage
│       │   │   └── widgets/        # MapControls, SearchBar, ReachInfo, etc.
│       │   ├── onboarding/
│       │   │   ├── pages/          # OnboardingPage
│       │   │   └── widgets/
│       │   └── settings/
│       │       ├── pages/          # SettingsPage
│       │       └── widgets/        # FlowUnitPicker, NotificationSettings, etc.
│       └── routing/
│           ├── app_router.dart
│           └── app_routes.dart
│
├── utils/
│   ├── flow_formatter.dart         # CFS/CMS formatting
│   ├── date_formatter.dart         # Forecast date display
│   └── validators/                 # Email, reach ID validation
│
└── main.dart
```

### Why Numbered Folders?

IDEs sort folders alphabetically. The numbered prefixes (`0_config`, `1_contracts`, `2_coordinators`...) ensure the architectural hierarchy is **visually apparent** in your file explorer. A developer opening the project for the first time sees the layers in dependency order without reading any documentation.

---

## Models Layer: What RIVR Is About

The models layer contains RIVR's pure business concepts. Nothing in this layer knows about Flutter, Firebase, HTTP, or any external framework. If you removed every other layer, these classes would still compile as pure Dart.

### Domain Entities (`1_domain/`)

Domain entities represent the real-world objects RIVR cares about without any technical implementation details. A `ReachData` entity knows about river names, coordinates, and return period thresholds. It has no knowledge of JSON, NOAA API response formats, or Firestore documents.

**`shared/entities/`** contains entities referenced across multiple features:

```
1_domain/shared/entities/
├── reach_data.dart             # River reach: ID, name, location, return periods
├── favorite_river.dart         # A user's saved reach with custom name
├── user_settings.dart          # Preferences: flow unit, notifications, background
└── forecast_response.dart      # Wrapper for forecast data by type
```

**`features/`** contains entities specific to individual features:

```
1_domain/features/
└── forecast/
    └── entities/
        ├── daily_flow_forecast.dart       # Aggregated daily forecast with hourly data
        └── daily_forecast_collection.dart # Collection with date range operations
```

**Key principles:**
- Zero Flutter imports. Zero package imports. Pure Dart only.
- Entities are immutable. Use `copyWith()` for updates.
- Domain methods express business concepts, not technical operations.

**Example — pure domain entity:**

```dart
class DailyFlowForecast {
  final DateTime date;
  final double minFlow;
  final double maxFlow;
  final double avgFlow;
  final Map<DateTime, double> hourlyData;
  final String flowCategory;  // 'Normal', 'Elevated', 'High', 'Flood Risk'
  final String dataSource;

  const DailyFlowForecast({
    required this.date,
    required this.minFlow,
    required this.maxFlow,
    required this.avgFlow,
    required this.hourlyData,
    required this.flowCategory,
    required this.dataSource,
  });
}
```

This entity knows what a daily forecast *is* — flows, categories, time ranges. It doesn't know where the data came from (NOAA API? cache? mock?) or how it will be displayed (chart? card? table?).

**What changes from today:** `ReachData` currently has `fromNoaaApi()`, `fromReturnPeriodApi()`, `fromJson()`, and `toJson()` alongside domain methods. In the target architecture, parsing lives in datasources and DTOs — the entity is pure.

### Use Cases (`2_usecases/`)

Use cases contain RIVR's application-specific business logic. They orchestrate the flow of data between entities and define the policies the app follows.

A well-written use case typically:

1. **Validates input** — fast-fail on invalid reach IDs or parameters
2. **Applies business rules** — determine if cached data is sufficient, check flow thresholds
3. **Coordinates operations** — call one or more repository contracts
4. **Maps errors** — translate technical failures into user-friendly messages

```dart
class LoadForecastOverviewUseCase {
  final IForecastRepository _repository;

  const LoadForecastOverviewUseCase(this._repository);

  Future<ServiceResult<ForecastResponse>> call(String reachId) async {
    // 1. Validate input
    if (reachId.isEmpty) {
      return ServiceResult.failure(
        ServiceException.validation('Reach ID cannot be empty'),
      );
    }

    // 2. Coordinate — delegate to repository contract
    return _repository.loadOverview(reachId);
  }
}
```

**Organization:** Use cases live in `features/` only:

```
2_usecases/features/
├── auth/
│   ├── sign_in_usecase.dart
│   ├── sign_up_usecase.dart
│   ├── sign_out_usecase.dart
│   ├── reset_password_usecase.dart
│   ├── get_auth_state_usecase.dart
│   ├── sign_in_with_biometrics_usecase.dart
│   ├── enable_biometric_usecase.dart
│   └── disable_biometric_usecase.dart
├── favorites/
│   ├── initialize_favorites_usecase.dart
│   ├── add_favorite_usecase.dart
│   ├── remove_favorite_usecase.dart
│   ├── update_favorite_usecase.dart
│   ├── reorder_favorites_usecase.dart
│   ├── refresh_all_favorites_usecase.dart
│   └── refresh_favorite_flow_usecase.dart
├── forecast/
│   ├── load_forecast_overview_usecase.dart
│   ├── load_forecast_supplementary_usecase.dart
│   ├── load_complete_forecast_usecase.dart
│   ├── refresh_forecast_usecase.dart
│   └── get_reach_details_usecase.dart
├── map/
│   └── get_reach_details_for_map_usecase.dart
└── settings/
    ├── get_user_settings_usecase.dart
    ├── update_flow_unit_usecase.dart
    ├── update_notifications_usecase.dart
    ├── update_notification_frequency_usecase.dart
    └── sync_settings_after_login_usecase.dart
```

**Pattern:** Each use case class has a single `call()` method returning `ServiceResult<T>`. One class, one method, one responsibility.

---

## Services Layer: How Data Flows

The services layer manages everything between RIVR's business logic and the outside world: configuration, interfaces, data coordination, external APIs, and wiring.

### Configuration (`0_config/`)

Configuration manages environment-specific settings: NOAA API endpoints, Mapbox token references, Firebase project IDs, and NWM API URLs.

```
0_config/shared/
├── app_config.dart             # API base URLs, vector tileset IDs
├── app_environment.dart        # Dev vs Production (future)
└── mapbox_config.dart          # Mapbox token, style URLs
```

Configuration is always `shared/` — features don't have their own config files. The existing `config.dart` (gitignored) maps into this layer.

### Contracts (`1_contracts/`)

Contracts define the interfaces that RIVR's use cases need from the data layer without specifying how those needs are fulfilled. These abstract classes are the agreements between business logic and data.

```dart
abstract class IForecastRepository {
  Future<ServiceResult<ForecastResponse>> loadOverview(String reachId);
  Future<ServiceResult<ForecastResponse>> loadSupplementary(
    String reachId,
    ForecastResponse existingData,
  );
  Future<ServiceResult<ForecastResponse>> loadComplete(String reachId);
  Future<ServiceResult<ForecastResponse>> refresh(String reachId);
  Future<ServiceResult<ReachDetailsData>> getReachDetails(String reachId);
}
```

A contract specifies *what* the app needs (load forecast overview, refresh a reach) but not *how* (NOAA HTTP call, local file cache, in-memory response cache). This is what makes business logic testable — tests mock the contract, not the NOAA API.

```
1_contracts/features/
├── auth/
│   └── i_auth_repository.dart
├── favorites/
│   └── i_favorites_repository.dart
├── forecast/
│   └── i_forecast_repository.dart
└── settings/
    └── i_settings_repository.dart
```

### Coordinators (`2_coordinators/`)

Coordinators **implement the contracts**. They make strategic decisions about:

- **Caching** — check the local file cache before hitting NOAA
- **Phased loading** — load overview data first, then supplementary, then complete
- **Offline behavior** — return cached reach data when network is unavailable
- **Error handling** — wrap NOAA timeouts in user-meaningful errors

```dart
class ForecastRepositoryImpl implements IForecastRepository {
  final ForecastApiDatasource _apiDatasource;
  final ForecastCacheDatasource _cacheDatasource;

  // In-memory response cache (5-min TTL, max 10 entries)
  final Map<String, _TimedEntry<ForecastResponse>> _responseCache = {};
  static const _responseCacheTtl = Duration(minutes: 5);
  static const _responseCacheMaxSize = 10;

  @override
  Future<ServiceResult<ForecastResponse>> loadOverview(String reachId) async {
    // 1. Check in-memory cache (rapid re-taps)
    final memCached = _responseCache[reachId];
    if (memCached != null && !memCached.isExpiredAfter(_responseCacheTtl)) {
      return ServiceResult.success(memCached.value);
    }

    // 2. Check disk cache (stale-while-revalidate)
    final diskResult = await _cacheDatasource.getCachedReach(reachId);
    if (diskResult.isSuccess && diskResult.data!.isFresh) {
      return ServiceResult.success(diskResult.data!.forecast);
    }

    // 3. Fetch from NOAA API
    final apiResult = await _apiDatasource.fetchOverview(reachId);
    if (apiResult.isSuccess) {
      _responseCache[reachId] = _TimedEntry(apiResult.data!);
      await _cacheDatasource.cacheReach(reachId, apiResult.data!);
    }

    // 4. Fall back to stale cache if API fails
    if (apiResult.isFailure && diskResult.isSuccess) {
      return ServiceResult.success(diskResult.data!.forecast);
    }

    return apiResult;
  }
}
```

**Cache invalidation strategy:**
- After `refresh()`, clear the in-memory entry for that reach and force a fresh API call
- `forceRefresh: true` bypasses all caches (used on pull-to-refresh)
- File cache uses 6-hour freshness / 180-day hard eviction
- In-memory cache has a 10-entry ceiling with 5-minute TTL

Coordinators contain the data flow strategy but delegate actual retrieval to datasources.

### Data Sources (`3_datasources/`)

Data sources handle the **actual mechanics** of retrieving and storing data from specific systems. Each datasource talks to exactly one external system.

```dart
class ForecastApiDatasource {
  final HttpClient _client;

  /// Fetch overview data (short-range forecast + current flow) from NOAA.
  Future<ServiceResult<ForecastResponse>> fetchOverview(String reachId) async {
    try {
      final response = await _client.getWithRetry(
        '${AppConfig.noaaBaseUrl}/reaches/$reachId/streamflow',
        timeout: const Duration(seconds: 15),
      );
      final data = ForecastResponseDto.fromNoaaApi(response.body);
      return ServiceResult.success(data.toEntity());
    } on TimeoutException {
      return ServiceResult.failure(
        ServiceException.network('NOAA API timed out loading reach $reachId'),
      );
    } on FormatException catch (e) {
      return ServiceResult.failure(
        ServiceException.unknown('Failed to parse NOAA response: $e'),
      );
    }
  }
}
```

Datasources focus purely on technical concerns — HTTP requests, Firestore queries, file I/O. They make **no business decisions** about when or why to use the data.

```
3_datasources/features/
├── auth/
│   ├── auth_firebase_datasource.dart     # Firebase Auth SDK calls
│   └── biometric_datasource.dart         # local_auth + secure storage
├── favorites/
│   └── favorites_firestore_datasource.dart
├── forecast/
│   ├── forecast_api_datasource.dart      # NOAA HTTP calls
│   └── forecast_cache_datasource.dart    # File-based JSON cache
└── settings/
    ├── settings_firestore_datasource.dart
    └── settings_local_datasource.dart    # SharedPreferences for local prefs
```

### Infrastructure (`4_infrastructure/`)

Infrastructure manages low-level technical concerns and external service integrations. Organized by **technical domain**, not business feature:

```
4_infrastructure/
├── auth/                   # Firebase Auth wrapper
├── firebase/               # Firestore client, Cloud Functions
├── http/                   # HTTP client with retry, timeout tiers
├── local_storage/          # File-based cache, SharedPreferences, secure storage
├── map/                    # Mapbox SDK, geocoding, vector tiles
├── notifications/          # FCM token management
└── shared/                 # ServiceResult, ServiceException, AppLogger
```

Multiple features use Firebase. Multiple features need HTTP. Grouping by technical domain avoids duplication and makes it easy to swap providers.

The `shared/` folder holds the foundational pieces: the `ServiceResult` wrapper, base exception classes, the `AppLogger`, and network utilities.

### Dependency Injection (`5_injection/`)

Dependency injection configures and wires together all components.

```
5_injection/
├── dependency_container.dart       # Orchestrates registration order
└── features/
    ├── auth/
    │   └── auth_dependencies.dart
    ├── favorites/
    │   └── favorites_dependencies.dart
    ├── forecast/
    │   └── forecast_dependencies.dart
    ├── map/
    │   └── map_dependencies.dart
    └── settings/
        └── settings_dependencies.dart
```

Each feature has its own registration file. The central `dependency_container.dart` calls them in the correct order (see [Two-Phase Wiring](#dependency-injection-two-phase-wiring)).

---

## UI Layer: How Users Interact

### State Management (`1_state/`)

RIVR uses **Provider with ChangeNotifier** for state management. Providers coordinate between the UI and use cases, translating user actions into use case calls and transforming results into states suitable for display.

```dart
class FavoritesProvider with ChangeNotifier {
  final InitializeFavoritesUseCase _initializeUseCase;
  final AddFavoriteUseCase _addFavoriteUseCase;
  final RemoveFavoriteUseCase _removeFavoriteUseCase;
  final RefreshFavoriteFlowUseCase _refreshFlowUseCase;

  List<FavoriteRiver> _favorites = [];
  bool _isLoading = false;
  String? _errorMessage;

  // Expose immutable state to UI
  List<FavoriteRiver> get favorites => List.unmodifiable(_favorites);
  bool get isLoading => _isLoading;
  bool get isEmpty => _favorites.isEmpty;
  String? get errorMessage => _errorMessage;

  Future<void> initialize(String userId) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    final result = await _initializeUseCase.call(userId);
    if (result.isSuccess) {
      _favorites = result.data!;
    } else {
      _errorMessage = result.errorMessage;
    }
    _isLoading = false;
    notifyListeners();
  }

  Future<void> addFavorite(String reachId) async {
    final result = await _addFavoriteUseCase.call(reachId);
    if (result.isSuccess) {
      _favorites = [..._favorites, result.data!];
      notifyListeners();
    }
  }
}
```

**Key pattern:** Providers receive use cases via DI and expose simple loading/error/data states. They contain no business logic — that lives in use cases and coordinators.

```
1_state/
├── shared/
│   ├── connectivity_provider.dart
│   └── theme_provider.dart
└── features/
    ├── auth/
    │   └── auth_provider.dart
    ├── favorites/
    │   └── favorites_provider.dart
    └── forecast/
        └── reach_data_provider.dart
```

### Presentation (`2_presentation/`)

The presentation layer contains RIVR's screens, widgets, dialogs, and visual elements. This layer focuses purely on user experience **without containing business logic**.

Presentation components:
- Read state from providers via `context.watch<FavoritesProvider>()`
- Call provider methods on user actions
- Handle only visual concerns (layout, animation, styling)

```
2_presentation/
├── shared/
│   ├── widgets/            # Reusable: shimmer cards, navigation buttons, etc.
│   ├── dialogs/            # Confirmation, error, info dialogs
│   └── theme/              # CupertinoThemeData, colors, text styles
├── features/
│   ├── auth/
│   │   ├── pages/          # AuthCoordinator (auth state routing)
│   │   └── widgets/        # LoginForm, SignUpForm, BiometricPrompt
│   ├── favorites/
│   │   ├── pages/          # FavoritesPage (home screen)
│   │   └── widgets/        # FavoriteRiverCard, shimmer loader, coach marks
│   ├── forecast/
│   │   ├── pages/          # ReachOverviewPage
│   │   └── widgets/        # DailyExpandableWidget, ChartPreview, HourlyDisplay
│   ├── map/
│   │   ├── pages/          # MapPage
│   │   └── widgets/        # MapControls, SearchBar, ReachInfoSheet
│   ├── onboarding/
│   │   ├── pages/          # OnboardingPage
│   │   └── widgets/
│   └── settings/
│       ├── pages/          # SettingsPage
│       └── widgets/        # FlowUnitPicker, NotificationFrequencyPicker
└── routing/
    ├── app_router.dart
    └── app_routes.dart
```

**Routing** is a first-class concern. Route definitions, deep link handling, and navigation guards (auth checks, onboarding gates) live in `routing/`.

---

## Utilities: Cross-Cutting Helpers

Utilities provide common functionality used across **all** layers. Because they serve every layer, they live at the root level of `lib/`.

```
utils/
├── flow_formatter.dart         # Format flow values with CFS/CMS unit
├── date_formatter.dart         # Forecast date/time display helpers
├── unit_converter.dart         # CFS ↔ CMS conversion
└── validators/
    └── reach_id_validator.dart
```

Utilities should be:
- **Pure functions or stateless classes** — no side effects, no external dependencies
- **Genuinely cross-cutting** — if it only serves one layer, put it in that layer
- **Small and focused** — a utility that grows complex belongs in a service or domain object

---

## Shared vs Features Organization

Every layer uses the same principle: `shared/` for cross-feature code, `features/` for feature-specific code.

```
any_layer/
├── shared/       # Used by 2+ features
└── features/
    ├── auth/     # Only used by auth
    ├── favorites/ # Only used by favorites
    └── ...
```

**Rules:**
- `shared/` code can be imported by any feature
- Feature code **cannot import from other features** — only from `shared/`
- When a second feature needs something from the first, **promote it to shared/**

**The promotion lifecycle:**
1. Code starts in a feature folder
2. A second feature needs the same concept
3. Move it to `shared/` — this is normal and expected, not a sign of poor planning

**RIVR example:** `ReachData` is used by favorites, forecast, and map — it belongs in `shared/entities/`. `DailyFlowForecast` is only used by the forecast feature — it belongs in `features/forecast/entities/`.

**Exception — Infrastructure uses technical domain grouping:** `4_infrastructure/` groups by *what technical system it wraps* (`firebase/`, `http/`, `map/`), not by business feature.

---

## Dependency Flow and Import Rules

The numbered folders enforce a strict dependency hierarchy. **Lower layers never import from higher layers.**

```
models/1_domain/           ← Depends on NOTHING (pure Dart)
models/2_usecases/         ← Depends on 1_domain + contracts only
services/0_config/         ← Depends on nothing
services/1_contracts/      ← Depends on 1_domain
services/2_coordinators/   ← Depends on 1_contracts + 3_datasources
services/3_datasources/    ← Depends on 1_domain + 4_infrastructure
services/4_infrastructure/ ← Depends on external packages only
services/5_injection/      ← Depends on EVERYTHING (wiring layer)
ui/1_state/                ← Depends on 2_usecases + 1_domain
ui/2_presentation/         ← Depends on 1_state + 1_domain
utils/                     ← Depends on nothing (pure Dart helpers)
```

**The critical rules:**
1. **Models never import from Services or UI** — `ReachData` doesn't know about Firebase or Cupertino
2. **Services never import from UI** — `ForecastRepositoryImpl` doesn't know about widgets
3. **Features never import from other features** — only from `shared/`
4. **Only `5_injection/` sees everything** — it's the only layer that knows all concrete types

These rules prevent circular dependencies and make each layer independently testable.

---

## Error Handling: The ServiceResult Pattern

Rather than throwing exceptions across layer boundaries, use a **result wrapper** that makes success and failure explicit:

```dart
class ServiceResult<T> {
  final bool isSuccess;
  final T? data;
  final String? errorMessage;        // User-friendly
  final ServiceException? exception; // Technical details for logging

  ServiceResult.success(T data) : isSuccess = true, data = data, ...;
  ServiceResult.failure(ServiceException e) : isSuccess = false, ...;

  bool get isFailure => !isSuccess;

  /// Transform success data while preserving failures
  ServiceResult<R> map<R>(R Function(T) mapper) { ... }

  /// Chain async operations, short-circuiting on failure
  Future<ServiceResult<R>> then<R>(Future<ServiceResult<R>> Function(T) next) { ... }
}

class ServiceException {
  final ServiceErrorType type;
  final String message;           // User-friendly
  final String? technicalDetail;  // For logging

  ServiceException.network(String msg) : type = ServiceErrorType.network, ...;
  ServiceException.auth(String msg) : type = ServiceErrorType.authentication, ...;
  ServiceException.validation(String msg) : type = ServiceErrorType.validation, ...;
  ServiceException.notFound(String msg) : type = ServiceErrorType.notFound, ...;
  ServiceException.unknown(String msg) : type = ServiceErrorType.unknown, ...;
}

enum ServiceErrorType {
  network,
  authentication,
  validation,
  notFound,
  cache,
  configuration,
  unknown,
}
```

**Flow through layers in RIVR:**
1. **Datasource** catches NOAA timeout / Firebase exception → returns `ServiceResult.failure(...)` with technical details
2. **Coordinator** adds business context → "reach not found" vs "network unavailable"
3. **Use case** adds user-facing error messages → returns `ServiceResult` to Provider
4. **Provider** checks `result.isSuccess` → sets state (loaded or error)
5. **UI** reads provider state → displays error message or forecast data

**RIVR-specific error types:**

| Error Type | RIVR Example |
|---|---|
| `network` | NOAA API timeout, no internet connection |
| `authentication` | Firebase session expired, biometric failed |
| `validation` | Invalid reach ID, empty search query |
| `notFound` | Reach ID not in NOAA database |
| `cache` | Corrupted cached reach data, file I/O failure |
| `configuration` | Missing Mapbox token, invalid API URL |

---

## Dependency Injection: Two-Phase Wiring

### Phase 1: Horizontal Foundation

Register shared infrastructure that every feature depends on:

```dart
class RivrDependencyContainer {
  static Future<void> initialize() async {
    final container = GetIt.instance;

    // Phase 1: Shared infrastructure (order matters)
    await _registerSharedInfrastructure(container);

    // Phase 2: Vertical features (order may matter for cross-feature deps)
    await _registerFeatures(container);
  }

  static Future<void> _registerSharedInfrastructure(GetIt container) async {
    // HTTP client — shared by all API datasources
    container.registerLazySingleton(() => HttpClient());

    // Firebase — shared by auth, favorites, settings
    container.registerLazySingleton(() => FirebaseAuth.instance);
    container.registerLazySingleton(() => FirebaseFirestore.instance);

    // Local storage — shared by cache, settings, auth
    container.registerLazySingleton<SecureStorage>(() => SecureStorage());
  }
}
```

### Phase 2: Vertical Features

Each feature registers its own dependencies:

```dart
class ForecastDependencies {
  static void register(GetIt container) {
    // Guard against double registration
    if (container.isRegistered<ForecastApiDatasource>()) return;

    // Datasources
    container.registerLazySingleton<ForecastApiDatasource>(
      () => ForecastApiDatasource(client: container<HttpClient>()),
    );
    container.registerLazySingleton<ForecastCacheDatasource>(
      () => ForecastCacheDatasource(),
    );

    // Coordinator (implements contract)
    container.registerLazySingleton<IForecastRepository>(
      () => ForecastRepositoryImpl(
        apiDatasource: container<ForecastApiDatasource>(),
        cacheDatasource: container<ForecastCacheDatasource>(),
      ),
    );

    // Use cases
    container.registerFactory(
      () => LoadForecastOverviewUseCase(container<IForecastRepository>()),
    );
    container.registerFactory(
      () => RefreshForecastUseCase(container<IForecastRepository>()),
    );
    // ... other forecast use cases

    // Provider — registered with Provider in main.dart, not here
  }
}
```

**Key patterns:**
- **Lazy singletons** for repositories, datasources, coordinators (reused across app)
- **Factory** for use cases (stateless, new instance per injection)
- **Guard clauses** to prevent double registration
- **Feature registration order** matters when features depend on each other

**Registration order for RIVR:**
```dart
// Phase 2: Features (order matters)
AuthDependencies.register(container);       // No feature deps
SettingsDependencies.register(container);   // Depends on auth infra
ForecastDependencies.register(container);   // No feature deps
FavoritesDependencies.register(container);  // Depends on forecast
MapDependencies.register(container);        // Depends on forecast
```

---

## Cross-Feature Communication

Features are **vertically independent** — no Provider listens to another Provider, and no feature imports from another feature's folder. When features need to react to each other, use these patterns:

### 1. Navigation with Domain Entities

Pass shared entities through navigation:

```dart
// Map feature navigates to forecast, passing the reach
Navigator.push(context, ReachOverviewPage(reachId: selectedReachId));
```

The forecast feature receives a reach ID (a primitive) or a `ReachData` entity (from `shared/entities/`) — it doesn't import anything from the map feature.

### 2. Shared Domain Entities

`ReachData`, `FavoriteRiver`, and `UserSettings` live in `shared/entities/` precisely because multiple features need them. The favorites feature creates `FavoriteRiver` objects; the forecast feature reads `ReachData`. Both reference shared entities without knowing about each other.

### 3. Force-Refresh After Mutations

When one feature's action should cause another feature's data to refresh:

```dart
// In FavoritesProvider, after adding a favorite:
final result = await _addFavoriteUseCase.call(reachId);
if (result.isSuccess) {
  _favorites = [..._favorites, result.data!];
  notifyListeners();
  // The forecast feature doesn't need to know — it loads data independently
  // when the user navigates to a reach
}
```

**The rule:** Features communicate through shared domain concepts (entities in `shared/`), never through direct feature-to-feature imports.

---

## Testing Structure

Tests mirror the architecture, organized **feature-first** for practical navigation:

```
test/
├── models/
│   ├── domain/                    # Entity and value object tests
│   │   ├── reach_data_test.dart
│   │   ├── favorite_river_test.dart
│   │   └── user_settings_test.dart
│   └── usecases/                  # Use case tests (mocked repositories)
│       ├── forecast/
│       └── favorites/
├── services/
│   ├── coordinators/              # Coordinator tests (mocked datasources)
│   │   ├── forecast_repository_impl_test.dart
│   │   └── favorites_repository_impl_test.dart
│   ├── datasources/               # Datasource tests (mocked HTTP/Firestore)
│   │   ├── forecast_api_datasource_test.dart
│   │   └── favorites_firestore_datasource_test.dart
│   └── infrastructure/            # Infrastructure tests
│       ├── http_client_test.dart
│       └── reach_cache_test.dart
├── ui/
│   ├── state/                     # Provider tests (mocked use cases)
│   │   ├── favorites_provider_test.dart
│   │   └── auth_provider_test.dart
│   └── presentation/              # Widget tests (mocked providers)
│       ├── favorites/
│       └── forecast/
├── utils/                         # Utility function tests
├── helpers/
│   ├── test_helpers.dart          # pumpApp() wrapper with mock providers
│   └── fake_data.dart             # Factory methods for test entities
└── integration_test/              # End-to-end tests
    └── helpers/
```

**Testing by layer:**

| Layer | What to Test | How to Mock |
|---|---|---|
| Domain entities | Construction, validation, equality, copyWith | No mocks needed (pure Dart) |
| Use cases | Business logic, error mapping, input validation | Mock the contract (repository interface) |
| Coordinators | Caching strategy, phased loading, fallback logic | Mock the datasource |
| Datasources | HTTP call construction, JSON parsing, error wrapping | Mock the HTTP client / Firestore |
| Providers | State transitions per action | Mock the use cases |
| Widgets | User interaction, display logic | Mock the Provider |

---

## Development Order: Horizontal Foundation, Vertical Features

### Phase 1: Horizontal Foundation

Build the shared infrastructure every feature needs:

**Step 1 — Shared types:**
```
models/1_domain/shared/entities/    → ReachData, FavoriteRiver, UserSettings
services/4_infrastructure/shared/   → ServiceResult, ServiceException, AppLogger
utils/                              → FlowFormatter, DateFormatter
```

**Step 2 — Technical foundation:**
```
services/4_infrastructure/http/     → HTTP client with retry
services/4_infrastructure/firebase/ → Firestore client wrapper
services/0_config/shared/           → API endpoints, environment config
services/5_injection/               → Basic DI container setup
```

### Phase 2: Vertical Feature Development

Implement features one at a time, in dependency order (features with fewer deps first):

For each feature (e.g., Settings → Auth → Forecast → Favorites → Map):

```
Step 1: Define the interface
  services/1_contracts/features/settings/  → ISettingsRepository

Step 2: Build the data pipeline
  services/3_datasources/features/settings/  → SettingsFirestoreDatasource
  services/2_coordinators/features/settings/ → SettingsRepositoryImpl

Step 3: Add business logic
  models/2_usecases/features/settings/  → UpdateFlowUnitUseCase, etc.

Step 4: Connect to UI
  ui/1_state/features/settings/   → SettingsProvider (if needed)
  ui/2_presentation/features/settings/  → SettingsPage, widgets

Step 5: Wire dependencies
  services/5_injection/features/settings/  → SettingsDependencies.register()
```

### Why This Order Works

- **Contracts first** — establishes the spec that guides both data layer and business logic
- **Data pipeline before business logic** — ensures data flows before adding rules
- **Business logic before UI** — ensures providers have working use cases
- **DI last** — wires everything together once all pieces exist

Each completed feature is fully functional, testable, and independent before you move to the next.

---

## RIVR-Specific Decisions

These decisions adapt the Oqupa architecture to RIVR's specific needs and constraints.

### Provider Instead of BLoC

RIVR uses **Provider with ChangeNotifier** instead of BLoC. This is appropriate because:

- RIVR's state flows are straightforward (load data, show it, handle errors)
- Provider is already deeply integrated (4 providers, 35+ tests)
- The team is productive with Provider
- BLoC's event-driven ceremony adds overhead without proportional benefit for RIVR's complexity

Providers follow the same principles as BLoCs: they receive use cases via DI, expose loading/error/data states, and contain no business logic.

### No Value Objects (For Now)

RIVR has minimal user input — mostly search queries and auth credentials. Value objects (`Email`, `ReachId`) would add ceremony without proportional benefit. Add them when input validation becomes complex enough to warrant typed wrappers.

### Selective Coordinator Layer

Not every feature needs a coordinator between datasource and contract:

| Feature | Coordinator? | Reason |
|---|---|---|
| **Forecast** | Yes | Complex: in-memory TTL cache, file cache, phased loading, stale-while-revalidate |
| **Favorites** | Yes | Multi-source: Firestore + forecast data enrichment + cache |
| **Auth** | Optional | Could just let datasource implement contract directly |
| **Settings** | Optional | Simple Firestore CRUD + local preferences |
| **Map** | No | Primarily UI services, minimal data coordination |

When a coordinator would be `return datasource.doThing()` with no caching, offline, or coordination logic — skip it. The contracts layer still protects testability.

### Entity/DTO Separation Strategy

Not every model needs a separate DTO immediately:

| Model | Separate DTO? | Reason |
|---|---|---|
| **ReachData** | Yes | 800+ lines, mixed parsing + domain logic, most-touched file |
| **FavoriteRiver** | Yes | Has `toFirestoreMap()` / `fromFirestore()` mixed in |
| **UserSettings** | Yes | Has `fromJson()` / `toJson()` for Firestore |
| **DailyFlowForecast** | No | Already a pure domain entity |
| **HourlyFlowData** | No | Simple data class, minimal parsing |

---

## When to Break the Rules

### Skip the Use Case Layer

If a use case is literally `return repository.doThing()` with no validation, no error mapping, and no coordination — let the Provider call the contract directly. Add the use case later when real business logic appears. The contracts layer still protects testability.

### Skip the Coordinator Layer

If a datasource has no caching strategy and no multi-source coordination, let the datasource implement the contract directly. The coordinator exists to add value, not to exist.

### Let Infrastructure Group by Technical Domain

`4_infrastructure/firebase/` is better than scattering Firebase code across feature folders. Multiple features share Firebase — let the folder structure reflect that.

### Keep Existing Patterns That Work

RIVR's existing patterns — phased loading, generation-based request cancellation, `_TimedEntry<T>` caching — are solid. The architecture migration wraps these in cleaner layers; it doesn't replace what already works.

---

## Summary

| Principle | Rule |
|---|---|
| **Layer direction** | Models ← Services ← UI (never reverse) |
| **Feature isolation** | Features import from `shared/`, never from other features |
| **Numbered folders** | Enforce visual hierarchy in IDE |
| **Contracts separate concerns** | Use cases talk to contracts, not datasources |
| **Infrastructure by technical domain** | Groups around what it wraps, not who uses it |
| **Two-phase DI** | Horizontal foundation, then vertical features |
| **ServiceResult pattern** | Explicit success/failure at every layer boundary |
| **No cross-Provider communication** | Features coordinate via shared domain, not state |
| **Testing mirrors architecture** | Feature-first, then unit/widget/integration |
| **Provider over BLoC** | ChangeNotifier is sufficient for RIVR's complexity |
| **Pragmatic layers** | Skip coordinators/use cases when they add no value |

---

*Adapted from the Oqupa Flutter Architecture Guide.*
*RIVR: 5 features, 26 use cases, Provider/ChangeNotifier, Firebase + NOAA API.*
*Last updated: 2026-04-06*
