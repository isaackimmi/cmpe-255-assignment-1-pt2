import { createTheme } from "@mui/material/styles";

export const atlasTheme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#2b817d" },
    secondary: { main: "#e87854" },
    background: { default: "#f6f5f0", paper: "#ffffff" },
    text: { primary: "#152536", secondary: "#697879" },
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: 'Manrope, Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    button: { textTransform: "none", fontWeight: 700 },
  },
  components: {
    MuiButton: { defaultProps: { disableElevation: true } },
    MuiCard: { styleOverrides: { root: { border: "1px solid #d9e0db", boxShadow: "0 12px 28px #1c393b08" } } },
  },
});
