/**
 * Tests for SearchModeNotice component.
 *
 * Requirements: 6.7, 6.10, 19.2, 19.3
 */

import { render, screen } from "@testing-library/react";
import { axe, toHaveNoViolations } from "jest-axe";
import { describe, expect, it, vi } from "vitest";

import { SearchModeNotice } from "./SearchModeNotice";

expect.extend(toHaveNoViolations);

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "search.degradedMode": "Using basic search. Some features may be limited.",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("SearchModeNotice", () => {
  it("renders nothing for full_text mode", () => {
    const { container } = render(<SearchModeNotice mode="full_text" />);

    expect(container.firstChild).toBeNull();
  });

  it("renders nothing for fuzzy mode", () => {
    const { container } = render(<SearchModeNotice mode="fuzzy" />);

    expect(container.firstChild).toBeNull();
  });

  it("renders notice for degraded mode", () => {
    render(<SearchModeNotice mode="degraded" />);

    expect(
      screen.getByText("Using basic search. Some features may be limited."),
    ).toBeInTheDocument();
  });

  it("has role=status for screen readers", () => {
    render(<SearchModeNotice mode="degraded" />);

    const notice = screen.getByRole("status");
    expect(notice).toBeInTheDocument();
  });

  it("has aria-live=polite for announcements", () => {
    render(<SearchModeNotice mode="degraded" />);

    const notice = screen.getByRole("status");
    expect(notice).toHaveAttribute("aria-live", "polite");
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<SearchModeNotice mode="degraded" />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("applies custom className", () => {
    render(<SearchModeNotice mode="degraded" className="mt-4" />);

    const notice = screen.getByRole("status");
    expect(notice).toHaveClass("mt-4");
  });

  it("displays warning icon", () => {
    const { container } = render(<SearchModeNotice mode="degraded" />);

    const icon = container.querySelector("svg");
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveAttribute("aria-hidden", "true");
  });
});
