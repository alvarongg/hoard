import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { LoadingSpinner } from "./LoadingSpinner";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "ui.loading": "Loading",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("LoadingSpinner", () => {
  it("renders with role status", () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("has aria-label for screen readers", () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-label", "Loading");
  });

  it("renders sr-only text for screen readers", () => {
    render(<LoadingSpinner />);
    expect(screen.getByText("Loading")).toBeInTheDocument();
  });

  it("renders medium size by default", () => {
    const { container } = render(<LoadingSpinner />);
    const svg = container.querySelector("svg");
    const classes = svg?.getAttribute("class") ?? "";
    expect(classes).toContain("h-8");
    expect(classes).toContain("w-8");
  });

  it("renders small size", () => {
    const { container } = render(<LoadingSpinner size="sm" />);
    const svg = container.querySelector("svg");
    const classes = svg?.getAttribute("class") ?? "";
    expect(classes).toContain("h-4");
    expect(classes).toContain("w-4");
  });

  it("renders large size", () => {
    const { container } = render(<LoadingSpinner size="lg" />);
    const svg = container.querySelector("svg");
    const classes = svg?.getAttribute("class") ?? "";
    expect(classes).toContain("h-12");
    expect(classes).toContain("w-12");
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<LoadingSpinner />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
