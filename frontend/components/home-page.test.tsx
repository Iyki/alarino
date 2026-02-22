import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HomePage } from "@/components/home-page";

const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: replaceMock
  }),
  usePathname: () => "/"
}));

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

    if (url.includes("/daily-word")) {
      return jsonResponse({
        success: true,
        status: 200,
        message: "ok",
        data: {
          yoruba_word: "ọrẹ",
          english_word: "friend"
        }
      });
    }

    if (url.includes("/proverb")) {
      return jsonResponse({
        success: true,
        status: 200,
        message: "ok",
        data: {
          yoruba_text: "Ọ̀rọ̀ ni ń tọ́ni",
          english_text: "Words guide us"
        }
      });
    }

    if (url.includes("/translate")) {
      return jsonResponse({
        success: true,
        status: 200,
        message: "ok",
        data: {
          source_word: "hello",
          translation: ["bawo"],
          to_language: "yo"
        }
      });
    }

    return jsonResponse({ success: false, status: 404, message: "not found", data: null }, 404);
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  replaceMock.mockReset();
});

describe("HomePage", () => {
  it("submits translations and updates the word route", async () => {
    const user = userEvent.setup();
    render(<HomePage />);

    await user.type(screen.getByLabelText(/enter an english word/i), "hello");
    await user.click(screen.getByRole("button", { name: "Translate" }));

    await waitFor(() => {
      expect(screen.getByText("hello")).toBeInTheDocument();
      expect(screen.getByText("bawo")).toBeInTheDocument();
      expect(replaceMock).toHaveBeenCalledWith("/word/hello", { scroll: false });
    });
  });

  it("toggles word-of-day translation and opens/closes contribution modal", async () => {
    const user = userEvent.setup();
    render(<HomePage />);

    await user.click(screen.getByRole("button", { name: "View translation" }));
    expect(screen.getByText("friend")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "+ Add a word" }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Close" }));
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });
});
