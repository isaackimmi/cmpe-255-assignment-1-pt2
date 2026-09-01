import { createTheme } from "@mui/material/styles";

export const taxiTheme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#111a2e" },
    secondary: { main: "#e2765b" },
    background: { default: "#f5f3ed", paper: "#fbfaf6" },
    success: { main: "#467563" },
  },
  typography: {
    fontFamily: "Manrope, Inter, system-ui, sans-serif",
    button: { textTransform: "none", fontWeight: 800 },
  },
  shape: { borderRadius: 2 },
  components: {
    MuiButton: { defaultProps: { disableElevation: true } },
    MuiTextField: { defaultProps: { size: "small", variant: "outlined" } },
  },
});
