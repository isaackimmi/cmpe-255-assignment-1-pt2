import { Theme } from "@radix-ui/themes";
import { render } from "@testing-library/react";

export function renderWithTheme(node) {
  return render(<Theme appearance="dark" accentColor="lime">{node}</Theme>);
}
