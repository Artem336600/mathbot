# Security Runbook

## Baseline Before Production

- Set strong secrets in `.env`:
  - `BOT_TOKEN`
  - `POSTGRES_PASSWORD`
  - `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`
  - `S3_ACCESS_KEY` / `S3_SECRET_KEY`
- Keep `WEBAPP_AUTH_MODE=telegram_strict`.
- Set strict CORS allowlist in `WEBAPP_ALLOWED_ORIGINS`.
- Keep `MINIO_BUCKET_PUBLIC=false` unless explicitly required.
- Enable HTTPS and set `WEBAPP_ENABLE_HSTS=true` behind TLS.

## Secure Startup

- Development:
  - `docker-compose up -d`
- Production-hardened profile:
  - `docker-compose -f docker-compose.yml -f compose.production.yml up -d`

## Incident Response

1. Revoke Telegram bot token in BotFather and update `BOT_TOKEN`.
2. Rotate DB and MinIO credentials:
   - `POSTGRES_PASSWORD`
   - `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD`
   - `S3_ACCESS_KEY` / `S3_SECRET_KEY`
3. Restart services after rotation.
4. Review logs for:
   - repeated auth failures (`[WEBAPP:AUTH] reject reason=...`)
   - rate-limit blocks (`request_blocked reason=rate_limited`)
   - oversized payload attempts (`payload_too_large`)
5. If abuse is ongoing:
   - temporarily tighten `WEBAPP_RATE_LIMIT_SENSITIVE_PER_WINDOW`
   - restrict `WEBAPP_ALLOWED_ORIGINS` further
   - disable broadcast operations operationally.

## Operational Monitoring

- Track:
  - 401/403 rate on `/api/*`
  - 429 spikes on sensitive endpoints
  - attachment upload failures by reason
- Ensure logs never contain:
  - full `X-Init-Data`
  - bot tokens or storage secrets
  - raw credentials in exception messages

