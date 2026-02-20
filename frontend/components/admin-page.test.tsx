import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AdminPage } from "@/components/admin-page";

function jsonResponse(payload: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(payload), {
      status,
      headers: { "content-type": "application/json" }
    })
  );
}

beforeEach(() => {
  vi.spyOn(global, "fetch").mockImplementation((input) => {
    const url = String(input);

    if (url.includes("/admin/bulk-upload")) {
      return jsonResponse({
        success: true,
        status: 200,
        message: "ok",
        data: {
          dry_run: true,
          successful_pairs: [{ english: "hello", yoruba: "bawo" }],
          failed_pairs: [{ line: "bad", reason: "invalid" }]
        }
      });
    }

    return jsonResponse({ success: false, status: 404, message: "missing", data: null }, 404);
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AdminPage", () => {
  it("renders bulk upload summary with success and failure rows", async () => {
    const user = userEvent.setup();
    render(<AdminPage />);

    await user.type(screen.getByLabelText(/api key/i), "test-key");
    await user.type(screen.getByLabelText(/comma-separated word pairs/i), "hello,bawo");
    await user.click(screen.getByRole("button", { name: "Submit" }));

    await waitFor(() => {
      expect(screen.getByText("Total pairs: 2")).toBeInTheDocument();
      expect(screen.getByText(/hello, bawo/i)).toBeInTheDocument();
      expect(screen.getByText(/bad - Reason: invalid/i)).toBeInTheDocument();
    });
  });
});
