# Deployment

## Portable Docker

```bash
docker run -d --name open-system \
  -e HERMES_HOME=/opt/data \
  -e HERMES_DASHBOARD=true \
  -e HERMES_DASHBOARD_HOST=0.0.0.0 \
  -e HERMES_DASHBOARD_PORT=9119 \
  -e HERMES_DASHBOARD_BASIC_AUTH_USERNAME=admin \
  -e HERMES_DASHBOARD_BASIC_AUTH_PASSWORD=changeme \
  -e HERMES_DASHBOARD_BASIC_AUTH_SECRET=changeme-long-secret \
  -e API_SERVER_ENABLED=true \
  -e API_SERVER_HOST=0.0.0.0 \
  -e API_SERVER_PORT=8642 \
  -e API_SERVER_KEY=changeme-min-16-chars \
  -e HERMES_GATEWAY_BOOTSTRAP_STATE=running \
  -v open-system-data:/opt/data \
  -p 9119:9119 -p 8642:8642 \
  kairocasino/open-system@sha256:<DIGEST>
```

Same image runs on Zeabur, VPS, or local Docker.

## Production pin

Always prefer `@sha256:…` over `:latest`.
