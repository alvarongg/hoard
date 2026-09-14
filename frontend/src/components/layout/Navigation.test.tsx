import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { Navigation } from "./Navigation";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "navigation.main": "Main navigation",
        "navigation.home": "Home",
        "navigation.collections": "Collections",
        "navigation.catalogs": "Catalogs",
        "navigation.catalogManagement": "Catalog Management",
        "navigation.suppliers": "Suppliers",
      };
      return translations[key] ?? key;
    },
    i18n: {
      language: "en",
      changeLanguage: vi.fn(),
    },
  }),
}));

function renderWithRouter(initialEntries: string[] = ["/"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Navigation />
    </MemoryRouter>,
  );
}

describe("Navigation", () => {
  it("renders all navigation links", () => {
    renderWithRouter();

    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Collections")).toBeInTheDocument();
    expect(screen.getByText("Catalogs")).toBeInTheDocument();
    expect(screen.getByText("Catalog Management")).toBeInTheDocument();
    expect(screen.getByText("Suppliers")).toBeInTheDocument();
  });

  it("points the catalog management link to /catalogs/manage", () => {
    renderWithRouter();

    expect(screen.getByText("Catalog Management")).toHaveAttribute(
      "href",
      "/catalogs/manage",
    );
  });

  it("has accessible navigation landmark with label", () => {
    renderWithRouter();

    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    expect(nav).toBeInTheDocument();
  });

  it("sets aria-current page on active Home link", () => {
    renderWithRouter(["/"]);

    const homeLink = screen.getByText("Home");
    expect(homeLink).toHaveAttribute("aria-current", "page");
  });

  it("sets aria-current page on active Collections link", () => {
    renderWithRouter(["/collections"]);

    const collectionsLink = screen.getByText("Collections");
    expect(collectionsLink).toHaveAttribute("aria-current", "page");
  });

  it("sets aria-current page on active Catalogs link", () => {
    renderWithRouter(["/catalogs"]);

    const catalogsLink = screen.getByText("Catalogs");
    expect(catalogsLink).toHaveAttribute("aria-current", "page");
  });

  it("sets aria-current page on active Catalog Management link", () => {
    renderWithRouter(["/catalogs/manage"]);

    expect(screen.getByText("Catalog Management")).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("sets aria-current page on active Suppliers link", () => {
    renderWithRouter(["/suppliers"]);

    expect(screen.getByText("Suppliers")).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("does not mark the Catalogs link active on the management route", () => {
    renderWithRouter(["/catalogs/manage"]);

    expect(screen.getByText("Catalogs")).not.toHaveAttribute("aria-current");
  });

  it("does not set aria-current on inactive links", () => {
    renderWithRouter(["/collections"]);

    const homeLink = screen.getByText("Home");
    expect(homeLink).not.toHaveAttribute("aria-current");
  });

  it("links are keyboard accessible via tab", async () => {
    const user = userEvent.setup();
    renderWithRouter();

    await user.tab();
    expect(screen.getByText("Home")).toHaveFocus();

    await user.tab();
    expect(screen.getByText("Collections")).toHaveFocus();

    await user.tab();
    expect(screen.getByText("Catalogs")).toHaveFocus();

    await user.tab();
    expect(screen.getByText("Catalog Management")).toHaveFocus();

    await user.tab();
    expect(screen.getByText("Suppliers")).toHaveFocus();
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithRouter();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
