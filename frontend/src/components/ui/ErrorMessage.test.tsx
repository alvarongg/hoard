import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { ErrorMessage } from "./ErrorMessage";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "errors.generic": "Something went wrong",
        "common.retry": "Retry",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("ErrorMessage", () => {
  it("renders with role alert", () => {
    render(<ErrorMessage />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("renders default message when none provided", () => {
    render(<ErrorMessage />);
    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
  });

  it("renders custom message", () => {
    render(<ErrorMessage message="Custom error" />);
    expect(screen.getByText("Custom error")).toBeInTheDocument();
  });

  it("renders retry button when onRetry is provided", () => {
    render(<ErrorMessage onRetry={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("does not render retry button when onRetry is not provided", () => {
    render(<ErrorMessage />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("calls onRetry when retry button is clicked", async () => {
    const onRetry = vi.fn();
    const user = userEvent.setup();
    render(<ErrorMessage onRetry={onRetry} />);
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<ErrorMessage onRetry={vi.fn()} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
