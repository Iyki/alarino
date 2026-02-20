"use client";

import { FormEvent, useState } from "react";

import { bulkUploadWords } from "@/lib/api";
import type { BulkUploadResult } from "@/lib/types";

const EMPTY_RESULT: BulkUploadResult = {
  successful_pairs: [],
  failed_pairs: [],
  dry_run: true
};

export function AdminPage() {
  const [apiKey, setApiKey] = useState("");
  const [textInput, setTextInput] = useState("");
  const [dryRun, setDryRun] = useState(true);
  const [result, setResult] = useState<BulkUploadResult>(EMPTY_RESULT);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    setHasSubmitted(true);
    setLoading(true);
    setErrorMessage(null);

    const response = await bulkUploadWords(textInput, dryRun, apiKey);

    if (response.success && response.data) {
      setResult(response.data);
      setLoading(false);
      return;
    }

    const pairCount = textInput.split("\n").filter((line) => line.trim()).length;
    setResult({
      successful_pairs: [],
      failed_pairs: [
        {
          line: "bulk-upload",
          reason: response.message || "Bulk upload failed"
        }
      ],
      dry_run: dryRun
    });

    setErrorMessage(response.message || "Bulk upload failed.");

    if (pairCount > 0) {
      setResult((current) => ({
        ...current,
        failed_pairs: current.failed_pairs.length
          ? current.failed_pairs
          : [{ line: "bulk-upload", reason: response.message || "Bulk upload failed" }]
      }));
    }

    setLoading(false);
  };

  const totalCount = result.successful_pairs.length + result.failed_pairs.length;

  return (
    <main className="mx-auto w-full max-w-4xl px-4 pb-16 pt-10 sm:px-6 lg:px-8">
      <section className="text-center">
        <p className="font-heading text-sm uppercase tracking-[0.2em] text-brand-cream/85">Operations</p>
        <h1 className="mt-3 font-heading text-4xl text-white sm:text-5xl">Admin Bulk Upload</h1>
      </section>

      <section className="mt-10 rounded-3xl bg-brand-beige p-5 shadow-card sm:p-7">
        <form className="space-y-4" onSubmit={onSubmit}>
          <div>
            <label htmlFor="apiKey" className="block text-sm font-semibold text-brand-ink">
              API Key
            </label>
            <input
              id="apiKey"
              name="apiKey"
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="Enter your API key"
              className="mt-1 w-full rounded-xl border border-brand-brown/20 bg-white px-4 py-3 text-brand-ink"
            />
          </div>

          <div>
            <label htmlFor="wordPairs" className="block text-sm font-semibold text-brand-ink">
              Comma-separated word pairs (english,yoruba)
            </label>
            <textarea
              id="wordPairs"
              name="wordPairs"
              rows={10}
              value={textInput}
              onChange={(event) => setTextInput(event.target.value)}
              placeholder={"hello,bawo\nworld,agbaye"}
              className="mt-1 w-full rounded-xl border border-brand-brown/20 bg-white px-4 py-3 text-brand-ink"
            />
          </div>

          <label className="inline-flex items-center gap-2 text-sm font-medium text-brand-ink">
            <input
              type="checkbox"
              checked={dryRun}
              onChange={(event) => setDryRun(event.target.checked)}
              className="h-4 w-4 rounded border-brand-brown/40"
            />
            Dry Run
          </label>

          <button
            type="submit"
            disabled={loading}
            className="block rounded-xl bg-brand-forest px-5 py-3 text-sm font-semibold text-white transition hover:brightness-110 disabled:opacity-60"
          >
            {loading ? "Submitting..." : "Submit"}
          </button>
        </form>
      </section>

      {hasSubmitted ? (
        <section className="mt-10 rounded-3xl bg-brand-beige p-5 shadow-card sm:p-7">
          <h2 className="font-heading text-2xl text-brand-ink">Summary</h2>
          <div className="mt-2 grid gap-1 text-sm text-brand-ink/80">
            <p>Total pairs: {totalCount}</p>
            <p>Successful: {result.successful_pairs.length}</p>
            <p>Failed: {result.failed_pairs.length}</p>
            <p>Run mode: {result.dry_run ? "Dry run" : "Live"}</p>
          </div>

          {errorMessage ? <p className="mt-3 text-sm text-red-700">{errorMessage}</p> : null}

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="text-lg font-semibold text-brand-ink">Successful uploads</h3>
              <ul className="mt-2 min-h-24 list-disc rounded-xl bg-white p-4 pl-9 text-sm text-brand-ink">
                {result.successful_pairs.length ? (
                  result.successful_pairs.map((item) => (
                    <li key={`${item.english}-${item.yoruba}`}>{item.english}, {item.yoruba}</li>
                  ))
                ) : (
                  <li className="list-none pl-0 text-brand-ink/60">No successful uploads.</li>
                )}
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-brand-ink">Failed uploads</h3>
              <ul className="mt-2 min-h-24 list-disc rounded-xl bg-white p-4 pl-9 text-sm text-brand-ink">
                {result.failed_pairs.length ? (
                  result.failed_pairs.map((item) => (
                    <li key={`${item.line}-${item.reason}`}>{item.line} - Reason: {item.reason}</li>
                  ))
                ) : (
                  <li className="list-none pl-0 text-brand-ink/60">No failed uploads.</li>
                )}
              </ul>
            </div>
          </div>
        </section>
      ) : null}
    </main>
  );
}
