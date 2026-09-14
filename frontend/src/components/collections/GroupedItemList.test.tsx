/**
 * Test for GroupedItemList component.
 *
 * Tests render of collection items grouped by category with counts.
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { GroupedItemList } from "./GroupedItemList";
import type { CollectionItemGroup } from "../../types/collection";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, options?: { count?: number; defaultValue?: string }) => {
      const translations: Record<string, string> = {
        "collections.grouped.title": "Items by Category",
        "collections.grouped.empty": "No items in this collection",
        "collections.grouped.uncategorized": "Uncategorized",
        "collections.grouped.itemCount": `${options?.count ?? 0} items`,
      };
      return translations[key] ?? options?.defaultValue ?? key;
    },
  }),
}));

describe("GroupedItemList", () => {
  const mockGroups: CollectionItemGroup[] = [
    {
      mainCategoryId: "cat-1",
      mainCategoryName: "Video Games",
      subCategoryId: "sub-1",
      subCategoryName: "Nintendo 64",
      itemCount: 15,
    },
    {
      mainCategoryId: "cat-2",
      mainCategoryName: "Music",
      subCategoryId: "sub-2",
      subCategoryName: "Vinyl Records",
      itemCount: 8,
    },
  ];

  it("renders the heading", () => {
    render(<GroupedItemList groups={mockGroups} />);

    expect(
      screen.getByRole("heading", { name: /items by category/i })
    ).toBeInTheDocument();
  });

  it("displays category names for each group", () => {
    render(<GroupedItemList groups={mockGroups} />);

    expect(screen.getByText("Video Games")).toBeInTheDocument();
    expect(screen.getByText("Music")).toBeInTheDocument();
  });

  it("displays sub-category names", () => {
    render(<GroupedItemList groups={mockGroups} />);

    expect(screen.getByText("Nintendo 64")).toBeInTheDocument();
    expect(screen.getByText("Vinyl Records")).toBeInTheDocument();
  });

  it("displays item counts for each group", () => {
    render(<GroupedItemList groups={mockGroups} />);

    expect(screen.getByText("15 items")).toBeInTheDocument();
    expect(screen.getByText("8 items")).toBeInTheDocument();
  });

  it("displays empty state when no groups", () => {
    render(<GroupedItemList groups={[]} />);

    expect(screen.getByText("No items in this collection")).toBeInTheDocument();
  });

  it("displays 'Uncategorized' when main category is null", () => {
    const uncategorizedGroup: CollectionItemGroup[] = [
      {
        mainCategoryId: null,
        mainCategoryName: null,
        subCategoryId: null,
        subCategoryName: null,
        itemCount: 5,
      },
    ];

    render(<GroupedItemList groups={uncategorizedGroup} />);

    expect(screen.getByText("Uncategorized")).toBeInTheDocument();
  });

  it("uses semantic HTML with section and list", () => {
    const { container } = render(<GroupedItemList groups={mockGroups} />);

    expect(container.querySelector("section")).toBeInTheDocument();
    expect(container.querySelector("ul[role='list']")).toBeInTheDocument();
    expect(container.querySelectorAll("li").length).toBe(2);
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<GroupedItemList groups={mockGroups} />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with empty groups", async () => {
    const { container } = render(<GroupedItemList groups={[]} />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with null category names", async () => {
    const nullCategoryGroup: CollectionItemGroup[] = [
      {
        mainCategoryId: null,
        mainCategoryName: null,
        subCategoryId: null,
        subCategoryName: null,
        itemCount: 3,
      },
    ];

    const { container } = render(<GroupedItemList groups={nullCategoryGroup} />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
