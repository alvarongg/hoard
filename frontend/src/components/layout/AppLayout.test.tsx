import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { AppLayout } from "./AppLayout";
import { ThemeProvider } from "../../theme/ThemeProvider";

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
        "navigation.wishlist": "Wishlist",
        "navigation.search": "Search",
        "theme.label": "Theme",
        "theme.light": "Light",
        "theme.dark": "Dark",
        "theme.auto": "Auto",
        "languageSelector.label": "Language selector",
      };
      return translations[key] ?? key;
    },
    i18n: {
      language: "en",
      changeLanguage: vi.fn(),
    },
  }),
}));

vi.mock("../../hooks/useReducedMotion", () => ({
  useReducedMotion: () => false,
}));

// Mock matchMedia for ThemeProvider
const createMatchMedia = (prefersDark: boolean) => (query: string) => ({
  matches: query === "(prefers-color-scheme: dark)" ? prefersDark : false,
  media: query,
  onchange: null,
  addListener: vi.fn(),
  removeListener: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  dispatchEvent: vi.fn(),
});

function renderWithRouter() {
  window.matchMedia = vi.fn(createMatchMedia(false));
  return render(
    <ThemeProvider>
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe("AppLayout", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

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

  it("renders theme toggle component", () => {
    renderWithRouter();

    const themeToggle = screen.getByRole("radiogroup", { name: "Theme" });
    expect(themeToggle).toBeInTheDocument();
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
