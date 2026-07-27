import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";

import { App } from "./App";
import { Dashboard } from "./pages/Dashboard";
import { TraceDetails } from "./pages/TraceDetails";
import { Traces } from "./pages/Traces";
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
    ],
  },
]);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
