import Image from "next/image";
import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-brand-gold/25 bg-brand-brown/95 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-6 px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="inline-flex items-center gap-3 text-white">
          <Image
            src="/alarino-logo-fit.svg"
            alt="Alarino logo"
            width={42}
            height={42}
            priority
            className="brightness-0 invert"
          />
        </Link>

        <nav className="flex items-center gap-5 text-sm font-medium text-brand-cream">
          <Link href="/about" className="transition hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold">
            About
          </Link>
          <a
            href="https://github.com/Iyki/alarino/issues"
            target="_blank"
            rel="noreferrer"
            className="transition hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
          >
            Contribute
          </a>
          <Link href="/admin" className="transition hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold">
            Admin
          </Link>
        </nav>
      </div>
    </header>
  );
}
