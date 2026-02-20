const DEFAULT_FRONTEND_SITE_URL = "https://alarino.com";
const DEFAULT_BACKEND_INTERNAL_URL = "http://127.0.0.1:5001";

export function getFrontendSiteUrl(): string {
  return process.env.FRONTEND_SITE_URL || DEFAULT_FRONTEND_SITE_URL;
}

export function getBackendInternalUrl(): string {
  return process.env.BACKEND_INTERNAL_URL || DEFAULT_BACKEND_INTERNAL_URL;
}
