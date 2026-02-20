const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host"
]);

export function getBackendInternalUrl(): string {
  return process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:5001";
}

export function buildBackendUrl(pathSegments: string[], search: string): string {
  const cleanSegments = pathSegments.map((segment) => encodeURIComponent(segment));
  const path = cleanSegments.join("/");
  return `${getBackendInternalUrl()}/api/${path}${search}`;
}

export function filterForwardHeaders(headers: Headers): Headers {
  const filtered = new Headers();

  headers.forEach((value, key) => {
    const lowerKey = key.toLowerCase();

    if (HOP_BY_HOP_HEADERS.has(lowerKey)) {
      return;
    }

    filtered.set(key, value);
  });

  return filtered;
}
