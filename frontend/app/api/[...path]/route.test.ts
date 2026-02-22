import { afterEach, describe, expect, it, vi } from "vitest";

import { GET, POST } from "@/app/api/[...path]/route";
import { buildBackendUrl, filterForwardHeaders } from "@/lib/api-proxy";

afterEach(() => {
  vi.restoreAllMocks();
  delete process.env.BACKEND_INTERNAL_URL;
});

describe("api proxy route", () => {
  it("builds backend urls against BACKEND_INTERNAL_URL", () => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:5001";
    const backendUrl = buildBackendUrl(["translate"], "?q=test");

    expect(backendUrl).toBe("http://backend:5001/api/translate?q=test");
  });

  it("filters hop-by-hop headers", () => {
    const headers = new Headers({
      "Content-Type": "application/json",
      Host: "example.com",
      Connection: "keep-alive"
    });

    const filtered = filterForwardHeaders(headers);

    expect(filtered.get("Content-Type")).toBe("application/json");
    expect(filtered.get("Host")).toBeNull();
    expect(filtered.get("Connection")).toBeNull();
  });

  it("forwards method, query, body, and status code", async () => {
    process.env.BACKEND_INTERNAL_URL = "http://backend:5001";

    const fetchMock = vi.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ message: "missing" }), {
        status: 404,
        headers: { "content-type": "application/json" }
      })
    );

    const request = new Request("http://localhost:3000/api/translate?source=en", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Host: "localhost"
      },
      body: JSON.stringify({ text: "hello" })
    });

    const response = await POST(request, { params: Promise.resolve({ path: ["translate"] }) });
    const body = await response.json();

    expect(response.status).toBe(404);
    expect(body).toEqual({ message: "missing" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://backend:5001/api/translate?source=en",
      expect.objectContaining({ method: "POST" })
    );

    const options = fetchMock.mock.calls[0][1] as RequestInit;
    const forwardedHeaders = options.headers as Headers;
    expect(forwardedHeaders.get("Host")).toBeNull();
    expect(typeof options.body).toBe("object");
  });

  it("returns 502 when backend is unreachable", async () => {
    vi.spyOn(global, "fetch").mockRejectedValue(new Error("boom"));

    const request = new Request("http://localhost:3000/api/proverb", {
      method: "GET"
    });

    const response = await GET(request, { params: Promise.resolve({ path: ["proverb"] }) });
    const body = await response.json();

    expect(response.status).toBe(502);
    expect(body.message).toContain("Backend is unreachable");
  });
});
