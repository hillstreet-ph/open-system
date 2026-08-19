# Runbook

## 502 on Zeabur

1. Logs: startup probe connection refused?
2. Is dashboard refusing bind (missing basic auth env)?
3. Is health check pointing at the correct port id?
4. Increase probe failure threshold for cold start
5. Confirm image digest and `/opt/data` volume still mounted

## Promote production image

1. CI green on `main`
2. Docker release published; note digest
3. Staging smoke
4. Backup volume
5. Pin production to digest
6. Health + Telegram smoke
7. Keep previous digest for rollback

## Upstream update

1. Let `upstream-sync` open PR
2. Review checklist in UPSTREAM-SYNC.md
3. Merge only when required checks pass
4. Does **not** auto-change production image
