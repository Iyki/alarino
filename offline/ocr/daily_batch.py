#!/usr/bin/env python3
"""Daily batch driver for OCRing the full 1913 CMS dictionary.

One invocation per day (via cron or by hand):
1. OCRs up to a per-model daily budget of new pages (Gemini in one thread;
   the two OpenRouter models sequentially in another, since they share the
   account rate limit). Rate-limit failures just leave pages for tomorrow.
2. Rebuilds cross-model comparisons.
3. Harvests pages that have transcripts from all --min-models models and
   were never uploaded, into a dated batch CSV of unanimous pairs.
4. Dry-runs the batch through bulk_upload_words; uploads live only if the
   dry-run rejects nothing; records uploaded pages in a ledger.

Everything is resumable: state is the filesystem (transcripts, comparison
reports, the uploaded-pages ledger).

Usage:
    python offline/ocr/daily_batch.py            # full daily run
    python offline/ocr/daily_batch.py --no-upload  # OCR + compare only
"""

import argparse
import csv
import datetime
import json
import subprocess
import sys
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OCR_DIR = REPO_ROOT / "offline" / "ocr"
PAGES_DIR = REPO_ROOT / "offline" / "scans" / "pages"
OUT_DIR = REPO_ROOT / "offline" / "out"
LEDGER = OUT_DIR / "uploaded_pages.json"
PYTHON = sys.executable

# Dictionary content starts after the front matter (title, preface, notes on
# orthography — pg000..pg010).
FIRST_CONTENT_PAGE = "pg011"

# Each dict is one worker thread of {model alias: daily budget of newly
# transcribed pages}, models within a thread running sequentially.
# Panel (2026-09-05): Qwen3-VL 235B is the paid anchor (~$1 per full book
# pass, no daily cap); gemma + dots are :free and share the OpenRouter
# account limit (1,000/day on a funded account). Gemini Flash was dropped:
# its current free tier allows only ~20 requests/day per model.
THREADS = [
    {"qwen3-vl-235b": 460},
    {"gemma-4-31b": 300, "dots-3-note": 300},
    # Best-quality model, but its free tier allows only ~20 requests/day —
    # a slow drip. Per policy it must be present for any unanimous harvest.
    {"gemini-3.8-flash": 18},
]
ALL_MODELS = {alias: b for thread in THREADS for alias, b in thread.items()}

# Models that MUST have transcribed a page before it can be harvested,
# regardless of how many other models covered it.
REQUIRED_MODELS = ("gemini-3.8-flash",)

# Extra ocr_pages.py arguments per model. Gemini free tier is 5 RPM (per
# the AI Studio dashboard) with a small daily request quota: --pace 13s
# stays under the RPM window so requests succeed instead of burning the
# quota on retries, and --max-requests hard-caps the day's attempts.
MODEL_EXTRA_ARGS = {"gemini-3.8-flash": ["--max-requests", "20", "--pace", "13"]}


def content_pages() -> list[Path]:
    return sorted(
        p for p in PAGES_DIR.iterdir()
        if p.suffix.lower() in (".png", ".jpg", ".jpeg")
        and p.stem >= FIRST_CONTENT_PAGE
    )


def transcript(model: str, page_stem: str) -> Path:
    return OUT_DIR / model / f"{page_stem}.txt"


def run_ocr(models: dict[str, int], pages: list[Path], log_dir: Path) -> None:
    """Run ocr_pages.py for each model in turn (used as a thread target)."""
    for model, budget in models.items():
        log_path = log_dir / f"{model}.log"
        with log_path.open("w") as log:
            subprocess.run(
                [PYTHON, str(OCR_DIR / "ocr_pages.py"),
                 "--model", model, "--out", str(OUT_DIR),
                 "--budget", str(budget),
                 *MODEL_EXTRA_ARGS.get(model, []), *map(str, pages)],
                stdout=log, stderr=subprocess.STDOUT, cwd=REPO_ROOT,
            )


def upload_batch(csv_path: Path) -> tuple[bool, str]:
    """Dry-run then (if clean) live-upload one batch CSV. Returns
    (uploaded, summary)."""
    sys.path.insert(0, str(OCR_DIR))
    from ocr_pages import load_env_file  # reuse the .env loader
    load_env_file(REPO_ROOT / "alarino_backend" / ".env")
    import alarino_backend.app as app_module
    import alarino_backend.translation_service as ts
    from alarino_backend import db

    text = csv_path.read_text()
    app = app_module.create_app()
    with app.app_context():
        dry, status = ts.bulk_upload_words(db, text, dry_run=True)
        rejected = dry["data"]["failed_pairs"] if status == 200 else None
        if status != 200 or rejected:
            return False, (f"dry-run FAILED (status={status}, "
                           f"rejected={len(rejected or [])}) — batch held for review")
        live, status = ts.bulk_upload_words(db, text, dry_run=False)
        if status != 200 or live["data"]["failed_pairs"]:
            return False, f"live upload FAILED (status={status}) — investigate"
        return True, f"uploaded {len(live['data']['successful_pairs'])} pairs"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-upload", action="store_true",
                    help="run OCR and comparison, but skip harvesting/uploading")
    ap.add_argument("--min-models", type=int, default=3,
                    help="transcripts required before a page is harvested "
                         "(default 3; drop to 2 for the endgame)")
    args = ap.parse_args()

    today = datetime.date.today().isoformat()
    log_dir = OUT_DIR / "logs" / today
    log_dir.mkdir(parents=True, exist_ok=True)
    pages = content_pages()
    print(f"=== daily batch {today}: {len(pages)} content pages ===")

    # Phase 1: OCR under budgets, one worker thread per THREADS entry.
    threads = [
        threading.Thread(target=run_ocr, args=(models, pages, log_dir))
        for models in THREADS
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Phase 1.5: an empty transcript alongside a substantive one from
    # another model is a failed OCR (models occasionally return nothing for
    # a dense page), not a blank scan — delete it so a later run retries.
    reconciled = 0
    for page in pages:
        existing = {
            m: transcript(m, page.stem)
            for m in ALL_MODELS if transcript(m, page.stem).exists()
        }
        sizes = {m: t.stat().st_size for m, t in existing.items()}
        if sizes and max(sizes.values()) > 200:
            for m, size in sizes.items():
                if size == 0:
                    existing[m].unlink()
                    reconciled += 1
    if reconciled:
        print(f"reconciled {reconciled} empty transcript(s) for retry")

    coverage = {}
    for model in ALL_MODELS:
        done = sum(1 for p in pages if transcript(model, p.stem).exists())
        coverage[model] = done
        print(f"coverage {model}: {done}/{len(pages)}")

    # Phase 2: rebuild comparisons across the current panel.
    subprocess.run(
        [PYTHON, str(OCR_DIR / "compare_runs.py"), "--out", str(OUT_DIR),
         "--models", *ALL_MODELS],
        cwd=REPO_ROOT, capture_output=True,
    )

    if args.no_upload:
        print("(--no-upload: stopping after comparison)")
        return

    # Phase 3: harvest fully transcribed, never-uploaded pages.
    ledger = json.loads(LEDGER.read_text()) if LEDGER.exists() else []
    ready = [
        p.stem for p in pages
        if p.stem not in ledger
        and all(transcript(m, p.stem).exists() for m in REQUIRED_MODELS)
        and sum(1 for m in ALL_MODELS if transcript(m, p.stem).exists()) >= args.min_models
        and (OUT_DIR / "comparison" / f"{p.stem}.json").exists()
    ]
    if not ready:
        print("no new fully-transcribed pages to harvest")
        return

    batch_csv = OUT_DIR / "batches" / f"{today}.csv"
    batch_csv.parent.mkdir(parents=True, exist_ok=True)
    build = subprocess.run(
        [PYTHON, str(OCR_DIR / "build_dataset.py"), "--out", str(OUT_DIR),
         "--csv", str(batch_csv), "--pages", *ready],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    print(build.stdout.strip())
    if build.returncode != 0:
        print(f"build_dataset failed: {build.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    n_pairs = max(0, len(batch_csv.read_text().splitlines()) - 1)
    if n_pairs == 0:
        print(f"harvested {len(ready)} pages but no unanimous pairs; marking done")
        LEDGER.write_text(json.dumps(sorted(ledger + ready), indent=1))
        return

    # Phase 4: gated upload.
    uploaded, summary = upload_batch(batch_csv)
    print(f"upload: {summary}")
    if uploaded:
        LEDGER.write_text(json.dumps(sorted(ledger + ready), indent=1))
        print(f"ledger: {len(ledger) + len(ready)} pages uploaded total")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
