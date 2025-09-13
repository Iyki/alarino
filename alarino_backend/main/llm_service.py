# llm_service.py
import os
import json
import time
from abc import ABC, abstractmethod
from typing import List, Optional

from gradient import Gradient

from data.seed_data_utils import is_valid_yoruba_word
from main import logger

class LLMService(ABC):
    @abstractmethod
    def get_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[List[str]]:
        pass

class GradientLLMService(LLMService):
    def __init__(self, access_key: Optional[str] = None, model: str = "openai-gpt-oss-120b", max_retries: int = 3):
        if not access_key:
            access_key = os.environ.get("GRADIENT_MODEL_ACCESS_KEY")
        if not access_key:
            raise ValueError("Gradient access key not provided or found in environment variables.")
        
        self.client = Gradient(model_access_key=access_key)
        self.model = model
        self.max_retries = max_retries


    def get_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[List[str]]:
        prompt = (
            f"Translate the following English word to Yoruba with the proper diacritics: {text} "
            "Provide 1 to 3 of the most accurate translations you are highly confident in. If you are not sure (99% confidence), provide an empty list"
            "The response must be a valid JSON array of strings, with no additional text or formatting. "
            "For example: [\"translation1\", \"translation2\"]"
        )
        for attempt in range(1, self.max_retries + 1):
            content = self.call_translate_llm(prompt, text)
            if content is None:
                logger.warning(f"Attempt {attempt} failed, retrying...")
                continue
            try:
                # Validate and parse the response
                translations = json.loads(content)
                if not isinstance(translations, list) or not (1 <= len(translations) <= 5):
                    logger.warning(f"LLM response for '{text}' was not a valid list of 1-3 strings: {content}")
                    return None

                valid_translations = [t for t in translations if is_valid_yoruba_word(t)]
                return valid_translations

            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from LLM response for '{text}': {content}")
                return None
            except Exception as e:
                logger.error(f"Error getting translation from Gradient for '{text}': {e}")
                return None


    def call_translate_llm(self, prompt: str, text: str) -> Optional[str]:
        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                    "Reasoning": "medium",
                    "response_format": "json",
                }
            ],
            model=self.model,
        )
        content = response.choices[0].message.content
        return content

def get_llm_service() -> Optional[LLMService]:
    """Factory function to get the configured LLM service."""
    access_key = os.environ.get("GRADIENT_MODEL_ACCESS_KEY")
    if access_key:
        return GradientLLMService(access_key=access_key)
    return None