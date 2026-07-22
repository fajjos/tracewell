export function App() {
  return (
    <main className="min-h-screen bg-surface text-ink">
      <section className="mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-16">
        <p className="mb-3 text-sm font-medium uppercase tracking-wide text-accent">
          Tracewell MVP
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-normal sm:text-5xl">
          AI agent observability for developers.
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
          This frontend is scaffolded for the first Tracewell dashboard. Product
          views and API integrations will be added after the backend contracts
          are defined.
        </p>
      </section>
    </main>
  );
}
