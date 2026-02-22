import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-brand-brown/10 bg-brand-cream/60 backdrop-blur-sm">
      <div className="mx-auto flex w-full max-w-6xl flex-col items-center gap-4 px-4 py-8 sm:flex-row sm:justify-between sm:px-6 lg:px-8">
        <p className="text-sm text-brand-ink/60">
          &copy; {new Date().getFullYear()} Alarino. A community-backed Yoruba dictionary.
        </p>
        <nav className="flex items-center gap-6">
          <Link
            href="/about"
            className="text-sm text-brand-ink/60 transition-colors hover:text-brand-forest focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
          >
            About
          </Link>
          <a
            href="https://github.com/Iyki/alarino"
            target="_blank"
            rel="noreferrer"
            className="text-sm text-brand-ink/60 transition-colors hover:text-brand-forest focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
          >
            GitHub
          </a>
          <a
            href="https://github.com/Iyki/alarino/issues"
            target="_blank"
            rel="noreferrer"
            className="text-sm text-brand-ink/60 transition-colors hover:text-brand-forest focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
          >
            Contribute
          </a>
        </nav>
      </div>
    </footer>
  );
}
