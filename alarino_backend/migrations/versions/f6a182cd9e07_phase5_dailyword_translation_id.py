"""phase 5: normalize DailyWord to reference Translation

Revision ID: f6a182cd9e07
Revises: e5a9c2b48d76
Create Date: 2026-04-25

Implements Phase 5 of the schema evolution plan
(docs/plans/schema_evolution_plan.md).

Replaces DailyWord.word_id + DailyWord.en_word_id (two independent FKs to
words, with no schema-level guarantee that the two words actually form a
translation pair) with a single DailyWord.translation_id FK to translations.

Phase 4 settled on directed storage with bidirectional lookup, so the
backfill must look for the matching Translation row in BOTH directions
(word_id, en_word_id) and (en_word_id, word_id) — either is a valid match.

OPERATOR PREFLIGHT (production):
    The migration aborts with a list of offending dw_id values if any
    DailyWord row has no matching Translation in either direction.
    Surface this in staging first; the offending rows are corrupt data
    (a daily word that points at two unrelated Words) and must be
    reconciled manually before production. Two reconciliation paths:
        a) Delete the bad daily_words row.
        b) Insert the intended translation pair manually into translations,
           then re-run the migration.
    Do NOT silently auto-create a translation here — that would launder
    the corruption into accepted curated data.

REVERSIBILITY:
    Forward path makes a destructive column drop (word_id, en_word_id).
    Downgrade re-adds the columns and backfills them from the linked
    translation, recovering the same bytes that were dropped — but only
    when the backfill was clean (every daily_words row had a matching
    translation). This is reversible WITHOUT the data-loss opt-in escape
    hatch other phases use, because the data is recoverable from the
    referenced Translation.
"""
from alembic import op
import sqlalchemy as sa


revision = "f6a182cd9e07"
down_revision = "e5a9c2b48d76"
branch_labels = None
depends_on = None


def upgrade():
    # ---- Step 1: add translation_id, nullable initially so the backfill can run ----
    with op.batch_alter_table("daily_words", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "translation_id",
                sa.Integer(),
                sa.ForeignKey(
                    "translations.t_id",
                    name="fk_daily_words_translation_id",
                    ondelete="CASCADE",
                ),
                nullable=True,
            )
        )

    # ---- Step 2: backfill translation_id from existing word_id + en_word_id ----
    connection = op.get_bind()
    daily_rows = connection.execute(
        sa.text("SELECT dw_id, word_id, en_word_id FROM daily_words")
    ).fetchall()

    unmatched: list[int] = []
    for dw_id, word_id, en_word_id in daily_rows:
        # Phase 4 stores translations as directed edges; check both possible
        # directions for the matching pair.
        match = connection.execute(
            sa.text(
                "SELECT t_id FROM translations "
                "WHERE (source_word_id = :a AND target_word_id = :b) "
                "OR (source_word_id = :b AND target_word_id = :a) "
                "ORDER BY t_id LIMIT 1"
            ),
            {"a": word_id, "b": en_word_id},
        ).fetchone()
        if match is None:
            unmatched.append(dw_id)
            continue
        connection.execute(
            sa.text(
                "UPDATE daily_words SET translation_id = :t WHERE dw_id = :d"
            ),
            {"t": match[0], "d": dw_id},
        )

    if unmatched:
        raise RuntimeError(
            "Phase 5 (revision f6a182cd9e07) cannot proceed: the following "
            f"daily_words rows have no matching translation in either direction: {unmatched}. "
            "These are corrupt: a daily word that points at two unrelated Words. "
            "Reconcile by either deleting the bad daily_words rows or inserting "
            "the intended translation pair manually into translations, then "
            "re-run the migration. Do NOT auto-create a translation here — "
            "that would launder the corruption into accepted curated data."
        )

    # ---- Step 3: tighten translation_id, add unique constraint, drop old columns ----
    with op.batch_alter_table("daily_words", schema=None) as batch_op:
        batch_op.alter_column(
            "translation_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.create_unique_constraint(
            "unique_daily_words_translation_id",
            ["translation_id"],
        )
        batch_op.drop_column("en_word_id")
        batch_op.drop_column("word_id")


def downgrade():
    # ---- Re-add word_id and en_word_id columns ----
    with op.batch_alter_table("daily_words", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "word_id",
                sa.Integer(),
                sa.ForeignKey("words.w_id", name="fk_daily_words_word_id"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "en_word_id",
                sa.Integer(),
                sa.ForeignKey(
                    "words.w_id", name="fk_daily_words_en_word_id"
                ),
                nullable=True,
            )
        )

    # ---- Backfill word_id and en_word_id from the linked translation. ----
    # The original schema's word_id was conventionally the Yoruba side and
    # en_word_id was the English side, derived from Word.language.
    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT dw.dw_id, t.source_word_id, t.target_word_id, "
            "       sw.language AS source_lang, tw.language AS target_lang "
            "FROM daily_words dw "
            "JOIN translations t ON t.t_id = dw.translation_id "
            "JOIN words sw ON sw.w_id = t.source_word_id "
            "JOIN words tw ON tw.w_id = t.target_word_id"
        )
    ).fetchall()
    for dw_id, source_id, target_id, source_lang, target_lang in rows:
        if source_lang == "yo":
            yo_id, en_id = source_id, target_id
        else:
            yo_id, en_id = target_id, source_id
        connection.execute(
            sa.text(
                "UPDATE daily_words SET word_id = :yo, en_word_id = :en "
                "WHERE dw_id = :d"
            ),
            {"yo": yo_id, "en": en_id, "d": dw_id},
        )

    # ---- Tighten + drop translation_id ----
    with op.batch_alter_table("daily_words", schema=None) as batch_op:
        batch_op.alter_column(
            "word_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "en_word_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.drop_constraint(
            "unique_daily_words_translation_id", type_="unique"
        )
        batch_op.drop_column("translation_id")
