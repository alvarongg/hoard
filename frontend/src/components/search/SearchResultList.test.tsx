/**
 * Tests for SearchResultList component.
 *
 * Requirements: 6.7, 6.10, 19.2, 19.3
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import { describe, expect, it, vi } from "vitest";

import { SearchResultList } from "./SearchResultList";
import type { CatalogSearchResultItem } from "../../types/search";

expect.extend(toHaveNoViolations);

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "common.loading": "Loading...",
        "search.noResults": "No results found",
        "search.noResultsHint": "Try adjusting your search or filters",
        "search.resultsLabel": "Search results",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("SearchResultList", () => {
  const mockItems: CatalogSearchResultItem[] = [
    {
      id: "item-1",
      title: "The Legend of Zelda: Ocarina of Time",
      subtitle: "Nintendo 64",
      catalogId: "N64-001",
    },
    {
      id: "item-2",
      title: "Super Mario 64",
      subtitle: null,
      catalogId: "N64-002",
    },
    {
      id: "item-3",
      title: "GoldenEye 007",
      subtitle: "First-person shooter",
      catalogId: "N64-003",
    },
  ];

  it("renders list of search results", () => {
    render(<SearchResultList items={mockItems} />);

    expect(screen.getByRole("listbox")).toBeInTheDocument();
    expect(screen.getByText("The Legend of Zelda: Ocarina of Time")).toBeInTheDocument();
    expect(screen.getByText("Super Mario 64")).toBeInTheDocument();
    expect(screen.getByText("GoldenEye 007")).toBeInTheDocument();
  });

  it("displays subtitle when present", () => {
    render(<SearchResultList items={mockItems} />);

    expect(screen.getByText("Nintendo 64")).toBeInTheDocument();
    expect(screen.getByText("First-person shooter")).toBeInTheDocument();
  });

  it("displays catalog ID for each item", () => {
    render(<SearchResultList items={mockItems} />);

    expect(screen.getByText("N64-001")).toBeInTheDocument();
    expect(screen.getByText("N64-002")).toBeInTheDocument();
    expect(screen.getByText("N64-003")).toBeInTheDocument();
  });

  it("calls onSelect when clicking an item", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();

    render(<SearchResultList items={mockItems} onSelect={onSelect} />);

    await user.click(screen.getByText("The Legend of Zelda: Ocarina of Time"));

    expect(onSelect).toHaveBeenCalledWith(mockItems[0]);
  });

  it("shows loading state", () => {
    render(<SearchResultList items={[]} isLoading />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows empty state when no results", () => {
    render(<SearchResultList items={[]} />);

    expect(screen.getByText("No results found")).toBeInTheDocument();
    expect(screen.getByText("Try adjusting your search or filters")).toBeInTheDocument();
  });

  it("shows custom empty message", () => {
    render(<SearchResultList items={[]} emptyMessage="No games found" />);

    expect(screen.getByText("No games found")).toBeInTheDocument();
  });

  it("has accessible listbox role", () => {
    render(<SearchResultList items={mockItems} />);

    const listbox = screen.getByRole("listbox", { name: "Search results" });
    expect(listbox).toBeInTheDocument();
  });

  it("has options for each item", () => {
    render(<SearchResultList items={mockItems} />);

    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(3);
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<SearchResultList items={mockItems} />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("supports keyboard navigation", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();

    render(<SearchResultList items={mockItems} onSelect={onSelect} />);

    // Tab into the listbox
    await user.tab();

    // The first option should be focusable
    const firstOption = screen.getAllByRole("option")[0];
    expect(firstOption).toHaveFocus();

    // Press Enter to select
    await user.keyboard("{Enter}");
    expect(onSelect).toHaveBeenCalledWith(mockItems[0]);
  });

  it("announces empty state to screen readers", () => {
    render(<SearchResultList items={[]} />);

    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
  });

  it("announces loading state to screen readers", () => {
    render(<SearchResultList items={[]} isLoading />);

    const status = screen.getByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
  });
});
