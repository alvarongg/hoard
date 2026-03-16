import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { CollectionList } from "./CollectionList";
import type { Collection } from "../../types/collection";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, string>) => {
      const translations: Record<string, string> = {
        "collections.singleCategory": "Single Category",
        "collections.multiCategory": "Multi Category",
        "collections.mixed": "Mixed",
        "collections.empty": "No collections yet",
        "common.edit": "Edit",
        "common.delete": "Delete",
        "errors.loadFailed": "Failed to load data",
        "ui.loading": "Loading",
        "ui.emptyTitle": "Nothing here yet",
        "ui.emptyDescription": "Get started by creating your first item",
      };
      if (key === "collections.editLabel") return `Edit ${opts?.name}`;
      if (key === "collections.deleteLabel") return `Delete ${opts?.name}`;
      return translations[key] ?? key;
    },
  }),
}));

const mockCollections: Collection[] = [
  {
    id: "col-1",
    name: "N64 Collection",
    description: null,
    collectionType: "single_category",
    theme: null,
    themeDescription: null,
    restrictedToSubCategoryId: "sub-1",
    goalDescription: null,
    goalItemsCount: null,
    displayOrder: "custom",
    isPublic: false,
    isActive: true,
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
  {
    id: "col-2",
    name: "Mixed Games",
    description: null,
    collectionType: "mixed",
    theme: null,
    themeDescription: null,
    restrictedToSubCategoryId: null,
    goalDescription: null,
    goalItemsCount: null,
    displayOrder: "custom",
    isPublic: false,
    isActive: true,
    createdAt: "2024-01-02T00:00:00Z",
    updatedAt: "2024-01-02T00:00:00Z",
  },
];

describe("CollectionList", () => {
  it("shows loading spinner when loading", () => {
    render(
      <CollectionList
        collections={[]}
        isLoading={true}
        error={null}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("shows error message on error", () => {
    render(
      <CollectionList
        collections={[]}
        isLoading={false}
        error={new Error("fail")}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Failed to load data")).toBeInTheDocument();
  });

  it("shows empty state when no collections", () => {
    render(
      <CollectionList
        collections={[]}
        isLoading={false}
        error={null}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("No collections yet")).toBeInTheDocument();
  });

  it("renders collection cards when data is present", () => {
    render(
      <CollectionList
        collections={mockCollections}
        isLoading={false}
        error={null}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "N64 Collection" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Mixed Games" }),
    ).toBeInTheDocument();
  });

  it("has no accessibility violations with collections", async () => {
    const { container } = render(
      <CollectionList
        collections={mockCollections}
        isLoading={false}
        error={null}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations when empty", async () => {
    const { container } = render(
      <CollectionList
        collections={[]}
        isLoading={false}
        error={null}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
