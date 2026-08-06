# Offline data creation

Tooling for growing the Alarino dictionary outside the app: OCR of public-domain
scanned dictionaries, cleanup passes, and preparation of bulk-upload files.
Nothing in here runs in production or is imported by the backend.

## Layout

```
offline/
  ocr/
    ocr_pages.py     # OCR page scans with a selectable vision model
  scans/             # input page images (gitignored)
  out/               # OCR output, one subfolder per model (gitignored)
```

## OCR quickstart

Put page images (`.png`/`.jpg`) in `offline/scans/`, put API keys in
`offline/.env` (copy `offline/.env.example`; the file is gitignored), then:

```bash
python offline/ocr/ocr_pages.py --model gemini-2.5-flash offline/scans --out offline/out
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

The OCR prompt's alphabet and the output normalization both come from
`alarino_backend.normalization` (the same module the app's storage layer
uses), so offline output is always in the exact NFC form the backend expects.

## Sources

- CMS *Dictionary of the Yoruba Language* (1913), archive.org — public domain.
- Crowther, *Vocabulary of the Yoruba Language* (1843), archive.org — public domain.

Convert PDFs to page images with e.g. `pdftoppm -png -r 300 book.pdf scans/page`.
