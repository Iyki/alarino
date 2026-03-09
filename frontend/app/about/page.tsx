import { promises as fs } from "node:fs";
import path from "node:path";

import Markdown from "react-markdown";

import { HeroBanner } from "@/components/hero-banner";

export const metadata = {
  title: "About Alarino"
};

async function getAboutMarkdown(): Promise<string> {
  const filePath = path.join(process.cwd(), "content", "about.md");

  try {
    return await fs.readFile(filePath, "utf8");
  } catch {
    return "About content is currently unavailable.";
  }
}

export default async function AboutPage() {
  const markdown = await getAboutMarkdown();

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-8">
      <HeroBanner>About Alarino</HeroBanner>
      <article className="animate-fade-in-up-delay-1 rounded-3xl bg-brand-cream p-6 shadow-card sm:p-10">
        <div className="prose prose-lg prose-stone max-w-none prose-headings:font-heading prose-headings:font-bold prose-headings:text-brand-ink prose-p:text-brand-ink/90 prose-li:text-brand-ink/90 prose-a:font-medium prose-a:text-brand-forest prose-a:decoration-brand-forest/30 prose-a:underline-offset-4 hover:prose-a:decoration-brand-forest prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl prose-strong:text-brand-ink">
          <Markdown>{markdown}</Markdown>
        </div>
      </article>
    </main>
  );
}
