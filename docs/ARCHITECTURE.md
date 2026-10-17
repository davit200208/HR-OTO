# HR-OTO — Architecture

## 1. არქიტექტურული ხედვა

HR-OTO იყენებს modular monolith-first მიდგომას: ერთი FastAPI server-ის შიგნით მკაფიო bounded modules და საერთო უსაფრთხოების/tenant kernel, ხოლო Flutter აპები იზიარებენ domain contracts-სა და design system-ს. ეს ამცირებს საწყის ოპერაციულ სირთულეს და ტოვებს მომავალში ცალკე worker/integration services-ზე გამოყოფის შესაძლებლობას.

```text
HR-OTO Employee/Admin/Owner (Flutter)
              |
        HTTPS REST API
              |
       FastAPI application
   Auth | Tenant | RBAC | Audit
      | domain modules | files
      +--------+---------+
      |        |         |
 Central  Tenant DBs  Redis
 PostgreSQL (one/company)  Secret Storage
      |
 SQLite encrypted offline stores (per client)
```

## 2. Repository layout

```text
HR-OTO/
├─ assets/
│  └─ branding/            # approved OTO-HR logo and future brand assets
├─ apps/
│  ├─ employee_flutter/
│  ├─ admin_flutter/
│  └─ owner_flutter/
├─ services/
│  └─ api/                 # FastAPI modular backend
├─ packages/
│  ├─ flutter_core/        # networking, auth, sync, localization
│  ├─ flutter_design_system/
│  └─ api_contracts/
├─ infra/                  # Docker, compose, deployment templates
├─ tests/
├─ docs/
└─ README.md
```

## 3. Backend layers

- API layer: versioned REST routers, request validation, error envelope.
- Application layer: use cases/commands, authorization decisions, transactions.
- Domain layer: entities, policies, ports/interfaces; verification provider lives here.
- Infrastructure layer: SQLAlchemy repositories, Redis, secret provider, file storage, notification adapters.
- Cross-cutting: tenant context, audit, idempotency, observability, rate limiting.

## 4. Central database and tenant isolation

Central database ინახავს tenants, users, roles, sessions, licenses და provisioning metadata-ს. თითოეულ კომპანიას provisioning service უქმნის ცალკე PostgreSQL database-ს და tenant migration-ს. Tenant-owned rows ამ database-ში აღარ იზიარებს სხვა კომპანიის database-ს. Repository API tenant context-ის გარეშე ვერ იმუშავებს. Service layer ამოწმებს user-to-tenant membership-სა და permission-ს. Redis keys, file paths, jobs და audit records tenant-scoped იქნება. Owner routes ცალკე global context-ში იმუშავებს და tenant routes-ზე პირდაპირი იმპერსონაცია მხოლოდ audit-ით და explicit authorization-ით იქნება შესაძლებელი.

URL-ის company code, Company ID ან სხვა client-provided value მხოლოდ lookup hint-ია. საბოლოო tenant identity მიიღება signed access token-ის session-იდან და server-side user record-იდან; mismatch აბრუნებს 403-ს tenant database-მდე მისვლამდე.

შემდგომი hardening-ისთვის განიხილება PostgreSQL Row-Level Security, მაგრამ ის არ ჩაანაცვლებს application-level authorization-ს; ორივე ფენა defense-in-depth-ისთვის გამოიყენება.

## 5. მონაცემთა მოდელი — პირველი ბირთვი

Central: `tenants`, `users`, `user_sessions`, `password_reset_tokens`, `plans`, `plan_features`, `subscriptions`, `licenses`, `secret_metadata`, `system_settings`.  
Per-tenant database: `employees`, `departments`, `positions`, `branches`, `devices`, `schedules`, `attendance_events`, `leave_requests`, `documents`, `notifications`, `audit_events`.

Payroll და performance მოდულები ფინანსური/PII რისკის გამო ცალკე migration-ებითა და მკაცრი permission matrix-ით დაემატება.

## 6. Authentication, authorization და audit

- Access/refresh token strategy server-side revocation-ით.
- Role + permission model: Owner, tenant admin, HR roles, manager, employee; საბოლოო როლები discovery-ში დაზუსტდება.
- Device registration და session list/revoke.
- ყოველი მაღალი რისკის mutation: actor, tenant, action, target, timestamp, result, correlation id.
- API idempotency keys sync და billing mutations-ისთვის.
- Passwords are Argon2-hashed; access tokens are short-lived JWTs and refresh sessions are persisted server-side with revocation.
- Password reset uses one-time, hashed, expiring tokens; reset requests are intentionally response-generic.
- MFA enrollment/verification is available for administrative accounts through TOTP; secret material is never logged.

## 7. Offline synchronization

Flutter core-ში იქნება `SyncEngine`, `EncryptedLocalStore`, `Outbox`, `Inbox` და `ConflictResolver` interfaces. Server მხარეს ექნება cursor/version-based sync API. თითოეული command-ს ექნება client-generated operation ID; server duplicate request-ს უსაფრთხოდ ამოიცნობს.

## 8. Secrets და integrations

`SecretStore` abstraction-ის უკან განთავსდება გარემოს შესაბამისი Secret Storage. Brevo/SMSOffline adapters იღებენ secret-ს მხოლოდ server runtime-ში. Owner API-ს შეუძლია value-ის დაწერა/rotate/test, მაგრამ secret არასდროს გადაეცემა client-ს ან log-ს. Notification domain იყენებს provider-independent interface-ს, რათა Brevo/SMSOffline-ის ცვლილება business logic-ს არ შეეხოს.

## 9. Deployment/operations

- Docker images: API, worker (საჭიროების შემთხვევაში), PostgreSQL, Redis; production managed DB/Redis რეკომენდებულია.
- Alembic migrations CI-ში და release gate-ებში.
- Health/readiness endpoints, structured logs, metrics, tracing და alerting.
- Backup/restore drill, retention policy და disaster recovery runbook აუცილებელია production-მდე.
- Secrets injection runtime-ზე; `.env` მხოლოდ local development-ისთვის და არასდროს commit-ში.

## 10. Quality/security gates

- Unit, integration, API contract, tenant isolation, sync and permission tests.
- Static analysis, formatting, dependency scanning, secret scanning.
- DAST/SAST და external penetration test production launch-მდე.
- No client-trusted tenant ID, no plaintext sensitive offline DB, no secrets in binaries/logs.
