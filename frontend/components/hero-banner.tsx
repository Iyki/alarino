import type { ReactNode } from "react";

import Image from "next/image";
import Link from "next/link";

interface HeroBannerProps {
  children: ReactNode;
}

export function HeroBanner({ children }: HeroBannerProps) {
  return (
    <div className="animate-fade-in-up relative mb-5 overflow-hidden rounded-3xl bg-gradient-to-br from-brand-brown to-[#2a1a0e] px-8 py-10 md:px-12">
      <div
        className="pointer-events-none absolute -right-8 -top-8 h-64 w-64 rounded-full"
        style={{ background: "radial-gradient(circle, rgba(200,149,46,0.2) 0%, transparent 70%)" }}
      />
      <div
        className="pointer-events-none absolute -bottom-12 left-[10%] h-48 w-48 rounded-full"
        style={{ background: "radial-gradient(circle, rgba(26,92,50,0.15) 0%, transparent 70%)" }}
      />
      <Link href="/" className="relative z-10 mb-7 inline-flex items-center gap-2.5">
        <Image
          src="/alarino_logo_only.svg"
          alt="Alarino logo"
          width={32}
          height={32}
          priority
          className="brightness-0 invert"
        />
        <span className="font-heading text-xl font-extrabold tracking-tight text-white">Alarino</span>
      </Link>
      <h1 className="relative z-10 font-heading text-[clamp(2rem,4vw,3rem)] font-extrabold leading-[1.15] text-white">
        {children}
      </h1>
    </div>
  );
}
