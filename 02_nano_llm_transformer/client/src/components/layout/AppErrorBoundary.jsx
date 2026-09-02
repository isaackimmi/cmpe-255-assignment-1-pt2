import React from "react";
import { Button, Callout } from "@radix-ui/themes";

export class AppErrorBoundary extends React.Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <main className="fatal-boundary" role="alert">
          <Callout.Root color="red">
            <Callout.Text>The evidence studio could not render. Reload to restore the application.</Callout.Text>
            <Button variant="soft" onClick={() => window.location.reload()}>Reload application</Button>
          </Callout.Root>
        </main>
      );
    }
    return this.props.children;
  }
}
