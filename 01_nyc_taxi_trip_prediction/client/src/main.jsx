import React from "react";
import { createRoot } from "react-dom/client";
import { CssBaseline, ThemeProvider } from "@mui/material";
import App from "./App";
import { taxiTheme } from "./theme";
import "./styles.css";

createRoot(document.querySelector("#app")).render(
  <React.StrictMode>
    <ThemeProvider theme={taxiTheme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>,
);
