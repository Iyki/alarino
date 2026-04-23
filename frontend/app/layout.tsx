import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";

import "@/app/globals.css";
import { SiteFooter } from "@/components/site-footer";
import { getFrontendSiteUrl } from "@/lib/env";
const SITE_URL = getFrontendSiteUrl();

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap"
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-heading",
  display: "swap"
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "Alarino | English to Yoruba Translator & Dictionary Online",
  description: "Alarino is a community-backed English to Yoruba translation dictionary with daily learning tools.",
  keywords: ["Yoruba", "English", "translation", "dictionary", "African languages"],
  icons: {
    icon: [{ url: "/alarino_logo_only.svg?v=1", type: "image/svg+xml" }],
    shortcut: "/alarino_logo_only.svg?v=1"
  },
  alternates: {
    canonical: "/"
  }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <body className="font-body text-brand-ink antialiased">
        <div className="flex min-h-screen flex-col bg-brand-beige">
          <div className="flex-1">{children}</div>
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}
