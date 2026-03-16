import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { CollectionForm } from "./CollectionForm";
import type { MainCategory, SubCategory } from "../../types/category";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "collections.name": "Name",
        "collections.description": "Description",
        "collections.type": "Type",
        "collections.singleCategory": "Single Category",
        "collections.multiCategory": "Multi Category",
        "collections.mixed": "Mixed",
        "collections.form.nameRequired": "Name is required",
        "collections.form.mainCategory": "Main Category",
        "collections.form.selectMainCategory": "Select main category",
        "collections.form.subCategory": "Sub-category",
        "collections.form.selectSubCategory": "Select sub-category",
        "collections.form.subCategoryRequired":
          "Sub-category is required for single category collections",
        "common.save": "Save",
        "common.cancel": "Cancel",
        "common.loading": "Loading...",
      };
      return translations[key] ?? key;
    },
  }),
}));

const mockMainCategories: MainCategory[] = [
  {
    id: "main-1",
    name: "Video Games",
    description: null,
    icon: null,
    displayOrder: 1,
    isActive: true,
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
];

const mockSubCategories: SubCategory[] = [
  {
    id: "sub-1",
    mainCategoryId: "main-1",
    name: "Nintendo 64",
    description: null,
    icon: null,
    displayOrder: 1,
    isActive: true,
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
  {
    id: "sub-2",
    mainCategoryId: "main-1",
    name: "PlayStation",
    description: null,
    icon: null,
    displayOrder: 2,
    isActive: true,
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
];

const defaultProps = {
  mainCategories: mockMainCategories,
  subCategories: mockSubCategories,
  onMainCategoryChange: vi.fn(),
  onSubmit: vi.fn(),
  onCancel: vi.fn(),
  isLoading: false,
};

describe("CollectionForm", () => {
  it("renders name and description inputs", () => {
    render(<CollectionForm {...defaultProps} />);
    expect(screen.getByLabelText("Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Description")).toBeInTheDocument();
  });

  it("renders type selector", () => {
    render(<CollectionForm {...defaultProps} />);
    expect(screen.getByLabelText("Type")).toBeInTheDocument();
  });

  it("validates required name field on submit", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CollectionForm {...defaultProps} onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(screen.getByText("Name is required")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows main category and sub-category selectors for single_category type", () => {
    render(<CollectionForm {...defaultProps} />);
    expect(screen.getByLabelText("Main Category")).toBeInTheDocument();
    expect(screen.getByLabelText("Sub-category")).toBeInTheDocument();
  });

  it("hides category selectors for multi_category type", async () => {
    const user = userEvent.setup();
    render(<CollectionForm {...defaultProps} />);

    await user.selectOptions(screen.getByLabelText("Type"), "multi_category");

    expect(screen.queryByLabelText("Main Category")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Sub-category")).not.toBeInTheDocument();
  });

  it("calls onMainCategoryChange when main category is selected", async () => {
    const onMainCategoryChange = vi.fn();
    const user = userEvent.setup();
    render(
      <CollectionForm {...defaultProps} onMainCategoryChange={onMainCategoryChange} />,
    );

    await user.selectOptions(screen.getByLabelText("Main Category"), "main-1");
    expect(onMainCategoryChange).toHaveBeenCalledWith("main-1");
  });

  it("validates sub-category required for single_category on submit", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CollectionForm {...defaultProps} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Name"), "Test Collection");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(
      screen.getByText(
        "Sub-category is required for single category collections",
      ),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("calls onSubmit with form data when valid", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<CollectionForm {...defaultProps} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("Name"), "My Collection");
    await user.selectOptions(screen.getByLabelText("Main Category"), "main-1");
    await user.selectOptions(screen.getByLabelText("Sub-category"), "sub-1");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "My Collection",
        collectionType: "single_category",
        restrictedToSubCategoryId: "sub-1",
      }),
    );
  });

  it("calls onCancel when cancel button is clicked", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();
    render(<CollectionForm {...defaultProps} onCancel={onCancel} />);

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<CollectionForm {...defaultProps} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
