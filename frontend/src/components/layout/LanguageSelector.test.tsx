import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
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

describe("LanguageSelector", () => {
  it("renders ES and EN buttons", () => {
    render(<LanguageSelector />);

    expect(screen.getByText("ES")).toBeInTheDocument();
    expect(screen.getByText("EN")).toBeInTheDocument();
  });

  it("has accessible group role with label", () => {
    render(<LanguageSelector />);

    const group = screen.getByRole("group", { name: "Language selector" });
    expect(group).toBeInTheDocument();
  });

  it("marks EN button as pressed when language is en", () => {
    render(<LanguageSelector />);

    expect(screen.getByText("EN")).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("ES")).toHaveAttribute("aria-pressed", "false");
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

  it("buttons are keyboard accessible", async () => {
    const user = userEvent.setup();
    render(<LanguageSelector />);

    await user.tab();
    expect(screen.getByText("ES")).toHaveFocus();

    await user.tab();
    expect(screen.getByText("EN")).toHaveFocus();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<LanguageSelector />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
