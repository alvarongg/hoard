import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { Select } from "./Select";

expect.extend(toHaveNoViolations);

const OPTIONS = [
  { value: "mint", label: "Mint" },
  { value: "good", label: "Good" },
  { value: "poor", label: "Poor" },
];

describe("Select", () => {
  it("renders label associated with select", () => {
    render(<Select label="Condition" options={OPTIONS} />);
    const select = screen.getByLabelText("Condition");
    expect(select).toBeInTheDocument();
    expect(select.tagName).toBe("SELECT");
  });

  it("renders all options", () => {
    render(<Select label="Condition" options={OPTIONS} />);
    expect(screen.getByText("Mint")).toBeInTheDocument();
    expect(screen.getByText("Good")).toBeInTheDocument();
    expect(screen.getByText("Poor")).toBeInTheDocument();
  });

  it("renders placeholder option when provided", () => {
    render(<Select label="Condition" options={OPTIONS} placeholder="Select..." />);
    expect(screen.getByText("Select...")).toBeInTheDocument();
  });

  it("shows error message with role alert", () => {
    render(<Select label="Condition" options={OPTIONS} error="Required" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Required");
  });

  it("sets aria-invalid when error is present", () => {
    render(<Select label="Condition" options={OPTIONS} error="Required" />);
    expect(screen.getByLabelText("Condition")).toHaveAttribute("aria-invalid", "true");
  });

  it("calls onChange when option is selected", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    render(<Select label="Condition" options={OPTIONS} onChange={onChange} />);
    await user.selectOptions(screen.getByLabelText("Condition"), "good");
    expect(onChange).toHaveBeenCalled();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<Select label="Condition" options={OPTIONS} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
