import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { PriceAggregatesPanel } from "./PriceAggregatesPanel";
import type { PriceAggregates } from "../../types/wishlist";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "wishlist.aggregates.title": "Price Statistics",
        "wishlist.aggregates.average": "Average Price",
        "wishlist.aggregates.minimum": "Minimum Price",
        "wishlist.aggregates.maximum": "Maximum Price",
        "wishlist.aggregates.totalSightings": "Total Sightings",
        "wishlist.aggregates.availableCount": `${params?.count ?? 0} currently available`,
        "wishlist.aggregates.noData": "No data",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("PriceAggregatesPanel", () => {
  const mockAggregates: PriceAggregates = {
    avgPrice: 100,
    minPrice: 50,
    maxPrice: 150,
    totalSightings: 10,
    availableSightings: 5,
  };

  it("renders the title", () => {
    render(<PriceAggregatesPanel aggregates={mockAggregates} />);
    expect(screen.getByRole("heading", { name: /price statistics/i })).toBeInTheDocument();
  });

  it("renders average price", () => {
    render(<PriceAggregatesPanel aggregates={mockAggregates} />);
    expect(screen.getByText("Average Price")).toBeInTheDocument();
    expect(screen.getByText("$100.00")).toBeInTheDocument();
  });

  it("renders minimum price", () => {
    render(<PriceAggregatesPanel aggregates={mockAggregates} />);
    expect(screen.getByText("Minimum Price")).toBeInTheDocument();
    expect(screen.getByText("$50.00")).toBeInTheDocument();
  });

  it("renders maximum price", () => {
    render(<PriceAggregatesPanel aggregates={mockAggregates} />);
    expect(screen.getByText("Maximum Price")).toBeInTheDocument();
    expect(screen.getByText("$150.00")).toBeInTheDocument();
  });

  it("renders total sightings", () => {
    render(<PriceAggregatesPanel aggregates={mockAggregates} />);
    expect(screen.getByText("Total Sightings")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("renders available count when there are sightings", () => {
    render(<PriceAggregatesPanel aggregates={mockAggregates} />);
    expect(screen.getByText("5 currently available")).toBeInTheDocument();
  });

  it("renders no data for null prices", () => {
    const noDataAggregates: PriceAggregates = {
      avgPrice: null,
      minPrice: null,
      maxPrice: null,
      totalSightings: 0,
      availableSightings: 0,
    };
    render(<PriceAggregatesPanel aggregates={noDataAggregates} />);
    expect(screen.getAllByText("No data")).toHaveLength(3);
  });

  it("does not render available count when no sightings", () => {
    const noSightingsAggregates: PriceAggregates = {
      avgPrice: null,
      minPrice: null,
      maxPrice: null,
      totalSightings: 0,
      availableSightings: 0,
    };
    render(<PriceAggregatesPanel aggregates={noSightingsAggregates} />);
    expect(screen.queryByText(/currently available/i)).not.toBeInTheDocument();
  });

  it("uses custom currency", () => {
    render(<PriceAggregatesPanel aggregates={mockAggregates} currency="EUR" />);
    expect(screen.getByText("€100.00")).toBeInTheDocument();
  });
});
