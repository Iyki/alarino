"""phase 1: drop redundant indexes, tighten nullability, dedupe examples

Revision ID: 7e3a89c4b21f
Revises: 1233050fe93a
Create Date: 2026-04-25

Implements Phase 1 of the schema evolution plan
(docs/plans/schema_evolution_plan.md).

OPERATOR PREFLIGHT (production):
    Before applying, confirm the indexes being dropped are not in use:

        SELECT indexrelname, idx_scan
        FROM pg_stat_user_indexes
        WHERE indexrelname IN (
            'idx_words_language_word',
            'idx_words_language',
            'idx_missing_text_source_target',
            'idx_proverbs_yoruba_text',
            'idx_translations_source_word_id'
        );

    All idx_scan values should be at or near zero. Each redundant index is
    covered by a unique constraint with the same or wider key, so the
    planner has no reason to use it.

    Also review _phase1_removed_examples in staging after the migration
    runs. The Step 3 deduplication is intentionally non-reversible; the
    sidecar table is the only audit trail of removed duplicate rows.

REVERSIBILITY:
    Steps 1 and 2 (index drops, NOT NULL tightening) are fully reversible.
    Step 3 (Example dedup) is NOT reversible — the deleted duplicate rows
    cannot be reconstructed from this migration alone.

    Downgrade therefore FAILS LOUDLY by default rather than silently doing
    a partial reversal that leaves deleted rows lost while restoring the
    surrounding schema. Operators who explicitly accept the data loss
    (e.g., dev-environment reset, restoring from a separate backup) can
    set ALARINO_FORCE_DOWNGRADE_DATA_LOSS=1 in the environment to opt in.
    With that env var set, the downgrade proceeds with the partial
    reversal: it relaxes NOT NULL, restores indexes, and drops the unique
    constraint, but leaves _phase1_removed_examples in place as the only
    audit trail of the deleted rows.
"""
import os

from alembic import op
import sqlalchemy as sa


revision = "7e3a89c4b21f"
down_revision = "1233050fe93a"
branch_labels = None
depends_on = None


def upgrade():
    # ---- Step 1: drop redundant indexes (reversible) ----
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.drop_index("idx_words_language_word")
        batch_op.drop_index("idx_words_language")

    with op.batch_alter_table("missing_translations", schema=None) as batch_op:
        batch_op.drop_index("idx_missing_text_source_target")

    with op.batch_alter_table("proverbs", schema=None) as batch_op:
        batch_op.drop_index("idx_proverbs_yoruba_text")

    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.drop_index("idx_translations_source_word_id")

    # ---- Step 2: tighten nullability and defaults (reversible) ----
    # Backfill any NULL created_at values before the NOT NULL constraint lands.
    for table in (
        "words",
        "translations",
        "daily_words",
        "missing_translations",
        "examples",
        "proverbs",
    ):
        op.execute(
            f"UPDATE {table} SET created_at = CURRENT_TIMESTAMP "
            f"WHERE created_at IS NULL"
        )
    op.execute(
        "UPDATE missing_translations SET hit_count = 1 WHERE hit_count IS NULL"
    )

    for table in (
        "words",
        "translations",
        "daily_words",
        "missing_translations",
        "examples",
        "proverbs",
    ):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(),
                nullable=False,
                server_default=sa.func.now(),
            )

    with op.batch_alter_table("missing_translations", schema=None) as batch_op:
        batch_op.alter_column(
            "hit_count",
            existing_type=sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        )

    # ---- Step 3: deduplicate examples + add unique constraint (NOT reversible) ----
    # Snapshot every duplicate row (any e_id that is not the minimum for its
    # (translation_id, example_source, example_target) group) into a sidecar
    # table for audit, then delete the duplicates and add the constraint.
    op.execute(
        """
        CREATE TABLE _phase1_removed_examples (
            e_id INTEGER,
            translation_id INTEGER,
            example_source TEXT,
            example_target TEXT,
            created_at TIMESTAMP,
            removed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        INSERT INTO _phase1_removed_examples
            (e_id, translation_id, example_source, example_target, created_at)
        SELECT e_id, translation_id, example_source, example_target, created_at
        FROM examples
        WHERE e_id NOT IN (
            SELECT MIN(e_id)
            FROM examples
            GROUP BY translation_id, example_source, example_target
        )
        """
    )
    op.execute(
        """
        DELETE FROM examples
        WHERE e_id NOT IN (
            SELECT MIN(e_id)
            FROM examples
            GROUP BY translation_id, example_source, example_target
        )
        """
    )
    with op.batch_alter_table("examples", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "unique_example_per_translation",
            ["translation_id", "example_source", "example_target"],
        )


def downgrade():
    if os.environ.get("ALARINO_FORCE_DOWNGRADE_DATA_LOSS") != "1":
        raise RuntimeError(
            "Phase 1 (revision 7e3a89c4b21f) is NOT reversible: the duplicate "
            "Example rows deleted in step 3 cannot be reconstructed from this "
            "migration. Restore them from _phase1_removed_examples or from a "
            "backup before downgrading. To proceed anyway and accept the data "
            "loss, set ALARINO_FORCE_DOWNGRADE_DATA_LOSS=1 in the environment."
        )

    # ---- Step 3 reverse (PARTIAL): drop the unique constraint. Cannot restore
    # deleted duplicate rows. _phase1_removed_examples is left in place so
    # operators can copy data back manually if needed. ----
    with op.batch_alter_table("examples", schema=None) as batch_op:
        batch_op.drop_constraint(
            "unique_example_per_translation", type_="unique"
        )

    # ---- Step 2 reverse: relax NOT NULL and drop server defaults. ----
    with op.batch_alter_table("missing_translations", schema=None) as batch_op:
        batch_op.alter_column(
            "hit_count",
            existing_type=sa.Integer(),
            nullable=True,
            server_default=None,
        )

    for table in (
        "proverbs",
        "examples",
        "missing_translations",
        "daily_words",
        "translations",
        "words",
    ):
        with op.batch_alter_table(table, schema=None) as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(),
                nullable=True,
                server_default=None,
            )

    # ---- Step 1 reverse: re-create the dropped indexes. ----
    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.create_index(
            "idx_translations_source_word_id", ["source_word_id"], unique=False
        )

    with op.batch_alter_table("proverbs", schema=None) as batch_op:
        batch_op.create_index(
            "idx_proverbs_yoruba_text", ["yoruba_text"], unique=False
        )

    with op.batch_alter_table("missing_translations", schema=None) as batch_op:
        batch_op.create_index(
            "idx_missing_text_source_target",
            ["text", "source_language", "target_language"],
            unique=False,
        )

    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.create_index("idx_words_language", ["language"], unique=False)
        batch_op.create_index(
            "idx_words_language_word", ["language", "word"], unique=False
        )
