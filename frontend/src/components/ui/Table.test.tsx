import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { Table, TableColumn } from "./Table";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, string>) => {
      if (key === "a11y.sortAscending") {
        return `${opts?.column}, sorted ascending, click to sort descending`;
      }
      if (key === "a11y.sortDescending") {
        return `${opts?.column}, sorted descending, click to remove sort`;
      }
      if (key === "a11y.sortNone") {
        return `${opts?.column}, not sorted, click to sort ascending`;
      }
      const translations: Record<string, string> = {
        "common.noResults": "No results found",
      };
      return translations[key] ?? key;
    },
  }),
}));

interface TestRow {
  id: string;
  name: string;
  value: number;
}

const mockRows: TestRow[] = [
  { id: "1", name: "Item 1", value: 100 },
  { id: "2", name: "Item 2", value: 200 },
  { id: "3", name: "Item 3", value: 300 },
];

const mockColumns: TableColumn<TestRow>[] = [
  {
    key: "name",
    header: "Name",
    accessor: (row) => row.name,
    sortable: true,
  },
  {
    key: "value",
    header: "Value",
    accessor: (row) => row.value,
    sortable: true,
  },
  {
    key: "status",
    header: "Status",
    accessor: () => "Active",
    sortable: false,
  },
];

describe("Table", () => {
  it("renders with required caption", () => {
    render(
      <Table caption="Test table" columns={mockColumns} rows={mockRows} />
    );

    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("Test table")).toBeInTheDocument();
  });

  it("renders all column headers with scope='col'", () => {
    render(
      <Table caption="Test table" columns={mockColumns} rows={mockRows} />
    );

    const columnHeaders = screen.getAllByRole("columnheader");
    expect(columnHeaders).toHaveLength(3);

    columnHeaders.forEach((header) => {
      expect(header).toHaveAttribute("scope", "col");
    });
  });

  it("renders all rows with data", () => {
    render(
      <Table caption="Test table" columns={mockColumns} rows={mockRows} />
    );

    expect(screen.getByText("Item 1")).toBeInTheDocument();
    expect(screen.getByText("Item 2")).toBeInTheDocument();
    expect(screen.getByText("Item 3")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(screen.getByText("300")).toBeInTheDocument();
  });

  it("shows empty state when no rows", () => {
    render(
      <Table caption="Test table" columns={mockColumns} rows={[]} />
    );

    expect(screen.getByText("No results found")).toBeInTheDocument();
  });

  it("supports sorting with aria-sort attribute", async () => {
    const user = userEvent.setup();
    const handleSort = vi.fn();

    render(
      <Table
        caption="Test table"
        columns={mockColumns}
        rows={mockRows}
        onSort={handleSort}
      />
    );

    const nameHeader = screen.getByRole("columnheader", { name: /Name/ });

    // Initially no sort
    expect(nameHeader).toHaveAttribute("aria-sort", "none");

    // Click to sort ascending
    await user.click(nameHeader);
    expect(nameHeader).toHaveAttribute("aria-sort", "ascending");
    expect(handleSort).toHaveBeenCalledWith("name", "ascending");

    // Click again to sort descending
    await user.click(nameHeader);
    expect(nameHeader).toHaveAttribute("aria-sort", "descending");
    expect(handleSort).toHaveBeenCalledWith("name", "descending");

    // Click again to remove sort
    await user.click(nameHeader);
    expect(nameHeader).toHaveAttribute("aria-sort", "none");
    expect(handleSort).toHaveBeenCalledWith("name", "none");
  });

  it("does not set aria-sort on non-sortable columns", () => {
    render(
      <Table caption="Test table" columns={mockColumns} rows={mockRows} />
    );

    const statusHeader = screen.getByRole("columnheader", { name: /Status/ });
    expect(statusHeader).not.toHaveAttribute("aria-sort");
    expect(statusHeader).not.toHaveAttribute("tabindex");
  });

  it("supports keyboard navigation for sortable headers", async () => {
    const user = userEvent.setup();
    const handleSort = vi.fn();

    render(
      <Table
        caption="Test table"
        columns={mockColumns}
        rows={mockRows}
        onSort={handleSort}
      />
    );

    const nameHeader = screen.getByRole("columnheader", { name: /Name/ });

    // Focus and press Enter
    nameHeader.focus();
    await user.keyboard("{Enter}");
    expect(handleSort).toHaveBeenCalledWith("name", "ascending");

    // Press Space
    await user.keyboard(" ");
    expect(handleSort).toHaveBeenCalledWith("name", "descending");
  });

  it("has accessible sort labels", () => {
    render(
      <Table caption="Test table" columns={mockColumns} rows={mockRows} />
    );

    const nameHeader = screen.getByRole("columnheader", { name: /Name/ });
    expect(nameHeader).toHaveAttribute(
      "aria-label",
      "Name, not sorted, click to sort ascending"
    );
  });

  it("updates sort label based on current sort state", async () => {
    const user = userEvent.setup();

    render(
      <Table caption="Test table" columns={mockColumns} rows={mockRows} />
    );

    const nameHeader = screen.getByRole("columnheader", { name: /Name/ });

    // Click to sort ascending
    await user.click(nameHeader);
    expect(nameHeader).toHaveAttribute(
      "aria-label",
      "Name, sorted ascending, click to sort descending"
    );

    // Click to sort descending
    await user.click(nameHeader);
    expect(nameHeader).toHaveAttribute(
      "aria-label",
      "Name, sorted descending, click to remove sort"
    );
  });

  it("has overflow-x-auto container for 200% zoom support", () => {
    const { container } = render(
      <Table caption="Test table" columns={mockColumns} rows={mockRows} />
    );

    const tableContainer = container.querySelector(".overflow-x-auto");
    expect(tableContainer).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(
      <Table
        caption="Test table"
        columns={mockColumns}
        rows={mockRows}
        className="custom-class"
      />
    );

    const tableContainer = container.querySelector(".overflow-x-auto");
    expect(tableContainer).toHaveClass("custom-class");
  });

  it("uses row id as key when available", () => {
    const rowsWithIds = [
      { id: "custom-id-1", name: "Item 1", value: 100 },
    ];

    render(
      <Table caption="Test table" columns={mockColumns} rows={rowsWithIds} />
    );

    expect(screen.getByText("Item 1")).toBeInTheDocument();
  });

  it("uses index as key when id is not available", () => {
    const rowsWithoutIds = [
      { name: "Item A", value: 100 },
      { name: "Item B", value: 200 },
    ];

    const columns: TableColumn<{ name: string; value: number }>[] = [
      { key: "name", header: "Name", accessor: (row) => row.name },
      { key: "value", header: "Value", accessor: (row) => row.value },
    ];

    render(
      <Table caption="Test table" columns={columns} rows={rowsWithoutIds} />
    );

    expect(screen.getByText("Item A")).toBeInTheDocument();
    expect(screen.getByText("Item B")).toBeInTheDocument();
  });

  it("supports custom getRowKey function", () => {
    const rows = [
      { code: "A1", name: "Item A", value: 100 },
      { code: "B2", name: "Item B", value: 200 },
    ];

    const columns: TableColumn<{ code: string; name: string; value: number }>[] = [
      { key: "name", header: "Name", accessor: (row) => row.name },
      { key: "value", header: "Value", accessor: (row) => row.value },
    ];

    render(
      <Table
        caption="Test table"
        columns={columns}
        rows={rows}
        getRowKey={(row) => row.code}
      />
    );

    expect(screen.getByText("Item A")).toBeInTheDocument();
    expect(screen.getByText("Item B")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <Table caption="Test table" columns={mockColumns} rows={mockRows} />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with sortable columns", async () => {
    const { container } = render(
      <Table
        caption="Test table"
        columns={mockColumns}
        rows={mockRows}
        onSort={vi.fn()}
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with empty state", async () => {
    const { container } = render(
      <Table caption="Test table" columns={mockColumns} rows={[]} />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
