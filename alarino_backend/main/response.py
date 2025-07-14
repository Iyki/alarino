from dataclasses import dataclass, asdict
from typing import List, Optional, Any

from main.languages import Language


@dataclass
class BaseResponseData:
    def to_json(self):
        return asdict(self)


@dataclass
class TranslationResponseData(BaseResponseData):
    translation: List[str]
    source_word: str
    to_language: Language


@dataclass
class WordOfTheDayResponseData(BaseResponseData):
    yoruba_word: str
    english_word: str


@dataclass
class ProverbResponseData(BaseResponseData):
    yoruba_text: str
    english_text: str


class APIResponse:
    def __init__(self, success: bool, status: int, message: str, data: Optional[BaseResponseData] = None):
        self.success = success
        self.status = status
        self.message = message
        self.data = data

    def to_json(self) -> dict:
        response = {
            "success": self.success,
            "status": self.status,
            "message": self.message,
            "data": self.data.to_json() if self.data else None
        }
        return response

    def as_response(self) -> tuple[dict, int]:
        return self.to_json(), self.status

    @classmethod
    def success(cls, message: str, data: Optional[BaseResponseData] = None, status: int = 200) -> 'APIResponse':
        return cls(True, status, message, data)

    @classmethod
    def error(cls, message: str, status: int = 400, data: Optional[BaseResponseData] = None) -> 'APIResponse':
        return cls(False, status, message, data)
