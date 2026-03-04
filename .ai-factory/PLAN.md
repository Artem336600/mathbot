# Plan: Security Hardening and Reliability Maximum

## Context
- Date: 2026-03-04
- Mode: fast (`$aif-plan fast`)
- Scope: eliminate discovered vulnerabilities and raise operational reliability for bot + admin webapp + infra.

## Settings
- Testing: Yes (mandatory for each security change)
- Logging: Verbose (DEBUG in development, configurable by `LOG_LEVEL`)
- Documentation: Yes (update README and security/deploy notes after implementation)

## Goals
- Remove production auth bypasses and weak validation paths.
- Lock down API surface (CORS, headers, rate limiting, request size controls).
- Remove insecure infrastructure defaults (public storage, default credentials, unsafe exposure).
- Add reliability controls (timeouts, health checks, transactional safety where needed).
- Prove changes with automated tests and security-focused regression tests.

## Research Context
- Critical findings:
  - Dev auth bypass in mini app auth flow via `test_dev=` header path.
  - CORS configured as wildcard with credentials.
  - Public MinIO bucket and default credentials in compose/example config.
  - Unsafe HTML rendering path in broadcast preview (`innerHTML` from server-provided text).
  - Missing replay-window validation for Telegram `auth_date`.
  - No API rate limiting.

## Tasks

### Phase 1: Authentication and Access Hardening

- [x] T1. Remove auth bypass and strengthen Telegram initData validation.
  - Files: `webapp/auth.py`, `tests/webapp/test_auth.py`
  - Deliverable:
    - Remove/disable `test_dev=` bypass in non-test runtime.
    - Use `hmac.compare_digest(...)` for hash comparison.
    - Validate `auth_date` freshness with strict TTL (for example, 5-10 minutes, configurable by env).
    - Keep strict admin + ban checks unchanged.
  - Logging:
    - Log auth rejection reason category only (`missing_header`, `bad_signature`, `expired_auth`, `not_admin`, `banned`).
    - Never log raw `X-Init-Data`, token, or full user payload.
  - Dependency: none.

- [x] T2. Add explicit environment-controlled auth mode for tests/dev only.
  - Files: `bot/config.py`, `webapp/auth.py`, `.env.example`, `tests/webapp/conftest.py`
  - Deliverable:
    - Add `WEBAPP_AUTH_MODE` with safe default `telegram_strict`.
    - Optional dev/test mode must be explicitly enabled and isolated to test env.
  - Logging:
    - On startup log effective auth mode once (sanitized).
    - Warn if insecure mode enabled.
  - Dependency: T1.

### Phase 2: API Surface Protection

- [x] T3. Replace permissive CORS with allowlist and safe defaults.
  - Files: `webapp/main.py`, `bot/config.py`, `.env.example`, `tests/webapp/test_admin_api.py`
  - Deliverable:
    - Add `WEBAPP_ALLOWED_ORIGINS` config.
    - Fail-safe behavior: if no allowlist in production-like mode, deny cross-origin.
    - Keep support for Telegram WebApp domain/origin list.
  - Logging:
    - Log active CORS mode and count of allowed origins on startup.
    - Warn on wildcard origin usage.
  - Dependency: T2.

- [x] T4. Add security headers middleware.
  - Files: `webapp/main.py`, tests in `tests/webapp/` (new `test_security_headers.py`)
  - Deliverable:
    - Add CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`.
    - Add HSTS toggle for HTTPS deployments.
    - Ensure headers are present for API and static responses.
  - Logging:
    - Startup log with enabled header policy profile (`strict`/`relaxed`).
  - Dependency: T3.

- [x] T5. Add API rate limiting and request size limits.
  - Files: `webapp/main.py`, `webapp/routers/*.py`, `bot/config.py`, tests in `tests/webapp/`
  - Deliverable:
    - Per-IP/admin limits for sensitive routes (broadcast send, import, uploads, ban/unban).
    - Global request body limit and upload caps aligned with existing attachment limits.
    - Clear HTTP 429/413 responses.
  - Logging:
    - Structured rate-limit events with route, actor id/ip, and bucket status.
    - Log blocked oversized requests without body content.
  - Dependency: T4.

### Phase 3: XSS and Input Safety

- [x] T6. Fix broadcast preview XSS vector.
  - Files: `webapp/routers/broadcast.py`, `webapp/static/broadcast.js`, tests in `tests/webapp/`
  - Deliverable:
    - Return plain text preview from API.
    - Render with safe text APIs (`textContent`) or trusted sanitizer when HTML is explicitly needed.
    - Preserve user-visible newline formatting safely.
  - Logging:
    - Log preview request metadata only (length, admin id), no full payload.
  - Dependency: T5.

- [x] T7. Harden file upload validation and object naming safety.
  - Files: `webapp/routers/attachments.py`, `services/storage_service.py`, tests in `tests/webapp/test_attachments.py`
  - Deliverable:
    - Normalize/sanitize uploaded filename component used in object keys.
    - Optional content signature checks for image/doc types (defense in depth).
    - Add per-file and per-request count limits.
  - Logging:
    - Log upload verdict per file (`accepted`/`rejected`) with reason code.
    - Avoid logging raw filenames if they contain suspicious characters.
  - Dependency: T6.

### Phase 4: Infrastructure and Secrets Hardening

- [x] T8. Remove insecure defaults from compose and env templates.
  - Files: `docker-compose.yml`, `.env.example`, `README.md`, `docs/` (new security deployment doc if needed)
  - Deliverable:
    - Replace default static passwords with required env vars.
    - Remove automatic `mc anonymous set public` for production profile.
    - Split dev/prod behavior (safe by default).
    - Add explicit secret rotation and bootstrap instructions.
  - Logging:
    - Startup warns if known default/dev credentials detected.
  - Dependency: T7.

- [x] T9. Add production profile and network hardening.
  - Files: `docker-compose.yml` (or `compose.production.yml`), `Dockerfile`, docs
  - Deliverable:
    - Restrict exposed ports by profile.
    - Run app as non-root where feasible.
    - Add read-only rootfs/tmpfs recommendations and healthchecks.
    - Harden container restart/resource policies.
  - Logging:
    - Add deployment-time checklist log points (config sanity checks).
  - Dependency: T8.

### Phase 5: Reliability and Verification

- [x] T10. Expand automated security regression suite.
  - Files: `tests/webapp/`, `tests/services/`, `pytest.ini`
  - Deliverable:
    - Add tests for expired/replayed initData, CORS allowlist enforcement, CSP headers, rate limits, XSS-safe preview, upload edge cases.
    - Keep fuzz tests green and add targeted property checks for auth parser.
  - Logging:
    - Test logs should assert no secrets/tokens appear in captured logs.
  - Dependency: T1-T9.

- [x] T11. Add operational runbook and incident playbook.
  - Files: `README.md`, `docs/SECURITY.md` (new), optional `docs/OPERATIONS.md`
  - Deliverable:
    - Security baseline checklist for deployment.
    - Emergency actions: revoke token, rotate DB/Redis/MinIO creds, invalidate sessions.
    - Monitoring/alerting recommendations for auth failures, 429 spikes, storage abuse.
  - Logging:
    - Document mandatory log fields and retention guidance.
  - Dependency: T10.

## Dependency Graph (Simplified)
- T1 -> T2 -> T3 -> T4 -> T5 -> T6 -> T7 -> T8 -> T9 -> T10 -> T11

## Commit Plan
- Checkpoint 1 (after T1-T3):
  - `fix(security): harden webapp auth and cors policy`
- Checkpoint 2 (after T4-T6):
  - `fix(security): add headers rate-limits and xss-safe preview`
- Checkpoint 3 (after T7-T9):
  - `chore(security): harden uploads storage and deployment defaults`
- Final checkpoint (after T10-T11):
  - `test(docs): add security regression suite and ops runbook`

## Acceptance Criteria
- No bypass path for admin API auth in production mode.
- Replay/expired Telegram initData is rejected.
- CORS + security headers + rate limiting are enforced and tested.
- Broadcast preview cannot execute injected scripts in admin UI.
- Storage and infra defaults are non-public and non-default-credential in safe profile.
- Security regression tests pass in CI/local.

## Rollout Strategy
1. Implement behind config flags where behavior can break existing local flows.
2. Deploy to staging with strict auth + CORS allowlist and observe logs/metrics.
3. Rotate secrets before production rollout.
4. Enable strict profiles in production and validate post-deploy checklist.
