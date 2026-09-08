# Offline data creation

Tooling for growing the Alarino dictionary outside the app: OCR of public-domain
scanned dictionaries, cleanup passes, and preparation of bulk-upload files.
Nothing in here runs in production or is imported by the backend.

## Layout

```
offline/
  ocr/
    ocr_pages.py     # OCR page scans with a selectable vision model
    compare_runs.py  # cross-model diff: unanimous / diacritic / divergent
  scans/             # input page images (gitignored)
  out/               # OCR output, one subfolder per model (gitignored)
```

## OCR quickstart

Put page images (`.png`/`.jpg`) in `offline/scans/`, put API keys in
`offline/.env` (copy `offline/.env.example`; the file is gitignored), then:

```bash
python offline/ocr/ocr_pages.py --model gemini-3.6-flash offline/scans --out offline/out
```

Useful flags:

- `--list-models` — show the model aliases and which API key each needs.
- `--model openrouter:google/gemma-4-12b-it:free` — use any provider model
  not in the alias table (`openrouter:<id>` or `gemini:<id>`).
- `--limit 10` — only process the first N images (for gold-set experiments).
- `--force` — re-OCR pages that already have output.
- `--prompt-file my_prompt.txt` — override the built-in Yorùbá OCR prompt.

Output goes to `out/<model-alias>/<page>.txt`, with a `manifest.jsonl` per
model recording timing and token usage, so results from different models can
be diffed page-by-page for the bake-off.

After OCRing the same pages with 2+ models, compare them:

```bash
python offline/ocr/compare_runs.py --out offline/out
```

This aligns entries across models by headword and buckets each entry as
unanimous, diacritic_dispute (same base letters, different tone marks or
subdots), divergent, or partial, writing per-page detail to
`out/comparison/<page>.json`. Models are treated as optional votes: pages
are compared across whichever model transcripts exist.

Then build an upload-ready dataset from the entries every model agreed on:

```bash
python offline/ocr/build_dataset.py --out offline/out
```

This writes `out/bulk_upload.csv` in the bulk-upload API's extended format
(`english,yoruba,pos,provenance,confidence` with a header row): POS parsed
from the printed markers, provenance naming the source book and page, and
confidence scaled by how many models agreed.

The OCR prompt's alphabet and the output normalization both come from
`alarino_backend.normalization` (the same module the app's storage layer
uses), so offline output is always in the exact NFC form the backend expects.

## Full-book runs

`daily_batch.py` drives the whole pipeline for the 458-page CMS 1913 scan
under daily rate-limit budgets — OCR (Gemini parallel to the OpenRouter
models), compare, harvest fully-transcribed pages, dry-run-gated upload,
uploaded-pages ledger. Run it once a day until coverage is complete:

```bash
python offline/ocr/daily_batch.py
```

Page images come from extracting the PDF's embedded scans at native
resolution (pymupdf), not re-rasterizing:
`doc.extract_image(...)` per page into `scans/pages/pgNNN.*`.

## Sources

- CMS *Dictionary of the Yoruba Language* (1913), archive.org — public domain.
- Crowther, *Vocabulary of the Yoruba Language* (1843), archive.org — public domain.

Convert PDFs to page images with e.g. `pdftoppm -png -r 300 book.pdf scans/page`.
