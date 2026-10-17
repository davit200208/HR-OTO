# HR-OTO Security Status

- Tenant context is derived from the authenticated session; URL/company code cannot switch tenants.
- Owner-only provider endpoints are separate from Company Admin endpoints.
- Provider secrets are never returned in full and are not stored as plaintext database fields.
- Employee payroll, documents, leave and attendance APIs are self-scoped.
- Offline lease is server-issued and expires after 48 hours; local restart cannot extend it.
- Idempotency keys and server sync event ledger prevent duplicate event acceptance.
- Payroll final approval requires an online authenticated request and calculated state.
- Attendance verification is disabled until a real provider is selected.

Before production: configure KMS/Vault, rotate bootstrap/JWT secrets, enable HTTPS, run PostgreSQL/Redis backups and restore drills, install dependency scanning, configure platform signing, and complete penetration testing.
