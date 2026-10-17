# HR-OTO — Architecture Decision Record

## ADR-001 — Native client applications

**გადაწყვეტილება:** პროდუქტი იქმნება Flutter-ის native mobile/desktop applications-ად Android, iOS და Windows-ისთვის.  
**მიზეზი:** მომხმარებელმა გამორიცხა website/browser application; საჭიროა ერთი საერთო კოდის ბაზა და პლატფორმის შესაბამისი packaging.  
**შედეგი:** საჭიროა platform-specific secure storage, signing, permissions და adaptive UI.

## ADR-002 — Modular monolith-first backend

**გადაწყვეტილება:** საწყისი backend იქნება ერთი modular FastAPI service მკაფიო domain boundaries-ით.  
**მიზეზი:** SaaS-ის პირველ ვერსიაში სწრაფი, თანმიმდევრული transaction და დაბალი ოპერაციული overhead.  
**შედეგი:** integration/worker modules მომავალში ცალკე deployable service-ებად გამოიყოფა საჭიროებისას.

## ADR-003 — Server-enforced tenant isolation

**გადაწყვეტილება:** tenant context, authorization და data filtering backend-ის სავალდებულო პასუხისმგებლობაა; ყველა tenant-owned record-ს აქვს tenant scope.  
**მიზეზი:** client-supplied tenant ID-ზე დაყრდნობა მონაცემთა გაჟონვის რისკს ქმნის.  
**შედეგი:** საჭიროა repository/service guardrails, composite constraints და ავტომატური isolation tests.

## ADR-004 — Owner as separate global context

**გადაწყვეტილება:** Owner აპი და authorization context განცალკევებულია tenant admin-ისგან.  
**მიზეზი:** კომერციული და სისტემური მართვა არ უნდა აირიოს კომპანიის მონაცემთა კონტექსტში.  
**შედეგი:** Owner-ის tenant impersonation/inspection იქნება explicit, audited და შეზღუდული.

## ADR-005 — Encrypted offline storage with 48-hour maximum

**გადაწყვეტილება:** Employee/Admin-ს ექნება encrypted SQLite და sync queue, მაქსიმუმ 48-საათიანი offline window-ით.  
**მიზეზი:** მომხმარებლის მოთხოვნა და PII-ის დაცვის საჭიროება.  
**შედეგი:** საჭიროა secure key store, sync versioning, conflict policies და restricted state.

## ADR-006 — Extensible verification provider

**გადაწყვეტილება:** შეიქმნება `VerificationProvider` interface; PIN არ განხორციელდება და attendance method მოგვიანებით აირჩევა.  
**მიზეზი:** მეთოდი ჯერ არ არის არჩეული და domain-ის ხელახალი გადაკეთება არ უნდა გახდეს საჭირო.  
**შედეგი:** პირველი iteration გამოიყენებს mock/provider contract-ს; რეალური provider მოგვიანებით დაემატება.

## ADR-007 — Secrets server-side only

**გადაწყვეტილება:** Brevo/SMSOffline keys ინახება server Secret Storage-ში და client-ს არასდროს გადაეცემა.  
**მიზეზი:** credential compromise-ის რისკის შემცირება და მომხმარებლის პირდაპირი მოთხოვნა.  
**შედეგი:** Owner-ს ექნება masked management/test flow; საჭიროა rotation და audit.

## ADR-008 — Archive over delete for commercial plans

**გადაწყვეტილება:** პაკეტები archived state-ში გადადიან და არ იშლებიან ფიზიკურად.  
**მიზეზი:** ისტორიული subscriptions, invoices/usage და audit records უნდა დარჩეს გასაგები.  
**შედეგი:** ყველა query-ში active/archived semantics მკაფიოდ უნდა განისაზღვროს.

## ADR-009 — Georgian-first design system

**გადაწყვეტილება:** ქართული იქნება default locale, ხოლო UI ააგება reusable design system-ზე Dark/Light Mode-ით.  
**მიზეზი:** პროდუქტის ძირითადი ბაზრის მოთხოვნა და თანმიმდევრული premium UX.  
**შედეგი:** localization keys თავიდანვე გამოიყენება; ტექსტი screens-ში hardcode არ უნდა იყოს.

## ADR-010 — Central database plus database-per-tenant

**გადაწყვეტილება:** central PostgreSQL ინახავს platform identity/provisioning metadata-ს; ყოველი კომპანია იღებს ცალკე PostgreSQL database-ს tenant migrations-ით.  
**მიზეზი:** HR მონაცემების მკაცრი ფიზიკური იზოლაცია და კომპანიის database-ის დამოუკიდებელი backup/restore შესაძლებლობა.  
**შედეგი:** provisioning არის asynchronous-ready service boundary; tenant connection string არასდროს მიეწოდება Flutter client-ს.

## ADR-011 — Server-side authentication and session revocation

**გადაწყვეტილება:** Argon2 password hashes, short-lived JWT access tokens, persisted refresh sessions და server-side logout/revocation.  
**მიზეზი:** token theft-ის blast radius-ის შემცირება და logout-ის რეალური ძალაში ყოფნა.  
**შედეგი:** თითოეული API request ამოწმებს JWT-ს, session-ს, expiry-ს, revocation-ს და user active state-ს.

## ADR-012 — Explicit role permissions and tenant guard

**გადაწყვეტილება:** role-to-permission map backend-შია განსაზღვრული; URL/company code ვერ განსაზღვრავს tenant context-ს.  
**მიზეზი:** UI-based authorization და client-provided tenant ID უსაფრთხოების კონტროლი არ არის.  
**შედეგი:** cross-tenant access-ზე ავტომატური 403 და regression tests სავალდებულოა.

## ADR-013 — Versioned commercial contracts

**გადაწყვეტილება:** Package price changes create a new effective-dated price version; each company subscription stores agreed monthly/annual prices independently.  
**მიზეზი:** Owner-ის ფასის ცვლილებამ არსებული ხელშეკრულება დადასტურებისა და წესის გარეშე არ უნდა შეცვალოს.  
**შედეგი:** ახალი კლიენტები ხედავენ აქტუალურ ფასს, არსებული კონტრაქტები ინარჩუნებს agreed price-ს.

## ADR-014 — Effective entitlements and immutable security controls

**გადაწყვეტილება:** entitlement engine merges package features/limits with active company overrides; authentication, tenant isolation and audit features are mandatory and cannot be disabled.  
**მიზეზი:** commercial flexibility უნდა დარჩეს server-side security boundary-ის ქვეშ.  
**შედეგი:** feature/limit checks are reusable backend enforcement functions; lowering a limit blocks new operations but never deletes existing data.

## ADR-015 — Provider adapters and secret boundary

**გადაწყვეტილება:** Brevo და SMSOffline იყოფა დამოუკიდებელ adapter-ებად; Brevo მხოლოდ ოფიციალურად დადასტურებულ API contract-ს იყენებს, SMSOffline კი documentation-ის არქონამდე Mock Adapter-ით რჩება. Credentials ინახება SecretStore abstraction-ის მიღმა და არა PostgreSQL-ში.

**მიზეზი:** provider-specific შეცდომები არ უნდა გავრცელდეს notification domain-ში; უცნობი SMS API endpoint-ის გამოგონება უსაფრთხო და ტექნიკურად მიუღებელია.

**შედეგი:** production deployment-ში EnvironmentSecretStore უნდა ჩანაცვლდეს Vault/KMS adapter-ით; Owner rotation endpoint განზრახ აბრუნებს 503-ს, სანამ ასეთი secret manager არ იქნება კონფიგურირებული.

