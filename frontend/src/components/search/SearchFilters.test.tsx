/**
 * Tests for SearchFilters component.
 *
 * Requirements: 6.4, 6.7, 6.10, 19.2, 19.3
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { SearchFilters } from "./SearchFilters";
import type { CatalogSearchFilters } from "../../types/search";

expect.extend(toHaveNoViolations);

/**
 * Stateful wrapper that mirrors how a parent uses SearchFilters, so that
 * controlled inputs round-trip their value across keystrokes. `onChange` is
 * invoked on every update to allow assertions on the accumulated filters.
 */
function ControlledFilters({
  initialFilters = {},
  onChange,
  options,
}: {
  initialFilters?: CatalogSearchFilters;
  onChange: (filters: CatalogSearchFilters) => void;
  options?: React.ComponentProps<typeof SearchFilters>["options"];
}) {
  const [filters, setFilters] = useState<CatalogSearchFilters>(initialFilters);
  return (
    <SearchFilters
      filters={filters}
      onFiltersChange={(next) => {
        setFilters(next);
        onChange(next);
      }}
      options={options}
    />
  );
}

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "search.filters.title": "Filters",
        "search.filters.mainCategory": "Main Category",
        "search.filters.subCategory": "Sub Category",
        "search.filters.language": "Language",
        "search.filters.region": "Region",
        "search.filters.rarity": "Rarity",
        "search.filters.yearMin": "Year From",
        "search.filters.yearMax": "Year To",
        "search.filters.manufacturer": "Manufacturer",
        "search.filters.publisher": "Publisher",
        "search.filters.developer": "Developer",
        "search.filters.brand": "Brand",
        "common.all": "All",
        "common.clearFilters": "Clear filters",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("SearchFilters", () => {
  const defaultFilters: CatalogSearchFilters = {};
  const defaultOnChange = vi.fn();

  const mockOptions = {
    mainCategories: [
      { id: "cat-1", name: "Video Games" },
      { id: "cat-2", name: "Board Games" },
    ],
    subCategories: [
      { id: "sub-1", name: "Nintendo 64" },
      { id: "sub-2", name: "PlayStation" },
    ],
    languages: ["English", "Spanish", "Japanese"],
    regions: ["NTSC", "PAL"],
    rarities: ["Common", "Rare", "Legendary"],
  };

  it("renders filter heading", () => {
    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={defaultOnChange}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Filters" }),
    ).toBeInTheDocument();
  });

  it("renders category dropdowns when options provided", () => {
    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={defaultOnChange}
        options={mockOptions}
      />,
    );

    expect(
      screen.getByLabelText("Main Category"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Sub Category"),
    ).toBeInTheDocument();
  });

  it("calls onFiltersChange when selecting a category", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onChange}
        options={mockOptions}
      />,
    );

    const mainCategorySelect = screen.getByLabelText("Main Category");
    await user.selectOptions(mainCategorySelect, "cat-1");

    expect(onChange).toHaveBeenCalledWith({
      mainCategoryId: "cat-1",
    });
  });

  it("displays current filter values", () => {
    const filters: CatalogSearchFilters = {
      mainCategoryId: "cat-1",
      language: "English",
      yearMin: 1990,
      manufacturer: "Nintendo",
    };

    render(
      <SearchFilters
        filters={filters}
        onFiltersChange={defaultOnChange}
        options={mockOptions}
      />,
    );

    expect(screen.getByLabelText("Main Category")).toHaveValue("cat-1");
    expect(screen.getByLabelText("Language")).toHaveValue("English");
    expect(screen.getByLabelText("Year From")).toHaveValue(1990);
    expect(screen.getByLabelText("Manufacturer")).toHaveValue("Nintendo");
  });

  it("shows clear filters button when filters are active", () => {
    const filters: CatalogSearchFilters = { language: "English" };

    render(
      <SearchFilters
        filters={filters}
        onFiltersChange={defaultOnChange}
        options={mockOptions}
      />,
    );

    expect(
      screen.getByRole("button", { name: "Clear filters" }),
    ).toBeInTheDocument();
  });

  it("hides clear filters button when no filters active", () => {
    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={defaultOnChange}
        options={mockOptions}
      />,
    );

    expect(
      screen.queryByRole("button", { name: "Clear filters" }),
    ).not.toBeInTheDocument();
  });

  it("clears filters when clicking clear button", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const filters: CatalogSearchFilters = {
      q: "zelda",
      language: "English",
    };

    render(
      <SearchFilters
        filters={filters}
        onFiltersChange={onChange}
        options={mockOptions}
      />,
    );

    const clearButton = screen.getByRole("button", { name: "Clear filters" });
    await user.click(clearButton);

    // Should preserve the query but clear other filters
    expect(onChange).toHaveBeenCalledWith({ q: "zelda" });
  });

  it("updates year filters with numeric values", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<ControlledFilters onChange={onChange} options={mockOptions} />);

    const yearMinInput = screen.getByLabelText("Year From");
    await user.type(yearMinInput, "1990");

    // Should be called multiple times (once per character)
    expect(onChange).toHaveBeenCalled();
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(lastCall.yearMin).toBe(1990);
  });

  it("updates text filters", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<ControlledFilters onChange={onChange} options={mockOptions} />);

    const manufacturerInput = screen.getByLabelText("Manufacturer");
    await user.type(manufacturerInput, "Nintendo");

    expect(onChange).toHaveBeenCalled();
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(lastCall.manufacturer).toBe("Nintendo");
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <SearchFilters
        filters={{ language: "English" }}
        onFiltersChange={defaultOnChange}
        options={mockOptions}
      />,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("supports keyboard navigation", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onChange}
        options={mockOptions}
      />,
    );

    // Tab through form elements
    await user.tab();
    expect(screen.getByLabelText("Main Category")).toHaveFocus();

    await user.tab();
    expect(screen.getByLabelText("Sub Category")).toHaveFocus();
  });

  it("does not render category filters without options", () => {
    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={defaultOnChange}
      />,
    );

    expect(
      screen.queryByLabelText("Main Category"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText("Language"),
    ).not.toBeInTheDocument();
  });

  it("always renders year and text filters", () => {
    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={defaultOnChange}
      />,
    );

    expect(screen.getByLabelText("Year From")).toBeInTheDocument();
    expect(screen.getByLabelText("Year To")).toBeInTheDocument();
    expect(screen.getByLabelText("Manufacturer")).toBeInTheDocument();
    expect(screen.getByLabelText("Publisher")).toBeInTheDocument();
    expect(screen.getByLabelText("Developer")).toBeInTheDocument();
    expect(screen.getByLabelText("Brand")).toBeInTheDocument();
  });
});
