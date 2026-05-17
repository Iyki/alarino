import { HeroBanner } from "@/components/hero-banner";
import { KeyboardDesigns } from "@/components/keyboard/keyboard-designs";

export const metadata = {
  title: "Yoruba Keyboard",
};

export default function KeyboardPage() {
  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-8">
      <HeroBanner>Yoruba Keyboard</HeroBanner>
      <KeyboardDesigns />
    </main>
  );
}
