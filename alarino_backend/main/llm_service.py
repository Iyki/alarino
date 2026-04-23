# llm_service.py
import json
import os
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import List, Optional

from gradient import Gradient

from data.seed_data_utils import is_valid_yoruba_word
from main import logger

LANGUAGE_NAMES = {
    "en": "English",
    "yo": "Yoruba",
}
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("GRADIENT_TIMEOUT_SECONDS", "20"))


class LLMService(ABC):
    @abstractmethod
    def get_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[List[str]]:
        pass


class GradientLLMService(LLMService):
    def __init__(
        self,
        access_key: Optional[str] = None,
        model: str = "openai-gpt-oss-120b",
        max_retries: int = 3,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        if not access_key:
            access_key = os.environ.get("GRADIENT_MODEL_ACCESS_KEY")
        if not access_key:
            raise ValueError("Gradient access key not provided or found in environment variables.")

        self.client = Gradient(
            model_access_key=access_key,
            max_retries=max_retries,
            timeout=timeout,
        )
        self.model = model
        self.max_retries = max_retries

    def _build_prompt(self, text: str, source_lang: str, target_lang: str) -> str:
        source_name = LANGUAGE_NAMES.get(source_lang, source_lang.upper())
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang.upper())
        return (
            f"Translate the following {source_name} word to {target_name} with the proper spelling and diacritics: {text}. "
            "Provide 1 to 4 of the most accurate translations you are highly confident in. "
            "If you are not sure (99% confidence), provide an empty list. "
            "The response must be a valid JSON array of strings, with no additional text or formatting. "
            "For example: [\"translation1\", \"translation2\"]"
        )

    def get_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[List[str]]:
        prompt = self._build_prompt(text, source_lang, target_lang)
        for attempt in range(1, self.max_retries + 1):
            content = self.call_translate_llm(prompt, text)
            if content is None:
                logger.warning(f"Attempt {attempt} failed, retrying...")
                continue
            try:
                translations = json.loads(content)
                if not isinstance(translations, list) or not (1 <= len(translations) <= 5):
                    logger.warning(
                        f"Attempt {attempt} returned an invalid translation list of 1-5 strings for '{text}': {content}"
                    )
                    continue

                valid_translations = self._filter_valid_translations(translations, target_lang)
                return valid_translations

            except json.JSONDecodeError:
                logger.error(f"Attempt {attempt} failed to decode JSON from LLM response for '{text}': {content}")
                continue
            except Exception as e:
                logger.error(f"Attempt {attempt} failed while processing Gradient response for '{text}': {e}")
                continue

        return None

    def _filter_valid_translations(self, translations: List[str], target_lang: str) -> List[str]:
        cleaned = [t.strip() for t in translations if isinstance(t, str) and t.strip()]
        if target_lang == "yo":
            return [t for t in cleaned if is_valid_yoruba_word(t)]
        return cleaned


    def call_translate_llm(self, prompt: str, text: str) -> Optional[str]:
        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=self.model,
        )
        content = response.choices[0].message.content
        return content


@lru_cache(maxsize=1)
def get_llm_service() -> Optional[LLMService]:
    """Factory function to get the configured LLM service."""
    access_key = os.environ.get("GRADIENT_MODEL_ACCESS_KEY")
    if access_key:
        return GradientLLMService(access_key=access_key)
    return None
