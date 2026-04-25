r"""phase 3: add proverb_words join table and backfill from existing proverbs

Revision ID: d2e8f60a7c14
Revises: c8d4f1a2b903
Create Date: 2026-04-25

Implements Phase 3 of the schema evolution plan
(docs/plans/schema_evolution_plan.md).

The backfill mirrors the runtime semantics of seed_data_utils.add_proverb:
tokenize each proverb (re.findall(r'\b\w+\b', ...)), normalize each token
(strip punctuation, lowercase, NFC), validate it against the same
language-specific character set used at runtime, then either link to an
existing Word row or CREATE one if it does not exist. Tokens that fail
validation are silently skipped (matching add_word's None-return path).

The validation rules are inlined here rather than imported from
seed_data_utils so the migration stays frozen in time — if the runtime
rules ever change, this migration still represents what was extracted at
the time it ran.

Position values are 0-indexed within each language sequence and only
increment for tokens that result in a Word link, so they stay dense even
when some tokens fail validation.

REVERSIBILITY:
    Fully reversible. Downgrade drops the proverb_words table. Word rows
    that this migration created are intentionally left in place — they are
    legitimate vocabulary entries, not migration artifacts.
"""
import re
import unicodedata

from alembic import op
import sqlalchemy as sa


revision = "d2e8f60a7c14"
down_revision = "c8d4f1a2b903"
branch_labels = None
depends_on = None


# ---- Inlined runtime word-validation rules (frozen as of seed_data_utils
# at the time this migration was written). Keep in sync with the runtime
# only when intentionally re-running the backfill on already-migrated DBs. ----

_YORUBA_CONSONANTS = "bdfghjklmnprstwygbṣ"
_YORUBA_VOWELS = "aàáeèéẹẹ̀ẹ́iìíoòóọọ̀ọ́uùú"
_YORUBA_NASAL_VOWELS = "mḿm̀nńǹ"
_YORUBA_CHARACTER_SET = (
    _YORUBA_CONSONANTS + _YORUBA_VOWELS + _YORUBA_NASAL_VOWELS
)


def _normalize_token(token: str) -> str:
    cleaned = token.strip().strip(" ,.?!()").lower()
    return unicodedata.normalize("NFC", cleaned)


def _is_valid_yoruba_word(word: str) -> bool:
    if not word:
        return False
    valid_chars = unicodedata.normalize("NFC", _YORUBA_CHARACTER_SET + "'- ")
    pattern = f"^[{re.escape(valid_chars)}]+$"
    return bool(re.match(pattern, word, re.UNICODE))


def _is_valid_english_word(word: str) -> bool:
    if not word:
        return False
    return bool(re.match(r"^[a-z'\- ]+$", word, re.UNICODE))


def _get_or_create_word_id(connection, language: str, raw_token: str):
    normalized = _normalize_token(raw_token)
    if not normalized:
        return None
    if language == "yo" and not _is_valid_yoruba_word(normalized):
        return None
    if language == "en" and not _is_valid_english_word(normalized):
        return None
    row = connection.execute(
        sa.text(
            "SELECT w_id FROM words "
            "WHERE language = :lang AND word = :word"
        ),
        {"lang": language, "word": normalized},
    ).fetchone()
    if row is not None:
        return row[0]
    # Mirror add_word()'s create-if-missing semantics so pre-Phase-3
    # proverbs whose tokens are not yet in the words table still become
    # discoverable through get_proverbs_containing().
    connection.execute(
        sa.text(
            "INSERT INTO words (language, word) VALUES (:lang, :word)"
        ),
        {"lang": language, "word": normalized},
    )
    row = connection.execute(
        sa.text(
            "SELECT w_id FROM words "
            "WHERE language = :lang AND word = :word"
        ),
        {"lang": language, "word": normalized},
    ).fetchone()
    return row[0]


def upgrade():
    op.create_table(
        "proverb_words",
        sa.Column(
            "proverb_id",
            sa.Integer(),
            sa.ForeignKey("proverbs.p_id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "word_id",
            sa.Integer(),
            sa.ForeignKey("words.w_id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("language", sa.String(length=3), primary_key=True, nullable=False),
        sa.Column("position", sa.Integer(), primary_key=True, nullable=False),
        sa.CheckConstraint(
            "language IN ('en', 'yo')",
            name="ck_proverb_words_language_valid",
        ),
    )
    with op.batch_alter_table("proverb_words", schema=None) as batch_op:
        batch_op.create_index(
            "idx_proverb_words_word_id", ["word_id"], unique=False
        )

    # Backfill from existing proverbs.
    connection = op.get_bind()
    proverbs = connection.execute(
        sa.text("SELECT p_id, yoruba_text, english_text FROM proverbs")
    ).fetchall()

    for proverb_row in proverbs:
        p_id = proverb_row[0]
        for language_code, raw_text in (
            ("yo", proverb_row[1]),
            ("en", proverb_row[2]),
        ):
            position = 0
            for token in re.findall(r"\b\w+\b", raw_text or ""):
                word_id = _get_or_create_word_id(
                    connection, language_code, token
                )
                if word_id is None:
                    continue
                connection.execute(
                    sa.text(
                        "INSERT INTO proverb_words "
                        "(proverb_id, word_id, language, position) "
                        "VALUES (:p, :w, :lang, :pos)"
                    ),
                    {
                        "p": p_id,
                        "w": word_id,
                        "lang": language_code,
                        "pos": position,
                    },
                )
                position += 1


def downgrade():
    with op.batch_alter_table("proverb_words", schema=None) as batch_op:
        batch_op.drop_index("idx_proverb_words_word_id")
    op.drop_table("proverb_words")
