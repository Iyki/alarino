# Schema Evolution Plan

## Objective

Evolve the existing alarino database in place — using Alembic migrations on the live PostgreSQL database — to fix a small number of correctness bugs, retire schema hygiene debt, and restructure the core lexical model so it can represent a real bilingual dictionary (senses, definitions, sense-scoped examples, connected proverbs) rather than a flat word-pair store.

The work is sequenced so each phase is independently shippable. Most phases are individually reversible; the few that aren't (data dedup, dropping columns) are explicitly called out. Higher-value but higher-risk structural changes come after the safe hygiene work has built confidence in the migration pipeline.

## Current Problems

Bugs:

- `Word.created_at` uses `default=datetime.now()` (called once at import) instead of `default=datetime.now` (callable). Every new `Word` row gets the timestamp the process started.
- `MissingTranslation.hit_count` is incremented via read-modify-write in `translation_service.log_missing_translation`, which loses concurrent increments.

Hygiene:

- Several declared indexes duplicate the btree that backs a unique constraint (`idx_words_language_word`, `idx_missing_text_source_target`, prefix of `idx_proverbs_yoruba_text` and `idx_translations_source_word_id`).
- `idx_words_language` indexes a 2-value column and is never used by the planner.
- `created_at` is nullable on every table and has no `server_default`, so direct SQL inserts produce NULLs.
- `MissingTranslation.hit_count` is nullable.
- `Example` has no unique constraint; the same example can be inserted N times against the same translation.

Structural:

- There is no sense layer between `Word` and `Translation`. `part_of_speech` lives on `Word` even though POS depends on sense, and `UNIQUE (language, word)` then prevents the same word from carrying multiple POS values. Polysemous entries ("bank" → financial vs riverbank) are stored as undifferentiated translation pairs.
- `Translation` carries no metadata (definition, gloss, register, domain, source, confidence). Examples attach to `Translation`, not to a sense, so they cannot be disambiguated.
- `Translation` is stored as a directed edge but lookup queries only one direction (`translation_service.translate` filters on `source_word_id` only). Reverse lookups silently miss unless an inverse row was also inserted, and nothing in the schema enforces the inverse.
- `DailyWord` stores two independent FKs (`word_id`, `en_word_id`) with no constraint that they actually form a translation pair.
- `Proverb` has no relationship to `Word`. The seed loader extracts individual words and discards the link.
- `language` is a free-form `String(3)` with no constraint; `'en'`, `'eng'`, `'EN'` could all coexist.
- `MissingTranslation` mixes telemetry (`user_ip`, `user_agent`, `hit_count`) into the lexical schema. After the Phase 0 upsert change, only one row exists per missed (text, source, target) tuple, so `user_ip` cannot represent meaningful "who asked" telemetry — it can only represent "the first asker" or "an arbitrary later asker."
- `Word.word` has a TODO to be renamed to `text`.

## Non-Goals

- No move to fully multilingual storage in this plan. The remaining bilingual hardcoding (`Proverb.yoruba_text`/`english_text`, `is_valid_english_word` / `is_valid_yoruba_word` validators) is left intact. `DailyWord` is rewritten in Phase 5 because the change is independently valuable as a normalization fix, not as multilingual prep. If a third language becomes a real roadmap item, a follow-up plan can replace `Proverb`'s text columns with a `proverb_translations` join table and broaden the validator registry.
- No new product features (audio/IPA, tags, user accounts, edit history, attribution UI). The schema is left structured so these can be added without further restructuring, but they are out of scope here.
- No rewrite of the LLM translation path.
- No data backfill from external sources.
- No introduction of per-request telemetry. The plan removes `user_ip` rather than reshaping it; if per-event analytics is wanted later, that's a separate `missing_translation_events` table done as its own follow-up.

## Migration Principles

- Every phase ships as one or more Alembic revisions. No phase depends on uncommitted work in the next.
- Destructive column changes follow expand/contract: add the new shape, dual-write, cut reads over, drop the old. A rollback during cutover means flipping reads back, not restoring data.
- Backfills run in the same revision as the column add when the table is small (every table here qualifies). For anything that grows past ~100k rows during the plan, the backfill moves to a separate batched script.
- Alembic revisions stay deterministic. Anything that requires a runtime secret, reads from external services, or could fail nondeterministically lives in a controlled backfill script that runs *outside* the Alembic upgrade, with an explicit preflight check that the script ran before the next revision is applied.
- Data-destructive operations (deletes, dropping columns) are always called out explicitly. Before any destructive step, the migration logs the rows being removed to a sidecar table (or to stdout in development) so the deletion can be audited.
- Before any phase that drops or renames a column, ensure no code references the old name. CI runs the test suite against a fresh migrate-from-empty *and* a migrate-from-previous-revision.
- Each phase is reviewed and merged independently. No "big bang" PR.

## Phase 0 — Bug Fixes (no migrations)

Code-only changes. No schema impact.

1. `db_models.Word.created_at`: change `default=datetime.now()` to `default=datetime.now`.
2. `translation_service.log_missing_translation`: replace the read-modify-write with a single atomic upsert against the `unique_missing_translation` constraint:
   ```
   INSERT INTO missing_translations (...) VALUES (...)
   ON CONFLICT (text, source_language, target_language)
   DO UPDATE SET hit_count = missing_translations.hit_count + 1
   ```
   Use SQLAlchemy's `postgresql.insert(...).on_conflict_do_update(...)`.

Risk: minimal. Tests cover both paths.

## Phase 1 — Index and Constraint Hygiene

One Alembic revision. Index drops and column-tightening are reversible. The `Example` deduplication step is **not reversible** and is called out explicitly.

1. Drop redundant indexes (reversible):
   - `idx_words_language_word` (covered by `unique_language_word`)
   - `idx_words_language` (low-cardinality, never used)
   - `idx_missing_text_source_target` (covered by `unique_missing_translation`)
   - `idx_proverbs_yoruba_text` (covered by `unique_proverb_pair` prefix)
   - `idx_translations_source_word_id` (covered by `unique_translation_pair` prefix)
2. Tighten nullability and defaults (reversible):
   - Backfill any NULL `created_at` rows with `now()`.
   - Alter every `created_at` column to `NOT NULL` with `server_default=func.now()`.
   - Alter `MissingTranslation.hit_count` to `NOT NULL DEFAULT 1`.
3. **Data-destructive:** Deduplicate `Example` rows on `(translation_id, example_source, example_target)`, then add `UNIQUE (translation_id, example_source, example_target)`. Removed rows are logged to a `_phase1_removed_examples` sidecar table (raw JSON of each row) so the deletion can be reviewed. Downgrade only drops the constraint — it cannot reconstruct the deleted duplicates. The sidecar table is dropped in the next phase after manual review.

Risk: low for steps 1–2. Step 3 is irreversible by design; review the sidecar dump in staging before running in prod.

## Phase 2 — Language Constraint and Telemetry Cleanup

One Alembic revision.

1. Add `CHECK (language IN ('en', 'yo'))` on `Word.language`, `MissingTranslation.source_language`, `MissingTranslation.target_language`. (A `languages` reference table is overkill at two values; revisit if multilingual work happens.)
2. Drop `MissingTranslation.user_ip` entirely. Rationale: after Phase 0's upsert change, only one row exists per missed tuple, so the column can hold at most one IP per missed word — that's neither meaningful "who asked" data nor useful aggregate telemetry. Dropping it is cleaner than hashing a value that has no analytic use, and it removes the privacy footprint with no loss of signal. If per-request telemetry is wanted later, add a separate events table (out of scope).

Risk: low. The CHECK constraint will fail the migration loudly if any row carries a non-canonical language code — that surfaces existing data quality issues, which is the point. Dropping `user_ip` is data-destructive but the data has no remaining utility; rows are dumped to `_phase2_removed_user_ips` for audit.

## Phase 3 — Connect Proverbs to Vocabulary

One Alembic revision plus one backfill.

1. Add `proverb_words(proverb_id, word_id, language, position)` join table with composite PK `(proverb_id, word_id, language, position)`. `position` preserves word order in the proverb.
2. Backfill by re-running the existing word-extraction logic in `seed_data_utils.add_proverb` against every existing `Proverb` row, inserting `proverb_words` entries pointing at matching `Word` rows (creating any missing `Word` rows as it does today).
3. Add a service method `get_proverbs_containing(word)` and update `add_proverb` so new inserts populate `proverb_words` going forward.

Risk: low. Purely additive. If the backfill is incomplete (e.g., a proverb word doesn't match any `Word` row), the proverb still works as before; only the new "proverbs containing X" query is affected.

## Phase 3a — NFC-Normalize Existing Proverb Text (Bug Fix)

Discovered during Phase 3 implementation review: every runtime *write* path historically bypassed Unicode normalization in different ways, so existing data could be in mixed NFC/NFD forms. The Phase 3 proverb-words connection assumes consistent normalization to dedupe correctly, and the Phase 0 missing-translation upsert assumes consistent normalization on the read path to aggregate hits correctly.

The runtime bug fixes are code-only:

- New `normalize_word_text` and `normalize_text` helpers in `seed_data_utils`.
- `add_proverb` normalizes `yoruba_text` and `english_text` before storage and before duplicate detection.
- `is_valid_yoruba_word`, `is_valid_yoruba_text`, `is_valid_english_word`, and `is_valid_english_text` self-NFC-normalize input. Without this, NFD Yoruba input was rejected because the regex character class is NFC.
- `translate()` and `translate_llm()` route input through `normalize_word_text` so reads against NFC-stored Word rows match NFD requests, and so `log_missing_translation` aggregates by canonical form.

The data migration brings existing rows into NFC:

1. Snapshot every Proverb row's original text into `_phase3a_pre_normalize_proverbs` (full audit trail).
2. Group rows by their NFC pair. For groups with >1 row (NFC/NFD collisions), keep `min(p_id)` and log the rest into `_phase3a_removed_proverb_duplicates` before deleting them.
3. UPDATE remaining rows to NFC.

Risk: low for the schema impact, medium for the data destruction *if* normalization-collision duplicates exist. Operator preflight: count rows in `_phase3a_removed_proverb_duplicates` after staging before promoting to prod.

Reversibility: text UPDATE is reversible from the snapshot; row DELETE is not. Downgrade fails loudly by default (same `ALARINO_FORCE_DOWNGRADE_DATA_LOSS=1` opt-in escape hatch as Phase 1 and Phase 2).

## Phase 3b — Lock In Normalization Defenses (Defense in Depth)

Phase 3a fixed the runtime drift and normalized existing data. Phase 3b makes future drift structurally harder to introduce. Rationale: every normalization bug we fixed in Phase 3a was an instance of "a writer forgot to call `normalize_word_text`." That pattern will recur unless the constraint moves out of call-site discipline and into a place where forgetting is impossible.

No data migration. Code changes only.

1. **SQLAlchemy `TypeDecorator` for canonical text columns.** Add a `NFCWord` (lowercase + strip + NFC, mirrors `normalize_word_text`) and `NFCText` (NFC + strip, mirrors `normalize_text`) TypeDecorator. Apply `NFCWord` to `Word.word` and `MissingTranslation.text`; apply `NFCText` to `Proverb.yoruba_text` and `Proverb.english_text`. The `process_bind_param` hook normalizes on every ORM write, so call sites can no longer skip it. Raw SQL still bypasses, but raw SQL into these tables is already a yellow flag worth flagging at code review.

2. **Property tests for every text-touching API path.** For each of `add_word`, `add_proverb`, `translate`, `translate_llm`, `log_missing_translation`, `get_proverbs_containing`: assert that calling with NFC and NFD of the same Yoruba string produces byte-identical observable outcomes (same row count, same stored bytes, same query results). New text-handling code added later that breaks this property fails CI before it merges.

3. **Schema integrity assertion.** Add a single CI check (or a smoke test that runs against staging) that runs:
   ```sql
   SELECT count(*) FROM words WHERE word != normalize(word, NFC);
   SELECT count(*) FROM proverbs WHERE yoruba_text != normalize(yoruba_text, NFC) OR english_text != normalize(english_text, NFC);
   SELECT count(*) FROM missing_translations WHERE text != normalize(text, NFC);
   ```
   All must return 0. Postgres has `unicode_normalize()` since PG13; the check runs in <1s on tables this size and surfaces drift before it propagates.

Risk: very low. The TypeDecorator is a no-op when input is already canonical (which it will be after Phase 3a + the runtime fixes). Property tests and the integrity check are pure additions.

Out of scope here (considered and rejected): a Postgres `CHECK (text = unicode_normalize(text, 'NFC'))` constraint diverges from SQLite test behavior and would require dialect-specific migration code; a `BEFORE INSERT` normalization trigger silently corrects bugs instead of surfacing them, which masks drift. The TypeDecorator gives the same guarantee at the ORM layer with neither downside.

## Phase 3c — Agentic Enforcement (Process Defenses)

Phase 3b puts the constraint in the type system; Phase 3c puts a second pair of eyes on every change that could subvert it. Phase 3a fixed six different drift bugs that all looked the same in retrospect ("a writer forgot to call `normalize_word_text`"). LLM review is a cheap way to catch the seventh one before it merges.

These are tooling additions, not application code. Each item is independently shippable and independently removable.

1. **PR-time normalization-reviewer subagent.** A GitHub Action (or equivalent CI step) that triggers on PRs touching `alarino_backend/src/alarino_backend/db_models.py`, `alarino_backend/src/alarino_backend/translation_service.py`, `alarino_backend/src/alarino_backend/data/seed_data_utils.py`, or any file under `alarino_backend/migrations/versions/`. The action calls a focused prompt: *"Given this diff, does it introduce or modify a code path that writes user text to a canonical column without routing through `normalize_word_text` / `normalize_text` / the `NFCWord` / `NFCText` TypeDecorator? Return specific file:line references, or 'clean' if none."* Posts a single PR comment with the verdict. Cost: a few cents per touched PR. Failure mode: false positives that reviewers can dismiss; far better than the false negative we already paid for in Phase 3a.

2. **Scheduled drift-detection agent.** A daily `/schedule` job that connects to staging, runs the Phase 3b integrity queries, and opens a GitHub issue (with a sample of offending rows) if any return non-zero. Independent backstop for whatever slipped past the PR reviewer. Cost: one query per day per table; negligible.

3. **Author-invoked review skill.** A `.claude/skills/normalization-review.md` skill definition that encodes the contract from this plan. Author runs `/normalization-review` against the working tree before pushing for any change that touches text-handling code. Catches what local linting can't reason about. Cost: zero until invoked.

Sequencing: ship #1 first (catches the most cases at the right moment), #2 next (cheap insurance), #3 last (only worth defining once the contract from items #1-#2 is stable enough to encode in a skill).

Out of scope here (considered and rejected): live request-time LLM inspection (too slow, redundant with the TypeDecorator that already runs on every write); LLM auto-fix that rewrites the diff (silent correction defeats the goal of surfacing intent — same reasoning as rejecting the DB-level normalization trigger in Phase 3b).

Risk: very low. None of these touch production data or runtime code. Worst case is a noisy CI bot that reviewers ignore, which is recoverable by removing the action.

## Phase 4 — Bidirectional Translation Lookup

**Decision (recorded after design discussion):** keep `Translation` as a directed edge (one row per curated direction, no auto-mirror) and fix the *lookup* code to query both columns. This was chosen over the originally-considered alternatives (canonical undirected storage with consolidation; auto-creating the inverse on every insert) because it preserves curatorial intent — the schema honestly records what was added in which direction — while still giving users a "translations are symmetric" experience.

The bug being fixed: today `translate()` filters only on `source_word_id`. A row `(en:hello → yo:bawo)` makes `translate("hello", en→yo)` work, but `translate("bawo", yo→en)` returns "translation not available" even though the data is right there. Verified end-to-end in the Phase 3a Docker validation (test G3): bulk-upload created the en→yo direction only, and the yo→en lookup failed.

No schema change. No migration. No new constraints. One service-layer change plus tests.

**Implementation:**

1. In `translation_service.translate()`, change the Translation query from "source_word_id = X" to "source_word_id = X OR target_word_id = X". For each match, return the *other* word — `target_word` if the lookup matched the source side, `source_word` if it matched the target side. Filter the "other word" by the requested target language and dedupe by `w_id` so a pair curated in both directions doesn't return the same Yoruba word twice.
2. Add a `direction` field on `TranslationResponseData` (or similar — final shape TBD) so the frontend can distinguish results from the curated direction vs the implicit reverse, if it ever wants to surface that. Default presentation is identical regardless.
3. No write-path changes. `create_translation` keeps its current single-direction semantics. Contributors who want both directions explicitly can add both rows; nothing requires them to.

**Tests:**

- Property test: insert a single `(en:hello → yo:bawo)` row through the public API; `translate("hello", en→yo)` returns `["bawo"]`; `translate("bawo", yo→en)` returns `["hello"]`. Both directions resolve from the one curated row.
- Dedup test: insert both `(en:hello → yo:bawo)` and `(yo:bawo → en:hello)`; lookup in either direction returns each translation exactly once.
- Negative test: empty translations table → both directions return "translation not available."

Risk: very low. No schema change, no migration, no data destruction. The only behavioral change is that lookups that previously returned 404 because only the inverse was curated will now return 200. That's the intended fix.

## Phase 5 — Normalize `DailyWord` to Reference `Translation`

One Alembic revision.

Phase 4 settled on directed storage with bidirectional lookup (no auto-mirror). That means a `Translation` row may have its source and target columns in either language order — whichever direction the curator originally added. **Read paths must derive the Yoruba and English sides by joining `Word` and inspecting `Word.language`, not by assuming `source_word_id` is Yoruba and `target_word_id` is English.** The current `get_word_of_the_day` code makes that positional assumption today and must be updated as part of this phase.

A daily word is conceptually a translation pair, but today `DailyWord` stores `word_id` and `en_word_id` as two independent FKs to `Word`. Nothing in the schema requires those two words to actually be a translation of each other. Replacing both columns with a single `translation_id` FK makes the relationship correct by construction.

1. Add `DailyWord.translation_id` (nullable) FK → `translations.t_id`.
2. Backfill: for each existing `DailyWord` row, find the matching `Translation` by querying both directions (`(word_id, en_word_id)` and `(en_word_id, word_id)`).
3. **Stop the migration on integrity failure.** If any `DailyWord` row has no matching `Translation`, the migration aborts with a list of offending `dw_id` values. Rationale: a daily word that points at two unrelated words is corrupt input, not a row to launder by manufacturing a translation pair. The operator must either delete the bad daily word or insert the intended translation manually before re-running the migration. Do *not* silently create a translation, because doing so makes the corruption permanent and indistinguishable from real curated data.
4. Update `translation_service.get_word_of_the_day` and any write paths to use `translation_id`.
5. Make `translation_id` `NOT NULL`.
6. Drop `word_id` and `en_word_id`.

Risk: low for the schema change. The fail-loud backfill *is* the safety mechanism; expect the first run in staging to surface real integrity issues that need human review.

## Phase 6 — Sense Layer (Core Restructure)

The largest change. Multiple Alembic revisions across two release cycles, expand/contract throughout.

### 6a — Add the sense layer alongside existing structure

1. Add `senses` table:
   - `sense_id` PK
   - `word_id` FK → `words.w_id`
   - `part_of_speech` (moved from `Word`, but kept on `Word` for now)
   - `sense_label` (short disambiguator, e.g. "financial", "river")
   - `definition` (Text, nullable)
   - `register` (formal/colloquial/slang/archaic, nullable)
   - `domain` (medical/legal/etc, nullable)
   - `created_at` with proper defaults
2. Add `translations.source_sense_id` and `translations.target_sense_id` (nullable initially), each FK to `senses`.
3. Add metadata columns on `Translation`:
   - `note` (Text, nullable)
   - `confidence` (Float, nullable)
   - `source` (String, nullable — e.g. `'curated'`, `'llm'`, `'community'`)
4. Backfill: for every existing `Word`, create one `senses` row carrying that word's current `part_of_speech`. For every existing `Translation`, set `source_sense_id` and `target_sense_id` to those single senses.

After 6a, the schema supports senses but nothing forces their use. Reads still work as before.

### 6b — Cut writes over to senses

1. Update `seed_data_utils` and `translation_service` write paths so new translations always create or reuse a `Sense` and reference it.
2. Move `Example` to attach to a `(source_sense_id, target_sense_id)` pair instead of `translation_id`. Migrate existing rows by copying the now-known sense IDs from the parent translation. Keep `translation_id` on `Example` until 6d.

### 6c — Cut reads over to senses

1. Update `translate()` to return sense-grouped results (multiple senses → multiple result groups, each with its own translations and examples).
2. Update API response shape behind a feature flag or a new endpoint version (`/api/v2/translate`). Old endpoint remains until the frontend cuts over.

### 6d — Drop legacy

1. Make `translations.source_sense_id` and `translations.target_sense_id` `NOT NULL`.
2. Drop `Example.translation_id`.
3. Drop `Word.part_of_speech`.
4. Remove the v1 translate endpoint once frontend traffic is fully on v2.

Risk: medium. The expand/contract pattern keeps each step reversible until 6d, but the API change in 6c is user-visible. Coordinate with the frontend.

## Phase 7 — Rename `word` to `text`

One Alembic revision, expand/contract.

1. Add `Word.text` column, copy `word` into it, set `NOT NULL`.
2. Recreate `unique_language_word` as `unique_language_text` on `(language, text)`.
3. Update all reads to use `text`.
4. Drop `word`.

Risk: low. Deferred to last so it doesn't entangle with sense-layer work.

## Out of Scope (Possible Follow-Ups)

- **Multilingual conversion.** Replace `Proverb.yoruba_text`/`english_text` with `proverb_translations(proverb_id, language, text)`, broaden the language CHECK constraint, and replace `is_valid_yoruba_word` / `is_valid_english_word` with a generic per-language validator registry. Only worth doing if a third language is on the roadmap. (`DailyWord` is already covered by Phase 5.)
- **Per-request telemetry.** Add a `missing_translation_events(text, source, target, requested_at, ...)` append-only table to capture the "who asked, when" signal that `user_ip` was vaguely gesturing at. Distinct from the aggregated `missing_translations` row, which keeps its role as the unique-per-tuple counter.
- **Pronunciation, audio, IPA, tags, lemma/inflection model.** All additive; no current blocker.
- **Edit history and contributor identity.** Requires an auth model first.

## Testing Expectations

- Every phase adds tests covering: the new constraint or column behavior, the backfill correctness on representative fixture data, and a regression test for any read path whose query changed.
- Each migration is exercised both forward and back (`alembic upgrade head && alembic downgrade -1 && alembic upgrade head`) in CI. Phases with explicitly non-reversible steps (Phase 1 step 3, Phase 2 user_ip drop, Phase 3a duplicate consolidation, Phase 6d) test forward-only and assert that downgrade fails cleanly with a clear message rather than silently leaving the schema half-migrated. (Phase 4 has no migration.)
- Phase 4 adds property tests for bidirectional lookup: a single curated `(en:hello → yo:bawo)` row makes `translate("hello", en→yo)` and `translate("bawo", yo→en)` both succeed; curating both directions returns each translation exactly once (dedup); empty translations table returns "translation not available" in both directions.
- Phase 6 adds a property test: a polysemous word (e.g. "bank") with two senses and two distinct target translations returns two grouped result sets from `translate()`, each with its own examples — verifying the sense layer is actually load-bearing and not just structurally present.
