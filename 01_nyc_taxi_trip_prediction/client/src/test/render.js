import { ThemeProvider } from "@mui/material";
import { render } from "@testing-library/react";
import { createElement } from "react";
import { taxiTheme } from "../theme";

export function renderWithTheme(ui) {
  return render(createElement(ThemeProvider, { theme: taxiTheme }, ui));
}
