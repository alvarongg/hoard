/**
 * Property 10: Accesibilidad de componentes
 * ∀ interactive component: has aria-label or aria-labelledby ∧ passes axe-core
 *
 * Validates: REQ-011.1, REQ-011.2
 */
import { render } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import * as fc from "fast-check";
import { axe, toHaveNoViolations } from "jest-axe";
import { Button } from "./Button";
import { Input } from "./Input";
import { Select } from "./Select";
import { ErrorMessage } from "./ErrorMessage";
import { LoadingSpinner } from "./LoadingSpinner";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "common.loading": "Loading...",
        "common.retry": "Retry",
        "errors.generic": "Something went wrong",
        "ui.loading": "Loading",
        "ui.close": "Close",
      };
      return translations[key] ?? key;
    },
  }),
}));

const safeString = fc.string({ minLength: 1, maxLength: 50 }).map((s) => s.replace(/[<>"&]/g, "x"));

describe("Property 10: Accessibility of interactive components", () => {
  it("Button always passes axe-core for any variant and label", async () => {
    await fc.assert(
      fc.asyncProperty(
        safeString,
        fc.constantFrom("primary" as const, "secondary" as const, "danger" as const),
        async (label, variant) => {
          const { container } = render(
            <Button variant={variant} aria-label={label}>
              {label}
            </Button>,
          );
          const results = await axe(container);
          expect(results).toHaveNoViolations();
        },
      ),
      { numRuns: 10 },
    );
  });

  it("Input always has associated label and passes axe-core", async () => {
    await fc.assert(
      fc.asyncProperty(safeString, async (label) => {
        const { container } = render(<Input label={label} />);
        const input = container.querySelector("input");
        expect(input).not.toBeNull();
        const labelEl = container.querySelector("label");
        expect(labelEl).not.toBeNull();
        expect(labelEl?.getAttribute("for")).toBe(input?.getAttribute("id"));
        const results = await axe(container);
        expect(results).toHaveNoViolations();
      }),
      { numRuns: 10 },
    );
  });

  it("Select always has associated label and passes axe-core", async () => {
    const optionArb = fc.record({
      value: fc.string({ minLength: 1, maxLength: 20 }).map((s) => s.replace(/[<>"&]/g, "x")),
      label: safeString,
    });

    await fc.assert(
      fc.asyncProperty(
        safeString,
        fc.array(optionArb, { minLength: 1, maxLength: 5 }),
        async (label, options) => {
          const uniqueOptions = options.reduce<Array<{ value: string; label: string }>>(
            (acc, opt) => {
              if (!acc.some((o) => o.value === opt.value)) {
                acc.push(opt);
              }
              return acc;
            },
            [],
          );
          if (uniqueOptions.length === 0) return;

          const { container } = render(
            <Select label={label} options={uniqueOptions} />,
          );
          const select = container.querySelector("select");
          expect(select).not.toBeNull();
          const labelEl = container.querySelector("label");
          expect(labelEl?.getAttribute("for")).toBe(select?.getAttribute("id"));
          const results = await axe(container);
          expect(results).toHaveNoViolations();
        },
      ),
      { numRuns: 10 },
    );
  });

  it("ErrorMessage always has role=alert", () => {
    fc.assert(
      fc.property(safeString, (message) => {
        const { container } = render(<ErrorMessage message={message} />);
        const alert = container.querySelector('[role="alert"]');
        expect(alert).not.toBeNull();
      }),
      { numRuns: 10 },
    );
  });

  it("LoadingSpinner always has role=status and aria-label", () => {
    fc.assert(
      fc.property(
        fc.constantFrom("sm" as const, "md" as const, "lg" as const),
        (size) => {
          const { container } = render(<LoadingSpinner size={size} />);
          const status = container.querySelector('[role="status"]');
          expect(status).not.toBeNull();
          expect(status?.getAttribute("aria-label")).toBeTruthy();
        },
      ),
      { numRuns: 3 },
    );
  });
});
