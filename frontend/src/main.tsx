import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { App } from "./App";
import { Dashboard } from "./pages/Dashboard";
import { EvaluationDetails } from "./pages/EvaluationDetails";
import { EvaluationEdit } from "./pages/EvaluationEdit";
import { EvaluationRunDetails } from "./pages/EvaluationRunDetails";
import { Evaluations } from "./pages/Evaluations";
import { TraceDetails } from "./pages/TraceDetails";
import { Traces } from "./pages/Traces";
import { EfficiencyInsights } from "./pages/EfficiencyInsights";
import "@xyflow/react/dist/style.css";
import "./styles.css";

const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: "traces",
        element: <Traces />,
      },
      {
        path: "traces/:traceId",
        element: <TraceDetails />,
      },
      { path: "efficiency", element: <EfficiencyInsights /> },
      {
        path: "evaluations",
        element: <Evaluations />,
      },
      {
        path: "evaluations/:evaluationId",
        element: <EvaluationDetails />,
      },
      {
        path: "evaluations/:evaluationId/edit",
        element: <EvaluationEdit />,
      },
      {
        path: "evaluation-runs/:runId",
        element: <EvaluationRunDetails />,
      },
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
