# Droplet Bootstrap (Docker + Network)

This is the source-of-truth host bootstrap flow for a fresh DigitalOcean Droplet.
It codifies Docker installation and firewall/network setup so deployment is reproducible.

## What This Configures
- Docker Engine + Docker Compose from Debian repositories (`docker.io` + `docker-compose`)
- Swapfile setup by default (`CONFIGURE_SWAP=true`, `SWAP_SIZE_GB=2`)
- Optional host UFW inbound rules (only when `CONFIGURE_HOST_FIREWALL=true`):
  - SSH port `22/tcp`
  - `80/tcp`
  - `443/tcp`
- Caddy runtime via Docker image (`caddy:2`) in compose, not a host-level Caddy install

## Run Bootstrap
From repo root on the droplet:

```bash
sudo ./scripts/bootstrap_droplet.sh
```

This bootstrap targets Debian 13 (`trixie`) with distro-native Docker packages.

Optional overrides:

```bash
sudo CONFIGURE_SWAP=false ./scripts/bootstrap_droplet.sh
sudo SWAP_SIZE_GB=4 ./scripts/bootstrap_droplet.sh
sudo CONFIGURE_HOST_FIREWALL=true ./scripts/bootstrap_droplet.sh
```

## Recommended Port Policy
- Open: `22`, `80`, `443`
- Production traffic flows through `caddy` on `80/443` to `frontend`.
- Browser API calls use same-origin `/api` through frontend.
- If you need a separate backend host/path, route it through your edge layer (Caddy/load balancer) on `80/443` instead of exposing host `5001`.

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
   docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build backend frontend caddy
   ```

## Validation
```bash
swapon --show
free -h
docker compose ps
curl -I -H "Host: alarino.com" http://127.0.0.1/
curl -sS https://alarino.com/api/health
```

Expected:
- `caddy`, `frontend`, and `backend` containers are up
- first curl returns `308` redirect to `https://alarino.com/...`
- health returns success JSON with status 200 (once DNS points to droplet and cert is issued)
