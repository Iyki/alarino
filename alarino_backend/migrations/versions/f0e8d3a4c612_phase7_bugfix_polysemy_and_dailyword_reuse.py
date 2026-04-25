"""phase 7 bug-fix: relax DailyWord uniqueness, move Translation uniqueness to sense pair

Revision ID: f0e8d3a4c612
Revises: e7c195a8b340
Create Date: 2026-04-25

Two schema bugs surfaced after the Phase 5/6 cutover:

1. DailyWord.translation_id was made UNIQUE in Phase 5, but
   find_random_unused_translation defaults to can_reuse=True. Once a
   translation has been used as a daily word once, the next time the
   picker selects it the INSERT into daily_words violates the unique
   constraint and the endpoint 500s. Fix: drop the unique constraint.
   Date uniqueness (one daily word per date) is preserved via the date
   column's existing UNIQUE.

2. translations was UNIQUE on (source_word_id, target_word_id) — carried
   over from before the sense layer. That blocks the polysemy use case
   the sense layer is supposed to unlock: "bank (financial) -> X" and
   "bank (river) -> X" can't coexist if both target the same surface
   word. Fix: drop unique_translation_pair, replace with
   unique_translation_sense_pair on (source_sense_id, target_sense_id).
   Phase 6d already made the sense FKs NOT NULL, so the sense pair is
   well-defined for every Translation.

The dropped translations word-pair constraint also implicitly covered
source_word_id with its prefix index. Add an explicit
idx_translations_source_word_id to keep the bidirectional translate()
join from regressing to a scan.

REVERSIBILITY:
    Fully reversible. Downgrade restores both unique constraints and
    drops the new index. The translations data must already satisfy
    the original (source_word_id, target_word_id) uniqueness for the
    downgrade to apply cleanly — operators who curated polysemy that
    relies on the new sense-pair uniqueness will need to deduplicate
    before downgrading.
"""
from alembic import op


revision = "f0e8d3a4c612"
down_revision = "e7c195a8b340"
branch_labels = None
depends_on = None


def upgrade():
    # ---- Translations: move uniqueness from word pair to sense pair ----
    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.drop_constraint("unique_translation_pair", type_="unique")
    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "unique_translation_sense_pair",
            ["source_sense_id", "target_sense_id"],
        )
        batch_op.create_index(
            "idx_translations_source_word_id",
            ["source_word_id"],
            unique=False,
        )

    # ---- DailyWord: drop uniqueness on translation_id ----
    # SQLite stored the unique=True column as a constraint named
    # "daily_words_translation_id_key" or similar via SQLAlchemy. To handle
    # both the SQLAlchemy-default name and the Postgres-default name
    # portably, drop via batch_alter_table.alter_column with unique=False.
    with op.batch_alter_table("daily_words", schema=None) as batch_op:
        batch_op.drop_constraint(
            "unique_daily_words_translation_id", type_="unique"
        )


def downgrade():
    with op.batch_alter_table("daily_words", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "unique_daily_words_translation_id",
            ["translation_id"],
        )

    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.drop_index("idx_translations_source_word_id")
        batch_op.drop_constraint(
            "unique_translation_sense_pair", type_="unique"
        )
    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "unique_translation_pair",
            ["source_word_id", "target_word_id"],
        )
