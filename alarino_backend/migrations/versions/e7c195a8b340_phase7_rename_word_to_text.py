"""phase 7: rename words.word column to words.text

Revision ID: e7c195a8b340
Revises: d8a3f0b71e5c
Create Date: 2026-04-25

Final phase of the schema evolution plan: rename the lexical-string column
on the words table from `word` to `text`. The class is still named Word
(it represents a vocabulary entry); only the column was renamed for clarity
since `word.word` was awkward and `word.text` reads naturally.

Atomic: schema rename + the (language, word) unique-constraint rename
land in a single revision because every code path that reads or writes
this column is updated in the same release.

OPERATOR PREFLIGHT (production):
    None required. Pure rename — no data loss, no constraint drift.

REVERSIBILITY:
    Fully reversible. Downgrade renames the column back to `word` and
    restores the unique_language_word constraint name. Data is preserved
    end-to-end.
"""
from alembic import op


revision = "e7c195a8b340"
down_revision = "d8a3f0b71e5c"
branch_labels = None
depends_on = None


def upgrade():
    # Split into two batches: combining drop_constraint + alter_column +
    # create_unique_constraint in a single batch_alter_table block on SQLite
    # silently loses the new constraint when the table is reconstructed.
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.drop_constraint("unique_language_word", type_="unique")
        batch_op.alter_column("word", new_column_name="text")
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "unique_language_text", ["language", "text"]
        )


def downgrade():
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.drop_constraint("unique_language_text", type_="unique")
        batch_op.alter_column("text", new_column_name="word")
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "unique_language_word", ["language", "word"]
        )
