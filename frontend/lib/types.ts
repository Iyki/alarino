export interface ApiResponse<T> {
  success: boolean;
  status: number;
  message: string;
  data: T | null;
}

export interface TranslationData {
  translation: string[];
  source_word: string;
  to_language: string;
}

export interface DailyWordData {
  yoruba_word: string;
  english_word: string;
}

export interface ProverbData {
  yoruba_text: string;
  english_text: string;
}

export interface BulkUploadResult {
  successful_pairs: Array<{
    english: string;
    yoruba: string;
  }>;
  failed_pairs: Array<{
    line: string;
    reason: string;
  }>;
  dry_run: boolean;
}
