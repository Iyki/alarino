from enum import Enum

class Language(str, Enum):
    ENGLISH = "en"
    YORUBA = "yo"

    def __str__(self):
        return self.value

#todo add words(pick name) with word text and language attributes