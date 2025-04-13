from languages import Language

class ResponseData:
    def __init__(self, translation: list[str], source_word: str, language: Language):
        self.translation = translation
        self.source_word = source_word
        self.language = language

    def to_json(self):
        return {
            "translation": self.translation,
            "source_word": self.source_word,
            "language": self.language
        }


class APIResponse:
    def __init__(self, success: bool, status: int, message: str, data: ResponseData = None):
        self.success = success
        self.status = status
        self.message = message
        self.data = data

    def to_json(self) -> dict:
        return {
            "success": self.success,
            "status": self.status,
            "message": self.message,
            "data": self.data.to_json() if self.data else None
        }

    def as_response(self) -> tuple[dict, int]:
        return self.to_json(), self.status

    @classmethod
    def success(cls, message: str, data=None, status=200):
        return cls(True, status, message, data)

    @classmethod
    def error(cls, message: str, status=400, data=None):
        return cls(False, status, message, data)


