import type { MetadataRoute } from "next";

import { getBackendInternalUrl, getFrontendSiteUrl } from "@/lib/env";

const SITE_URL = getFrontendSiteUrl();

// Regenerate the sitemap at most once a day so newly added words show up
// without a redeploy. If the backend is unreachable (e.g. during the build)
// we still emit the static routes below rather than failing.
export const revalidate = 86400;

const STATIC_ROUTES: MetadataRoute.Sitemap = [
  { url: `${SITE_URL}/`, changeFrequency: "daily", priority: 1 },
  { url: `${SITE_URL}/keyboard`, changeFrequency: "monthly", priority: 0.6 },
  { url: `${SITE_URL}/about`, changeFrequency: "monthly", priority: 0.4 }
];

async function fetchTranslatableWords(): Promise<string[]> {
  try {
    const res = await fetch(`${getBackendInternalUrl()}/api/words`, {
      next: { revalidate }
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
