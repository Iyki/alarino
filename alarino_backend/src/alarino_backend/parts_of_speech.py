"""Canonical part-of-speech codes for alarino.

str-backed Enum, mirroring the alarino_backend.languages.Language pattern.
Values are the short linguistic abbreviations stored in the DB. CHECK
constraints on words.part_of_speech and senses.part_of_speech allow NULL
(not every word needs POS marked) or any value from this set.

Adding a new POS code requires both a new enum entry here and an Alembic
migration that drops + re-adds the CHECK constraints with the broader
allowed set."""

from enum import Enum


class PartOfSpeech(str, Enum):
    NOUN = "n"
    VERB = "v"
    ADJECTIVE = "adj"
    ADVERB = "adv"
    PRONOUN = "pron"
    PREPOSITION = "prep"
    CONJUNCTION = "conj"
    INTERJECTION = "interj"
    DETERMINER = "det"
    NUMERAL = "num"
    PARTICLE = "part"

    def __str__(self):
        return self.value


# Sorted for stable CHECK-constraint SQL across migrations.
ALLOWED_POS_VALUES: tuple[str, ...] = tuple(sorted(p.value for p in PartOfSpeech))
