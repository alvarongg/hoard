import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { Input } from "./Input";

expect.extend(toHaveNoViolations);

describe("Input", () => {
  it("renders label associated with input via htmlFor/id", () => {
    render(<Input label="Email" />);
    const input = screen.getByLabelText("Email");
    expect(input).toBeInTheDocument();
    expect(input.tagName).toBe("INPUT");
  });

  it("uses external id when provided", () => {
    render(<Input label="Name" id="custom-id" />);
    const input = screen.getByLabelText("Name");
    expect(input).toHaveAttribute("id", "custom-id");
  });

  it("shows error message with role alert", () => {
    render(<Input label="Email" error="Invalid email" />);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Invalid email");
  });

  it("sets aria-invalid when error is present", () => {
    render(<Input label="Email" error="Required" />);
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("sets aria-describedby linking to error message", () => {
    render(<Input label="Email" error="Required" id="email" />);
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-describedby", "email-error");
  });

  it("does not set aria-invalid when no error", () => {
    render(<Input label="Email" />);
    const input = screen.getByLabelText("Email");
    expect(input).not.toHaveAttribute("aria-invalid");
  });

  it("accepts user input", async () => {
    const user = userEvent.setup();
    render(<Input label="Name" />);
    const input = screen.getByLabelText("Name");
    await user.type(input, "Hello");
    expect(input).toHaveValue("Hello");
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<Input label="Email" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with error", async () => {
    const { container } = render(<Input label="Email" error="Invalid" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
