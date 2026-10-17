# HR-OTO — Roadmap და დამოკიდებულებები

## Current delivery

Stage 6 — Company Admin Application.

## Stage 0 — დოკუმენტაცია და დაგეგმვა (მიმდინარე)

**შედეგი:** მოთხოვნების baseline, არქიტექტურა, ეტაპები, გადაწყვეტილებების ჟურნალი, საწყისი საქაღალდეები.  
**დამოკიდებულება:** მომხმარებლის მოთხოვნები.  
**სტატუსი:** დასრულებული.

## Stage 1 — Foundation და უსაფრთხოების ბირთვი

**შედეგი:** repository conventions, Flutter shells სამივე აპისთვის, FastAPI skeleton, Docker local stack, config, health checks, CI baseline, PostgreSQL/Alembic bootstrap, Redis, logging, error model.  
**დამოკიდებულია:** Stage 0; logo/assets-ის მიღება optional.  
**Exit:** სამივე app build იწყება; API/DB/Redis local stack ჯანმრთელია; no secrets committed.

## Stage 2 — Identity, tenancy და licensing core

**შედეგი:** central database, authentication/session/device lifecycle, Owner global context, tenant creation/activation/blocking, company code/subdomain, database-per-tenant provisioning and migrations, RBAC, plan/license/trial/subscription primitives, audit trail.  
**დამოკიდებულია:** Stage 1.  
**Exit:** automated cross-tenant isolation and permission tests pass.

## Stage 3 — Flutter design system და app shells

**შედეგი:** Georgian localization foundation, typography/colors/components, dark/light mode, navigation, adaptive Windows/mobile layouts, secure token storage, encrypted SQLite bootstrap.  
**დამოკიდებულია:** Stage 1–2.  
**Exit:** Employee/Admin/Owner shells usable with authenticated states.

## Stage 4 — Owner commercial management

**შედეგი:** packages, versioned monthly/annual pricing, currency/discounts, feature catalog, resource limits, company overrides, trial grants, subscription price locks, effective entitlements engine, Owner UI and audit enforcement.  
**დამოკიდებულია:** Stage 2–3.  
**სტატუსი:** დასრულებული.

## Stage 5 — Offline sync foundation და Verification interface

**შედეგი:** 48-hour policy, outbox/inbox, retry/backoff, cursors, conflict contracts, restricted offline state, extensible `VerificationProvider` interface; no PIN implementation.  
**დამოკიდებულია:** Stage 2–4.  
**Exit:** deterministic sync tests and provider mock pass.

## Stage 6 — Organization და employee core

**შედეგი:** employees, departments, positions, branches, administrators, devices, tenant limits, Admin mobile/Windows parity baseline.  
**დამოკიდებულია:** Stage 2–5.

## Stage 7 — Attendance, schedules და leave

**შედეგი:** schedules, attendance/work hours, breaks, lateness/absence, leave; Verification provider integration remains configurable.  
**დამოკიდებულია:** Stage 5–6.

## Stage 8 — Notifications, documents და announcements

**შედეგი:** in-app/push abstraction, Brevo/SMSOffline server adapters, templates/senders/quotas, secure documents, announcements.  
**დამოკიდებულია:** Stage 2, 6; provider credentials and secret storage decision.

## Stage 9 — Payroll, KPI, discipline, recruitment და training

**შედეგი:** financial/PII-heavy and performance modules with approval/audit workflows.  
**დამოკიდებულია:** Stage 6–8; detailed domain rules and legal review.

## Stage 10 — Reports და Owner commercial operations

**შედეგი:** Excel/PDF reports, plan feature flags, limits, individualized terms, subscription controls, monitoring dashboards.  
**დამოკიდებულია:** Stage 2, 6–9.

## Stage 11 — Production hardening და release

**შედეგი:** observability, backups/restore, load/security testing, app signing, store/Windows packaging, release runbooks, support/admin procedures.  
**დამოკიდებულია:** ყველა წინა stage.

## Dependency summary

```text
0 → 1 → 2 → 3 → 4 → 5 → 6
              ├→ 7 ─────┐
              └→ 8 ─────┼→ 9 → 10
```

Parallel work is allowed only when it does not bypass the dependency gates, especially tenant isolation, authorization and encrypted offline storage.
