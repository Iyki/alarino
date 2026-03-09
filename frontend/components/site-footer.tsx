import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="bg-brand-brown">
      <div className="mx-auto flex max-w-[80rem] items-center justify-center gap-6 px-6 py-6 text-sm">
        <Link
          href="/"
          className="text-brand-gold transition-colors md:text-[rgba(250,246,239,0.65)] md:hover:text-brand-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          Home
        </Link>
        <span className="h-[3px] w-[3px] rounded-full bg-[rgba(250,246,239,0.2)]" aria-hidden="true" />
        <Link
          href="/about"
          className="text-brand-gold transition-colors md:text-[rgba(250,246,239,0.65)] md:hover:text-brand-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          About
        </Link>
        <span className="h-[3px] w-[3px] rounded-full bg-[rgba(250,246,239,0.2)]" aria-hidden="true" />
        <a
          href="https://github.com/Iyki/alarino"
          target="_blank"
          rel="noreferrer"
          className="text-brand-gold transition-colors md:text-[rgba(250,246,239,0.65)] md:hover:text-brand-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          GitHub
        </a>
        <span className="h-[3px] w-[3px] rounded-full bg-[rgba(250,246,239,0.2)]" aria-hidden="true" />
        <a
          href="https://github.com/Iyki/alarino/issues"
          target="_blank"
          rel="noreferrer"
          className="text-brand-gold transition-colors md:text-[rgba(250,246,239,0.65)] md:hover:text-brand-gold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          Contribute
        </a>
      </div>
    </footer>
  );
}
