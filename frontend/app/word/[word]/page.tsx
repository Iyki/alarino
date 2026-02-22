import type { Metadata } from "next";

import { HomePage } from "@/components/home-page";
import { getFrontendSiteUrl } from "@/lib/env";
import { makeWordPageTitle } from "@/lib/seo";

const SITE_URL = getFrontendSiteUrl();

interface WordPageProps {
  params: Promise<{ word: string }>;
}

export async function generateMetadata({ params }: WordPageProps): Promise<Metadata> {
  const { word } = await params;
  const decodedWord = decodeURIComponent(word).toLowerCase();

  return {
    title: makeWordPageTitle(decodedWord),
    description: `What is "${decodedWord}" in Yoruba? Find the Yoruba translation for "${decodedWord}" on Alarino.`,
    alternates: {
      canonical: `${SITE_URL}/word/${encodeURIComponent(decodedWord)}`
    }
  };
}

export default async function WordPage({ params }: WordPageProps) {
  const { word } = await params;
  return <HomePage initialWord={decodeURIComponent(word)} />;
}
