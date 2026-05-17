import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

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
});
