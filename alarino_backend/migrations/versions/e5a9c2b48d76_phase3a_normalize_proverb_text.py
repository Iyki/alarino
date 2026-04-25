"""phase 3a: NFC-normalize existing Proverb.yoruba_text and english_text

Revision ID: e5a9c2b48d76
Revises: d2e8f60a7c14
Create Date: 2026-04-25

Companion to Phase 3. The runtime add_proverb() path historically wrote
yoruba_text and english_text without Unicode normalization, so existing
rows can be in mixed forms (some NFC, some NFD, some inconsistent within
a single row). After this revision, runtime writes go through normalize_text
and only insert NFC forms; this migration brings existing data into the
same canonical form.

Strategy:
    1. Snapshot every proverb row (original text) into _phase3a_pre_normalize_proverbs.
    2. Compute NFC of each (yoruba_text, english_text) pair in Python.
    3. Group by the NFC pair. For groups with multiple rows, keep min(p_id)
       and delete the rest (their original text is in the sidecar and the
       DELETE itself is logged to _phase3a_removed_proverb_duplicates).
    4. UPDATE remaining rows to their NFC values.

OPERATOR PREFLIGHT:
    Estimate impact before running:
        SELECT count(*) FROM proverbs;
        -- After running, compare:
        SELECT count(*) FROM _phase3a_removed_proverb_duplicates;

    If the removed-duplicates count is non-zero, review the sidecar in
    staging before running in prod.

REVERSIBILITY:
    The UPDATE step is reversible from _phase3a_pre_normalize_proverbs.
    The DELETE step (when normalization-collision duplicates exist) is
    NOT reversible from this migration alone. Downgrade therefore FAILS
    LOUDLY by default; set ALARINO_FORCE_DOWNGRADE_DATA_LOSS=1 to opt
    into the partial reversal that restores text values from the sidecar
    but cannot restore deleted rows.
"""
import os
import unicodedata

from alembic import op
import sqlalchemy as sa


revision = "e5a9c2b48d76"
down_revision = "d2e8f60a7c14"
branch_labels = None
depends_on = None


def _nfc(text):
    if text is None:
        return None
    return unicodedata.normalize("NFC", text)


def upgrade():
    op.execute(
        """
        CREATE TABLE _phase3a_pre_normalize_proverbs (
            p_id INTEGER PRIMARY KEY,
            original_yoruba_text TEXT,
            original_english_text TEXT,
            snapshotted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE _phase3a_removed_proverb_duplicates (
            p_id INTEGER,
            original_yoruba_text TEXT,
            original_english_text TEXT,
            kept_p_id INTEGER,
            removed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT p_id, yoruba_text, english_text FROM proverbs")
    ).fetchall()

    # Snapshot every row's original text.
    for row in rows:
        connection.execute(
            sa.text(
                "INSERT INTO _phase3a_pre_normalize_proverbs "
                "(p_id, original_yoruba_text, original_english_text) "
                "VALUES (:p, :y, :e)"
            ),
            {"p": row[0], "y": row[1], "e": row[2]},
        )

    # Group by NFC pair to find collision-duplicates.
    groups: dict[tuple[str, str], list[tuple[int, str, str]]] = {}
    for p_id, y_text, e_text in rows:
        key = (_nfc(y_text) or "", _nfc(e_text) or "")
        groups.setdefault(key, []).append((p_id, y_text, e_text))

    rows_to_delete: list[tuple[int, str, str, int]] = []
    rows_to_update: list[tuple[int, str, str]] = []
    for (y_nfc, e_nfc), group in groups.items():
        group.sort(key=lambda r: r[0])
        keeper_p_id = group[0][0]
        for p_id, y_orig, e_orig in group[1:]:
            rows_to_delete.append((p_id, y_orig, e_orig, keeper_p_id))
        # Update keeper to NFC if it isn't already.
        keeper_y_orig = group[0][1]
        keeper_e_orig = group[0][2]
        if keeper_y_orig != y_nfc or keeper_e_orig != e_nfc:
            rows_to_update.append((keeper_p_id, y_nfc, e_nfc))

    # Log + delete duplicates first so the UPDATE doesn't trip the unique
    # constraint when one row in a group is already NFC.
    for p_id, y_orig, e_orig, keeper_p_id in rows_to_delete:
        connection.execute(
            sa.text(
                "INSERT INTO _phase3a_removed_proverb_duplicates "
                "(p_id, original_yoruba_text, original_english_text, kept_p_id) "
                "VALUES (:p, :y, :e, :k)"
            ),
            {"p": p_id, "y": y_orig, "e": e_orig, "k": keeper_p_id},
        )
        connection.execute(
            sa.text("DELETE FROM proverbs WHERE p_id = :p"),
            {"p": p_id},
        )

    # Now safely update keepers to NFC form.
    for p_id, y_nfc, e_nfc in rows_to_update:
        connection.execute(
            sa.text(
                "UPDATE proverbs SET yoruba_text = :y, english_text = :e "
                "WHERE p_id = :p"
            ),
            {"p": p_id, "y": y_nfc, "e": e_nfc},
        )


def downgrade():
    if os.environ.get("ALARINO_FORCE_DOWNGRADE_DATA_LOSS") != "1":
        raise RuntimeError(
            "Phase 3a (revision e5a9c2b48d76) is NOT cleanly reversible if "
            "any normalization-collision duplicates were removed. Inspect "
            "_phase3a_removed_proverb_duplicates first; if it is non-empty "
            "those rows cannot be restored from this migration. To proceed "
            "with the partial reversal (restore text values from "
            "_phase3a_pre_normalize_proverbs, leave deleted rows lost), set "
            "ALARINO_FORCE_DOWNGRADE_DATA_LOSS=1 in the environment."
        )

    connection = op.get_bind()
    snapshot_rows = connection.execute(
        sa.text(
            "SELECT p_id, original_yoruba_text, original_english_text "
            "FROM _phase3a_pre_normalize_proverbs"
        )
    ).fetchall()
    for p_id, y_orig, e_orig in snapshot_rows:
        connection.execute(
            sa.text(
                "UPDATE proverbs SET yoruba_text = :y, english_text = :e "
                "WHERE p_id = :p"
            ),
            {"p": p_id, "y": y_orig, "e": e_orig},
        )
