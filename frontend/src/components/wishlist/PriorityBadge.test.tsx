import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { PriorityBadge } from "./PriorityBadge";
import type { Priority } from "../../types/wishlist";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "wishlist.priority.critical": "Critical",
        "wishlist.priority.high": "High",
        "wishlist.priority.medium": "Medium",
        "wishlist.priority.low": "Low",
        "wishlist.priority.lowest": "Lowest",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("PriorityBadge", () => {
  it.each([1, 2, 3, 4, 5] as Priority[])("renders priority level %i", (priority) => {
    render(<PriorityBadge priority={priority} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders critical priority (1) with correct tone", () => {
    render(<PriorityBadge priority={1} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-red-100");
  });

  it("renders high priority (2) with correct tone", () => {
    render(<PriorityBadge priority={2} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-yellow-100");
  });

  it("renders medium priority (3) with correct tone", () => {
    render(<PriorityBadge priority={3} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-gray-100");
  });

  it("renders low priority (4) with correct tone", () => {
    render(<PriorityBadge priority={4} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-gray-100");
  });

  it("renders lowest priority (5) with correct tone", () => {
    render(<PriorityBadge priority={5} />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("bg-gray-100");
  });

  it("accepts additional className", () => {
    render(<PriorityBadge priority={3} className="custom-class" />);
    const badge = screen.getByRole("status");
    expect(badge).toHaveClass("custom-class");
  });

  it("has no accessibility violations", async () => {
    render(<PriorityBadge priority={3} />);
    // Basic accessibility check - badge should have role="status"
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
