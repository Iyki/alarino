from dataclasses import dataclass, asdict, field
from typing import List, Optional, Any

from alarino_backend.languages import Language


@dataclass
class BaseResponseData:
    def to_json(self):
        return asdict(self)


@dataclass
class TranslationInSenseGroup:
    """A single target-language translation surfaced under a sense group.
    Carries the per-Translation metadata (note, provenance) as well as
    sense-scoped examples (Phase 6b backfilled examples to point at sense
    pairs; this surfaces them here)."""

    word: str
    note: Optional[str] = None
    provenance: Optional[str] = None
    examples: List[dict] = field(default_factory=list)


@dataclass
class SenseGroup:
    """Sense-grouped translation results, added in Phase 6c. One group per
    distinct sense of the looked-up word. ``label``, ``definition``,
    ``register``, ``domain``, ``part_of_speech`` come from the looked-up
    word's sense; ``translations`` lists target-language matches under
    that sense.

    Today most words have a single default sense with NULL metadata
    fields, so a typical response carries one group with mostly-empty
    metadata. As polysemy data is curated (e.g., "bank — financial" vs
    "bank — riverbank") the same response shape naturally surfaces
    multiple groups without an API rev."""

    label: Optional[str] = None
    definition: Optional[str] = None
    register: Optional[str] = None
    domain: Optional[str] = None
    part_of_speech: Optional[str] = None
    translations: List[TranslationInSenseGroup] = field(default_factory=list)


@dataclass
class TranslationResponseData(BaseResponseData):
    translation: List[str]
    source_word: str
    to_language: Language
    senses: List[SenseGroup] = field(default_factory=list)


@dataclass
class WordOfTheDayResponseData(BaseResponseData):
    yoruba_word: str
    english_word: str


@dataclass
class ProverbResponseData(BaseResponseData):
    yoruba_text: str
    english_text: str


@dataclass
class BulkUploadResponseData(BaseResponseData):
    successful_pairs: List[dict]
    failed_pairs: List[dict]
    dry_run: bool


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
