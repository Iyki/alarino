#!/usr/bin/env python3
"""OCR scanned dictionary pages with a selectable vision model.

Stdlib only — no dependencies beyond Python 3.10+.

Usage:
    python offline/ocr/ocr_pages.py --model gemini-2.5-flash offline/scans --out offline/out

API keys are read from the environment: GEMINI_API_KEY for gemini models,
OPENROUTER_API_KEY for openrouter models. See --list-models.
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The Yorùbá alphabet and normalization MUST match the backend exactly, so both
# come from alarino_backend.normalization (stdlib-only module, no Flask/DB).
# The sys.path fallback covers running outside the conda env where the backend
# package is installed editable.
try:
    from alarino_backend import normalization
except ModuleNotFoundError:
    sys.path.insert(0, str(REPO_ROOT / "alarino_backend" / "src"))
    from alarino_backend import normalization

# Friendly alias -> (provider, provider model id). Anything not listed can be
# used with an explicit "provider:model_id" --model value.
MODELS = {
    "gemini-2.5-flash": ("gemini", "gemini-2.5-flash"),
    "gemini-2.5-flash-lite": ("gemini", "gemini-2.5-flash-lite"),
    "gemma-4-31b": ("openrouter", "google/gemma-4-31b-it:free"),
    "gemma-4-26b-a4b": ("openrouter", "google/gemma-4-26b-a4b-it:free"),
    "nemotron-12b-vl": ("openrouter", "nvidia/nemotron-nano-12b-v2-vl:free"),
    "nemotron-30b-omni": ("openrouter", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"),
    # Paid but cheap (~$1-2 per full book pass); the strongest open VLs.
    "qwen3-vl-235b": ("openrouter", "qwen/qwen3-vl-235b-a22b-instruct"),
    "qwen3-vl-32b": ("openrouter", "qwen/qwen3-vl-32b-instruct"),
}

KEY_ENV = {"gemini": "GEMINI_API_KEY", "openrouter": "OPENROUTER_API_KEY"}

def _spaced_graphemes(chars: str) -> str:
    """Render a character-set string as space-separated, deduplicated
    graphemes, keeping combining marks attached to their base (e.g. 'ẹ́'
    stays one unit). Dedup matters for YORUBA_CONSONANTS, which repeats
    g and b to spell the 'gb' digraph."""
    clusters: list[str] = []
    for ch in unicodedata.normalize("NFC", chars):
        if unicodedata.combining(ch) and clusters:
            clusters[-1] += ch
        else:
            clusters.append(ch)
    return " ".join(dict.fromkeys(clusters))


# The alphabet lines are generated from the backend's canonical character sets
# so the prompt can never drift from what the app accepts and stores.
DEFAULT_PROMPT = unicodedata.normalize("NFC", f"""\
You are transcribing a page from a scanned Yorùbá–English dictionary.

Transcribe ALL text on the page exactly as printed, top to bottom, one
dictionary entry per line. Preserve the original entry structure
(headword, part of speech, definition) with its original punctuation.

Critical requirements:
- The Yorùbá alphabet in this dictionary uses exactly these letters
  (plus their capitals):
  vowels: {_spaced_graphemes(normalization.YORUBA_VOWELS)}
  syllabic nasals: {_spaced_graphemes(normalization.YORUBA_NASAL_VOWELS)}
  consonants: {_spaced_graphemes(normalization.YORUBA_CONSONANTS)} (and the digraph gb)
- Reproduce every tone mark and every subdot (ẹ ọ ṣ) exactly as printed.
  Never silently drop a tone mark or subdot, and never substitute a
  plain letter for a subdotted one.
- Output plain text only: no markdown, no commentary, no page numbers or
  running headers.
- If a character is illegible, transcribe it as ⟨?⟩ rather than guessing.
""")

RETRY_STATUSES = {429, 500, 502, 503}
MAX_RETRIES = 5
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass
class OcrResult:
    text: str
    usage: dict
    elapsed_s: float


def http_post_json(url: str, payload: dict, headers: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    for attempt in range(MAX_RETRIES + 1):
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json", **headers}
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            if e.code in RETRY_STATUSES and attempt < MAX_RETRIES:
                wait = min(2**attempt * 5, 120)
                print(f"    HTTP {e.code}, retrying in {wait}s: {detail}", file=sys.stderr)
                time.sleep(wait)
                continue
            raise RuntimeError(f"HTTP {e.code} from {url}: {detail}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < MAX_RETRIES:
                wait = min(2**attempt * 5, 120)
                print(f"    network error, retrying in {wait}s: {e}", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("unreachable")


def encode_image(path: Path) -> tuple[str, str]:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    return mime, base64.b64encode(path.read_bytes()).decode("ascii")


def ocr_gemini(model_id: str, api_key: str, prompt: str, image: Path) -> OcrResult:
    mime, data = encode_image(image)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime, "data": data}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0},
    }
    start = time.monotonic()
    resp = http_post_json(url, payload, {"x-goog-api-key": api_key})
    elapsed = time.monotonic() - start
    try:
        text = resp["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"unexpected Gemini response: {json.dumps(resp)[:500]}") from e
    return OcrResult(text, resp.get("usageMetadata", {}), elapsed)


def ocr_openrouter(model_id: str, api_key: str, prompt: str, image: Path) -> OcrResult:
    mime, data = encode_image(image)
    payload = {
        "model": model_id,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}},
                ],
            }
        ],
    }
    start = time.monotonic()
    resp = http_post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        payload,
        {"Authorization": f"Bearer {api_key}"},
    )
    elapsed = time.monotonic() - start
    if "error" in resp:
        raise RuntimeError(f"OpenRouter error: {json.dumps(resp['error'])[:500]}")
    try:
        text = resp["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"unexpected OpenRouter response: {json.dumps(resp)[:500]}") from e
    return OcrResult(text, resp.get("usage", {}), elapsed)


PROVIDERS = {"gemini": ocr_gemini, "openrouter": ocr_openrouter}


def resolve_model(spec: str) -> tuple[str, str, str]:
    """Return (alias, provider, model_id) for an alias or 'provider:model_id' spec."""
    if spec in MODELS:
        provider, model_id = MODELS[spec]
        return spec, provider, model_id
    provider, sep, model_id = spec.partition(":")
    if sep and provider in PROVIDERS and model_id:
        alias = model_id.replace("/", "_").replace(":", "_")
        return alias, provider, model_id
    known = ", ".join(MODELS)
    sys.exit(f"error: unknown model '{spec}'. Known aliases: {known}; "
             f"or use 'gemini:<id>' / 'openrouter:<id>'.")


def load_env_file(path: Path) -> None:
    """Load KEY=VALUE lines from a .env file into os.environ. Real environment
    variables take precedence; lines starting with # are ignored."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def collect_images(inputs: list[Path]) -> list[Path]:
    images = []
    for p in inputs:
        if p.is_dir():
            images.extend(sorted(f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXTS))
        elif p.is_file():
            images.append(p)
        else:
            sys.exit(f"error: no such file or directory: {p}")
    return images


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("inputs", nargs="*", type=Path, help="image files or directories of scans")
    ap.add_argument("--model", default="gemini-2.5-flash",
                    help="model alias or 'provider:model_id' (see --list-models)")
    ap.add_argument("--out", type=Path, default=Path("offline/out"),
                    help="output root; results go to <out>/<model-alias>/")
    ap.add_argument("--limit", type=int, help="only process the first N images")
    ap.add_argument("--force", action="store_true", help="re-OCR pages with existing output")
    ap.add_argument("--prompt-file", type=Path, help="file with a custom OCR prompt")
    ap.add_argument("--list-models", action="store_true", help="list model aliases and exit")
    args = ap.parse_args()

    if args.list_models:
        for alias, (provider, model_id) in MODELS.items():
            print(f"{alias:24} {provider:11} {model_id:34} (needs {KEY_ENV[provider]})")
        return

    if not args.inputs:
        ap.error("no input images given")

    alias, provider, model_id = resolve_model(args.model)
    load_env_file(REPO_ROOT / "offline" / ".env")
    api_key = os.environ.get(KEY_ENV[provider])
    if not api_key:
        sys.exit(f"error: {KEY_ENV[provider]} is not set (required for {provider} models)")

    prompt = args.prompt_file.read_text() if args.prompt_file else DEFAULT_PROMPT
    images = collect_images(args.inputs)
    if args.limit:
        images = images[: args.limit]
    if not images:
        sys.exit("error: no images found")

    out_dir = args.out / alias
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "manifest.jsonl"
    ocr = PROVIDERS[provider]

    print(f"OCR {len(images)} page(s) with {model_id} ({provider}) -> {out_dir}")
    failures = 0
    for i, image in enumerate(images, 1):
        dest = out_dir / f"{image.stem}.txt"
        if dest.exists() and not args.force:
            print(f"[{i}/{len(images)}] {image.name}: exists, skipping")
            continue
        print(f"[{i}/{len(images)}] {image.name} ...", flush=True)
        try:
            result = ocr(model_id, api_key, prompt, image)
        except Exception as e:
            failures += 1
            print(f"    FAILED: {e}", file=sys.stderr)
            continue
        # Same canonicalization the backend applies at storage time.
        text = normalization.normalize_text(result.text)
        dest.write_text(text, encoding="utf-8")
        with manifest.open("a", encoding="utf-8") as mf:
            mf.write(json.dumps({
                "page": image.name,
                "model": model_id,
                "provider": provider,
                "chars": len(text),
                "elapsed_s": round(result.elapsed_s, 2),
                "usage": result.usage,
            }, ensure_ascii=False) + "\n")
        print(f"    ok: {len(text)} chars in {result.elapsed_s:.1f}s")

    if failures:
        sys.exit(f"done with {failures} failure(s)")
    print("done")


if __name__ == "__main__":
    main()
