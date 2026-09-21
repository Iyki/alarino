#!/usr/bin/env python3
"""Submit and retrieve Gemini Batch API OCR jobs for dictionary pages.

The Batch API runs at 50% of interactive pricing with its own quota pool
(no free-tier RPM/RPD dance) and a <=24h turnaround — the whole book in
one job for about a dollar. Requires billing on the API key's project.

Usage:
    python offline/ocr/batch_ocr.py submit            # pages missing a transcript
    python offline/ocr/batch_ocr.py status <batches/id>
    python offline/ocr/batch_ocr.py fetch  <batches/id>   # write transcripts

State: the submitted job name is appended to offline/out/batch_jobs.jsonl.
fetch writes transcripts to offline/out/<model>/<page>.txt exactly like
ocr_pages.py, so compare/harvest need no changes.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "offline" / "ocr"))
from ocr_pages import DEFAULT_PROMPT, load_env_file  # noqa: E402

try:
    from alarino_backend import normalization
except ModuleNotFoundError:
    sys.path.insert(0, str(REPO_ROOT / "alarino_backend" / "src"))
    from alarino_backend import normalization

MODEL = "gemini-3.8-flash"
BASE = "https://generativelanguage.googleapis.com"
PAGES_DIR = REPO_ROOT / "offline" / "scans" / "pages"
OUT_DIR = REPO_ROOT / "offline" / "out"
JOBS_LOG = OUT_DIR / "batch_jobs.jsonl"
FIRST_CONTENT_PAGE = "pg011"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def api_key() -> str:
    load_env_file(REPO_ROOT / "offline" / ".env")
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("error: GEMINI_API_KEY not set")
    return key


def call(method: str, url: str, data: bytes | None = None,
         headers: dict | None = None) -> tuple[dict, dict]:
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"x-goog-api-key": api_key(), **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            body = resp.read()
            return (json.loads(body) if body.strip() else {}), dict(resp.headers)
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} from {url}: {e.read().decode()[:600]}")


def missing_pages() -> list[Path]:
    return sorted(
        p for p in PAGES_DIR.iterdir()
        if p.suffix.lower() in MIME and p.stem >= FIRST_CONTENT_PAGE
        and not (OUT_DIR / MODEL / f"{p.stem}.txt").exists()
    )


def build_jsonl(pages: list[Path], dest: Path) -> None:
    with dest.open("w") as f:
        for page in pages:
            line = {
                "key": page.stem,
                "request": {
                    "contents": [{"parts": [
                        {"text": DEFAULT_PROMPT},
                        {"inline_data": {
                            "mime_type": MIME[page.suffix.lower()],
                            "data": base64.b64encode(page.read_bytes()).decode(),
                        }},
                    ]}],
                    "generation_config": {"temperature": 0, "maxOutputTokens": 8192},
                },
            }
            f.write(json.dumps(line) + "\n")


def upload_file(path: Path) -> str:
    """Resumable upload to the Files API; returns the file resource name."""
    size = path.stat().st_size
    _, headers = call(
        "POST", f"{BASE}/upload/v1beta/files",
        data=json.dumps({"file": {"display_name": path.name}}).encode(),
        headers={
            "Content-Type": "application/json",
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": "application/jsonl",
        },
    )
    lowered = {k.lower(): v for k, v in headers.items()}
    upload_url = lowered.get("x-goog-upload-url")
    if not upload_url:
        sys.exit("error: no resumable upload URL returned")
    resp, _ = call(
        "POST", upload_url, data=path.read_bytes(),
        headers={
            "X-Goog-Upload-Command": "upload, finalize",
            "X-Goog-Upload-Offset": "0",
        },
    )
    return resp["file"]["name"]


def submit(args) -> None:
    if args.pages:
        by_stem = {p.stem: p for p in PAGES_DIR.iterdir() if p.suffix.lower() in MIME}
        try:
            pages = [by_stem[s] for s in args.pages]
        except KeyError as e:
            sys.exit(f"error: no such page {e}")
    else:
        pages = missing_pages()
    if args.limit:
        pages = pages[: args.limit]
    if not pages:
        print("nothing to submit: every content page has a transcript")
        return
    jsonl = Path(os.environ.get("TMPDIR", "/tmp")) / "cms1913_batch.jsonl"
    print(f"building JSONL for {len(pages)} pages ...")
    build_jsonl(pages, jsonl)
    print(f"uploading {jsonl.stat().st_size / 1e6:.0f}MB ...")
    file_name = upload_file(jsonl)
    print("uploaded as", file_name)
    resp, _ = call(
        "POST", f"{BASE}/v1beta/models/{MODEL}:batchGenerateContent",
        data=json.dumps({"batch": {
            "display_name": f"cms1913-{len(pages)}pages",
            "input_config": {"file_name": file_name},
        }}).encode(),
        headers={"Content-Type": "application/json"},
    )
    job = resp.get("name")
    state = resp.get("metadata", {}).get("state")
    print(f"submitted: {job} ({state})")
    with JOBS_LOG.open("a") as f:
        f.write(json.dumps({"job": job, "pages": len(pages), "file": file_name}) + "\n")
    jsonl.unlink()


def status(args) -> None:
    resp, _ = call("GET", f"{BASE}/v1beta/{args.job}")
    meta = resp.get("metadata", {})
    print("state:", meta.get("state"))
    for k in ("batchStats", "outputInfo"):
        if k in meta:
            print(k + ":", json.dumps(meta[k]))
    if resp.get("error"):
        print("error:", json.dumps(resp["error"])[:400])


def fetch(args) -> None:
    resp, _ = call("GET", f"{BASE}/v1beta/{args.job}")
    meta = resp.get("metadata", {})
    state = meta.get("state")
    if state != "BATCH_STATE_SUCCEEDED":
        sys.exit(f"job not finished: {state}")
    dest_dir = Path(args.dest_dir) if args.dest_dir else OUT_DIR / MODEL
    dest_dir.mkdir(parents=True, exist_ok=True)
    written = skipped = failed = 0

    def handle(item: dict) -> None:
        nonlocal written, skipped, failed
        key = item.get("key") or item.get("metadata", {}).get("key")
        response = item.get("response", {})
        if not key:
            failed += 1
            return
        try:
            cand = response["candidates"][0]
            parts = cand.get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts)
            if not text and cand.get("finishReason") != "STOP":
                raise KeyError("empty non-STOP")
        except (KeyError, IndexError):
            failed += 1
            print(f"  {key}: no usable response", file=sys.stderr)
            return
        dest = dest_dir / f"{key}.txt"
        if dest.exists():
            skipped += 1
            return
        dest.write_text(normalization.normalize_text(text), encoding="utf-8")
        written += 1

    # Inline responses (small jobs) or a responses file (large jobs).
    inlined = resp.get("response", {}).get("inlinedResponses", {}).get("inlinedResponses")
    if inlined:
        for item in inlined:
            handle(item)
    else:
        responses_file = (resp.get("response", {}).get("responsesFile")
                          or meta.get("outputInfo", {}).get("responsesFile"))
        if not responses_file:
            sys.exit("no inlined responses and no responses file on job: "
                     + json.dumps(resp)[:400])
        raw, _hdrs = b"", None
        req = urllib.request.Request(f"{BASE}/download/v1beta/{responses_file}:download?alt=media",
                                     headers={"x-goog-api-key": api_key()})
        with urllib.request.urlopen(req, timeout=1800) as r:
            raw = r.read()
        for line in raw.decode("utf-8").splitlines():
            if line.strip():
                handle(json.loads(line))
    print(f"transcripts written: {written}, already existed: {skipped}, failed: {failed}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_submit = sub.add_parser("submit", help="submit pages missing a transcript")
    p_submit.add_argument("--limit", type=int, help="submit only the first N pages")
    p_submit.add_argument("--pages", nargs="+",
                          help="submit exactly these page stems (even if transcripts "
                               "exist) — e.g. for batch-vs-interactive quality checks")
    p_submit.set_defaults(func=submit)
    p_status = sub.add_parser("status", help="show job state")
    p_status.add_argument("job")
    p_status.set_defaults(func=status)
    p_fetch = sub.add_parser("fetch", help="download results into out/<model>/")
    p_fetch.add_argument("job")
    p_fetch.add_argument("--dest-dir",
                         help="write transcripts here instead of out/<model>/ "
                              "(e.g. out/gemini-3.8-flash-batch for quality checks)")
    p_fetch.set_defaults(func=fetch)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
