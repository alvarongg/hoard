import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { SupplierForm } from "./SupplierForm";
import type { Supplier } from "../../types/supplier";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "common.save": "Save",
        "common.cancel": "Cancel",
        "suppliers.name": "Name",
        "suppliers.type": "Type",
        "suppliers.country": "Country",
        "suppliers.city": "City",
        "suppliers.stateProvince": "State/Province",
        "suppliers.address": "Address",
        "suppliers.postalCode": "Postal Code",
        "suppliers.website": "Website",
        "suppliers.email": "Email",
        "suppliers.phone": "Phone",
        "suppliers.marketplaceUrl": "Marketplace URL",
        "suppliers.notes": "Notes",
        "suppliers.active": "Active",
        "suppliers.rating": "Rating",
        "suppliers.filters.all": "All",
        "suppliers.typeOptions.online": "Online Store",
        "suppliers.typeOptions.store": "Store",
        "suppliers.typeOptions.market": "Marketplace",
        "suppliers.typeOptions.individual": "Individual",
        "suppliers.typeOptions.other": "Other",
        "errors.supplier.nameRequired": "Name is required",
        "errors.supplier.ratingRange": "Rating must be between 0 and 5",
      };
      return translations[key] ?? key;
    },
  }),
}));

const existingSupplier: Supplier = {
  id: "supplier-1",
  name: "Acme Games",
  type: "online",
  country: "US",
  stateProvince: "NY",
  city: "New York",
  address: "123 Main St",
  postalCode: "10001",
  website: "https://acme-games.example.com",
  email: "hello@acme.example.com",
  phone: "+1 555 0100",
  marketplaceUrl: null,
  socialMedia: null,
  rating: 4.5,
  notes: "Reliable seller",
  isFavorite: false,
  isActive: true,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
};

function renderForm(props: Partial<React.ComponentProps<typeof SupplierForm>> = {}) {
  const onSubmit = vi.fn();
  const onCancel = vi.fn();
  const utils = render(
    <SupplierForm
      initialData={props.initialData ?? null}
      onSubmit={props.onSubmit ?? onSubmit}
      onCancel={props.onCancel ?? onCancel}
      isLoading={props.isLoading ?? false}
    />,
  );
  return { onSubmit, onCancel, ...utils };
}

describe("SupplierForm", () => {
  it("renders empty fields when no initial data is provided", () => {
    renderForm();
    expect(screen.getByLabelText("Name")).toHaveValue("");
    expect(screen.getByLabelText("Country")).toHaveValue("");
  });

  it("prefills fields when editing an existing supplier", () => {
    renderForm({ initialData: existingSupplier });
    expect(screen.getByLabelText("Name")).toHaveValue("Acme Games");
    expect(screen.getByLabelText("City")).toHaveValue("New York");
    expect(screen.getByLabelText("Rating")).toHaveValue(4.5);
  });

  it("shows a validation error and does not submit when name is empty", async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderForm();

    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Name is required")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Name")).toHaveAttribute("aria-invalid", "true");
  });

  it("shows a validation error when rating is out of range", async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderForm();

    await user.type(screen.getByLabelText("Name"), "New Supplier");
    await user.type(screen.getByLabelText("Rating"), "9");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(
      await screen.findByText("Rating must be between 0 and 5"),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits trimmed data with nulls for empty optional fields", async () => {
    const user = userEvent.setup();
    const { onSubmit } = renderForm();

    await user.type(screen.getByLabelText("Name"), "  New Supplier  ");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "New Supplier",
        type: null,
        country: null,
        rating: null,
        isActive: true,
      }),
    );
  });

  it("calls onCancel when the cancel button is clicked", async () => {
    const user = userEvent.setup();
    const { onCancel } = renderForm();

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("uses translated labels rather than hardcoded strings", () => {
    renderForm();
    expect(screen.getByLabelText("State/Province")).toBeInTheDocument();
    expect(screen.getByLabelText("Website")).toBeInTheDocument();
    expect(screen.getByLabelText("Notes")).toBeInTheDocument();
    expect(screen.getByLabelText("Active")).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = renderForm();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations while showing validation errors", async () => {
    const user = userEvent.setup();
    const { container } = renderForm();
    await user.click(screen.getByRole("button", { name: "Save" }));
    await screen.findByText("Name is required");
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
