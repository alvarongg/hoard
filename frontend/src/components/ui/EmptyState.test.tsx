import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { EmptyState } from "./EmptyState";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "ui.emptyTitle": "Nothing here yet",
        "ui.emptyDescription": "Get started by creating your first item",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("EmptyState", () => {
  it("renders default title and description", () => {
    render(<EmptyState />);
    expect(screen.getByText("Nothing here yet")).toBeInTheDocument();
    expect(screen.getByText("Get started by creating your first item")).toBeInTheDocument();
  });

  it("renders custom title and description", () => {
    render(<EmptyState title="No collections" description="Create one" />);
    expect(screen.getByText("No collections")).toBeInTheDocument();
    expect(screen.getByText("Create one")).toBeInTheDocument();
  });

  it("renders action when provided", () => {
    render(<EmptyState action={<button>Create</button>} />);
    expect(screen.getByRole("button", { name: "Create" })).toBeInTheDocument();
  });

  it("does not render action when not provided", () => {
    render(<EmptyState />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("has no accessibility violations", async () => {
    const { container } = render(<EmptyState />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
