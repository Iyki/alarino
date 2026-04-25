"""phase 6b-followup: constrain part_of_speech to a typed enum

Revision ID: c4b8e1a5d927
Revises: b3d217fa094e
Create Date: 2026-04-25

Adds CHECK constraints to words.part_of_speech and senses.part_of_speech
restricting non-NULL values to the canonical PartOfSpeech enum codes.
Mirrors the language CHECK pattern from Phase 2.

Lands BEFORE Phase 6c so the new sense-grouped /api/translate response
ships with consistent POS values from day one. NULL remains valid (not
every word needs POS marked); only non-NULL strings outside the enum are
rejected.

PREFLIGHT (built into the migration):
    The migration scans existing words.part_of_speech and senses.part_of_speech
    and aborts with a list of offending IDs if any non-NULL value is outside
    the canonical set. At alarino's current data state most POS values are
    NULL (the bulk-upload path doesn't set POS), so the preflight typically
    passes with nothing to clean. If it doesn't pass, the operator normalizes
    the strays manually before re-running.

REVERSIBILITY:
    Fully reversible. Downgrade drops both CHECK constraints. No data is
    touched.
"""
from alembic import op
import sqlalchemy as sa


revision = "c4b8e1a5d927"
down_revision = "b3d217fa094e"
branch_labels = None
depends_on = None


# Inlined to keep the migration frozen in time. Order matters for stable
# CHECK-constraint SQL across re-runs.
_ALLOWED_POS = (
    "adj", "adv", "conj", "det", "interj", "n", "num", "part", "prep", "pron", "v",
)


def _check_clause() -> str:
    return (
        "part_of_speech IS NULL OR part_of_speech IN ("
        + ", ".join(f"'{v}'" for v in _ALLOWED_POS)
        + ")"
    )


def upgrade():
    connection = op.get_bind()

    # ---- Preflight: surface any stray non-canonical POS values ----
    allowed_set = set(_ALLOWED_POS)

    bad_words = [
        row[0]
        for row in connection.execute(
            sa.text("SELECT w_id, part_of_speech FROM words WHERE part_of_speech IS NOT NULL")
        ).fetchall()
        if row[1] not in allowed_set
    ]
    bad_senses = [
        row[0]
        for row in connection.execute(
            sa.text("SELECT sense_id, part_of_speech FROM senses WHERE part_of_speech IS NOT NULL")
        ).fetchall()
        if row[1] not in allowed_set
    ]

    if bad_words or bad_senses:
        raise RuntimeError(
            "Phase 6b POS-check (revision c4b8e1a5d927) cannot proceed: the "
            "following rows have non-canonical part_of_speech values that are "
            f"not in {sorted(allowed_set)!r}.\n"
            f"  words.w_id: {bad_words}\n"
            f"  senses.sense_id: {bad_senses}\n"
            "Either normalize them to a canonical short code (e.g., 'noun' -> 'n', "
            "'Noun' -> 'n') or set them to NULL, then re-run the migration."
        )

    # ---- Add CHECK constraints ----
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_words_part_of_speech_valid", _check_clause()
        )
    with op.batch_alter_table("senses", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_senses_part_of_speech_valid", _check_clause()
        )


def downgrade():
    with op.batch_alter_table("senses", schema=None) as batch_op:
        batch_op.drop_constraint(
            "ck_senses_part_of_speech_valid", type_="check"
        )
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.drop_constraint(
            "ck_words_part_of_speech_valid", type_="check"
        )
