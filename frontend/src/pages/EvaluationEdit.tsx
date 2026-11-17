import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import {
  fetchEvaluation,
  getErrorMessage,
  updateEvaluation,
  type Evaluation,
  type EvaluationAssertion,
} from "../lib/api";

export function EvaluationEdit() {
  const { evaluationId } = useParams<{ evaluationId: string }>();
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [assertionsJson, setAssertionsJson] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const loadEvaluation = useCallback(async () => {
    if (!evaluationId) {
      setErrorMessage("Missing evaluation id.");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetchEvaluation(evaluationId);
      setEvaluation(response);
      setName(response.name);
      setDescription(response.description);
      setAssertionsJson(JSON.stringify(response.assertions, null, 2));
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, [evaluationId]);

  useEffect(() => {
    void loadEvaluation();
  }, [loadEvaluation]);

  const parsedAssertions = useMemo(() => {
    try {
      const parsed = JSON.parse(assertionsJson) as EvaluationAssertion[];
      return Array.isArray(parsed) ? parsed : null;
    } catch {
      return null;
    }
  }, [assertionsJson]);

  async function handleSave() {
    if (!evaluation || !parsedAssertions) {
      setErrorMessage("Assertions must be a valid JSON array.");
      return;
    }

    setIsSaving(true);
    setErrorMessage(null);
    setSaveMessage(null);
    try {
      const updated = await updateEvaluation(evaluation.evaluationId, {
        name,
        description,
        assertions: parsedAssertions,
      });
      setEvaluation(updated);
      setSaveMessage("Evaluation saved.");
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return <LoadingState label="Loading evaluation editor" />;
  }

  if (errorMessage && !evaluation) {
    return (
      <ErrorState
        title="Unable to load evaluation"
        message={errorMessage}
        onRetry={loadEvaluation}
      />
    );
  }

  if (!evaluation) {
    return null;
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
        <div>
          <Link
            to={`/evaluations/${evaluation.evaluationId}`}
            className="text-sm font-medium text-teal-700 hover:text-teal-800 dark:text-teal-300 dark:hover:text-teal-200"
          >
            Back to evaluation
          </Link>
          <h1 className="mt-3 text-3xl font-semibold tracking-normal">
            Edit regression test
          </h1>
        </div>
        <button
          type="button"
          onClick={handleSave}
          disabled={isSaving || parsedAssertions === null}
          className="inline-flex w-fit rounded-md bg-slate-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
        >
          {isSaving ? "Saving..." : "Save"}
        </button>
      </section>

      {errorMessage ? <ErrorState message={errorMessage} /> : null}
      {saveMessage ? (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
          {saveMessage}
        </div>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <div className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p className="mb-3 text-xs text-slate-500">Efficiency assertions: max_tokens, max_input_tokens, max_output_tokens, max_llm_calls, max_estimated_cost, and max_latency_ms. Missing measured data fails the assertion.</p>
          <label className="block text-sm font-medium">
            Name
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-2 block w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-teal-600 dark:border-slate-800 dark:bg-slate-950"
            />
          </label>
          <label className="mt-5 block text-sm font-medium">
            Description
            <textarea
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={5}
              className="mt-2 block w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-teal-600 dark:border-slate-800 dark:bg-slate-950"
            />
          </label>
        </div>

        <div className="rounded-md border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p className="mb-3 text-xs leading-5 text-slate-500 dark:text-slate-400">Efficiency assertion types: max_tokens, max_input_tokens, max_output_tokens, max_llm_calls, max_estimated_cost, and max_latency_ms. Missing usage or cost data fails the corresponding assertion.</p>
          <label className="block text-sm font-medium">
            Assertions JSON
            <textarea
              value={assertionsJson}
              onChange={(event) => setAssertionsJson(event.target.value)}
              rows={20}
              spellCheck={false}
              className="mt-2 block w-full rounded-md border border-slate-200 bg-white px-3 py-2 font-mono text-xs outline-none focus:border-teal-600 dark:border-slate-800 dark:bg-slate-950"
            />
          </label>
        </div>
      </section>
    </div>
  );
}
