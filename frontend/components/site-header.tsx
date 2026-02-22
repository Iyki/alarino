"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";

type NavItem = {
  label: string;
  href: string;
  external?: boolean;
};

const NAV_ITEMS: NavItem[] = [
  { label: "About", href: "/about" },
  { label: "Contribute", href: "https://github.com/Iyki/alarino/issues", external: true },
  { label: "Admin", href: "/admin" }
];

function NavLink({ item, className, onClick }: { item: NavItem; className: string; onClick?: () => void }) {
  if (item.external) {
    return (
      <a key={item.href} href={item.href} target="_blank" rel="noreferrer" onClick={onClick} className={className}>
        {item.label}
      </a>
    );
  }

  return (
    <Link key={item.href} href={item.href} onClick={onClick} className={className}>
      {item.label}
    </Link>
  );
}

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
    <header className="sticky top-0 z-50 border-b border-white/10 bg-brand-brown/95 backdrop-blur-md">
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

        <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              className="rounded-lg px-3 py-2 text-sm font-medium text-brand-cream/90 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
            />
          ))}
        </nav>

        <button
          type="button"
          aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={isMenuOpen}
          aria-controls="site-nav-drawer"
          onClick={() => setIsMenuOpen((value) => !value)}
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-brand-gold/30 text-brand-cream transition hover:bg-brand-gold/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold md:hidden"
        >
          <span className="sr-only">Menu</span>
          <span className="relative h-4 w-5">
            <span className={`absolute left-0 top-0 h-0.5 w-5 bg-current transition ${isMenuOpen ? "translate-y-[7px] rotate-45" : ""}`} />
            <span className={`absolute left-0 top-[7px] h-0.5 w-5 bg-current transition ${isMenuOpen ? "opacity-0" : "opacity-100"}`} />
            <span className={`absolute left-0 top-[14px] h-0.5 w-5 bg-current transition ${isMenuOpen ? "-translate-y-[7px] -rotate-45" : ""}`} />
          </span>
        </button>
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
            id="site-nav-drawer"
            className="fixed right-0 top-0 z-[70] h-full w-[min(22rem,100vw)] border-l border-brand-beige/20 bg-brand-cream p-6 text-brand-ink shadow-2xl"
          >
            <div className="mb-6 flex items-center justify-between border-b border-brand-brown/10 pb-4">
              <span className="text-sm font-semibold uppercase tracking-[0.2em] text-brand-ink">Menu</span>
              <button
                type="button"
                onClick={() => setIsMenuOpen(false)}
                className="rounded-lg border border-brand-brown/15 bg-white px-3 py-1.5 text-sm font-medium text-brand-ink transition-colors hover:bg-brand-beige focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
              >
                Close
              </button>
            </div>

            <nav aria-label="Mobile" className="flex flex-col gap-3 text-base font-semibold text-brand-ink">
              {NAV_ITEMS.map((item) => (
                <NavLink
                  key={item.href}
                  item={item}
                  onClick={() => setIsMenuOpen(false)}
                  className="rounded-xl border border-brand-brown/10 bg-white px-4 py-3 transition-colors hover:bg-brand-forest-light focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold"
                />
              ))}
            </nav>
          </aside>
        </div>
      ) : null}
    </header>
  );
}
