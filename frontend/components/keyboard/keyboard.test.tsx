import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DesignDiacriticRibbon } from "./design-diacritic-ribbon";
import { DVORAK_LAYOUT } from "./design-tile-mode-toggle-dvorak";
import { QWERTY_LAYOUT } from "./design-tile-mode-toggle-inline-b";
import {
  countCharacters,
  lastGraphemeLength,
  toNFC,
  useKeyboardText,
} from "./keyboard-chrome";
import { KeyboardDesigns } from "./keyboard-designs";
import { NUM_LAYOUT } from "./mobile-keyboard";
import { pickAlign, popoverAlignClass } from "./popover-align";
import { hasTones, retoneSuffix, toneVariants, vowelAccents } from "./tones";

describe("tones", () => {
  it("covers the seven vowels plus syllabic nasals", () => {
    for (const c of ["a", "e", "ẹ", "i", "o", "ọ", "u", "m", "n"]) {
      expect(hasTones(c)).toBe(true);
    }
    expect(hasTones("b")).toBe(false);
    expect(hasTones("gb")).toBe(false);
  });

  it("orders tone variants low, mid, high", () => {
    expect(toneVariants("a")).toEqual(["à", "a", "á"]);
    expect(toneVariants("o")).toEqual(["ò", "o", "ó"]);
    expect(toneVariants("z")).toBeNull();
  });

  it("offers the full Yoruba form set for held vowels", () => {
    expect(vowelAccents("a")).toEqual(["a", "à", "á"]);
    expect(vowelAccents("e")).toEqual(["e", "è", "é", "ẹ", "ẹ̀", "ẹ́"]);
    expect(vowelAccents("o")).toEqual(["o", "ò", "ó", "ọ", "ọ̀", "ọ́"]);
    expect(vowelAccents("b")).toBeNull();
  });
});

describe("popover alignment", () => {
  it("anchors edge keys inward and centers the rest", () => {
    expect(pickAlign(0, 5)).toBe("left");
    expect(pickAlign(4, 5)).toBe("right");
    expect(pickAlign(2, 5)).toBe("center");
    // wide rows reserve a 2-key buffer on each side
    expect(pickAlign(1, 11)).toBe("left");
    expect(pickAlign(9, 11)).toBe("right");
    expect(pickAlign(5, 11)).toBe("center");
  });

  it("maps alignment to non-overflowing classes", () => {
    expect(popoverAlignClass("left")).toContain("left-0");
    expect(popoverAlignClass("right")).toContain("right-0");
    expect(popoverAlignClass("center")).toContain("-translate-x-1/2");
  });
});

function mockViewport(isDesktop: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: isDesktop,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

describe("KeyboardDesigns (responsive)", () => {
  const originalMatchMedia = window.matchMedia;
  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  it("shows only the desktop ribbon on desktop, with no layout toggle", async () => {
    mockViewport(true);
    render(<KeyboardDesigns />);
    expect(
      await screen.findByPlaceholderText(/hold a vowel for its yoruba forms/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "QWERTY" }),
    ).not.toBeInTheDocument();
  });

  it("shows the mobile keyboard with a QWERTY/Dvorak toggle on mobile", async () => {
    mockViewport(false);
    render(<KeyboardDesigns />);

    const qwerty = await screen.findByRole("button", { name: "QWERTY" });
    const dvorak = screen.getByRole("button", { name: "Dvorak" });
    expect(qwerty).toHaveAttribute("aria-pressed", "true");
    expect(dvorak).toHaveAttribute("aria-pressed", "false");
    // desktop ribbon must not be present on mobile
    expect(
      screen.queryByPlaceholderText(/hold a vowel for its yoruba forms/i),
    ).not.toBeInTheDocument();

    await userEvent.click(dvorak);
    expect(dvorak).toHaveAttribute("aria-pressed", "true");
    expect(qwerty).toHaveAttribute("aria-pressed", "false");
  });

  it("preserves typed text when switching mobile layouts", async () => {
    mockViewport(false);
    render(<KeyboardDesigns />);

    const input = (await screen.findByLabelText(
      "Yoruba keyboard text input",
    )) as HTMLTextAreaElement;
    fireEvent.change(input, { target: { value: "kọ" } });
    expect(input).toHaveValue("kọ");

    await userEvent.click(screen.getByRole("button", { name: "Dvorak" }));

    // Same textarea instance must survive the layout swap.
    expect(
      screen.getByLabelText("Yoruba keyboard text input"),
    ).toHaveValue("kọ");
  });
});

describe("mobile tone menu", () => {
  const wait = (ms: number) =>
    act(async () => {
      await new Promise((r) => setTimeout(r, ms));
    });

  // jsdom has no real layout, so it omits document.elementFromPoint.
  // Stub it to drive the release hit-test deterministically.
  function stubElementFromPoint(el: Element | null) {
    const d = document as unknown as {
      elementFromPoint?: (x: number, y: number) => Element | null;
    };
    d.elementFromPoint = () => el;
    return () => {
      d.elementFromPoint = undefined;
    };
  }

  async function openToneMenu() {
    mockViewport(false);
    render(<KeyboardDesigns />);
    const ta = (await screen.findByLabelText(
      "Yoruba keyboard text input",
    )) as HTMLTextAreaElement;
    const eKey = document.querySelector(
      '.hg-button[data-skbtn="e"]',
    ) as HTMLElement;
    expect(eKey).toBeTruthy();
    fireEvent.pointerDown(eKey, { clientX: 0, clientY: 0 });
    await wait(470); // long-press timer (400ms) fires
    const menu = screen.getByRole("menu", { name: "Tone options" });
    return { ta, eKey, menu };
  }

  it("opens on long-press, is not clipped above (non-negative top), and labels options", async () => {
    const { menu } = await openToneMenu();
    const top = Number.parseFloat((menu as HTMLElement).style.top);
    expect(Number.isNaN(top)).toBe(false);
    expect(top).toBeGreaterThanOrEqual(0); // would be negative if clipped above
    const values = Array.from(menu.querySelectorAll("[data-tone-value]")).map(
      (b) => b.getAttribute("data-tone-value"),
    );
    expect(values).toEqual(["è", "e", "é"]);
  });

  it("inserts the tone via click (keyboard activation) and closes", async () => {
    const { ta, menu } = await openToneMenu();
    fireEvent.click(
      Array.from(menu.querySelectorAll("button")).find(
        (b) => b.getAttribute("data-tone-value") === "é",
      ) as HTMLElement,
    );
    await waitFor(() => expect(ta).toHaveValue("é"));
    expect(
      screen.queryByRole("menu", { name: "Tone options" }),
    ).not.toBeInTheDocument();
  });

  it("commits the option under the pointer on release (slide gesture)", async () => {
    const { ta, menu } = await openToneMenu();
    const high = Array.from(menu.querySelectorAll("button")).find(
      (b) => b.getAttribute("data-tone-value") === "é",
    ) as HTMLElement;
    const restore = stubElementFromPoint(high);
    fireEvent.pointerUp(window, { clientX: 1, clientY: 1 });
    await waitFor(() => expect(ta).toHaveValue("é"));
    expect(
      screen.queryByRole("menu", { name: "Tone options" }),
    ).not.toBeInTheDocument();
    restore();
  });

  it("emits the plain letter when released on the keyboard without choosing", async () => {
    const { ta, eKey } = await openToneMenu();
    const restore = stubElementFromPoint(eKey);
    fireEvent.pointerUp(window, { clientX: 1, clientY: 1 });
    await waitFor(() => expect(ta).toHaveValue("e"));
    restore();
  });

  it("inserts nothing when released off the keyboard (cancel)", async () => {
    const { ta } = await openToneMenu();
    const restore = stubElementFromPoint(document.body);
    fireEvent.pointerUp(window, { clientX: 1, clientY: 1 });
    await waitFor(() =>
      expect(
        screen.queryByRole("menu", { name: "Tone options" }),
      ).not.toBeInTheDocument(),
    );
    expect(ta).toHaveValue("");
    restore();
  });
});

describe("useHoldAccents (desktop ribbon)", () => {
  it("replaces the selected range instead of inserting before it", async () => {
    render(<DesignDiacriticRibbon />);
    const ta = screen.getByLabelText(
      "Yoruba keyboard text input",
    ) as HTMLTextAreaElement;

    fireEvent.change(ta, { target: { value: "abcd" } });
    ta.setSelectionRange(0, 4); // select the whole field

    // Quick tap of a vowel: keydown captures the range, keyup commits.
    fireEvent.keyDown(ta, { key: "e" });
    fireEvent.keyUp(ta, { key: "e" });

    await waitFor(() => expect(ta).toHaveValue("e"));
  });

  it("commits a tone via numeric shortcut while the accent menu is open", async () => {
    vi.useFakeTimers();
    try {
      render(<DesignDiacriticRibbon />);
      const ta = screen.getByLabelText(
        "Yoruba keyboard text input",
      ) as HTMLTextAreaElement;
      ta.setSelectionRange(0, 0);

      fireEvent.keyDown(ta, { key: "a" }); // arms the hold
      act(() => {
        vi.advanceTimersByTime(350); // HOLD_MS (300) elapses → panel opens
      });
      expect(
        screen.getByRole("menu", { name: "Yoruba forms of a" }),
      ).toBeInTheDocument();

      fireEvent.keyDown(ta, { key: "3" }); // options = [a, à, á] → "á"
      act(() => {
        vi.advanceTimersByTime(20);
      });
      expect(ta).toHaveValue("á");
      expect(
        screen.queryByRole("menu", { name: "Yoruba forms of a" }),
      ).not.toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("Escape dismisses the accent menu and falls back to the plain vowel", async () => {
    vi.useFakeTimers();
    try {
      render(<DesignDiacriticRibbon />);
      const ta = screen.getByLabelText(
        "Yoruba keyboard text input",
      ) as HTMLTextAreaElement;
      ta.setSelectionRange(0, 0);

      fireEvent.keyDown(ta, { key: "o" });
      act(() => {
        vi.advanceTimersByTime(350);
      });
      expect(
        screen.getByRole("menu", { name: "Yoruba forms of o" }),
      ).toBeInTheDocument();

      fireEvent.keyDown(ta, { key: "Escape" });
      act(() => {
        vi.advanceTimersByTime(20);
      });
      expect(ta).toHaveValue("o"); // fallback emits the bare vowel
      expect(
        screen.queryByRole("menu", { name: "Yoruba forms of o" }),
      ).not.toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("ribbon keyboard accessibility", () => {
  it("inserts a glyph via click (Enter/Space activation, not just pointer)", async () => {
    render(<DesignDiacriticRibbon />);
    const ta = screen.getByLabelText(
      "Yoruba keyboard text input",
    ) as HTMLTextAreaElement;

    // Native keyboard activation of a <button> dispatches click only.
    fireEvent.click(screen.getByRole("button", { name: "Insert gb" }));
    await waitFor(() => expect(ta).toHaveValue("gb"));
  });

  it("opens the tone menu on long-press and inserts the chosen tone via click", async () => {
    vi.useFakeTimers();
    try {
      render(<DesignDiacriticRibbon />);
      const ta = screen.getByLabelText(
        "Yoruba keyboard text input",
      ) as HTMLTextAreaElement;
      const aKey = screen.getByRole("button", { name: "a, hold for tones" });

      fireEvent.pointerDown(aKey);
      act(() => {
        vi.advanceTimersByTime(450); // long-press timer fires
      });

      const high = screen.getByRole("menuitem", { name: "Insert á" });
      fireEvent.click(high);
      act(() => {
        vi.advanceTimersByTime(0);
      });
      expect(ta).toHaveValue("á");
    } finally {
      vi.useRealTimers();
    }
  });

  it("renders the tone popover below the key with no clipping ancestor", async () => {
    vi.useFakeTimers();
    try {
      const { container } = render(<DesignDiacriticRibbon />);
      const aKey = screen.getByRole("button", { name: "a, hold for tones" });
      fireEvent.pointerDown(aKey);
      act(() => {
        vi.advanceTimersByTime(450);
      });

      const menu = screen.getByRole("menu", { name: "Tone options" });
      // Positioned below the key, not above where the strip would clip it.
      expect(menu.className).toContain("top-full");
      expect(menu.className).not.toContain("-top-14");

      // No overflow-hidden ancestor between the popover and the ribbon root
      // (the strip used to clip it).
      let el: HTMLElement | null = menu.parentElement;
      while (el && el !== container) {
        expect(el.className).not.toContain("overflow-hidden");
        el = el.parentElement;
      }
    } finally {
      vi.useRealTimers();
    }
  });
});

describe("retoneSuffix (post-vowel tone target)", () => {
  it("matches a bare base vowel/nasal at the caret", () => {
    expect(retoneSuffix("ka")).toEqual({ base: "a", len: 1 });
    expect(retoneSuffix("se")).toEqual({ base: "e", len: 1 });
    expect(retoneSuffix("gbẹ")).toEqual({ base: "ẹ", len: 1 });
    // m and n are tone-bearing syllabic nasals
    expect(retoneSuffix("km")).toEqual({ base: "m", len: 1 });
  });

  it("matches an already-toned precomposed form (1 code unit)", () => {
    expect(retoneSuffix("kò")).toEqual({ base: "o", len: 1 });
    expect(retoneSuffix("ká")).toEqual({ base: "a", len: 1 });
    expect(retoneSuffix("ḿ")).toEqual({ base: "m", len: 1 }); // U+1E3F
    expect(retoneSuffix("ǹ")).toEqual({ base: "n", len: 1 });
  });

  it("matches a combining-mark form (2 code units) before the 1-char form", () => {
    expect(retoneSuffix("ẹ̀")).toEqual({ base: "ẹ", len: 2 });
    expect(retoneSuffix("ọ́")).toEqual({ base: "ọ", len: 2 });
    expect(retoneSuffix("m̀")).toEqual({ base: "m", len: 2 });
  });

  it("returns null when the char before the caret can't carry tone", () => {
    expect(retoneSuffix("")).toBeNull();
    expect(retoneSuffix("k")).toBeNull();
    expect(retoneSuffix("gb")).toBeNull();
    expect(retoneSuffix("ka ")).toBeNull(); // trailing space
  });
});

describe("countCharacters / NFC (a tone mark is not a character)", () => {
  it("counts user-perceived characters, not code units", () => {
    expect(countCharacters("")).toBe(0);
    expect(countCharacters("abc")).toBe(3);
    // ẹ̀ / ọ́ are base + combining (2 code units) but ONE character each
    expect("ẹ̀".length).toBe(2);
    expect(countCharacters("ẹ̀")).toBe(1);
    expect(countCharacters("ọ́sé")).toBe(3);
    expect(countCharacters("kòsí")).toBe(4);
  });

  it("normalises to NFC and counts a decomposed sequence as one", () => {
    const decomposed = "é"; // e + combining acute = 2 code units
    expect(decomposed.length).toBe(2);
    expect(toNFC(decomposed)).toBe("é"); // precomposed é, 1 unit
    expect(toNFC(decomposed).length).toBe(1);
    expect(countCharacters(decomposed)).toBe(1);
  });
});

describe("layout geometry (muscle memory)", () => {
  const tokens = (rows: string[]) => rows.join(" ").split(/\s+/);

  it("Yorùbá QWERTY is a 10-slot top row: a blank in the q slot, no q", () => {
    expect(QWERTY_LAYOUT.yo.default[0]).toBe("{blank} w e r t y u i o p");
    expect(QWERTY_LAYOUT.yo.shift[0]).toBe("{blank} W E R T Y U I O P");
    expect(tokens(QWERTY_LAYOUT.yo.default)).not.toContain("q");
  });

  it("Yorùbá specials replace the unused z/x/c/v slots on row 3", () => {
    expect(QWERTY_LAYOUT.yo.default[2]).toBe("{shift} ẹ ọ ṣ gb b n m {bksp}");
    for (const dead of ["q", "c", "v", "x", "z"]) {
      expect(tokens(QWERTY_LAYOUT.yo.default)).not.toContain(dead);
    }
    for (const special of ["ẹ", "ọ", "ṣ", "gb"]) {
      expect(tokens(QWERTY_LAYOUT.yo.default)).toContain(special);
    }
  });

  it("English QWERTY keeps the standard q row (no blank)", () => {
    expect(QWERTY_LAYOUT.en.default[0]).toBe("q w e r t y u i o p");
    expect(tokens(QWERTY_LAYOUT.en.default)).not.toContain("{blank}");
  });

  it("Dvorak Yorùbá preserves the Dvorak home row and drops q", () => {
    expect(DVORAK_LAYOUT.yo.default[1]).toBe("a o e u i d h t n s");
    expect(tokens(DVORAK_LAYOUT.yo.default)).not.toContain("q");
    for (const special of ["ẹ", "ọ", "ṣ", "gb"]) {
      expect(tokens(DVORAK_LAYOUT.yo.default)).toContain(special);
    }
  });

  it("the numbers layout has exactly one ABC-return key", () => {
    const abcRows = NUM_LAYOUT.filter((r) => r.split(/\s+/).includes("{abc}"));
    expect(abcRows).toHaveLength(1);
    // it lives on the bottom row, where every layout's return key sits
    expect(NUM_LAYOUT[NUM_LAYOUT.length - 1]).toContain("{abc}");
  });
});

describe("mobile keyboard — text field, blank key & tone strip", () => {
  const originalMatchMedia = window.matchMedia;
  afterEach(() => {
    window.matchMedia = originalMatchMedia;
  });

  async function renderMobile() {
    mockViewport(false);
    render(<KeyboardDesigns />);
    const ta = (await screen.findByLabelText(
      "Yoruba keyboard text input",
    )) as HTMLTextAreaElement;
    return ta;
  }

  // Type into the field at a real caret position (the on-screen keyboard
  // and tone strip both read selectionStart), without raising a real
  // device keyboard.
  function seed(ta: HTMLTextAreaElement, text: string) {
    fireEvent.change(ta, { target: { value: text } });
    ta.setSelectionRange(text.length, text.length);
  }

  const toneButton = (name: RegExp) =>
    screen.getByRole("button", { name });

  it("suppresses the device keyboard and is focused for a caret", async () => {
    const ta = await renderMobile();
    expect(ta).toHaveAttribute("inputmode", "none");
    await waitFor(() => expect(ta).toHaveFocus());
  });

  it("keeps a non-interactive blank placeholder in the q slot", async () => {
    await renderMobile();
    const blank = document.querySelector(
      '.hg-button[data-skbtn="{blank}"]',
    ) as HTMLElement;
    expect(blank).toBeTruthy();
    expect(blank.className).toContain("kbd-blank");
    // zero-width space, never the literal word "blank"
    expect(blank.textContent).not.toMatch(/blank/i);
    // unreachable by keyboard / screen reader — purely a spacer
    await waitFor(() => {
      expect(blank.getAttribute("tabindex")).toBe("-1");
      expect(blank.getAttribute("aria-hidden")).toBe("true");
    });
  });

  it("offers only low and high tone keys (mid is the typed default)", async () => {
    await renderMobile();
    const strip = screen.getByRole("group", { name: "Tone marks" });
    const buttons = strip.querySelectorAll("button");
    expect(buttons).toHaveLength(2);
    expect(toneButton(/low tone/i)).toBeInTheDocument();
    expect(toneButton(/high tone/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /mid tone/i }),
    ).not.toBeInTheDocument();
  });

  it("retones the vowel before the caret and replaces (never stacks)", async () => {
    const ta = await renderMobile();
    seed(ta, "ko");

    fireEvent.click(toneButton(/high tone/i));
    await waitFor(() => expect(ta).toHaveValue("kó"));

    ta.setSelectionRange(ta.value.length, ta.value.length);
    fireEvent.click(toneButton(/low tone/i));
    await waitFor(() => expect(ta).toHaveValue("kò"));

    // switching back to high replaces the low mark rather than stacking
    ta.setSelectionRange(ta.value.length, ta.value.length);
    fireEvent.click(toneButton(/high tone/i));
    await waitFor(() => expect(ta).toHaveValue("kó"));
  });

  it("retones a sub-dot vowel using its combining form", async () => {
    const ta = await renderMobile();
    seed(ta, "ẹ");

    fireEvent.click(toneButton(/high tone/i));
    await waitFor(() => expect(ta).toHaveValue("ẹ́"));
    expect(ta.value.length).toBe(2); // ẹ + U+0301
    expect(countCharacters(ta.value)).toBe(1); // still one character
  });

  it("is a no-op when the caret isn't after a tone-bearing letter", async () => {
    const ta = await renderMobile();
    seed(ta, "k");
    fireEvent.click(toneButton(/high tone/i));
    await Promise.resolve();
    expect(ta).toHaveValue("k");
  });
});

describe("lastGraphemeLength (grapheme-aware delete)", () => {
  it("counts a base + combining mark as one deletable unit", () => {
    expect(lastGraphemeLength("kẹ̀")).toBe(2); // kẹ̀
    expect(lastGraphemeLength("kọ́")).toBe(2); // kọ́
    expect(lastGraphemeLength("m̀")).toBe(2); // m̀
    expect(lastGraphemeLength("é")).toBe(2); // decomposed é
  });

  it("is one unit for precomposed forms and plain letters", () => {
    expect(lastGraphemeLength("kò")).toBe(1); // precomposed ò
    expect(lastGraphemeLength("ḿ")).toBe(1); // ḿ
    expect(lastGraphemeLength("a")).toBe(1);
    expect(lastGraphemeLength("gb")).toBe(1); // last letter only
  });

  it("is zero for empty input", () => {
    expect(lastGraphemeLength("")).toBe(0);
  });
});

describe("backspace deletes a whole character", () => {
  // Minimal harness so backspace() is exercised directly (the {bksp}
  // key just calls it) without depending on library key event quirks.
  function Harness() {
    const { ref, value, setValue, backspace } = useKeyboardText();
    return (
      <div>
        <textarea
          ref={ref}
          value={value}
          aria-label="t"
          onChange={(e) => setValue(e.target.value)}
        />
        <button type="button" onClick={backspace}>
          del
        </button>
      </div>
    );
  }

  it("removes ẹ̀ in one press instead of leaving the base behind", async () => {
    render(<Harness />);
    const ta = screen.getByLabelText("t") as HTMLTextAreaElement;

    fireEvent.change(ta, { target: { value: "kẹ̀" } });
    expect(countCharacters(ta.value)).toBe(2);
    ta.setSelectionRange(ta.value.length, ta.value.length);

    fireEvent.click(screen.getByRole("button", { name: "del" }));
    await waitFor(() => expect(ta).toHaveValue("k"));

    // And a normal precomposed letter still deletes in one press.
    ta.setSelectionRange(ta.value.length, ta.value.length);
    fireEvent.click(screen.getByRole("button", { name: "del" }));
    await waitFor(() => expect(ta).toHaveValue(""));
  });
});

describe("desktop ribbon enforces the NFC invariant", () => {
  it("normalises decomposed text typed/pasted into the ribbon field", async () => {
    render(<DesignDiacriticRibbon />);
    const ta = screen.getByLabelText(
      "Yoruba keyboard text input",
    ) as HTMLTextAreaElement;

    // e + combining acute (decomposed, 2 code units)
    fireEvent.change(ta, { target: { value: "sé" } });

    await waitFor(() => expect(ta).toHaveValue("sé")); // composed
    expect(ta.value.length).toBe(2);
    expect(countCharacters(ta.value)).toBe(2);
  });
});
