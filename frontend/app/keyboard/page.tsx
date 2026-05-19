import { HeroBanner } from "@/components/hero-banner";
import { KeyboardDesigns } from "@/components/keyboard/keyboard-designs";

export const metadata = {
  title: "Yoruba Keyboard",
  description:
    "Type Yorùbá with correct tone marks and special characters (ẹ ọ ṣ gb) — an on-screen keyboard for mobile and a diacritic ribbon for desktop hardware keyboards.",
};

export default function KeyboardPage() {
  return (
    <main className="mx-auto w-full max-w-5xl px-3 py-6 sm:px-6 sm:py-8">
      <HeroBanner>Yoruba Keyboard</HeroBanner>
      <KeyboardDesigns />
    </main>
  );
}
