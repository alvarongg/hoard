import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, beforeAll } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { I18nextProvider } from "react-i18next";
import i18n from "i18next";
import { ThemeToggle } from "./ThemeToggle";
import { ThemeProvider } from "../../theme/ThemeProvider";

expect.extend(toHaveNoViolations);

// Mock useReducedMotion hook
vi.mock("../../hooks/useReducedMotion", () => ({
  useReducedMotion: () => false,
}));

// Mock matchMedia
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

// Initialize i18n for tests
const testI18n = i18n.createInstance({
  lng: "es",
  fallbackLng: "es",
  resources: {
    es: {
      translation: {
        theme: {
          label: "Tema",
          light: "Claro",
          dark: "Oscuro",
          auto: "Automático",
        },
      },
    },
  },
  interpolation: {
    escapeValue: false,
  },
});

beforeAll(async () => {
  await testI18n.init();
});

const renderWithTheme = (prefersDark = false) => {
  window.matchMedia = vi.fn(createMatchMedia(prefersDark));
  return render(
    <I18nextProvider i18n={testI18n}>
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    </I18nextProvider>,
  );
};

describe("ThemeToggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove("dark");
  });

  it("renders as a radiogroup with three options", () => {
    renderWithTheme();
    const radioGroup = screen.getByRole("radiogroup");
    expect(radioGroup).toBeInTheDocument();
    expect(radioGroup).toHaveAttribute("aria-label", "Tema");
  });

  it("renders all three theme options as radio buttons", () => {
    renderWithTheme();
    const radios = screen.getAllByRole("radio");
    expect(radios).toHaveLength(3);
  });

  it("has 'auto' selected by default", () => {
    renderWithTheme();
    const autoRadio = screen.getByRole("radio", { name: /automático/i });
    expect(autoRadio).toHaveAttribute("aria-checked", "true");
  });

  it("selects light theme when clicked", async () => {
    const user = userEvent.setup();
    renderWithTheme();

    const lightRadio = screen.getByRole("radio", { name: /claro/i });
    await user.click(lightRadio);

    await waitFor(() => {
      expect(lightRadio).toHaveAttribute("aria-checked", "true");
    });
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("selects dark theme when clicked", async () => {
    const user = userEvent.setup();
    renderWithTheme();

    const darkRadio = screen.getByRole("radio", { name: /oscuro/i });
    await user.click(darkRadio);

    await waitFor(() => {
      expect(darkRadio).toHaveAttribute("aria-checked", "true");
    });
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("selects auto theme when clicked", async () => {
    const user = userEvent.setup();
    renderWithTheme();

    // First select light
    const lightRadio = screen.getByRole("radio", { name: /claro/i });
    await user.click(lightRadio);

    await waitFor(() => {
      expect(lightRadio).toHaveAttribute("aria-checked", "true");
    });

    // Then select auto
    const autoRadio = screen.getByRole("radio", { name: /automático/i });
    await user.click(autoRadio);

    await waitFor(() => {
      expect(autoRadio).toHaveAttribute("aria-checked", "true");
    });
  });

  it("navigates between options with arrow keys", async () => {
    const user = userEvent.setup();
    renderWithTheme();

    const radios = screen.getAllByRole("radio");
    radios[0]!.focus();

    // Arrow Right should move to next option
    await user.keyboard("{ArrowRight}");
    expect(radios[1]).toHaveFocus();

    // Arrow Right again should move to last option
    await user.keyboard("{ArrowRight}");
    expect(radios[2]).toHaveFocus();

    // Arrow Right again should wrap to first
    await user.keyboard("{ArrowRight}");
    expect(radios[0]).toHaveFocus();
  });

  it("navigates with arrow left and up keys", async () => {
    const user = userEvent.setup();
    renderWithTheme();

    const radios = screen.getAllByRole("radio");
    radios[0]!.focus();

    // Arrow Left should wrap to last
    await user.keyboard("{ArrowLeft}");
    expect(radios[2]).toHaveFocus();

    // Arrow Up should move to middle
    await user.keyboard("{ArrowUp}");
    expect(radios[1]).toHaveFocus();
  });

  it("navigates to first option with Home key", async () => {
    const user = userEvent.setup();
    renderWithTheme();

    const radios = screen.getAllByRole("radio");
    radios[2]!.focus();

    await user.keyboard("{Home}");
    expect(radios[0]).toHaveFocus();
  });

  it("navigates to last option with End key", async () => {
    const user = userEvent.setup();
    renderWithTheme();

    const radios = screen.getAllByRole("radio");
    radios[0]!.focus();

    await user.keyboard("{End}");
    expect(radios[2]).toHaveFocus();
  });

  it("persists preference to localStorage", async () => {
    const user = userEvent.setup();
    renderWithTheme();

    const darkRadio = screen.getByRole("radio", { name: /oscuro/i });
    await user.click(darkRadio);

    await waitFor(() => {
      expect(localStorage.getItem("hoard.theme")).toBe("dark");
    });
  });

  it("clears localStorage when auto is selected", async () => {
    const user = userEvent.setup();
    localStorage.setItem("hoard.theme", "dark");
    renderWithTheme();

    const autoRadio = screen.getByRole("radio", { name: /automático/i });
    await user.click(autoRadio);

    await waitFor(() => {
      expect(localStorage.getItem("hoard.theme")).toBeNull();
    });
  });

  it("has no accessibility violations", async () => {
    const { container } = renderWithTheme();
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
