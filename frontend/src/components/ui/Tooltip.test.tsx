import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { Tooltip } from "./Tooltip";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, options?: { defaultValue?: string }) => {
      const translations: Record<string, string> = {
        "a11y.pressEscapeToClose": "Press Escape to close",
      };
      return translations[key] ?? options?.defaultValue ?? key;
    },
  }),
}));

describe("Tooltip", () => {
  it("does not render the tooltip content by default", () => {
    render(
      <Tooltip content="More information">
        <button>Trigger</button>
      </Tooltip>,
    );
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("shows the tooltip on focus (keyboard)", async () => {
    const user = userEvent.setup();
    render(
      <Tooltip content="More information">
        <button>Trigger</button>
      </Tooltip>,
    );

    await user.tab();
    expect(screen.getByRole("button", { name: "Trigger" })).toHaveFocus();
    expect(screen.getByRole("tooltip")).toHaveTextContent("More information");
  });

  it("hides the tooltip on blur", async () => {
    const user = userEvent.setup();
    render(
      <Tooltip content="More information">
        <button>Trigger</button>
      </Tooltip>,
    );

    await user.tab();
    expect(screen.getByRole("tooltip")).toBeInTheDocument();

    await user.tab();
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("shows the tooltip on mouse hover", async () => {
    const user = userEvent.setup();
    render(
      <Tooltip content="More information">
        <button>Trigger</button>
      </Tooltip>,
    );

    await user.hover(screen.getByRole("button", { name: "Trigger" }));
    expect(screen.getByRole("tooltip")).toBeInTheDocument();

    await user.unhover(screen.getByRole("button", { name: "Trigger" }));
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("associates the trigger with the tooltip via aria-describedby when visible", async () => {
    const user = userEvent.setup();
    render(
      <Tooltip content="More information">
        <button>Trigger</button>
      </Tooltip>,
    );

    const trigger = screen.getByRole("button", { name: "Trigger" });
    expect(trigger).not.toHaveAttribute("aria-describedby");

    await user.tab();
    const tooltip = screen.getByRole("tooltip");
    expect(trigger).toHaveAttribute("aria-describedby", tooltip.id);
  });

  it("closes the tooltip when Escape is pressed and returns focus to the trigger", async () => {
    const user = userEvent.setup();
    render(
      <Tooltip content="More information">
        <button>Trigger</button>
      </Tooltip>,
    );

    await user.tab();
    expect(screen.getByRole("tooltip")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Trigger" })).toHaveFocus();
  });

  it("preserves the child's own event handlers", async () => {
    const onFocus = vi.fn();
    const user = userEvent.setup();
    render(
      <Tooltip content="More information">
        <button onFocus={onFocus}>Trigger</button>
      </Tooltip>,
    );

    await user.tab();
    expect(onFocus).toHaveBeenCalledTimes(1);
  });

  it("has no accessibility violations when hidden", async () => {
    const { container } = render(
      <Tooltip content="More information">
        <button>Trigger</button>
      </Tooltip>,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations when visible", async () => {
    const user = userEvent.setup();
    const { container } = render(
      <Tooltip content="More information">
        <button>Trigger</button>
      </Tooltip>,
    );

    await user.tab();
    expect(screen.getByRole("tooltip")).toBeInTheDocument();

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
