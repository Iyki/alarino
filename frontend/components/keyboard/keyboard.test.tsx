import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DesignDiacriticRibbon } from "./design-diacritic-ribbon";
import { KeyboardDesigns } from "./keyboard-designs";
import { pickAlign, popoverAlignClass } from "./popover-align";
import { hasTones, toneVariants, vowelAccents } from "./tones";

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
