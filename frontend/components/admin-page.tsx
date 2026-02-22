"use client";

import { FormEvent, useState } from "react";

import { bulkUploadWords } from "@/lib/api";
import type { BulkUploadResult } from "@/lib/types";

const EMPTY_RESULT: BulkUploadResult = {
  successful_pairs: [],
  failed_pairs: [],
  dry_run: true
};

interface UploadSummaryProps {
  errorMessage: string | null;
  hasSubmitted: boolean;
  result: BulkUploadResult;
}

function UploadSummary({ errorMessage, hasSubmitted, result }: UploadSummaryProps) {
  if (!hasSubmitted) {
    return null;
  }

  const totalCount = result.successful_pairs.length + result.failed_pairs.length;

  return (
    <section className="mt-10 animate-fade-in-up rounded-3xl bg-brand-cream p-5 shadow-card sm:p-7">
      <h2 className="font-heading text-2xl font-semibold text-brand-ink">Summary</h2>
      <div className="mt-2 grid gap-1 text-sm text-brand-ink/80">
        <p>Total pairs: {totalCount}</p>
        <p>Successful: {result.successful_pairs.length}</p>
        <p>Failed: {result.failed_pairs.length}</p>
        <p>Run mode: {result.dry_run ? "Dry run" : "Live"}</p>
      </div>

      {errorMessage ? <p className="mt-3 text-sm text-red-700">{errorMessage}</p> : null}

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div>
          <h3 className="font-heading text-lg font-semibold text-brand-ink">Successful uploads</h3>
          <ul className="mt-2 min-h-24 list-disc rounded-xl bg-white p-4 pl-9 text-sm text-brand-ink shadow-sm">
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
          <h3 className="font-heading text-lg font-semibold text-brand-ink">Failed uploads</h3>
          <ul className="mt-2 min-h-24 list-disc rounded-xl bg-white p-4 pl-9 text-sm text-brand-ink shadow-sm">
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
  );
}

function buildFailureResult(reason: string, dryRun: boolean): BulkUploadResult {
  return {
    successful_pairs: [],
    failed_pairs: [
      {
        line: "bulk-upload",
        reason
      }
    ],
    dry_run: dryRun
  };
}

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

    const failureReason = response.message || "Bulk upload failed";
    setResult(buildFailureResult(failureReason, dryRun));
    setErrorMessage(failureReason);

    setLoading(false);
  };

  return (
    <main className="mx-auto w-full max-w-4xl px-4 pb-20 pt-12 sm:px-6 lg:px-8">
      <section className="animate-fade-in-up text-center">
        <p className="text-sm font-medium uppercase tracking-[0.25em] text-brand-gold">Operations</p>
        <h1 className="mt-3 font-heading text-4xl font-bold text-white sm:text-5xl">Admin Bulk Upload</h1>
      </section>

      <section className="mt-10 animate-fade-in-up-delay-1 rounded-3xl bg-brand-cream p-5 shadow-card sm:p-7">
        <form className="space-y-5" onSubmit={onSubmit}>
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
              className="mt-1 w-full rounded-xl border border-brand-brown/15 bg-white px-4 py-3 text-brand-ink shadow-sm transition-shadow focus-visible:outline-none focus-visible:shadow-md focus-visible:ring-2 focus-visible:ring-brand-forest"
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
              className="mt-1 w-full rounded-xl border border-brand-brown/15 bg-white px-4 py-3 text-brand-ink shadow-sm transition-shadow focus-visible:outline-none focus-visible:shadow-md focus-visible:ring-2 focus-visible:ring-brand-forest"
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
            className="block rounded-xl bg-brand-forest px-6 py-3 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:bg-brand-forest/90 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:translate-y-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-gold focus-visible:ring-offset-2"
          >
            {loading ? "Submitting..." : "Submit"}
          </button>
        </form>
      </section>

      <UploadSummary errorMessage={errorMessage} hasSubmitted={hasSubmitted} result={result} />
    </main>
  );
}
