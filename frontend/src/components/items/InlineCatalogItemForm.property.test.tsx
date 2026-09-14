import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, it, expect, vi } from "vitest";
import fc from "fast-check";
import { InlineCatalogItemForm } from "./InlineCatalogItemForm";
import { createWrapper } from "../../test/hookWrapper";
import type { ItemCondition } from "../../types/item";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const CONDITIONS: ItemCondition[] = [
  "mint",
  "near_mint",
  "excellent",
  "good",
  "fair",
  "poor",
];

const PARENT_LABELS = {
  condition: "parent.condition",
  notes: "parent.notes",
  purchasePrice: "parent.purchasePrice",
};

interface ParentFormState {
  condition: ItemCondition;
  notes: string;
  purchasePrice: string;
}

/**
 * Minimal harness that mimics the parent item form: it holds the
 * condition/notes/purchasePrice state and renders the inline catalog item form
 * on demand. `ItemForm` is not integrated yet (task 5), so this harness stands
 * in as the parent whose state must survive open + cancel.
 */
function ParentFormHarness() {
  const [condition, setCondition] = useState("");
  const [notes, setNotes] = useState("");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [showInlineForm, setShowInlineForm] = useState(false);

  return (
    <form onSubmit={(event) => event.preventDefault()} noValidate>
      <label htmlFor="condition">{PARENT_LABELS.condition}</label>
      <select
        id="condition"
        value={condition}
        onChange={(event) => setCondition(event.target.value)}
      >
        <option value="">--</option>
        {CONDITIONS.map((value) => (
          <option key={value} value={value}>
            {value}
          </option>
        ))}
      </select>

      <label htmlFor="notes">{PARENT_LABELS.notes}</label>
      <input
        id="notes"
        value={notes}
        onChange={(event) => setNotes(event.target.value)}
      />

      <label htmlFor="purchase-price">{PARENT_LABELS.purchasePrice}</label>
      <input
        id="purchase-price"
        type="number"
        step="0.01"
        value={purchasePrice}
        onChange={(event) => setPurchasePrice(event.target.value)}
      />

      <button type="button" onClick={() => setShowInlineForm(true)}>
        open-inline
      </button>

      {showInlineForm && (
        <InlineCatalogItemForm
          catalogId="catalog-1"
          onCreated={() => setShowInlineForm(false)}
          onCancel={() => setShowInlineForm(false)}
          isLoading={false}
        />
      )}
    </form>
  );
}

const parentStateArbitrary = fc.record<ParentFormState>({
  condition: fc.constantFrom(...CONDITIONS),
  notes: fc.string({ maxLength: 40 }),
  purchasePrice: fc
    .integer({ min: 0, max: 999_999 })
    .map((cents) => (cents / 100).toFixed(2)),
});

function readParentState(): ParentFormState {
  return {
    condition: (
      screen.getByLabelText(PARENT_LABELS.condition) as HTMLSelectElement
    ).value as ItemCondition,
    notes: (screen.getByLabelText(PARENT_LABELS.notes) as HTMLInputElement)
      .value,
    purchasePrice: (
      screen.getByLabelText(PARENT_LABELS.purchasePrice) as HTMLInputElement
    ).value,
  };
}

function fillParentForm(state: ParentFormState) {
  fireEvent.change(screen.getByLabelText(PARENT_LABELS.condition), {
    target: { value: state.condition },
  });
  fireEvent.change(screen.getByLabelText(PARENT_LABELS.notes), {
    target: { value: state.notes },
  });
  fireEvent.change(screen.getByLabelText(PARENT_LABELS.purchasePrice), {
    target: { value: state.purchasePrice },
  });
}

// Feature: inline-catalog-item-creation, Property 3: Cancelar creación inline preserva estado del formulario padre
describe("InlineCatalogItemForm properties", () => {
  it("preserves the parent form state after opening and cancelling the inline form", () => {
    fc.assert(
      fc.property(parentStateArbitrary, (state) => {
        const { wrapper } = createWrapper();
        render(<ParentFormHarness />, { wrapper });

        try {
          fillParentForm(state);
          const stateBeforeOpening = readParentState();

          fireEvent.click(screen.getByRole("button", { name: "open-inline" }));
          expect(
            screen.getByRole("heading", { name: "items.inline.createNew" }),
          ).toBeInTheDocument();

          fireEvent.click(
            screen.getByRole("button", { name: "common.cancel" }),
          );
          expect(
            screen.queryByRole("heading", { name: "items.inline.createNew" }),
          ).not.toBeInTheDocument();

          expect(readParentState()).toEqual(stateBeforeOpening);
        } finally {
          cleanup();
        }
      }),
      { numRuns: 100 },
    );
  });

  it("preserves the parent form state when the inline form is dismissed with Escape", () => {
    fc.assert(
      fc.property(parentStateArbitrary, (state) => {
        const { wrapper } = createWrapper();
        render(<ParentFormHarness />, { wrapper });

        try {
          fillParentForm(state);
          const stateBeforeOpening = readParentState();

          fireEvent.click(screen.getByRole("button", { name: "open-inline" }));
          fireEvent.keyDown(document, { key: "Escape" });

          expect(
            screen.queryByRole("heading", { name: "items.inline.createNew" }),
          ).not.toBeInTheDocument();
          expect(readParentState()).toEqual(stateBeforeOpening);
        } finally {
          cleanup();
        }
      }),
      { numRuns: 100 },
    );
  });
});
