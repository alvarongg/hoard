import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { http, HttpResponse } from "msw";
import { ItemForm } from "./ItemForm";
import { createWrapper } from "../../test/hookWrapper";
import { server } from "../../test/mocks/server";
import type { CatalogItem } from "../../types/item";

expect.extend(toHaveNoViolations);

const API_URL = "http://localhost:8000/api";

const LABELS = {
  catalogItem: "Catalog item",
  condition: "Condition",
  notes: "Notes",
  price: "Purchase price",
  inlineTitle: "Title",
  createNew: "Create new catalog item",
  save: "Save",
  cancel: "Cancel",
};

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "items.catalogItem": LABELS.catalogItem,
        "items.condition": LABELS.condition,
        "items.notes": LABELS.notes,
        "items.price": LABELS.price,
        "items.form.selectCatalogItem": "Select a catalog item",
        "items.form.selectCondition": "Select a condition",
        "items.form.catalogItemRequired": "Catalog item is required",
        "items.form.conditionRequired": "Condition is required",
        "items.mint": "Mint",
        "items.nearMint": "Near mint",
        "items.excellent": "Excellent",
        "items.good": "Good",
        "items.fair": "Fair",
        "items.poor": "Poor",
        "items.inline.createNew": LABELS.createNew,
        "items.inline.title": LABELS.inlineTitle,
        "items.inline.titleRequired": "Title is required",
        "items.inline.titleWhitespace": "Title cannot be only whitespace",
        "items.inline.optionalFields": "Optional fields",
        "items.inline.showOptional": "Show optional fields",
        "items.inline.hideOptional": "Hide optional fields",
        "items.inline.subtitle": "Subtitle",
        "items.inline.description": "Description",
        "items.inline.manufacturer": "Manufacturer",
        "items.inline.publisher": "Publisher",
        "items.inline.developer": "Developer",
        "items.inline.brand": "Brand",
        "items.inline.language": "Language",
        "items.inline.region": "Region",
        "items.inline.rarity": "Rarity",
        "items.inline.creating": "Creating catalog item...",
        "items.inline.createError":
          "Could not create the catalog item. Please try again.",
        "common.save": LABELS.save,
        "common.cancel": LABELS.cancel,
        "common.loading": "Loading...",
      };
      return translations[key] ?? key;
    },
  }),
}));

const existingCatalogItem: CatalogItem = {
  id: "cat-item-1",
  catalogId: "catalog-1",
  title: "The Legend of Zelda: Ocarina of Time",
  subtitle: null,
  description: null,
  releaseDate: null,
  manufacturer: null,
  publisher: null,
  developer: null,
  brand: null,
  language: null,
  region: null,
  rarity: null,
  customFields: {},
  coverImageUrl: null,
  variation: null,
  variationDetails: null,
  relatedItemsGroup: null,
  images: null,
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z",
};

function renderItemForm() {
  const onSubmit = vi.fn();
  const onCancel = vi.fn();
  const { wrapper } = createWrapper();

  const result = render(
    <ItemForm
      catalogItems={[existingCatalogItem]}
      catalogId="catalog-1"
      onSubmit={onSubmit}
      onCancel={onCancel}
      isLoading={false}
    />,
    { wrapper },
  );

  return { ...result, onSubmit, onCancel };
}

function mockCreateCatalogItem(title: string) {
  server.use(
    http.post(`${API_URL}/catalogs/:catalogId/items`, async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      return HttpResponse.json(
        {
          id: "new-cat-item",
          catalog_id: "catalog-1",
          title,
          subtitle: null,
          description: null,
          release_date: null,
          manufacturer: null,
          publisher: null,
          developer: null,
          brand: null,
          language: null,
          region: null,
          rarity: null,
          custom_fields: {},
          cover_image_url: null,
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
          ...body,
        },
        { status: 201 },
      );
    }),
  );
}

function getInlineForm() {
  return screen.getByRole("region", { name: LABELS.createNew });
}

function queryInlineForm() {
  return screen.queryByRole("region", { name: LABELS.createNew });
}

describe("ItemForm", () => {
  it("renders the create new catalog item button", () => {
    renderItemForm();

    expect(
      screen.getByRole("button", { name: LABELS.createNew }),
    ).toBeInTheDocument();
    expect(queryInlineForm()).not.toBeInTheDocument();
  });

  it("shows the inline catalog item form when the button is clicked", async () => {
    const user = userEvent.setup();
    renderItemForm();

    const createButton = screen.getByRole("button", { name: LABELS.createNew });
    expect(createButton).toHaveAttribute("aria-expanded", "false");

    await user.click(createButton);

    expect(getInlineForm()).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: LABELS.createNew }),
    ).toHaveAttribute("aria-expanded", "true");
    expect(within(getInlineForm()).getByLabelText(LABELS.inlineTitle)).toBeInTheDocument();
  });

  it("selects the newly created item and hides the inline form after creation", async () => {
    mockCreateCatalogItem("GoldenEye 007");
    const user = userEvent.setup();
    renderItemForm();

    await user.click(screen.getByRole("button", { name: LABELS.createNew }));

    const inlineForm = getInlineForm();
    await user.type(
      within(inlineForm).getByLabelText(LABELS.inlineTitle),
      "GoldenEye 007",
    );
    await user.click(within(inlineForm).getByRole("button", { name: LABELS.save }));

    await waitFor(() => expect(queryInlineForm()).not.toBeInTheDocument());

    const catalogItemSelect = screen.getByLabelText(
      LABELS.catalogItem,
    ) as HTMLSelectElement;
    expect(catalogItemSelect.value).toBe("new-cat-item");
    expect(
      screen.getByRole("option", { name: "GoldenEye 007" }),
    ).toBeInTheDocument();
  });

  it("keeps the parent form data when the inline form is cancelled", async () => {
    const user = userEvent.setup();
    renderItemForm();

    await user.selectOptions(screen.getByLabelText(LABELS.condition), "good");
    await user.type(screen.getByLabelText(LABELS.notes), "Boxed with manual");
    await user.type(screen.getByLabelText(LABELS.price), "45.50");

    await user.click(screen.getByRole("button", { name: LABELS.createNew }));
    const inlineForm = getInlineForm();
    await user.click(
      within(inlineForm).getByRole("button", { name: LABELS.cancel }),
    );

    expect(queryInlineForm()).not.toBeInTheDocument();
    expect(screen.getByLabelText(LABELS.condition)).toHaveValue("good");
    expect(screen.getByLabelText(LABELS.notes)).toHaveValue("Boxed with manual");
    expect(screen.getByLabelText(LABELS.price)).toHaveValue(45.5);
  });

  it("submits the parent form with the inline created item selected", async () => {
    mockCreateCatalogItem("Perfect Dark");
    const user = userEvent.setup();
    const { onSubmit } = renderItemForm();

    await user.click(screen.getByRole("button", { name: LABELS.createNew }));
    const inlineForm = getInlineForm();
    await user.type(
      within(inlineForm).getByLabelText(LABELS.inlineTitle),
      "Perfect Dark",
    );
    await user.click(
      within(inlineForm).getByRole("button", { name: LABELS.save }),
    );
    await waitFor(() => expect(queryInlineForm()).not.toBeInTheDocument());

    await user.selectOptions(screen.getByLabelText(LABELS.condition), "mint");
    await user.click(screen.getByRole("button", { name: LABELS.save }));

    expect(onSubmit).toHaveBeenCalledWith({
      catalogItemId: "new-cat-item",
      condition: "mint",
      notes: "",
      purchasePrice: "",
    });
  });

  it("has no accessibility violations", async () => {
    const { container } = renderItemForm();

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with the inline form open", async () => {
    const user = userEvent.setup();
    const { container } = renderItemForm();

    await user.click(screen.getByRole("button", { name: LABELS.createNew }));

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
