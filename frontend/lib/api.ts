import type {
  ApiResponse,
  BulkUploadResult,
  DailyWordData,
  ProverbData,
  TranslationData
} from "@/lib/types";

const API_BASE_PATH = "/api";
const DEFAULT_ERROR_MESSAGE = "An unexpected error occurred.";

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return DEFAULT_ERROR_MESSAGE;
}

function makeFailedResponse<T>(status: number, message: string): ApiResponse<T> {
  return {
    success: false,
    status,
    message,
    data: null
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function normalizeApiResponse<T>(payload: unknown, fallbackStatus: number): ApiResponse<T> {
  if (!isRecord(payload)) {
    return makeFailedResponse<T>(fallbackStatus, "Malformed JSON response from API.");
  }

  const message = typeof payload.message === "string" ? payload.message : DEFAULT_ERROR_MESSAGE;
  const status = typeof payload.status === "number" ? payload.status : fallbackStatus;
  const success = typeof payload.success === "boolean" ? payload.success : status >= 200 && status < 300;
  const data = "data" in payload ? (payload.data as T | null) : null;

  return { success, status, message, data };
}

async function requestApi<T>(path: string, init: RequestInit): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_PATH}${path}`, init);
    const contentType = response.headers.get("content-type");

    if (!contentType?.includes("application/json")) {
      const text = await response.text();
      return makeFailedResponse<T>(response.status, text || "Unexpected response type from API.");
    }

    return normalizeApiResponse<T>(await response.json(), response.status);
  } catch (error) {
    return makeFailedResponse<T>(500, getErrorMessage(error));
  }
}

export async function fetchDailyWord(): Promise<ApiResponse<DailyWordData>> {
  return requestApi<DailyWordData>("/daily-word", { method: "GET" });
}

export async function fetchRandomProverb(): Promise<ApiResponse<ProverbData>> {
  return requestApi<ProverbData>("/proverb", { method: "GET" });
}

export async function translateEnglishWord(text: string): Promise<ApiResponse<TranslationData>> {
  return requestApi<TranslationData>("/translate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      text,
      source_lang: "en",
      target_lang: "yo"
    })
  });
}

export async function bulkUploadWords(
  textInput: string,
  dryRun: boolean,
  apiKey: string
): Promise<ApiResponse<BulkUploadResult>> {
  return requestApi<BulkUploadResult>("/admin/bulk-upload", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      text_input: textInput,
      dry_run: dryRun
    })
  });
}
