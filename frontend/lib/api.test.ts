import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchDailyWord, translateEnglishWord } from "@/lib/api";

function jsonResponse(payload: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(payload), {
      status,
      headers: { "content-type": "application/json" }
    })
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("lib/api", () => {
  it("posts translation requests with expected payload", async () => {
    const fetchMock = vi.spyOn(global, "fetch").mockImplementation(() =>
      jsonResponse({
        success: true,
        status: 200,
        message: "ok",
        data: {
          source_word: "hello",
          translation: ["bawo"],
          to_language: "yo"
        }
      })
    );

    const response = await translateEnglishWord("hello");

    expect(response.success).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/translate",
      expect.objectContaining({ method: "POST" })
    );

    const options = fetchMock.mock.calls[0][1] as RequestInit;
    expect(options.body).toBe(
      JSON.stringify({
        text: "hello",
        source_lang: "en",
        target_lang: "yo"
      })
    );
  });

  it("returns a fallback error shape when fetch throws", async () => {
    vi.spyOn(global, "fetch").mockRejectedValue(new Error("network down"));

    const response = await fetchDailyWord();

    expect(response.success).toBe(false);
    expect(response.status).toBe(500);
    expect(response.message).toContain("network down");
  });
});
