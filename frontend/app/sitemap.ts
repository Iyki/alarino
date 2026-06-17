import type { MetadataRoute } from "next";

import { getBackendInternalUrl, getFrontendSiteUrl } from "@/lib/env";

const SITE_URL = getFrontendSiteUrl();

// Render at request time, never at build. The frontend image runs
// `next build` (frontend/Dockerfile) before the compose backend is
// reachable, so a prerendered or ISR sitemap would bake in the
// empty-backend fallback and keep serving a wordless sitemap until the
// revalidate window elapsed — re-baked wordless on every deploy.
// force-dynamic makes each request query the live backend instead.
export const dynamic = "force-dynamic";

const STATIC_ROUTES: MetadataRoute.Sitemap = [
  { url: `${SITE_URL}/`, changeFrequency: "daily", priority: 1 },
  { url: `${SITE_URL}/keyboard`, changeFrequency: "monthly", priority: 0.6 },
  { url: `${SITE_URL}/about`, changeFrequency: "monthly", priority: 0.4 }
];

async function fetchTranslatableWords(): Promise<string[]> {
  try {
    const res = await fetch(`${getBackendInternalUrl()}/api/words`, {
      cache: "no-store"
    });
    if (!res.ok) {
      return [];
    }
    const body = await res.json();
    const words = body?.data?.words;
    return Array.isArray(words) ? words : [];
  } catch {
    return [];
  }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const words = await fetchTranslatableWords();
  const wordRoutes: MetadataRoute.Sitemap = words.map((word) => ({
    url: `${SITE_URL}/word/${encodeURIComponent(word)}`,
    changeFrequency: "weekly",
    priority: 0.8
  }));

  return [...STATIC_ROUTES, ...wordRoutes];
}
