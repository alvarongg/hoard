import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { Card } from "./Card";

expect.extend(toHaveNoViolations);

describe("Card", () => {
  it("renders children content", () => {
    render(<Card><p>Card content</p></Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("renders as article element", () => {
    render(<Card>Content</Card>);
    expect(screen.getByRole("article")).toBeInTheDocument();
  });

  it("renders title as heading when provided", () => {
    render(<Card title="My Card">Content</Card>);
    expect(screen.getByRole("heading", { name: "My Card" })).toBeInTheDocument();
  });

  it("sets aria-labelledby linking to title", () => {
    render(<Card title="My Card">Content</Card>);
    const article = screen.getByRole("article");
    expect(article).toHaveAttribute("aria-labelledby");
    const labelId = article.getAttribute("aria-labelledby");
    expect(document.getElementById(labelId!)).toHaveTextContent("My Card");
  });

  it("does not render heading when no title", () => {
    render(<Card>Content</Card>);
    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<Card title="Test Card">Content</Card>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
