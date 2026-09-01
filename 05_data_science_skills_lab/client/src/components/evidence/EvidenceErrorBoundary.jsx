import { Component } from "react";
import Alert from "@mui/material/Alert";

export class EvidenceErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidUpdate(previousProps) {
    if (previousProps.resetKey !== this.props.resetKey && this.state.error) this.setState({ error: null });
  }

  render() {
    if (this.state.error) return <Alert severity="error">This evidence view could not render: {this.state.error.message}</Alert>;
    return this.props.children;
  }
}
