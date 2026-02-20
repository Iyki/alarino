import { getBackendInternalUrl } from "@/lib/env";

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
