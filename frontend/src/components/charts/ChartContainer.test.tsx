import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { ChartDataTable } from "./ChartDataTable";
import { ChartContainer } from "./ChartContainer";
import type { ChartSeries } from "../../types/chart";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => {
      const map: Record<string, string> = {
        "charts.viewDataTable": "View data table",
        "charts.noData": "No data for the chart",
        "charts.loadError": "Could not load the chart",
        "charts.category": "Category",
        "table.sortAscending": "Sort ascending",
        "table.sortDescending": "Sort descending",
      };
      return map[key] ?? fallback ?? key;
    },
  }),
}));

const series: ChartSeries[] = [
  {
    key: "value",
    label: "Value",
    marker: "circle",
    points: [
      { label: "2026-01", value: 100 },
      { label: "2026-02", value: 200 },
    ],
  },
];

describe("ChartDataTable", () => {
  it("renders one row per point with matching values", () => {
    render(<ChartDataTable caption="Chart" series={series} />);
    expect(screen.getByText("2026-01")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("2026-02")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <ChartDataTable caption="Chart" series={series} />,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});

describe("ChartContainer", () => {
  it("renders figure/figcaption and hides the visual from AT", () => {
    const { container } = render(
      <ChartContainer title="My chart" description="desc" data={series}>
        <svg data-testid="viz" />
      </ChartContainer>,
    );
    expect(screen.getAllByText("My chart").length).toBeGreaterThan(0);
    expect(container.querySelector("figure")).toBeInTheDocument();
    expect(container.querySelector("figcaption")).toBeInTheDocument();
    // visual wrapper is aria-hidden
    const hidden = container.querySelector('[aria-hidden="true"]');
    expect(hidden?.querySelector('[data-testid="viz"]')).toBeInTheDocument();
  });

  it("opens the data table via the keyboard-reachable summary", async () => {
    const user = userEvent.setup();
    render(
      <ChartContainer title="My chart" description="desc" data={series}>
        <svg />
      </ChartContainer>,
    );
    const summary = screen.getByText("View data table");
    await user.click(summary);
    expect(screen.getByText("2026-01")).toBeInTheDocument();
  });

  it("shows empty state when there is no data", () => {
    render(
      <ChartContainer title="c" description="d" data={[]}>
        <svg />
      </ChartContainer>,
    );
    expect(screen.getByText("No data for the chart")).toBeInTheDocument();
  });

  it("shows an isolated error with retry", async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    render(
      <ChartContainer
        title="c"
        description="d"
        data={series}
        error={new Error("x")}
        onRetry={onRetry}
      >
        <svg />
      </ChartContainer>,
    );
    expect(screen.getByText("Could not load the chart")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /retry/i }));
    expect(onRetry).toHaveBeenCalled();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <ChartContainer title="c" description="d" data={series}>
        <svg />
      </ChartContainer>,
    );
    expect(await axe(container)).toHaveNoViolations();
  });
});
