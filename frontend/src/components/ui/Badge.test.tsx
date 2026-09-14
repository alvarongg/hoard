import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { Badge } from "./Badge";

expect.extend(toHaveNoViolations);

describe("Badge", () => {
  it("renders the label text", () => {
    render(<Badge label="Completed" tone="success" />);
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it("exposes the badge as a status role", () => {
    render(<Badge label="Pending" tone="warning" />);
    expect(screen.getByRole("status")).toHaveTextContent("Pending");
  });

  it("renders the icon as decorative (aria-hidden)", () => {
    const { container } = render(
      <Badge label="Danger" tone="danger" icon={<svg data-testid="icon" />} />,
    );
    const iconWrapper = container.querySelector('[aria-hidden="true"]');
    expect(iconWrapper).toBeInTheDocument();
    expect(iconWrapper).toContainElement(screen.getByTestId("icon"));
  });

  it("does not render an icon wrapper when no icon is provided", () => {
    const { container } = render(<Badge label="Neutral" tone="neutral" />);
    expect(container.querySelector('[aria-hidden="true"]')).not.toBeInTheDocument();
  });

  it("conveys meaning through text, not color alone", () => {
    // The label must always be present so meaning is not lost for users
    // who cannot perceive the tone color (WCAG 2.1 AA - 1.4.1 Use of Color).
    render(<Badge label="Out of stock" tone="danger" />);
    expect(screen.getByText("Out of stock")).toBeInTheDocument();
  });

  it("applies additional class names", () => {
    render(<Badge label="Tagged" tone="neutral" className="custom-class" />);
    expect(screen.getByRole("status")).toHaveClass("custom-class");
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<Badge label="Active" tone="success" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with an icon", async () => {
    const { container } = render(
      <Badge label="Archived" tone="neutral" icon={<svg aria-hidden="true" />} />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
