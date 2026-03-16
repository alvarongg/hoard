import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { CollectionsPage } from "./CollectionsPage";

expect.extend(toHaveNoViolations);

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, opts?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "collections.title": "Collections",
        "collections.create": "Create Collection",
        "collections.empty": "No collections yet",
        "collections.deleteConfirm": "Are you sure?",
        "collections.singleCategory": "Single Category",
        "collections.multiCategory": "Multi Category",
        "collections.mixed": "Mixed",
        "collections.editLabel": `Edit ${opts?.name ?? ""}`,
        "collections.deleteLabel": `Delete ${opts?.name ?? ""}`,
        "errors.loadFailed": "Failed to load data",
        "common.edit": "Edit",
        "common.delete": "Delete",
        "common.save": "Save",
        "common.cancel": "Cancel",
        "common.loading": "Loading...",
        "common.retry": "Retry",
        "ui.loading": "Loading",
        "ui.close": "Close",
        "ui.emptyTitle": "Nothing here yet",
        "ui.emptyDescription": "Get started by creating your first item",
        "collections.name": "Name",
        "collections.description": "Description",
        "collections.type": "Type",
        "collections.form.subCategory": "Sub-category",
        "collections.form.selectSubCategory": "Select sub-category",
        "collections.form.mainCategory": "Main Category",
        "collections.form.selectMainCategory": "Select main category",
        "collections.form.nameRequired": "Name is required",
        "collections.form.subCategoryRequired": "Sub-category required",
      };
      return translations[key] ?? key;
    },
  }),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CollectionsPage", () => {
  beforeEach(() => {
    HTMLDialogElement.prototype.showModal = vi.fn();
    HTMLDialogElement.prototype.close = vi.fn();
  });

  it("renders page heading", async () => {
    renderWithProviders(<CollectionsPage />);
    expect(
      screen.getByRole("heading", { name: "Collections", level: 1 }),
    ).toBeInTheDocument();
  });

  it("renders create button", () => {
    renderWithProviders(<CollectionsPage />);
    expect(
      screen.getByRole("button", { name: "Create Collection" }),
    ).toBeInTheDocument();
  });

  it("renders collection list after loading", async () => {
    renderWithProviders(<CollectionsPage />);
    expect(
      await screen.findByText("My N64 Collection"),
    ).toBeInTheDocument();
  });

  it("opens create modal when create button is clicked", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CollectionsPage />);

    await user.click(
      screen.getByRole("button", { name: "Create Collection" }),
    );

    expect(screen.getByLabelText("Name")).toBeInTheDocument();
  });

  it("navigates to detail on edit", async () => {
    renderWithProviders(<CollectionsPage />);
    const editButton = await screen.findByRole("button", {
      name: /edit my n64 collection/i,
    });
    await userEvent.setup().click(editButton);
    expect(mockNavigate).toHaveBeenCalledWith("/collections/col-1");
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithProviders(<CollectionsPage />);
    await screen.findByText("My N64 Collection");
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
