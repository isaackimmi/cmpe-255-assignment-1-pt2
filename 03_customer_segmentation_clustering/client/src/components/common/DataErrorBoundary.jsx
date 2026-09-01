import React from "react";
import { Alert, Button } from "@mui/material";

export class DataErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) { return { error }; }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => this.setState({ error: null })}>Retry view</Button>}>
        This evidence section could not be rendered: {this.state.error.message}
      </Alert>
    );
  }
}
