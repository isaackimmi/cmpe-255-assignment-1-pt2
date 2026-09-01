import React from "react";
import ReactDOM from "react-dom/client";
import { Theme } from "@radix-ui/themes";
import "@radix-ui/themes/styles.css";
import "./styles/tokens.css";
import "./styles/layout.css";
import "./styles/components.css";
import { App } from "./App";
import { AppErrorBoundary } from "./components/layout/AppErrorBoundary";

ReactDOM.createRoot(document.getElementById("app")).render(
  <React.StrictMode>
    <Theme appearance="dark" accentColor="lime" grayColor="slate" radius="medium">
      <AppErrorBoundary><App /></AppErrorBoundary>
    </Theme>
  </React.StrictMode>,
);
