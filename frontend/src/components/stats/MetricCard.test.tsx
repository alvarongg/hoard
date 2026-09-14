import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { MetricCard } from "./MetricCard";
import { CollectionStatsTable } from "./CollectionStatsTable";
import { CategoryStatsTable } from "./CategoryStatsTable";
import type {
  CollectionStatsEntry,
  CategoryStatsEntry,
} from "../../types/stats";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const map: Record<string, string> = {
        "stats.empty": "No data to show",
        "stats.byCollection": "By collection",
        "stats.byCategory": "By category",
        "stats.totalItems": "Total items",
        "stats.totalInvested": "Invested",
        "stats.totalValue": "Current value",
        "stats.roi": "ROI",
        "stats.roiUnavailable": "no data",
        "table.sortAscending": "Sort ascending",
        "table.sortDescending": "Sort descending",
      };
      return map[key] ?? key;
    },
  }),
}));

describe("MetricCard", () => {
  it("renders label and value", () => {
    render(<MetricCard label="ROI" value="no data" />);
    expect(screen.getByText("ROI")).toBeInTheDocument();
    expect(screen.getByText("no data")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<MetricCard label="Items" value="5" />);
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("CollectionStatsTable", () => {
  const entries: CollectionStatsEntry[] = [
    {
      collectionId: "c1",
      collectionName: "Games",
      totalItems: 3,
      totalInvested: "100.00",
      currentValue: "150.00",
      roiPercentage: "50.00",
    },
  ];

  it("renders rows and ROI", () => {
    render(<CollectionStatsTable entries={entries} />);
    expect(screen.getByText("Games")).toBeInTheDocument();
    expect(screen.getByText("50.00%")).toBeInTheDocument();
  });

  it("renders null ROI as text", () => {
    render(
      <CollectionStatsTable
        entries={[{ ...entries[0]!, roiPercentage: null }]}
      />,
    );
    expect(screen.getByText("no data")).toBeInTheDocument();
  });

  it("shows empty state", () => {
    render(<CollectionStatsTable entries={[]} />);
    expect(screen.getByText("No data to show")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <CollectionStatsTable entries={entries} />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("CategoryStatsTable", () => {
  const entries: CategoryStatsEntry[] = [
    {
      subCategoryId: "s1",
      subCategoryName: "N64",
      itemCount: 2,
      currentValue: "80.00",
    },
  ];

  it("renders rows", () => {
    render(<CategoryStatsTable entries={entries} />);
    expect(screen.getByText("N64")).toBeInTheDocument();
    expect(screen.getByText("80.00")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<CategoryStatsTable entries={entries} />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
