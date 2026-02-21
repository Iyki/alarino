# Droplet Bootstrap (Docker + Network)

This is the source-of-truth host bootstrap flow for a fresh DigitalOcean Droplet.
It codifies Docker installation and firewall/network setup so deployment is reproducible.

## What This Configures
- Docker Engine + Docker Compose plugin
- Optional host UFW inbound rules (only when `CONFIGURE_HOST_FIREWALL=true`):
  - SSH port (default `22`)
  - `80/tcp`
  - `443/tcp`
  - optional API port `5001/tcp` (disabled by default)
- Caddy runtime via Docker image (`caddy:2`) in compose, not a host-level Caddy install

## Run Bootstrap
From repo root on the droplet:

```bash
sudo SSH_PORT=22 CONFIGURE_HOST_FIREWALL=false ./scripts/bootstrap_droplet.sh
```

Optional host firewall configuration with UFW:

```bash
sudo SSH_PORT=22 CONFIGURE_HOST_FIREWALL=true ALLOW_API_PORT=false ./scripts/bootstrap_droplet.sh
```

Optional (only if you want direct public API access on host port `5001`):

```bash
sudo SSH_PORT=22 CONFIGURE_HOST_FIREWALL=true ALLOW_API_PORT=true API_PORT=5001 ./scripts/bootstrap_droplet.sh
```

## Recommended Port Policy
- Open: `22`, `80`, `443`
- Keep `5001` closed unless you explicitly need direct backend access from the internet.
- Production traffic flows through `caddy` on `80/443` to `frontend`.
- Browser API calls use same-origin `/api` through frontend.

## After Bootstrap
1. Add your SSH key to `/root/.ssh/authorized_keys`.
2. Clone repo as root:
   ```bash
   git clone https://github.com/Iyki/alarino.git
   cd alarino
   ```
3. Ensure GitHub Actions secrets are configured:
   - `SSH_KEY_DEPLOY`
   - `DO_USERNAME`
   - `DO_HOST`
   - `BACKEND_ENV_FILE`
4. Deploy via CI (push to `main`) or manually:
   ```bash
   PRIMARY_DOMAIN=alarino.com SECONDARY_DOMAIN=www.alarino.com \
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build backend frontend caddy
   ```

## Validation
```bash
docker compose ps
curl -I -H "Host: alarino.com" http://127.0.0.1/
curl -sS https://alarino.com/api/health
```

Expected:
- `caddy`, `frontend`, and `backend` containers are up
- first curl returns `308` redirect to `https://alarino.com/...`
- health returns success JSON with status 200 (once DNS points to droplet and cert is issued)
