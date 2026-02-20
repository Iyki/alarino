import type { Metadata } from "next";
import { Cormorant_Garamond, Plus_Jakarta_Sans } from "next/font/google";

import "@/app/globals.css";
import { SiteHeader } from "@/components/site-header";

const heading = Cormorant_Garamond({
  subsets: ["latin"],
  variable: "--font-heading",
  weight: ["500", "600", "700"]
});

const body = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "600", "700"]
});

const SITE_URL = process.env.FRONTEND_SITE_URL || "https://alarino.com";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: "Alarino | English to Yoruba Translator & Dictionary Online",
  description: "Alarino is a community-backed English to Yoruba translation dictionary with daily learning tools.",
  keywords: ["Yoruba", "English", "translation", "dictionary", "African languages"],
  alternates: {
    canonical: "/"
  }
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${heading.variable} ${body.variable}`}>
      <body className="font-body text-brand-ink antialiased">
        <div className="min-h-screen bg-app-gradient pb-8">
          <SiteHeader />
          {children}
        </div>
      </body>
    </html>
  );
}
