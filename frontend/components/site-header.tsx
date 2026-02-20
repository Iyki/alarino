"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";

export function SiteHeader() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    if (!isMenuOpen) {
      document.body.classList.remove("overflow-hidden");
      return;
    }

    document.body.classList.add("overflow-hidden");

    const onEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsMenuOpen(false);
      }
    };

    window.addEventListener("keydown", onEscape);
    return () => {
      window.removeEventListener("keydown", onEscape);
      document.body.classList.remove("overflow-hidden");
    };
  }, [isMenuOpen]);

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

        <button
          type="button"
          aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={isMenuOpen}
          aria-controls="mobile-nav-drawer"
          onClick={() => setIsMenuOpen((value) => !value)}
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-brand-gold/30 text-brand-cream transition hover:bg-brand-gold/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
        >
          <span className="sr-only">Menu</span>
          <span className="relative h-4 w-5">
            <span className={`absolute left-0 top-0 h-0.5 w-5 bg-current transition ${isMenuOpen ? "translate-y-[7px] rotate-45" : ""}`} />
            <span className={`absolute left-0 top-[7px] h-0.5 w-5 bg-current transition ${isMenuOpen ? "opacity-0" : "opacity-100"}`} />
            <span className={`absolute left-0 top-[14px] h-0.5 w-5 bg-current transition ${isMenuOpen ? "-translate-y-[7px] -rotate-45" : ""}`} />
          </span>
        </button>

        <nav className="hidden items-center gap-5 text-sm font-medium text-brand-cream">
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

      {isMenuOpen ? (
        <div>
          <button
            type="button"
            aria-label="Close menu overlay"
            onClick={() => setIsMenuOpen(false)}
            className="fixed inset-0 z-[60] bg-brand-ink/80"
          />
          <aside
            id="mobile-nav-drawer"
            className="fixed right-0 top-0 z-[70] h-full w-[min(24rem,100vw)] border-l border-brand-brown/15 bg-white p-6 text-brand-ink shadow-2xl"
          >
            <div className="mb-6 flex items-center justify-between border-b border-brand-brown/15 pb-4">
              <span className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-ink">Menu</span>
              <button
                type="button"
                onClick={() => setIsMenuOpen(false)}
                className="rounded-md border border-brand-brown/25 bg-brand-beige px-2 py-1 text-brand-ink hover:bg-brand-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
              >
                Close
              </button>
            </div>

            <nav className="flex flex-col gap-3 text-base font-semibold text-brand-ink">
              <Link
                href="/about"
                onClick={() => setIsMenuOpen(false)}
                className="rounded-lg border border-brand-brown/15 bg-brand-beige px-3 py-2 transition hover:bg-brand-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
              >
                About
              </Link>
              <a
                href="https://github.com/Iyki/alarino/issues"
                target="_blank"
                rel="noreferrer"
                onClick={() => setIsMenuOpen(false)}
                className="rounded-lg border border-brand-brown/15 bg-brand-beige px-3 py-2 transition hover:bg-brand-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
              >
                Contribute
              </a>
              <Link
                href="/admin"
                onClick={() => setIsMenuOpen(false)}
                className="rounded-lg border border-brand-brown/15 bg-brand-beige px-3 py-2 transition hover:bg-brand-cream focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
              >
                Admin
              </Link>
            </nav>
          </aside>
        </div>
      ) : null}
    </header>
  );
}
