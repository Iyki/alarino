import { promises as fs } from "node:fs";
import path from "node:path";

import Markdown from "react-markdown";

export const metadata = {
  title: "About Alarino"
};

async function getAboutMarkdown(): Promise<string> {
  const filePath = path.join(process.cwd(), "content", "about.md");

  try {
    return await fs.readFile(filePath, "utf8");
  } catch {
    return "# About Alarino\n\nAbout content is currently unavailable.";
  }
}

export default async function AboutPage() {
  const markdown = await getAboutMarkdown();

  return (
    <main className="mx-auto w-full max-w-5xl px-4 pb-16 pt-10 sm:px-6 lg:px-8">
      <article className="rounded-3xl bg-brand-beige p-6 shadow-card sm:p-10">
        <div className="prose prose-lg prose-stone max-w-none prose-headings:font-heading prose-headings:text-brand-ink prose-p:text-brand-ink prose-li:text-brand-ink prose-a:text-brand-forest prose-a:underline-offset-4 prose-h1:text-3xl prose-h2:text-2xl prose-h3:text-xl">
          <Markdown>{markdown}</Markdown>
        </div>
      </article>
    </main>
  );
}
