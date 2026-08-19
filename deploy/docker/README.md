# Portable Docker run (any host)

```bash
# Prefer digest for production
IMAGE="${DOCKERHUB_USERNAME}/open-system@sha256:REPLACE_ME"

docker volume create open-system-data

docker run -d \
  --name open-system \
  --restart unless-stopped \
  -v open-system-data:/opt/data \
  -p 9119:9119 \
  -p 8642:8642 \
  -e HERMES_DASHBOARD=true \
  -e HERMES_DASHBOARD_HOST=0.0.0.0 \
  -e API_SERVER_ENABLED=true \
  -e API_SERVER_HOST=0.0.0.0 \
  -e API_SERVER_PORT=8642 \
  -e API_SERVER_KEY="from-secret-store" \
  -e HERMES_DASHBOARD_BASIC_AUTH_USERNAME=admin \
  -e HERMES_DASHBOARD_BASIC_AUTH_PASSWORD="from-secret-store" \
  "$IMAGE" \
  gateway run
```

Do **not** pass `--entrypoint` unless you have a verified reason.  
Restore data first with `scripts/restore.sh` when recovering from backup.
