"use client";

import { useEffect, useState } from "react";

// Returns null until mounted (so the caller can render a neutral
// placeholder and avoid an SSR/client mismatch), then the live match.
export function useMediaQuery(query: string): boolean | null {
  const [matches, setMatches] = useState<boolean | null>(null);

  useEffect(() => {
    const mql = window.matchMedia(query);
    const sync = () => setMatches(mql.matches);
    sync();
    mql.addEventListener("change", sync);
    return () => mql.removeEventListener("change", sync);
  }, [query]);

  return matches;
}
