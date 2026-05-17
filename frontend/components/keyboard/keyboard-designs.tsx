"use client";

import { DesignSection } from "./keyboard-chrome";
import { DesignDiacriticRibbon } from "./design-diacritic-ribbon";
import { DesignTileModeToggleDvorak } from "./design-tile-mode-toggle-dvorak";
import { DesignTileModeToggleInlineB } from "./design-tile-mode-toggle-inline-b";

export function KeyboardDesigns() {
  return (
    <div>
      <DesignSection
        title="Diacritic Ribbon"
        badge="Desktop"
        blurb="For fluent typists on a hardware keyboard: type normally, tap the ribbon for the Yoruba-specific glyphs, and hold any dotted key for its low / mid / high tone."
      >
        <DesignDiacriticRibbon />
      </DesignSection>

      <DesignSection
        title="Dvorak"
        badge="Mobile · mode toggle"
        blurb="Dvorak-style layout with vowels on the home row. Switch between Yorùbá and English; hold a dotted vowel or nasal for tones."
      >
        <DesignTileModeToggleDvorak />
      </DesignSection>

      <DesignSection
        title="Inline B · gb Moved to Row 3"
        badge="Mobile · mode toggle"
        blurb="QWERTY-familiar order filtered to the Yoruba alphabet, with the gb digraph relocated to Row 3 so the top rows stay evenly spaced. Hold a dotted key for tones."
      >
        <DesignTileModeToggleInlineB />
      </DesignSection>
    </div>
  );
}
