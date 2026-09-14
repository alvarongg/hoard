import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { SkipLink } from "./SkipLink";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "a11y.skipToContent": "Skip to main content",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("SkipLink", () => {
  it("renders as a link with accessible name", () => {
    render(<SkipLink targetId="main-content" />);
    expect(screen.getByRole("link", { name: "Skip to main content" })).toBeInTheDocument();
  });

  it("has href pointing to target element", () => {
    render(<SkipLink targetId="main-content" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "#main-content");
  });

  it("is visually hidden by default (sr-only)", () => {
    render(<SkipLink targetId="main-content" />);
    const link = screen.getByRole("link");
    expect(link.className).toContain("sr-only");
  });

  it("becomes visible when focused", () => {
    render(<SkipLink targetId="main-content" />);
    const link = screen.getByRole("link");
    expect(link.className).toContain("focus:not-sr-only");
    expect(link.className).toContain("focus:fixed");
  });

  it("moves focus to target element when clicked", async () => {
    const user = userEvent.setup();
    render(
      <>
        <SkipLink targetId="main-content" />
        <main id="main-content" data-testid="main" tabIndex={-1}>
          Main content
        </main>
      </>
    );

    const link = screen.getByRole("link");
    await user.click(link);

    // Focus should move to the main element
    const main = screen.getByTestId("main");
    expect(main).toHaveFocus();
  });

  it("moves focus to target element when Enter is pressed", async () => {
    const user = userEvent.setup();
    render(
      <>
        <SkipLink targetId="main-content" />
        <main id="main-content" data-testid="main" tabIndex={-1}>
          Main content
        </main>
      </>
    );

    const link = screen.getByRole("link");
    link.focus();
    await user.keyboard("{Enter}");

    const main = screen.getByTestId("main");
    expect(main).toHaveFocus();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <>
        <SkipLink targetId="main-content" />
        <main id="main-content">Main content</main>
      </>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("works with different target IDs", () => {
    render(<SkipLink targetId="custom-section" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "#custom-section");
  });
});
