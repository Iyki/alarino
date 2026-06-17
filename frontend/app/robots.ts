import type { MetadataRoute } from "next";

import { getFrontendSiteUrl } from "@/lib/env";

const SITE_URL = getFrontendSiteUrl();

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/admin", "/api/"]
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL
  };
}
