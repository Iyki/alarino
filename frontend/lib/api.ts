import type {
  ApiResponse,
  BulkUploadResult,
  DailyWordData,
  ProverbData,
  TranslationData
} from "@/lib/types";

const API_BASE_PATH = "/api";

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  return "An unexpected error occurred.";
}

async function parseApiResponse<T>(response: Response): Promise<ApiResponse<T>> {
  const contentType = response.headers.get("content-type");

  if (!contentType?.includes("application/json")) {
    const text = await response.text();
    throw new Error(text || "Unexpected response type from API.");
  }

  return (await response.json()) as ApiResponse<T>;
}

export async function fetchDailyWord(): Promise<ApiResponse<DailyWordData>> {
  try {
    const response = await fetch(`${API_BASE_PATH}/daily-word`, { method: "GET" });
    return await parseApiResponse<DailyWordData>(response);
  } catch (error) {
    return {
      success: false,
      status: 500,
      message: getErrorMessage(error),
      data: null
    };
  }
}

export async function fetchRandomProverb(): Promise<ApiResponse<ProverbData>> {
  try {
    const response = await fetch(`${API_BASE_PATH}/proverb`, { method: "GET" });
    return await parseApiResponse<ProverbData>(response);
  } catch (error) {
    return {
      success: false,
      status: 500,
      message: getErrorMessage(error),
      data: null
    };
  }
}

export async function translateEnglishWord(text: string): Promise<ApiResponse<TranslationData>> {
  try {
    const response = await fetch(`${API_BASE_PATH}/translate`, {
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

    return await parseApiResponse<TranslationData>(response);
  } catch (error) {
    return {
      success: false,
      status: 500,
      message: getErrorMessage(error),
      data: null
    };
  }
}

export async function bulkUploadWords(
  textInput: string,
  dryRun: boolean,
  apiKey: string
): Promise<ApiResponse<BulkUploadResult>> {
  try {
    const response = await fetch(`${API_BASE_PATH}/admin/bulk-upload`, {
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

    return await parseApiResponse<BulkUploadResult>(response);
  } catch (error) {
    return {
      success: false,
      status: 500,
      message: getErrorMessage(error),
      data: null
    };
  }
}
