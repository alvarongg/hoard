import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { LanguageSelector } from "./LanguageSelector";

expect.extend(toHaveNoViolations);

const mockChangeLanguage = vi.fn();

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    i18n: {
      language: "en",
      changeLanguage: mockChangeLanguage,
    },
  }),
}));

vi.mock("../../hooks/useReducedMotion", () => ({
  useReducedMotion: () => false,
}));

describe("LanguageSelector", () => {
  beforeEach(() => {
    mockChangeLanguage.mockClear();
  });

  it("renders all five language buttons", () => {
    render(<LanguageSelector />);

    expect(screen.getByText("ES")).toBeInTheDocument();
    expect(screen.getByText("EN")).toBeInTheDocument();
    expect(screen.getByText("PT")).toBeInTheDocument();
    expect(screen.getByText("FR")).toBeInTheDocument();
    expect(screen.getByText("DE")).toBeInTheDocument();
  });

  it("has accessible group role with label", () => {
    render(<LanguageSelector />);

    const group = screen.getByRole("group", { name: "languageSelector.label" });
    expect(group).toBeInTheDocument();
  });

  it("marks EN button as pressed when language is en", () => {
    render(<LanguageSelector />);

    expect(screen.getByText("EN")).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("ES")).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByText("PT")).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByText("FR")).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByText("DE")).toHaveAttribute("aria-pressed", "false");
  });

  it("calls changeLanguage with es when ES button is clicked", async () => {
    const user = userEvent.setup();
    render(<LanguageSelector />);

    await user.click(screen.getByText("ES"));

    expect(mockChangeLanguage).toHaveBeenCalledWith("es");
  });

  it("calls changeLanguage with en when EN button is clicked", async () => {
    const user = userEvent.setup();
    render(<LanguageSelector />);

    await user.click(screen.getByText("EN"));

    expect(mockChangeLanguage).toHaveBeenCalledWith("en");
  });

  it("calls changeLanguage with pt when PT button is clicked", async () => {
    const user = userEvent.setup();
    render(<LanguageSelector />);

    await user.click(screen.getByText("PT"));

    expect(mockChangeLanguage).toHaveBeenCalledWith("pt");
  });

  it("calls changeLanguage with fr when FR button is clicked", async () => {
    const user = userEvent.setup();
    render(<LanguageSelector />);

    await user.click(screen.getByText("FR"));

    expect(mockChangeLanguage).toHaveBeenCalledWith("fr");
  });

  it("calls changeLanguage with de when DE button is clicked", async () => {
    const user = userEvent.setup();
    render(<LanguageSelector />);

    await user.click(screen.getByText("DE"));

    expect(mockChangeLanguage).toHaveBeenCalledWith("de");
  });

  it("buttons are keyboard accessible", async () => {
    const user = userEvent.setup();
    render(<LanguageSelector />);

    await user.tab();
    expect(screen.getByText("ES")).toHaveFocus();

    await user.tab();
    expect(screen.getByText("EN")).toHaveFocus();

    await user.tab();
    expect(screen.getByText("PT")).toHaveFocus();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<LanguageSelector />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
