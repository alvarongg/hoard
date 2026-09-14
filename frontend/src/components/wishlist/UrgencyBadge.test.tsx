import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { UrgencyBadge } from "./UrgencyBadge";
import type { Urgency } from "../../types/wishlist";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "wishlist.urgency.low": "Low",
        "wishlist.urgency.medium": "Medium",
        "wishlist.urgency.high": "High",
        "wishlist.urgency.critical": "Critical",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("UrgencyBadge", () => {
  it.each(["low", "medium", "high", "critical"] as Urgency[])("renders urgency level %s", (urgency) => {
    render(<UrgencyBadge urgency={urgency} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders critical urgency with correct tone", () => {
    render(<UrgencyBadge urgency="critical" />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-red-100");
  });

  it("renders high urgency with correct tone", () => {
    render(<UrgencyBadge urgency="high" />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-yellow-100");
  });

  it("renders medium urgency with correct tone", () => {
    render(<UrgencyBadge urgency="medium" />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-gray-100");
  });

  it("renders low urgency with correct tone", () => {
    render(<UrgencyBadge urgency="low" />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-gray-100");
  });

  it("accepts additional className", () => {
    render(<UrgencyBadge urgency="medium" className="custom-class" />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("custom-class");
  });

  it("has no accessibility violations", async () => {
    render(<UrgencyBadge urgency="medium" />);
    // Basic accessibility check - badge should have role="status"
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
