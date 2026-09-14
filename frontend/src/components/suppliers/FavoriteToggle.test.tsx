import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { FavoriteToggle } from "./FavoriteToggle";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "suppliers.favorite": "Mark as favorite",
        "suppliers.unfavorite": "Remove from favorites",
      };
      return translations[key] ?? key;
    },
  }),
}));

describe("FavoriteToggle", () => {
  it("renders as a button", () => {
    render(<FavoriteToggle isFavorite={false} onToggle={vi.fn()} />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("has aria-pressed false when not favorite", () => {
    render(<FavoriteToggle isFavorite={false} onToggle={vi.fn()} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "false");
  });

  it("has aria-pressed true when favorite", () => {
    render(<FavoriteToggle isFavorite={true} onToggle={vi.fn()} />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
  });

  it("calls onToggle when clicked", async () => {
    const onToggle = vi.fn();
    const user = userEvent.setup();
    render(<FavoriteToggle isFavorite={false} onToggle={onToggle} />);

    await user.click(screen.getByRole("button"));
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("has accessible label for non-favorite state", () => {
    render(<FavoriteToggle isFavorite={false} onToggle={vi.fn()} />);
    expect(screen.getByRole("button")).toHaveAccessibleName("Mark as favorite");
  });

  it("has accessible label for favorite state", () => {
    render(<FavoriteToggle isFavorite={true} onToggle={vi.fn()} />);
    expect(screen.getByRole("button")).toHaveAccessibleName("Remove from favorites");
  });

  it("supports custom aria-label", () => {
    render(
      <FavoriteToggle
        isFavorite={false}
        onToggle={vi.fn()}
        ariaLabel="Mark Acme Corp as favorite"
      />,
    );
    expect(screen.getByRole("button")).toHaveAccessibleName("Mark Acme Corp as favorite");
  });

  it("is focusable and operable with keyboard", async () => {
    const onToggle = vi.fn();
    const user = userEvent.setup();
    render(<FavoriteToggle isFavorite={false} onToggle={onToggle} />);

    screen.getByRole("button").focus();
    expect(screen.getByRole("button")).toHaveFocus();

    await user.keyboard("{Enter}");
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it("has no accessibility violations when not favorite", async () => {
    const { container } = render(
      <FavoriteToggle isFavorite={false} onToggle={vi.fn()} />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations when favorite", async () => {
    const { container } = render(
      <FavoriteToggle isFavorite={true} onToggle={vi.fn()} />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
