import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SiteHeader } from "@/components/site-header";

vi.mock("next/image", () => ({
  default: () => <span data-testid="mock-image" />
}));

vi.mock("next/link", () => ({
  default: (props: Record<string, unknown>) => <a {...props} />
}));

describe("SiteHeader", () => {
  it("opens and closes the menu drawer", async () => {
    const user = userEvent.setup();
    render(<SiteHeader />);

    await user.click(screen.getByRole("button", { name: "Open menu" }));
    expect(screen.getByRole("navigation")).toBeInTheDocument();
    expect(document.body).toHaveClass("overflow-hidden");

    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => {
      expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    });
    expect(document.body).not.toHaveClass("overflow-hidden");

    await user.click(screen.getByRole("button", { name: "Open menu" }));
    await user.click(screen.getByRole("button", { name: "Close menu overlay" }));
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: "Close menu overlay" })).not.toBeInTheDocument();
    });
  });
});
