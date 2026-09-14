import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { CollectionStatsPanel } from "./CollectionStatsPanel";
import type { CollectionStats } from "../../types/collection";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "collections.stats.title": "Collection Statistics",
        "collections.stats.totalItems": "Total Items",
        "collections.stats.differentCategories": "Categories",
        "collections.stats.totalInvested": "Total Invested",
        "collections.stats.currentValue": "Current Value",
        "collections.stats.valueGain": "Value Gain",
        "collections.stats.roi": "ROI",
        "collections.stats.roiUnavailable": "N/A",
        "collections.stats.completeItems": "Complete Items",
        "collections.stats.gradedItems": "Graded Items",
      };
      return translations[key] ?? key;
    },
  }),
}));

const buildStats = (overrides: Partial<CollectionStats> = {}): CollectionStats => ({
  totalItems: 42,
  differentCategoriesCount: 3,
  totalInvested: 1000,
  currentValue: 1500,
  valueGain: 500,
  roiPercentage: 50,
  completeItems: 30,
  gradedItems: 12,
  ...overrides,
});

describe("CollectionStatsPanel", () => {
  it("renders the panel title as a heading", () => {
    render(<CollectionStatsPanel stats={buildStats()} />);

    expect(
      screen.getByRole("heading", { name: /collection statistics/i }),
    ).toBeInTheDocument();
  });

  it("labels the region with its heading", () => {
    render(<CollectionStatsPanel stats={buildStats()} />);

    expect(
      screen.getByRole("region", { name: /collection statistics/i }),
    ).toBeInTheDocument();
  });

  it("renders the total items count", () => {
    render(<CollectionStatsPanel stats={buildStats({ totalItems: 42 })} />);

    expect(screen.getByText("Total Items")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("formats monetary values as currency", () => {
    render(<CollectionStatsPanel stats={buildStats({ totalInvested: 1000 })} />);

    expect(screen.getByText("$1,000.00")).toBeInTheDocument();
  });

  it("formats a positive ROI with a plus sign", () => {
    render(<CollectionStatsPanel stats={buildStats({ roiPercentage: 50 })} />);

    expect(screen.getByText("+50.0%")).toBeInTheDocument();
  });

  it("formats a negative ROI with a minus sign", () => {
    render(<CollectionStatsPanel stats={buildStats({ roiPercentage: -25 })} />);

    expect(screen.getByText("-25.0%")).toBeInTheDocument();
  });

  it("renders a placeholder for null monetary values", () => {
    render(
      <CollectionStatsPanel
        stats={buildStats({ totalInvested: null, currentValue: null, valueGain: null })}
      />,
    );

    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("renders the unavailable label for null ROI", () => {
    render(<CollectionStatsPanel stats={buildStats({ roiPercentage: null })} />);

    expect(screen.getByText("N/A")).toBeInTheDocument();
  });

  it("has no accessibility violations with complete data", async () => {
    const { container } = render(<CollectionStatsPanel stats={buildStats()} />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with null values", async () => {
    const { container } = render(
      <CollectionStatsPanel
        stats={buildStats({
          totalInvested: null,
          currentValue: null,
          valueGain: null,
          roiPercentage: null,
        })}
      />,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
