#!/usr/bin/env bash
set -euo pipefail

# Idempotent host bootstrap for Ubuntu/Debian droplets.
# Installs Docker + Compose plugin.
# Optional: configures host UFW firewall (off by default).

SSH_PORT="${SSH_PORT:-22}"
CONFIGURE_HOST_FIREWALL="${CONFIGURE_HOST_FIREWALL:-false}"
ALLOW_API_PORT="${ALLOW_API_PORT:-false}"
API_PORT="${API_PORT:-5001}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root (or with sudo)." >&2
  exit 1
fi

echo "[bootstrap] Installing base packages..."
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  gnupg \
  lsb-release

echo "[bootstrap] Installing Docker engine and compose plugin..."
apt-get install -y --no-install-recommends docker.io docker-compose-plugin
systemctl enable --now docker

if [[ "${CONFIGURE_HOST_FIREWALL}" == "true" ]]; then
  echo "[bootstrap] Configuring UFW rules..."
  apt-get install -y --no-install-recommends ufw
  ufw allow "${SSH_PORT}/tcp"
  ufw allow 80/tcp
  ufw allow 443/tcp

  if [[ "${ALLOW_API_PORT}" == "true" ]]; then
    echo "[bootstrap] Opening API port ${API_PORT}/tcp"
    ufw allow "${API_PORT}/tcp"
  else
    echo "[bootstrap] API port ${API_PORT}/tcp left closed (recommended for same-origin /api deployments)."
  fi

  ufw --force enable
else
  echo "[bootstrap] Skipping host firewall changes (CONFIGURE_HOST_FIREWALL=false)."
  echo "[bootstrap] Ensure DigitalOcean Cloud Firewall allows 22/tcp, 80/tcp, and 443/tcp."
fi

echo
echo "[bootstrap] Complete."
echo "[bootstrap] Next steps:"
echo "  1) Add your SSH key to /root/.ssh/authorized_keys"
echo "  2) Clone repo as root: git clone https://github.com/Iyki/alarino.git"
echo "  3) Configure GitHub Actions secrets (SSH_KEY_DEPLOY, DO_USERNAME, DO_HOST, BACKEND_ENV_FILE)"
echo "  4) Deploy via push to main or run compose manually with PRIMARY_DOMAIN/SECONDARY_DOMAIN and caddy service."
