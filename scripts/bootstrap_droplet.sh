#!/usr/bin/env bash
set -euo pipefail

# Idempotent host bootstrap for Ubuntu/Debian droplets.
# Installs Docker Engine + Compose from Debian repositories.
# Configures swap by default for small droplets.
# Optional: configures host UFW firewall (off by default).

CONFIGURE_SWAP="${CONFIGURE_SWAP:-true}"
SWAP_SIZE_GB="${SWAP_SIZE_GB:-2}"
SWAPFILE_PATH="/swapfile"
CONFIGURE_HOST_FIREWALL="${CONFIGURE_HOST_FIREWALL:-false}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root (or with sudo)." >&2
  exit 1
fi

echo "[bootstrap] Installing base packages..."
apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git

echo "[bootstrap] Installing Docker engine and compose packages (Debian-native)..."
apt-get install -y --no-install-recommends docker.io docker-compose

systemctl enable --now docker

if docker compose version >/dev/null 2>&1; then
  echo "[bootstrap] Compose command detected: docker compose"
else
  echo "[bootstrap] No Docker Compose command found after install." >&2
  exit 1
fi

if [[ "${CONFIGURE_SWAP}" == "true" ]]; then
  echo "[bootstrap] Configuring swap (${SWAP_SIZE_GB}G at ${SWAPFILE_PATH})..."

  if [[ ! -f "${SWAPFILE_PATH}" ]]; then
    fallocate -l "${SWAP_SIZE_GB}G" "${SWAPFILE_PATH}"
    chmod 600 "${SWAPFILE_PATH}"
    mkswap "${SWAPFILE_PATH}"
  fi

  if ! swapon --show=NAME | grep -qx "${SWAPFILE_PATH}"; then
    swapon "${SWAPFILE_PATH}"
  fi

  if ! grep -q "^${SWAPFILE_PATH} " /etc/fstab; then
    echo "${SWAPFILE_PATH} none swap sw 0 0" >> /etc/fstab
  fi
else
  echo "[bootstrap] Skipping swap setup (CONFIGURE_SWAP=false)."
fi

if [[ "${CONFIGURE_HOST_FIREWALL}" == "true" ]]; then
  echo "[bootstrap] Configuring UFW rules..."
  apt-get install -y --no-install-recommends ufw
  ufw allow 22/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp

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
echo "  4) Deploy via push to main or run compose manually with backend/frontend/caddy services."
