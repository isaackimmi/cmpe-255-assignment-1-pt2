import { createTheme } from "@mui/material/styles";

export const labTheme = createTheme({
  palette: {
    mode: "dark",
    background: { default: "#07111f", paper: "#101d2d" },
    primary: { main: "#c9f36b", contrastText: "#07111f" },
    secondary: { main: "#61d4c5" },
    error: { main: "#f07d66" },
    text: { primary: "#edf2f2", secondary: "#8e9aa2" },
  },
  typography: {
    fontFamily: "Manrope, system-ui, sans-serif",
    button: { textTransform: "none", fontWeight: 600 },
  },
  shape: { borderRadius: 6 },
  components: {
    MuiButton: { styleOverrides: { root: { justifyContent: "flex-start" } } },
    MuiOutlinedInput: { styleOverrides: { notchedOutline: { borderColor: "#263747" } } },
  },
});
