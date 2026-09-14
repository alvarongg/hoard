import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { SupplierFilters } from "./SupplierFilters";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "suppliers.filters.all": "All",
        "suppliers.filters.byType": "By type",
        "suppliers.filters.byCountry": "By country",
        "suppliers.filters.favorites": "Favorites only",
        "suppliers.typeOptions.online": "Online Store",
        "suppliers.typeOptions.store": "Store",
        "suppliers.typeOptions.market": "Marketplace",
        "suppliers.typeOptions.individual": "Individual",
        "suppliers.typeOptions.other": "Other",
      };
      return translations[key] ?? key;
    },
  }),
}));

const defaultProps = {
  typeFilter: "",
  countryFilter: "",
  favoritesOnly: false,
  countries: ["US", "ES", "MX"],
  onTypeChange: vi.fn(),
  onCountryChange: vi.fn(),
  onFavoritesChange: vi.fn(),
};

describe("SupplierFilters", () => {
  it("renders type filter select", () => {
    render(<SupplierFilters {...defaultProps} />);
    expect(screen.getByLabelText("By type")).toBeInTheDocument();
  });

  it("renders country filter select", () => {
    render(<SupplierFilters {...defaultProps} />);
    expect(screen.getByLabelText("By country")).toBeInTheDocument();
  });

  it("renders favorites checkbox", () => {
    render(<SupplierFilters {...defaultProps} />);
    expect(screen.getByLabelText("Favorites only")).toBeInTheDocument();
  });

  it("calls onTypeChange when type is changed", async () => {
    const onTypeChange = vi.fn();
    const user = userEvent.setup();
    render(<SupplierFilters {...defaultProps} onTypeChange={onTypeChange} />);

    await user.selectOptions(screen.getByLabelText("By type"), "online");
    expect(onTypeChange).toHaveBeenCalledWith("online");
  });

  it("calls onCountryChange when country is changed", async () => {
    const onCountryChange = vi.fn();
    const user = userEvent.setup();
    render(<SupplierFilters {...defaultProps} onCountryChange={onCountryChange} />);

    await user.selectOptions(screen.getByLabelText("By country"), "US");
    expect(onCountryChange).toHaveBeenCalledWith("US");
  });

  it("calls onFavoritesChange when checkbox is toggled", async () => {
    const onFavoritesChange = vi.fn();
    const user = userEvent.setup();
    render(<SupplierFilters {...defaultProps} onFavoritesChange={onFavoritesChange} />);

    await user.click(screen.getByLabelText("Favorites only"));
    expect(onFavoritesChange).toHaveBeenCalledWith(true);
  });

  it("displays all type options", () => {
    render(<SupplierFilters {...defaultProps} />);
    const typeSelect = screen.getByLabelText("By type");

    expect(typeSelect).toHaveDisplayValue("All");
    expect(screen.getByRole("option", { name: "Online Store" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Store" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Marketplace" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Individual" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Other" })).toBeInTheDocument();
  });

  it("displays all country options", () => {
    render(<SupplierFilters {...defaultProps} />);
    const countrySelect = screen.getByLabelText("By country");

    expect(countrySelect).toHaveDisplayValue("All");
    expect(screen.getByRole("option", { name: "US" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "ES" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "MX" })).toBeInTheDocument();
  });

  it("shows checkbox as checked when favoritesOnly is true", () => {
    render(<SupplierFilters {...defaultProps} favoritesOnly={true} />);
    expect(screen.getByLabelText("Favorites only")).toBeChecked();
  });

  it("shows checkbox as unchecked when favoritesOnly is false", () => {
    render(<SupplierFilters {...defaultProps} favoritesOnly={false} />);
    expect(screen.getByLabelText("Favorites only")).not.toBeChecked();
  });

  it("disables country select when no countries available", () => {
    render(<SupplierFilters {...defaultProps} countries={[]} />);
    expect(screen.getByLabelText("By country")).toBeDisabled();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<SupplierFilters {...defaultProps} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
