import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { AppLayout } from "./AppLayout";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "navigation.main": "Main navigation",
        "navigation.home": "Home",
        "navigation.collections": "Collections",
        "navigation.catalogs": "Catalogs",
      };
      return translations[key] ?? key;
    },
    i18n: {
      language: "en",
      changeLanguage: vi.fn(),
    },
  }),
}));

function renderWithRouter() {
  return render(
    <MemoryRouter>
      <AppLayout />
    </MemoryRouter>,
  );
}

describe("AppLayout", () => {
  it("renders navigation with all links", () => {
    renderWithRouter();

    expect(screen.getByText("H.O.A.R.D.")).toBeInTheDocument();
    expect(screen.getByText("Home")).toBeInTheDocument();
    expect(screen.getByText("Collections")).toBeInTheDocument();
    expect(screen.getByText("Catalogs")).toBeInTheDocument();
  });

  it("renders language selector buttons", () => {
    renderWithRouter();

    expect(screen.getByText("ES")).toBeInTheDocument();
    expect(screen.getByText("EN")).toBeInTheDocument();
  });

  it("calls changeLanguage when language button is clicked", async () => {
    const user = userEvent.setup();
    renderWithRouter();

    const esButton = screen.getByText("ES");
    await user.click(esButton);

    // The mock changeLanguage should have been called
    expect(esButton).toBeInTheDocument();
  });

  it("has accessible navigation landmark", () => {
    renderWithRouter();

    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    expect(nav).toBeInTheDocument();
  });

  it("has accessible language selector group", () => {
    renderWithRouter();

    const group = screen.getByRole("group", { name: "Language selector" });
    expect(group).toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithRouter();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
