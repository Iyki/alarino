"""phase 6a: add senses table and translation metadata columns (additive)

Revision ID: a91f5e3b8c42
Revises: f6a182cd9e07
Create Date: 2026-04-25

Implements Phase 6a of the schema evolution plan
(docs/plans/schema_evolution_plan.md).

PURELY ADDITIVE. No existing column is dropped, no behavior changes.
After this migration:
  - A new senses table exists, with one row per existing Word, copying
    that Word's part_of_speech.
  - Translation has nullable source_sense_id, target_sense_id, note,
    confidence, and provenance columns. Existing rows are backfilled
    so source_sense_id and target_sense_id point at the lone sense of
    the source/target word.
  - Word.part_of_speech is intentionally kept (read paths still use it
    until Phase 6c). Phase 6d drops it.
  - The translation_id paths in Example, DailyWord, etc. are unchanged.

This is the safest possible point in the sense-layer rollout: legacy
schema and code keep working as before; the new structure is in place
for Phase 6b/6c/6d to build on.

REVERSIBILITY:
    Fully reversible. Downgrade drops the new columns from translations
    and drops the senses table. No data loss outside of the new columns
    (which were either NULL or backfilled-from-existing-data).

OPERATOR PREFLIGHT (production):
    None required. The backfill is a deterministic 1:1 mapping.
"""
from alembic import op
import sqlalchemy as sa


revision = "a91f5e3b8c42"
down_revision = "f6a182cd9e07"
branch_labels = None
depends_on = None


def upgrade():
    # ---- Step 1: create senses table ----
    op.create_table(
        "senses",
        sa.Column("sense_id", sa.Integer(), primary_key=True),
        sa.Column(
            "word_id",
            sa.Integer(),
            sa.ForeignKey("words.w_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("part_of_speech", sa.String(length=20), nullable=True),
        sa.Column("sense_label", sa.String(length=80), nullable=True),
        sa.Column("definition", sa.Text(), nullable=True),
        sa.Column("register", sa.String(length=40), nullable=True),
        sa.Column("domain", sa.String(length=80), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    with op.batch_alter_table("senses", schema=None) as batch_op:
        batch_op.create_index(
            "idx_senses_word_id", ["word_id"], unique=False
        )

    # ---- Step 2: backfill one sense per existing Word, copying part_of_speech ----
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "INSERT INTO senses (word_id, part_of_speech) "
            "SELECT w_id, part_of_speech FROM words"
        )
    )

    # ---- Step 3: add new columns to translations ----
    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "source_sense_id",
                sa.Integer(),
                sa.ForeignKey(
                    "senses.sense_id",
                    name="fk_translations_source_sense_id",
                    ondelete="CASCADE",
                ),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "target_sense_id",
                sa.Integer(),
                sa.ForeignKey(
                    "senses.sense_id",
                    name="fk_translations_target_sense_id",
                    ondelete="CASCADE",
                ),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("note", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("confidence", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("provenance", sa.String(length=40), nullable=True))

    # ---- Step 4: backfill source_sense_id / target_sense_id from existing
    # 1:1 word→sense mapping. Each existing Translation now points at the
    # senses that were created in Step 2. ----
    connection.execute(
        sa.text(
            "UPDATE translations "
            "SET source_sense_id = (SELECT sense_id FROM senses WHERE senses.word_id = translations.source_word_id), "
            "    target_sense_id = (SELECT sense_id FROM senses WHERE senses.word_id = translations.target_word_id)"
        )
    )


def downgrade():
    # ---- Reverse Step 3-4: drop the new translation columns ----
    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.drop_column("provenance")
        batch_op.drop_column("confidence")
        batch_op.drop_column("note")
        batch_op.drop_constraint(
            "fk_translations_target_sense_id", type_="foreignkey"
        )
        batch_op.drop_column("target_sense_id")
        batch_op.drop_constraint(
            "fk_translations_source_sense_id", type_="foreignkey"
        )
        batch_op.drop_column("source_sense_id")

    # ---- Reverse Step 1-2: drop the senses table (and its rows) ----
    with op.batch_alter_table("senses", schema=None) as batch_op:
        batch_op.drop_index("idx_senses_word_id")
    op.drop_table("senses")
