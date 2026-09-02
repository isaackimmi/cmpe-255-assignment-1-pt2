import { Alert, Box, Button, CircularProgress } from "@mui/material";

export function LoadingState({ label = "Loading evidence…" }) {
  return (
    <Box className="loading" role="status">
      <CircularProgress size={20} /> <span>{label}</span>
    </Box>
  );
}

export function ErrorState({ error, message, onRetry, retryLabel = "Retry" }) {
  return (
    <Alert
      severity="error"
      className="error-box"
      action={
        onRetry && (
          <Button color="inherit" onClick={onRetry}>
            {retryLabel}
          </Button>
        )
      }
    >
      {message || error?.message || "The request failed."}
    </Alert>
  );
}
