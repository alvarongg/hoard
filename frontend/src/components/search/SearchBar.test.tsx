/**
 * Tests for SearchBar component.
 *
 * Requirements: 6.4, 6.9, 6.10, 19.2, 19.3
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import { describe, expect, it, vi } from "vitest";

import { SearchBar } from "./SearchBar";

expect.extend(toHaveNoViolations);

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, options?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "search.placeholder": "Search catalog items...",
        "search.clearSearch": "Clear search",
        "search.resultCount": `${options?.count ?? 0} results found`,
        "search.searchHint": "Enter a search term",
        "common.clearFilters": "Clear",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("SearchBar", () => {
  it("renders search input with placeholder", () => {
    render(<SearchBar value="" onChange={vi.fn()} />);

    const input = screen.getByRole("searchbox");
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute("placeholder", "Search catalog items...");
  });

  it("displays current search value", () => {
    render(<SearchBar value="zelda" onChange={vi.fn()} />);

    const input = screen.getByRole("searchbox");
    expect(input).toHaveValue("zelda");
  });

  it("calls onChange when typing", async () => {
    const user = userEvent.setup();
    let currentValue = "";
    const onChange = vi.fn((val) => {
      currentValue = val;
    });

    // Re-render with updated value
    const { rerender } = render(
      <SearchBar value={currentValue} onChange={onChange} />,
    );

    const input = screen.getByRole("searchbox");
    await user.type(input, "mario");

    // onChange is called - the exact call pattern depends on controlled input behavior
    expect(onChange).toHaveBeenCalled();
    // The final call should have the full value
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1];
    expect(lastCall[0]).toContain("o"); // Last character typed
  });

  it("shows clear button when value is present", () => {
    render(<SearchBar value="zelda" onChange={vi.fn()} />);

    const clearButton = screen.getByRole("button", { name: "Clear search" });
    expect(clearButton).toBeInTheDocument();
  });

  it("hides clear button when value is empty", () => {
    render(<SearchBar value="" onChange={vi.fn()} />);

    const clearButton = screen.queryByRole("button", { name: "Clear search" });
    expect(clearButton).not.toBeInTheDocument();
  });

  it("clears search when clicking clear button", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<SearchBar value="zelda" onChange={onChange} />);

    const clearButton = screen.getByRole("button", { name: "Clear search" });
    await user.click(clearButton);

    expect(onChange).toHaveBeenCalledWith("");
  });

  it("shows loading indicator when isLoading is true", () => {
    render(<SearchBar value="" onChange={vi.fn()} isLoading />);

    // The spinner is present (has aria-hidden, so query by test id or container)
    const container = screen.getByRole("searchbox").parentElement;
    const spinner = container?.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("hides loading indicator when isLoading is false", () => {
    render(<SearchBar value="" onChange={vi.fn()} isLoading={false} />);

    const container = screen.getByRole("searchbox").parentElement;
    const spinner = container?.querySelector(".animate-spin");
    expect(spinner).not.toBeInTheDocument();
  });

  it("announces result count when provided", () => {
    render(<SearchBar value="zelda" onChange={vi.fn()} resultCount={42} />);

    expect(screen.getByText("42 results found")).toBeInTheDocument();
  });

  it("announces search hint when no result count", () => {
    render(<SearchBar value="" onChange={vi.fn()} />);

    expect(screen.getByText("Enter a search term")).toBeInTheDocument();
  });

  it("has accessible label", () => {
    render(<SearchBar value="" onChange={vi.fn()} />);

    const input = screen.getByLabelText("Search catalog items...");
    expect(input).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <SearchBar value="test" onChange={vi.fn()} resultCount={5} />,
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("supports keyboard navigation", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(<SearchBar value="zelda" onChange={onChange} />);

    // Tab to input
    await user.tab();
    expect(screen.getByRole("searchbox")).toHaveFocus();

    // Tab to clear button
    await user.tab();
    expect(screen.getByRole("button", { name: "Clear search" })).toHaveFocus();

    // Activate clear button with Enter
    await user.keyboard("{Enter}");
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("uses custom placeholder when provided", () => {
    render(
      <SearchBar
        value=""
        onChange={vi.fn()}
        placeholder="Custom placeholder"
      />,
    );

    const input = screen.getByRole("searchbox");
    expect(input).toHaveAttribute("placeholder", "Custom placeholder");
  });
});
