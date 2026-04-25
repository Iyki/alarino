"""phase 6b: add sense FKs to examples and backfill from translations

Revision ID: b3d217fa094e
Revises: a91f5e3b8c42
Create Date: 2026-04-25

Implements the schema portion of Phase 6b. Adds source_sense_id and
target_sense_id columns to the examples table (nullable) and backfills
them by copying from the linked Translation's sense IDs. Examples become
sense-scoped going forward — an example for "bank — financial" should
not appear under "bank — riverbank."

The application-side write-path change (create_translation now ensures a
default Sense for both words) ships in the same revision in code; this
migration only handles the schema and backfill.

translation_id is intentionally KEPT on examples until Phase 6d. Read
paths during 6b/6c can use either the legacy translation_id link or
the new sense-pair link; 6d drops translation_id once the sense-pair
link is fully load-bearing.

REVERSIBILITY:
    Fully reversible. Downgrade drops the two new columns. No data loss
    outside the new columns themselves (which were either NULL or
    backfilled-from-Translation values that are still recoverable from
    the linked Translation).

OPERATOR PREFLIGHT (production):
    None required. Backfill is a deterministic copy from each Example's
    linked Translation. Phase 6a guaranteed every existing Translation
    has both source_sense_id and target_sense_id set, so the copy is
    well-defined for every Example.
"""
from alembic import op
import sqlalchemy as sa


revision = "b3d217fa094e"
down_revision = "a91f5e3b8c42"
branch_labels = None
depends_on = None


def upgrade():
    # ---- Step 1: add sense FK columns to examples ----
    with op.batch_alter_table("examples", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "source_sense_id",
                sa.Integer(),
                sa.ForeignKey(
                    "senses.sense_id",
                    name="fk_examples_source_sense_id",
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
                    name="fk_examples_target_sense_id",
                    ondelete="CASCADE",
                ),
                nullable=True,
            )
        )

    # ---- Step 2: backfill from each Example's linked Translation ----
    op.execute(
        """
        UPDATE examples
        SET source_sense_id = (
                SELECT t.source_sense_id FROM translations t WHERE t.t_id = examples.translation_id
            ),
            target_sense_id = (
                SELECT t.target_sense_id FROM translations t WHERE t.t_id = examples.translation_id
            )
        """
    )


def downgrade():
    with op.batch_alter_table("examples", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_examples_target_sense_id", type_="foreignkey"
        )
        batch_op.drop_column("target_sense_id")
        batch_op.drop_constraint(
            "fk_examples_source_sense_id", type_="foreignkey"
        )
        batch_op.drop_column("source_sense_id")
