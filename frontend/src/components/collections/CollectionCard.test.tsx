import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { CollectionCard } from "./CollectionCard";
import type { Collection } from "../../types/collection";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, string>) => {
      const translations: Record<string, string> = {
        "collections.singleCategory": "Single Category",
        "collections.multiCategory": "Multi Category",
        "collections.mixed": "Mixed",
        "common.edit": "Edit",
        "common.delete": "Delete",
      };
      if (key === "collections.editLabel") return `Edit ${opts?.name}`;
      if (key === "collections.deleteLabel") return `Delete ${opts?.name}`;
      return translations[key] ?? key;
    },
  }),
}));

const mockCollection: Collection = {
  id: "col-1",
  name: "My N64 Collection",
  description: "Nintendo 64 games",
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
};

describe("CollectionCard", () => {
  it("renders collection name as heading", () => {
    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "My N64 Collection" }),
    ).toBeInTheDocument();
  });

  it("renders collection type", () => {
    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("Single Category")).toBeInTheDocument();
  });

  it("renders description when present", () => {
    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    expect(screen.getByText("Nintendo 64 games")).toBeInTheDocument();
  });

  it("calls onEdit with collection id when edit is clicked", async () => {
    const onEdit = vi.fn();
    const user = userEvent.setup();
    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={onEdit}
        onDelete={vi.fn()}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "Edit My N64 Collection" }),
    );
    expect(onEdit).toHaveBeenCalledWith("col-1");
  });

  it("calls onDelete with collection id when delete is clicked", async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={onDelete}
      />,
    );
    await user.click(
      screen.getByRole("button", { name: "Delete My N64 Collection" }),
    );
    expect(onDelete).toHaveBeenCalledWith("col-1");
  });

  it("renders as article with aria-labelledby", () => {
    render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    const article = screen.getByRole("article");
    expect(article).toHaveAttribute("aria-labelledby", "collection-col-1");
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <CollectionCard
        collection={mockCollection}
        onEdit={vi.fn()}
        onDelete={vi.fn()}
      />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
