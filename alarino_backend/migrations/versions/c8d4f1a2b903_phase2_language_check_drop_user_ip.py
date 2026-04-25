"""phase 2: add language CHECK constraints, drop missing_translations.user_ip

Revision ID: c8d4f1a2b903
Revises: 7e3a89c4b21f
Create Date: 2026-04-25

Implements Phase 2 of the schema evolution plan
(docs/plans/schema_evolution_plan.md).

OPERATOR PREFLIGHT (production):
    Before applying, verify that no rows carry a non-canonical language
    code. The CHECK constraint will fail to apply otherwise:

        SELECT DISTINCT language FROM words;
        SELECT DISTINCT source_language FROM missing_translations;
        SELECT DISTINCT target_language FROM missing_translations;

    All values must be 'en' or 'yo'. If anything else appears, decide
    case-by-case whether to normalize or delete the offending rows before
    re-running the migration.

    Also review _phase2_removed_user_ips after the migration runs. The
    column drop is intentionally non-reversible (the original IP values
    cannot be reconstructed); the sidecar table is the only audit trail.

REVERSIBILITY:
    The CHECK constraints are reversible (drop them on downgrade).
    The user_ip column drop is NOT reversible — the original IP values
    cannot be reconstructed from this migration alone.

    Downgrade therefore FAILS LOUDLY by default rather than silently doing
    a partial reversal that re-adds an empty user_ip column while leaving
    the original data lost. Operators who explicitly accept the data loss
    can set ALARINO_FORCE_DOWNGRADE_DATA_LOSS=1 in the environment to opt
    in. With that env var set, the downgrade proceeds with the partial
    reversal: it drops the CHECK constraints and re-adds user_ip as a
    nullable VARCHAR(45), and leaves _phase2_removed_user_ips in place as
    the only audit trail of the dropped values.
"""
import os

from alembic import op
import sqlalchemy as sa


revision = "c8d4f1a2b903"
down_revision = "7e3a89c4b21f"
branch_labels = None
depends_on = None


def upgrade():
    # ---- Step 1 (DATA-DESTRUCTIVE): snapshot user_ip then drop the column ----
    op.execute(
        """
        CREATE TABLE _phase2_removed_user_ips (
            m_id INTEGER,
            text VARCHAR(200),
            source_language VARCHAR(3),
            target_language VARCHAR(3),
            user_ip VARCHAR(45),
            removed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        INSERT INTO _phase2_removed_user_ips
            (m_id, text, source_language, target_language, user_ip)
        SELECT m_id, text, source_language, target_language, user_ip
        FROM missing_translations
        WHERE user_ip IS NOT NULL
        """
    )
    with op.batch_alter_table("missing_translations", schema=None) as batch_op:
        batch_op.drop_column("user_ip")

    # ---- Step 2: add CHECK constraints on language columns ----
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_words_language_valid",
            "language IN ('en', 'yo')",
        )
    with op.batch_alter_table("missing_translations", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_missing_translations_source_language_valid",
            "source_language IN ('en', 'yo')",
        )
        batch_op.create_check_constraint(
            "ck_missing_translations_target_language_valid",
            "target_language IN ('en', 'yo')",
        )


def downgrade():
    if os.environ.get("ALARINO_FORCE_DOWNGRADE_DATA_LOSS") != "1":
        raise RuntimeError(
            "Phase 2 (revision c8d4f1a2b903) is NOT reversible: the user_ip "
            "values dropped from missing_translations cannot be reconstructed "
            "from this migration. Restore them from _phase2_removed_user_ips "
            "or from a backup before downgrading. To proceed anyway and accept "
            "the data loss, set ALARINO_FORCE_DOWNGRADE_DATA_LOSS=1 in the "
            "environment."
        )

    # ---- Step 2 reverse: drop CHECK constraints ----
    with op.batch_alter_table("missing_translations", schema=None) as batch_op:
        batch_op.drop_constraint(
            "ck_missing_translations_target_language_valid", type_="check"
        )
        batch_op.drop_constraint(
            "ck_missing_translations_source_language_valid", type_="check"
        )
    with op.batch_alter_table("words", schema=None) as batch_op:
        batch_op.drop_constraint("ck_words_language_valid", type_="check")

    # ---- Step 1 reverse (PARTIAL): re-add user_ip column. Original values
    # cannot be restored from this migration; copy from _phase2_removed_user_ips
    # if needed. ----
    with op.batch_alter_table("missing_translations", schema=None) as batch_op:
        batch_op.add_column(sa.Column("user_ip", sa.String(length=45), nullable=True))
