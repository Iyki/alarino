"""phase 6d: drop legacy sense-layer columns and tighten sense FKs

Revision ID: d8a3f0b71e5c
Revises: c4b8e1a5d927
Create Date: 2026-04-25

Closes the sense-layer cutover:
  - Translation source_sense_id and target_sense_id become NOT NULL.
  - Examples lose translation_id and the unique_example_per_translation
    constraint; new uniqueness is on (source_sense_id, target_sense_id,
    example_source, example_target).
  - Word.part_of_speech is dropped (POS is sense-scoped now).

PREFLIGHT (built into the migration):
  - Every Translation must have non-NULL source_sense_id and
    target_sense_id. Phase 6a backfilled all existing rows; Phase 6b's
    create_translation populates them on every new Translation. A stray
    Translation inserted via raw SQL between 6a and 6d would surface
    here.
  - Every Example must have non-NULL source_sense_id and target_sense_id.
    Phase 6b backfilled existing rows; new Examples must set them
    explicitly. Strays surface here.

REVERSIBILITY:
  - Tightening Translation sense FKs to NOT NULL is reversible (downgrade
    relaxes them).
  - Dropping Word.part_of_speech is data-destructive (the column held
    POS values copied to Sense.part_of_speech in Phase 6a; the Sense
    column carries the same data and is not affected). Downgrade
    re-adds the Word column nullable but does NOT restore values —
    operators that need them can copy from senses.part_of_speech via
    the one-sense-per-word mapping that Phase 6a established.
  - Dropping Example.translation_id is data-destructive (the link to
    parent Translation is lost; sense-pair link via source_sense_id /
    target_sense_id replaces it). Downgrade re-adds the column nullable
    but does NOT restore values.

  Therefore downgrade FAILS LOUDLY by default. Set
  ALARINO_FORCE_DOWNGRADE_DATA_LOSS=1 to opt into the partial reversal
  that re-adds the columns empty.
"""
import os

from alembic import op
import sqlalchemy as sa


revision = "d8a3f0b71e5c"
down_revision = "c4b8e1a5d927"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    # ---- Preflight: Translation sense FKs must all be non-NULL ----
    null_translation_senses = [
        row[0]
        for row in connection.execute(
            sa.text(
                "SELECT t_id FROM translations "
                "WHERE source_sense_id IS NULL OR target_sense_id IS NULL"
            )
        ).fetchall()
    ]
    if null_translation_senses:
        raise RuntimeError(
            "Phase 6d (revision d8a3f0b71e5c) cannot proceed: the following "
            f"translations have NULL sense FKs: {null_translation_senses}. "
            "Phase 6a backfilled all existing rows and Phase 6b's create_translation "
            "populates new rows; stray Translations created via raw SQL between "
            "6a and 6d may have NULL sense FKs. Either delete them or set their "
            "source_sense_id/target_sense_id manually before re-running."
        )

    # ---- Preflight: Example sense FKs must all be non-NULL (only matters
    # because we're dropping translation_id; an Example with NULL sense FKs
    # AND no translation_id would be unattached to anything). ----
    null_example_senses = [
        row[0]
        for row in connection.execute(
            sa.text(
                "SELECT e_id FROM examples "
                "WHERE source_sense_id IS NULL OR target_sense_id IS NULL"
            )
        ).fetchall()
    ]
    if null_example_senses:
        raise RuntimeError(
            "Phase 6d (revision d8a3f0b71e5c) cannot proceed: the following "
            f"examples have NULL sense FKs: {null_example_senses}. Dropping "
            "translation_id would orphan them. Either delete them or set their "
            "source_sense_id/target_sense_id manually (e.g., copy from the "
            "linked Translation via examples.translation_id) before re-running."
        )

    # ---- Step 1: tighten Translation sense FKs ----
    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.alter_column(
            "source_sense_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "target_sense_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

    # ---- Step 2: replace Example uniqueness, drop translation_id ----
    with op.batch_alter_table("examples", schema=None) as batch_op:
        batch_op.drop_constraint(
            "unique_example_per_translation", type_="unique"
        )
        batch_op.create_unique_constraint(
            "unique_example_per_sense_pair",
            ["source_sense_id", "target_sense_id", "example_source", "example_target"],
        )
        batch_op.drop_column("translation_id")

    # ---- Step 3: drop Word.part_of_speech and its CHECK constraint ----
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.drop_constraint(
            "ck_words_part_of_speech_valid", type_="check"
        )
        batch_op.drop_column("part_of_speech")


def downgrade():
    if os.environ.get("ALARINO_FORCE_DOWNGRADE_DATA_LOSS") != "1":
        raise RuntimeError(
            "Phase 6d (revision d8a3f0b71e5c) is NOT cleanly reversible: "
            "Word.part_of_speech and Example.translation_id were dropped. "
            "Sense.part_of_speech carries the same POS data via the one-sense-"
            "per-word mapping Phase 6a established; operators who need to "
            "restore Example.translation_id values must derive them from the "
            "(source_sense_id, target_sense_id) pair. To proceed with the "
            "partial reversal that re-adds the columns empty and relaxes the "
            "NOT NULL constraints, set ALARINO_FORCE_DOWNGRADE_DATA_LOSS=1 "
            "in the environment."
        )

    # ---- Step 3 reverse: re-add Word.part_of_speech (empty) + CHECK ----
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("part_of_speech", sa.String(length=20), nullable=True)
        )
        batch_op.create_check_constraint(
            "ck_words_part_of_speech_valid",
            "part_of_speech IS NULL OR part_of_speech IN ("
            "'adj', 'adv', 'conj', 'det', 'interj', 'n', 'num', 'part', 'prep', 'pron', 'v')",
        )

    # ---- Step 2 reverse: re-add Example.translation_id (empty) + restore unique ----
    with op.batch_alter_table("examples", schema=None) as batch_op:
        batch_op.drop_constraint(
            "unique_example_per_sense_pair", type_="unique"
        )
        batch_op.add_column(
            sa.Column(
                "translation_id",
                sa.Integer(),
                sa.ForeignKey(
                    "translations.t_id",
                    name="fk_examples_translation_id",
                    ondelete="CASCADE",
                ),
                nullable=True,
            )
        )
        batch_op.create_unique_constraint(
            "unique_example_per_translation",
            ["translation_id", "example_source", "example_target"],
        )

    # ---- Step 1 reverse: relax Translation sense FKs ----
    with op.batch_alter_table("translations", schema=None) as batch_op:
        batch_op.alter_column(
            "target_sense_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.alter_column(
            "source_sense_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
