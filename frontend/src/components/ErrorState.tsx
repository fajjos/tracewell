type ErrorStateProps = {
  title?: string;
  message: string;
  onRetry?: () => void;
};

export function ErrorState({
  title = "Unable to load data",
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="rounded-md border border-rose-200 bg-rose-50 px-6 py-5 dark:border-rose-900 dark:bg-rose-950">
      <h2 className="text-base font-semibold text-rose-900 dark:text-rose-100">
        {title}
      </h2>
      <p className="mt-2 text-sm leading-6 text-rose-700 dark:text-rose-300">
        {message}
      </p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-md bg-rose-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-rose-800 dark:bg-rose-100 dark:text-rose-950 dark:hover:bg-rose-200"
        >
          Retry
        </button>
      ) : null}
    </div>
  );
}
