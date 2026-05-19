import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Allow a separate build directory (e.g. a production build for LAN
  // testing) so it doesn't clobber the dev server's .next.
  distDir: process.env.NEXT_DISTDIR || ".next"
};

export default nextConfig;
