# HR-OTO — Progress

## Current stage

**Verification checkpoint — 2026-10-17**  
**Status:** არსებული backend/foundation ეტაპები შემოწმებულია; პროექტი მზად არის შემდეგი development ეტაპისთვის, მაგრამ არა Production release-ისთვის.  
**Updated:** 2026-10-17 (Asia/Tbilisi)

## Stage 1 completed

- შემოწმდა `D:\HR-OTO` და დადასტურდა, რომ საქაღალდე ცარიელი იყო.
- შექმნილია modular monorepo-ს დირექტორიები და README/გაშვების ინსტრუქცია.
- შექმნილია Employee, Admin და Owner Flutter app shells Riverpod-ით, ქართული UI-ით, Material 3-ით, Dark/Light Mode-ით და საერთო OTO-HR logo asset-ით.
- შექმნილია shared `flutter_design_system` და `flutter_core` packages.
- შექმნილია FastAPI modular backend skeleton და live/ready health endpoints.
- PostgreSQL-ისთვის მომზადებულია SQLAlchemy/Alembic engine/configuration და foundation migration.
- Redis adapter და Docker Compose მომზადებულია PostgreSQL + Redis სერვისებით.
- დამატებულია backend contract/layout/integration test sources.
- მოწოდებული ლოგო შენახულია `assets/branding/oto-hr-logo.png`-ში და shared design package asset-ად არის ინტეგრირებული.

## Not started by design

- Flutter platform folders/build tooling generation on a machine with Flutter SDK.
- PostgreSQL/Redis runtime validation Docker-ის გაშვების შემდეგ.
- Offline sync implementation.
- PIN ან attendance verification-ის კონკრეტული მექანიზმი.
- Brevo/SMSOffline keys და integrations.
- Flutter SDK-ის ინსტალაცია და `flutter pub get/analyze/test` execution.

## Stage 2 implementation

- Central PostgreSQL schema დაემატა `tenants`, `users`, `user_sessions` და `password_reset_tokens` ცხრილებით.
- დაემატა Company ID, უნიკალური Company Code, subdomain, status და tenant database name.
- დაემატა ცალკე tenant database provisioning service და tenant schema migration.
- დაემატა company creation API Owner permission-ით; provisioning ჩავარდნისას კომპანია active არ ხდება.
- დაემატა password hashing, JWT access/refresh tokens, server-side session revocation და logout.
- დაემატა password reset საფუძველი და MFA enrollment/verification საფუძველი.
- დაემატა Owner, Company Owner, HR Admin, Manager და Employee role model და explicit permission map.
- დაემატა server-side tenant access guard; URL/Company Code ვერ ცვლის token-ის tenant context-ს.
- დაემატა ავტომატური cross-tenant isolation და Stage 2 contract tests.

## Stage 2 verification

- Python `compileall` შემოწმება: წარმატებული.
- Alembic central head: `0002_multitenant_identity`.
- Alembic tenant head: `tenant_0001_core`.
- Backend pytest: `12 passed`.
- FastAPI `/api/v1/health/live`: `200 OK`.
- FastAPI `/api/v1/health/ready`: `degraded`, რადგან ამ გარემოში PostgreSQL/Redis containers არ გაშვებულა.
- Docker Compose runtime ვერ გაეშვა, რადგან Docker CLI არ არის დაყენებული.

## Stage 3 implementation

- Owner-ისთვის შეიქმნა ცალკე `/owner` backend router და ცალკე Flutter app flow; Company Admin აპში Owner ფუნქციები არ დამატებულა.
- დაემატა რეალური Owner dashboard endpoint: კომპანიები, სტატუსები, Trial, ლიცენზიები და monthly revenue.
- დაემატა კომპანიების ძებნა/ფილტრი, დეტალური პროფილი, რედაქტირება, activate/block და Company Owner creation API.
- დაემატა Owner audit log API და company create/update/owner-create audit events.
- Owner Flutter app-ში დაემატა Login + MFA field, secure token storage, Dashboard, adaptive Sidebar/NavigationBar, Companies workspace და Audit Log.
- ყველა Owner მოქმედება მიბმულია რეალურ FastAPI endpoint-ზე; demo/static company data არ გამოიყენება.

## Stage 3 verification

- Backend migration head: `0003_owner_operations`.
- Owner backend contract tests დამატებულია.
- Flutter analyze/test ამ გარემოში ვერ გაეშვა, რადგან Flutter SDK არ არის დაყენებული.

## Stage 4 implementation

- შეიქმნა ბაზაში შენახული Packages, Price Versions, Features, Limits, Company Subscriptions, Commercial Overrides და Trial Grants მოდელები.
- დაემატა `0004_commercial_entitlements` migration და საწყისი START/BUSINESS/PRO პაკეტები.
- საწყისი ფასები: START 39 GEL/თვე, BUSINESS 89 GEL/თვე, PRO 179 GEL/თვე; თითოეულს აქვს თანამშრომლებისა და სხვა რესურსების საწყისი ლიმიტები.
- დაემატა პაკეტის შექმნა, რედაქტირება, არქივირება/გააქტიურება და ფასის versioned ცვლილება.
- დაემატა დამოუკიდებელი feature/limit API ცვლილებები.
- დაემატა company subscription assignment, individual feature/limit/price overrides და trial grant/extension.
- დაემატა Effective Entitlements Engine, რომელიც აერთიანებს subscription package-სა და აქტიურ company overrides-ს.
- Backend სავალდებულოდ ტოვებს `security.authentication`, `security.tenant_isolation` და `security.audit` features-ს ჩართულს.
- Subscription-ში შენახული agreed price არ იცვლება package-ის ახალი ფასის ვერსიის შექმნით.
- Owner Flutter-ში დაემატა ცალკე Packages workspace, რეალური API-driven create/edit/archive, pricing version, feature და limit მართვით.
- Company workspace-დან დაემატა subscription assignment, trial grant და feature/limit override მოქმედებები.

## Stage 4 verification

- Backend tests: `19 passed`, including disabled-feature and reduced-limit server enforcement tests.
- Python `compileall`: წარმატებული.
- Central Alembic head: `0004_commercial_entitlements`.
- Tenant Alembic head: `tenant_0001_core`.
- Central and tenant Alembic offline SQL generation: successful.
- Owner UI-ში START/BUSINESS/PRO ფასები hardcode არ არის; მონაცემები API/ბაზიდან მოდის.
- Tenant feature-access endpoint იყენებს Effective Entitlements Engine-ს და disabled feature-ს Backend-ზე 403-ით ბლოკავს.
- Flutter analyze/test ვერ გაეშვა, რადგან Flutter SDK ამ გარემოში არ არის დაყენებული.

## Open inputs before full runtime verification

1. Owner-ისა და tenant-ის როლების საბოლოო permission matrix.
2. კონკრეტული verification მეთოდი ან პირველი provider.
3. Trial/subscription billing-ის ბიზნეს-წესები, ვალუტა და tax requirements.
4. Brevo/SMSOffline account/API contract details.
5. მონაცემთა retention, backup, deletion/export და მოქმედი სამართლებრივი მოთხოვნები.

## Stage 5 implementation

- დაემატა `provider_integrations`, notification templates/quotas/messages/events მოდელები და `0005_integrations_notifications` migration.
- Owner-only Integrations API ამუშავებს provider configuration-ს, enable/disable-ს, masked secret metadata-ს, connection/message test-ს, quota-ს და history-ს.
- დაემატა Owner-only message template CRUD; template/provider IDs და message history central DB-ში ინახება.
- Brevo adapter იყენებს ოფიციალურად დადასტურებულ `GET /v3/account` და `POST /v3/smtp/email` endpoint-ებს, `api-key` header-ს და Idempotency-Key-ს.
- დაემატა SecretStore abstraction: სრულ secret-ს DB-ში არ ვინახავთ და API response-ში არ ვაბრუნებთ; default deployment adapter environment-only read არის და rotation-ს KMS/Vault-ის გარეშე განზრახ ბლოკავს.
- SMSOffline-ისთვის შეიქმნა დამოუკიდებელი Mock Adapter. უცნობი endpoint არ არის გამოგონილი; რეალური adapter-ის დასაკავშირებლად საჭიროა ოფიციალური API დოკუმენტაცია და credentials.
- დაემატა notification enqueue service Redis queue-ის, idempotency-ის, quota checks-ის და retry-ready message state-ის საფუძვლით.
- Owner Flutter-ში დაემატა `Integrations → SMS & Email Providers` adaptive workspace, provider status, masked secret state, connection test და enable/disable actions.

## Stage 5 verification

- Backend `compileall`: successful.
- Backend tests: `22 passed` (including Brevo official-path contract, secret masking and explicit SMSOffline-not-configured tests).
- რეალური Brevo/SMSOffline connection არ გამოცხადებულა წარმატებულად: ამ გარემოში credentials არ არის მოწოდებული; SMSOffline-ის endpoint contract არ არის დადასტურებული.
- Flutter analyze/test და PostgreSQL/Redis runtime ვერ გაეშვა, რადგან Flutter SDK/Docker ამ გარემოში არ არის დაყენებული.

## Stage 10 implementation

- Tenant migration `tenant_0006_leave_payroll_documents` დაემატა Leave Policies/Comments, configurable Payroll Rules/Periods/Entries და Document Versions.
- Leave API: მოთხოვნების სია, approval/rejection, კომენტარები და წესების კონფიგურაცია.
- Payroll API: წესების/პერიოდების შექმნა, calculation guard, approval guard, ისტორია და Employee-ისთვის მხოლოდ approved payroll-ის ჩვენება.
- Payroll calculation intentionally არ ასრულებს რეალურ დარიცხვას დაუმტკიცებელი ფორმულებით; final approval მოითხოვს calculated status-ს და online authenticated request-ს.
- Document API: PDF/მრავალფორმატიანი content upload, versioning, employee-only download და acknowledgement.
- Employee მონაცემებზე კვლავ მოქმედებს strict self-scope და payroll feature entitlement.
- საქართველოს საგადასახადო წესები hardcode არ არის; PayrollRule/configuration არის გაფართოებადი. ოფიციალური საგადასახადო წყარო: [საქართველოს შემოსავლების სამსახური](https://www.rs.ge/).

## Stage 10 verification

- Backend tests: `31 passed`.
- Python `compileall`: successful.
- Tenant Alembic head: `tenant_0006_leave_payroll_documents`.
- Flutter analyze/test და PostgreSQL/Redis runtime ვერ გაეშვა, რადგან Flutter SDK/Docker ამ გარემოში არ არის დაყენებული.

## Stage 11 implementation

- დაემატა KPI/goals, performance reviews, disciplinary cases, recruitment jobs/candidates და training courses/enrollments domain model/migration.
- Advanced HR API-ს ყველა ძირითადი create operation-ს აქვს tenant isolation, role guard და Owner Feature Entitlement check.
- Surveys და Internal Announcements-ის წინა foundation შენარჩუნებულია და იმავე tenant scope-ში რჩება.

## Stage 12 implementation

- არსებული Brevo/SMSOffline provider boundary, templates, queue, retries, delivery history, quotas და company overrides შენარჩუნებულია.
- დაემატა tenant reporting summary API attendance/leave/break/payroll approved aggregates-ით და date filters-ით.
- Provider secrets კვლავ Company Admin-ისთვის მიუწვდომელია; payment provider-ის live integration არ გამოგონილა.

## Stage 13 audit status

- ყველა არსებული backend test suite ხელახლა გაეშვა; runtime verification-ის წინ დარჩა Flutter SDK, Docker/PostgreSQL/Redis და real provider credentials.
- Release APK/AAB/EXE/Installer ამ გარემოში არ შექმნილა; არც ერთი build წარმატებულად არ გამოცხადებულა.
- Production release requires Flutter toolchain, platform signing keys, macOS/Xcode for iOS, Windows packaging toolchain, PostgreSQL/Redis deployment and KMS/Vault/provider credentials.

## Latest verification checkpoint

Repeated verification: 2026-10-17 — all checks below passed again; no corrective code changes were required.

## Build verification checkpoint

- Flutter: unavailable on the current Windows machine; `flutter analyze`, `flutter test`, Windows release builds and Android builds were not run.
- Dart: unavailable.
- Visual Studio/MSBuild and Windows SDK: unavailable.
- Android SDK/ADB: unavailable.
- Docker: unavailable.
- Inno Setup/WiX: unavailable.
- The three Flutter app directories currently contain source/test/pubspec files but no generated `android/` or `windows/` platform folders.
- No fake or empty installer/APK/AAB was created.
- `releases/README.md` documents that the directory contains no verified artifacts yet.
- Exact installation and build steps are in `docs/BUILD_WINDOWS.md`.

## Installer build checkpoint

Latest Windows environment check: Flutter, Dart, CMake, Ninja, MSBuild, Inno Setup and Windows SDK were not usable on this machine. `winget.exe` was present only as an inaccessible WindowsApps shim, so automatic installation could not be performed.

- Real Windows installers: not created; Flutter, Windows build tools and Inno Setup are unavailable.
- Real Android APK/AAB: not created; Flutter and Android SDK are unavailable.
- iOS/TestFlight: not created; requires macOS/Xcode and Apple Developer signing.
- Added fail-fast scripts: `scripts/build_windows_release.ps1` and `scripts/build_android_release.ps1`.
- Added installer definition: `scripts/installer.iss` with logo, shortcuts, uninstaller and version metadata safeguards.
- Added full workflow: `BUILD_INSTRUCTIONS.md`.
- `releases` contains documentation only; no empty or unverified binaries were added.
- Build script smoke test: correctly stopped with `flutter is unavailable`; no artifact was generated.

### წარმატებით შემოწმდა

- Backend Python `compileall`: successful.
- სრული backend test suite: `34 passed`, 1 არსებული Starlette/httpx deprecation warning.
- Central Alembic head: `0005_integrations_notifications`.
- Tenant Alembic head: `tenant_0007_advanced_hr`.
- Central migration offline SQL generation: successful.
- Tenant migration offline SQL generation: successful.
- FastAPI application import and route registration: successful (`18` routes registered).
- Stage 8 attendance engine, verification guard და break invariant tests.
- Stage 9 offline lease/idempotency/sync contract tests.
- Stage 10 leave/payroll/documents contract tests.
- Stage 11 advanced HR feature-guard contract tests.
- Stage 12 reporting/provider boundary contract tests.

### დარჩა შესამოწმებელი ან დასასრულებელი

- Flutter SDK არ არის ხელმისაწვდომი: `flutter analyze`, `flutter test`, Android APK/AAB და Windows build ვერ გაეშვა.
- Docker არ არის ხელმისაწვდომი: PostgreSQL/Redis live health, real migrations და worker runtime ვერ შემოწმდა.
- iOS build-ისთვის საჭიროა macOS/Xcode.
- Stage 11/12 ყველა ეკრანის სრული Flutter UI ჯერ არ არის დასრულებული; backend foundations/guards მზად არის.
- SMSOffline-ის რეალური adapter საჭიროებს ოფიციალურ API დოკუმენტაციასა და credentials-ს.
- Brevo/SMSOffline live provider tests credentials-ის გარეშე არ შესრულებულა.
- Production KMS/Vault, backup/restore drill, payment sandbox და platform signing ჯერ არ არის კონფიგურირებული.
- Git repository ამ სამუშაო საქაღალდეში არ არსებობს; ცვლილებებზე commit ვერ შეიქმნა.

## Stage 7 implementation

- Tenant migration `tenant_0003_employee_mobile` დაემატა schedules, attendance, breaks, leave balance/requests, announcements, in-app notifications და anonymous surveys.
- დაემატა Employee self-service API: dashboard, profile, დღეს/კვირა/თვე schedule, საკუთარი attendance/break history, leave balance/request, payroll entitlement gate, documents, announcements, notifications და surveys.
- Employee API ამოწმებს `UserRole.EMPLOYEE`, tenant context-ს და `Employee.user_id`/email linkage-ს; სხვა თანამშრომლის ID-ით მონაცემის მიღება შეუძლებელია.
- ხელფასის მონაცემები მხოლოდ `payroll` entitlement-ის არსებობისას ბრუნდება.
- დაემატა `VerificationProvider` interface და `PendingVerificationProvider`; attendance verification default-ად გამორთულია და დაუდასტურებელი ჩანაწერები verified-ად არ ითვლება. 6-ნიშნა PIN არ დამატებულა.
- Employee Flutter აპი შეიცვალა რეალურ API-driven Android/iOS flow-ად: Login + MFA, dashboard, profile summary, schedule, attendance, leave request, announcements, adaptive navigation და Dark/Light Mode.

## Stage 7 verification

- Backend tests: `26 passed`.
- Python `compileall`: successful.
- Central Alembic head: `0005_integrations_notifications`.
- Tenant Alembic head: `tenant_0003_employee_mobile`.
- Flutter analyze/test და PostgreSQL/Redis runtime ვერ გაეშვა, რადგან Flutter SDK/Docker ამ გარემოში არ არის დაყენებული.

## Stage 8 implementation

- დაემატა shift templates, overnight-aware schedules, schedule publication/history და shift swap data model foundation.
- დაემატა attendance calculation engine: worked, late, early leave, overtime და night minutes; timezone-aware datetime processing გამოიყენება.
- დაემატა Admin workforce API schedule assignment/publish/correction/active-break monitoring-ით.
- დაემატა Employee clock-in/clock-out და break start contract, მაგრამ Pending Verification Provider-ის გამო production write განზრახ დაბლოკილია.
- ერთი თანამშრომლის ერთზე მეტი active break server-side იკრძალება.

## Stage 9 implementation

- დაემატა encrypted SQLite storage abstraction; ciphertext ინახება SQLite-ში, AES key კი platform Secure Storage-იდან უნდა მოდიოდეს.
- დაემატა Device Registration, signed 48-hour offline lease, server time/clock skew metadata და server version cursor.
- დაემატა local outbox, UUID event IDs, idempotency keys, retry/conflict primitives და server sync event ledger.
- offline lease expiration-ის შემდეგ ახალი ცვლილებები client-side restricted რეჟიმში გადადის, ხოლო sync endpoint ხელმისაწვდომი რჩება.
- კრიტიკული attendance verification, Payroll/Owner/API-key/გადახდის მოქმედებები online-only boundary-ში რჩება.
- SMS/Email provider execution ისევ server-side online flow-შია; offline queue არ აგზავნის პირდაპირ provider-ზე.

## Stage 8–9 verification

- Backend tests: `29 passed`.
- Python `compileall`: successful.
- Central Alembic head: `0005_integrations_notifications`.
- Tenant Alembic head: `tenant_0005_offline_sync`.
- Tenant offline SQL generation: successful.
- Flutter analyze/test და PostgreSQL/Redis runtime ვერ გაეშვა, რადგან Flutter SDK/Docker ამ გარემოში არ არის დაყენებული.

## Stage 6 implementation

- Tenant migration `tenant_0002_admin_core` დაემატა Departments, Positions, Branches, Employees, Employee Documents და Tenant Settings ცხრილებით.
- Company Admin API დაემატა tenant-isolated Dashboard, employee CRUD, archive/restore, profile sensitivity controls, departments/positions/branches, branch manager field, entitlements, settings და company user role management.
- თანამშრომლის შექმნაზე, ფილიალზე, ადმინისტრატორის როლზე და import-ზე server-side entitlement limits მოწმდება; არსებული მონაცემები limit reduction-ისას არ იშლება.
- დაემატა Excel import foundation (`openpyxl`) და CSV export endpoint; export payload API-დან მიიღება, არა mock data-დან.
- Admin Flutter შეიცვალა რეალურ API-driven აპლიკაციად: Login + MFA, Dashboard, Employees workspace, company code context, adaptive Windows Sidebar/mobile NavigationBar, package/feature/limit view და organization/settings entry points.
- Salary/personal/document მონაცემებზე profile response-ში role-based field filtering მუშაობს; Company Admin-ს Owner global provider secrets-ზე წვდომა არ აქვს.

## Stage 6 verification

- Backend tests: `24 passed`.
- Python `compileall`: successful.
- Central Alembic head: `0005_integrations_notifications`.
- Tenant Alembic head: `tenant_0002_admin_core`.
- Flutter analyze/test და PostgreSQL/Redis runtime ვერ გაეშვა, რადგან Flutter SDK/Docker ამ გარემოში არ არის დაყენებული.

## Next approved action

შემდეგი სამუშაო შეიძლება დაიწყოს მხოლოდ Stage 5-ის ცალკე ინსტრუქციით; Stage 4-ის ძირითადი commercial management foundation დასრულებულია.

## GitHub Actions Windows installer preparation

- დაემატა `.github/workflows/windows-release.yml` manual `workflow_dispatch`-ით.
- Workflow runner-ზე აყენებს Flutter Stable-ს, Inno Setup 6-ს და ImageMagick-ს; იყენებს `windows-latest` Visual Studio C++/Windows toolchain-ს.
- Workflow უშვებს `flutter doctor -v`, Admin/Owner `flutter analyze`, `flutter test` და Windows release builds-ს.
- Inno Setup-ში შედის Flutter-ის build output-ის ყველა DLL/runtime ფაილი, Start Menu/Desktop shortcuts, uninstaller და supplied HR-OTO logo.
- დაემატა installer install/launch/uninstall smoke-test და მხოლოდ შემოწმებული Setup.exe-ების Artifact upload.
- განახლდა `BUILD_INSTRUCTIONS.md` GitHub Repository-ის დაკავშირების, manual run-ისა და Artifact-ის ჩამოტვირთვის ინსტრუქციებით.

### ამ ეტაპის რეალური სტატუსი

- Workflow ფაილი მომზადებულია, მაგრამ GitHub repository/remote ამ სამუშაო საქაღალდეში ჯერ არ არის დაკავშირებული.
- GitHub Actions run ჯერ არ შესრულებულა, ამიტომ `HR-OTO-Admin-Setup.exe` და `HR-OTO-Owner-Setup.exe` ამ ეტაპზე რეალურად შექმნილად არ ითვლება.
- ადგილობრივად Flutter/Visual Studio/Inno Setup არ არის ხელმისაწვდომი; build მიზანმიმართულად გადატანილია GitHub Windows Runner-ზე.
- Android/iOS build ამ ეტაპზე არ დაწყებულა.

### GitHub Actions Run #1 verification

- GitHub Windows Runner-ზე Flutter Stable, Inno Setup 6 და ImageMagick წარმატებით მომზადდა.
- Runner-მა `flutter doctor -v` ეტაპიც გაიარა.
- Run #1-მა `apps/owner_flutter/lib/main.dart`-ში Dart syntax errors გამოავლინა `flutter analyze/test` ეტაპზე; Installer build-მდე არ მისულა და Artifact არ შეიქმნა.
- შეცდომები გასწორდა Owner login, commercial dialog, packages page და integrations page-ის widget tree-ებში. შემდეგი ნაბიჯია ახალი commit/push და ხელახალი Workflow run.
- Run #3-ში გამოვლინდა ერთი დარჩენილი ზედმეტი class-closing brace `IntegrationsPage`-ის ბოლოს; ის გასწორდა, ხოლო `flutter analyze`-ის დარჩენილი შეტყობინებები მხოლოდ lint warning/info-ებია.
- Run #4-ში Owner სინტაქსი უკვე გაიარა; ჩავარდა მოძველებული widget test, რომელიც ახალ Login UI-ში აღარ არსებულ `Foundation მზად არის` ტექსტს ეძებდა. სამივე აპის foundation test განახლდა რეალურ Login UI ტექსტებზე.
- Run #5-ში ორივე აპის Analyze/Test ეტაპები წარმატებით გაიარა; Admin Windows build-ზე აღმოჩნდა Flutter CLI incompatibility — `flutter build windows`-ს `--target-platform` არგუმენტი არ აქვს. Workflow და local build script გასწორდა.
- Run #6-მა Build, Packaging და smoke-test წარმატებით გაიარა, მაგრამ მომხმარებლის კომპიუტერზე Installer-ის გაშვებისას გამოვლინდა Inno Setup runtime-check-ის შეცდომა: `InitializeSetup()` GitHub Runner-ის დროებით source path-ს ამოწმებდა. ეს check ამოღებულია; source file validation უკვე Inno compile-ის `[Files]` ეტაპზე ხდება.
