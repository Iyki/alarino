import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { HomePage } from "@/components/home-page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({}),
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

function createFetchMock({
  dbStatus = 200,
  dbData = {
    source_word: "hello",
    translation: ["bawo"],
    to_language: "yo"
  },
  experimentalStatus = 200,
  experimentalData = {
    source_word: "hello",
    translation: ["ẹ káàbọ̀"],
    to_language: "yo"
  }
}: {
  dbStatus?: number;
  dbData?: {
    source_word: string;
    translation: string[];
    to_language: string;
  } | null;
  experimentalStatus?: number;
  experimentalData?: {
    source_word: string;
    translation: string[];
    to_language: string;
  } | null;
} = {}) {
  return vi.spyOn(global, "fetch").mockImplementation((input) => {
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

    if (url.includes("/translate/llm")) {
      return jsonResponse(
        {
          success: experimentalStatus >= 200 && experimentalStatus < 300,
          status: experimentalStatus,
          message: experimentalStatus >= 200 && experimentalStatus < 300 ? "ok" : "missing",
          data: experimentalData
        },
        experimentalStatus
      );
    }

    if (url.includes("/translate")) {
      return jsonResponse(
        {
          success: dbStatus >= 200 && dbStatus < 300,
          status: dbStatus,
          message: dbStatus >= 200 && dbStatus < 300 ? "ok" : "missing",
          data: dbData
        },
        dbStatus
      );
    }

    return jsonResponse({ success: false, status: 404, message: "not found", data: null }, 404);
  });
}

const replaceStateSpy = vi.fn();

beforeEach(() => {
  replaceStateSpy.mockReset();
  vi.stubGlobal("history", { ...window.history, replaceState: replaceStateSpy });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("HomePage", () => {
  it("submits translations, renders experimental results, and updates the word route", async () => {
    createFetchMock();

    const user = userEvent.setup();
    render(<HomePage />);

    await user.type(screen.getByLabelText(/enter an english word/i), "hello");
    await user.click(screen.getByRole("button", { name: "Translate" }));

    await waitFor(() => {
      expect(screen.getByText("hello")).toBeInTheDocument();
      expect(screen.getByText("bawo")).toBeInTheDocument();
      expect(screen.getByText("Experimental")).toBeInTheDocument();
      expect(screen.getByText("ẹ káàbọ̀")).toBeInTheDocument();
      expect(replaceStateSpy).toHaveBeenCalledWith(null, "", "/word/hello");
    });
  });

  it("renders only the primary translation when the experimental call fails", async () => {
    createFetchMock({
      experimentalStatus: 500,
      experimentalData: null
    });

    const user = userEvent.setup();
    render(<HomePage />);

    await user.type(screen.getByLabelText(/enter an english word/i), "hello");
    await user.click(screen.getByRole("button", { name: "Translate" }));

    await waitFor(() => {
      expect(screen.getByText("bawo")).toBeInTheDocument();
      expect(screen.queryByText("Experimental")).not.toBeInTheDocument();
    });
  });

  it("renders the experimental translation when the dictionary lookup fails", async () => {
    createFetchMock({
      dbStatus: 404,
      dbData: null,
      experimentalData: {
        source_word: "xylophone",
        translation: ["sáfẹ́ẹ̀lì"],
        to_language: "yo"
      }
    });

    const user = userEvent.setup();
    render(<HomePage />);

    await user.type(screen.getByLabelText(/enter an english word/i), "xylophone");
    await user.click(screen.getByRole("button", { name: "Translate" }));

    await waitFor(() => {
      expect(screen.getByText("xylophone")).toBeInTheDocument();
      expect(screen.getByText("Experimental")).toBeInTheDocument();
      expect(screen.getByText("sáfẹ́ẹ̀lì")).toBeInTheDocument();
      expect(screen.getByText("Dictionary result not found. Showing experimental translation.")).toBeInTheDocument();
    });
  });

  it("shows the existing error copy when both translation calls fail", async () => {
    createFetchMock({
      dbStatus: 404,
      dbData: null,
      experimentalStatus: 404,
      experimentalData: null
    });

    const user = userEvent.setup();
    render(<HomePage />);

    await user.type(screen.getByLabelText(/enter an english word/i), "unknown");
    await user.click(screen.getByRole("button", { name: "Translate" }));

    await waitFor(() => {
      expect(screen.getByText("We're still learning! Please try another translation.")).toBeInTheDocument();
      expect(screen.queryByText("Experimental")).not.toBeInTheDocument();
    });
  });

  it("toggles word-of-day translation and opens/closes contribution modal", async () => {
    createFetchMock();

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
