import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { StatusBadge } from "../components/StatusBadge";
import { TraceFlowViewer } from "../components/TraceFlowViewer";
import { fetchTrace, getErrorMessage, type Trace } from "../lib/api";
import {
  formatCurrency,
  formatDateTime,
  formatLatency,
  formatNumber,
} from "../utils/format";

export function TraceDetails() {
  const { traceId } = useParams<{ traceId: string }>();
  const [trace, setTrace] = useState<Trace | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadTrace = useCallback(async () => {
    if (!traceId) {
      setErrorMessage("Missing trace id.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      setTrace(await fetchTrace(traceId));
    } catch (error) {
      setTrace(null);
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, [traceId]);

  useEffect(() => {
    void loadTrace();
  }, [loadTrace]);

  if (isLoading) {
    return <LoadingState label="Loading trace details" />;
  }

  if (errorMessage || !trace) {
    return (
      <div className="space-y-5">
        <ErrorState
          title="Unable to load trace"
          message={errorMessage ?? "The requested trace was not found."}
          onRetry={loadTrace}
        />
        <Link
          to="/traces"
          className="inline-flex rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white dark:bg-white dark:text-slate-950"
        >
          Back to traces
        </Link>
      </div>
    );
  }

  const metadata = [
    ["Project", trace.projectId],
    ["Session", trace.sessionId],
    ["Provider", trace.provider],
    ["Model", trace.model],
    ["Created", formatDateTime(trace.createdAt)],
  ];

  const metrics = [
    ["Latency", formatLatency(trace.latencyMs)],
    ["Input tokens", formatNumber(trace.inputTokens)],
    ["Output tokens", formatNumber(trace.outputTokens)],
    ["Total tokens", formatNumber(trace.totalTokens)],
    ["Cost", formatCurrency(trace.cost)],
  ];

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div className="min-w-0">
          <Link
            to="/traces"
            className="text-sm font-medium text-teal-700 hover:text-teal-800 dark:text-teal-300 dark:hover:text-teal-200"
          >
            Back to traces
          </Link>
          <h1 className="mt-3 truncate text-3xl font-semibold tracking-normal">
            {trace.traceId}
          </h1>
        </div>
        <StatusBadge status={trace.status} />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {metrics.map(([label, value]) => (
          <article
            key={label}
            className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="text-sm text-slate-500 dark:text-slate-400">{label}</div>
            <div className="mt-3 text-xl font-semibold tracking-normal">{value}</div>
          </article>
        ))}
      </section>

      <TraceFlowViewer trace={trace} />

      <section className="grid gap-6 xl:grid-cols-[1fr_1.4fr]">
        <div className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="text-base font-semibold">Metadata</h2>
          <dl className="mt-5 space-y-4">
            {metadata.map(([label, value]) => (
              <div key={label}>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  {label}
                </dt>
                <dd className="mt-1 break-words text-sm font-medium text-slate-900 dark:text-slate-100">
                  {value}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="space-y-6">
          <article className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-base font-semibold">Prompt</h2>
            <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700 dark:text-slate-300">
              {trace.prompt}
            </p>
          </article>

          <article className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
            <h2 className="text-base font-semibold">Response</h2>
            <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-slate-700 dark:text-slate-300">
              {trace.response || "No response captured."}
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}
