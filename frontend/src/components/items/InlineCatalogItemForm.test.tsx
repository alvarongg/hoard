import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { http, HttpResponse } from "msw";
import { InlineCatalogItemForm } from "./InlineCatalogItemForm";
import { createWrapper } from "../../test/hookWrapper";
import { server } from "../../test/mocks/server";
import { mockCatalogItem } from "../../test/mocks/handlers";

expect.extend(toHaveNoViolations);

const API_URL = "http://localhost:8000/api";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "items.inline.createNew": "Create new catalog item",
        "items.inline.title": "Title",
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
        "common.save": "Save",
        "common.cancel": "Cancel",
        "common.loading": "Loading...",
      };
      return translations[key] ?? key;
    },
  }),
}));

interface RenderOverrides {
  isLoading?: boolean;
  onCreated?: ReturnType<typeof vi.fn>;
  onCancel?: ReturnType<typeof vi.fn>;
}

function renderForm(overrides: RenderOverrides = {}) {
  const onCreated = overrides.onCreated ?? vi.fn();
  const onCancel = overrides.onCancel ?? vi.fn();
  const { wrapper } = createWrapper();

  const result = render(
    <InlineCatalogItemForm
      catalogId="catalog-1"
      onCreated={onCreated}
      onCancel={onCancel}
      isLoading={overrides.isLoading ?? false}
    />,
    { wrapper },
  );

  return { ...result, onCreated, onCancel };
}

function mockCreateItem() {
  const requestBodies: Record<string, unknown>[] = [];

  server.use(
    http.post(`${API_URL}/catalogs/:catalogId/items`, async ({ request }) => {
      const body = (await request.json()) as Record<string, unknown>;
      requestBodies.push(body);
      return HttpResponse.json(
        { ...mockCatalogItem, ...body, id: "new-cat-item" },
        { status: 201 },
      );
    }),
  );

  return requestBodies;
}

function mockCreateItemFailure() {
  server.use(
    http.post(`${API_URL}/catalogs/:catalogId/items`, () =>
      HttpResponse.json({ detail: "Catalog not found" }, { status: 404 }),
    ),
  );
}

describe("InlineCatalogItemForm", () => {
  it("renders the title field with the correct label", () => {
    renderForm();

    expect(
      screen.getByRole("heading", { name: "Create new catalog item" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
  });

  it("auto-focuses the title field on mount", () => {
    renderForm();

    expect(screen.getByLabelText("Title")).toHaveFocus();
  });

  it("shows an error when the title is empty on submit", async () => {
    const user = userEvent.setup();
    const { onCreated } = renderForm();

    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Title is required",
    );
    expect(onCreated).not.toHaveBeenCalled();
  });

  it("shows an error when the title is only whitespace on submit", async () => {
    const user = userEvent.setup();
    const { onCreated } = renderForm();

    await user.type(screen.getByLabelText("Title"), "   ");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Title cannot be only whitespace",
    );
    expect(onCreated).not.toHaveBeenCalled();
  });

  it("keeps optional fields hidden until the toggle is activated", async () => {
    const user = userEvent.setup();
    renderForm();

    const toggle = screen.getByRole("button", { name: "Show optional fields" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByLabelText("Manufacturer")).not.toBeVisible();

    await user.click(toggle);

    expect(
      screen.getByRole("button", { name: "Hide optional fields" }),
    ).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByLabelText("Manufacturer")).toBeVisible();
  });

  it("disables the submit button when isLoading is true", () => {
    renderForm({ isLoading: true });

    expect(screen.getByRole("button", { name: /loading/i })).toBeDisabled();
  });

  it("calls onCancel when Escape is pressed", async () => {
    const user = userEvent.setup();
    const { onCancel } = renderForm();

    await user.keyboard("{Escape}");

    await waitFor(() => expect(onCancel).toHaveBeenCalledTimes(1));
  });

  it("calls onCancel when the cancel button is clicked", async () => {
    const user = userEvent.setup();
    const { onCancel } = renderForm();

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("calls onCreated with the created item when submitting valid data", async () => {
    mockCreateItem();
    const user = userEvent.setup();
    const { onCreated } = renderForm();

    await user.type(screen.getByLabelText("Title"), "GoldenEye 007");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));
    expect(onCreated.mock.calls[0]?.[0]).toMatchObject({
      id: "new-cat-item",
      title: "GoldenEye 007",
    });
  });

  it("sends a trimmed payload with only the filled optional fields", async () => {
    const requestBodies = mockCreateItem();
    const user = userEvent.setup();
    const { onCreated } = renderForm();

    await user.type(screen.getByLabelText("Title"), "  Super Mario 64  ");
    await user.click(
      screen.getByRole("button", { name: "Show optional fields" }),
    );
    await user.type(screen.getByLabelText("Publisher"), " Nintendo ");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));
    expect(requestBodies).toHaveLength(1);
    expect(requestBodies[0] ?? {}).toEqual({
      title: "Super Mario 64",
      publisher: "Nintendo",
    });
  });

  it("submits when Enter is pressed inside the title field", async () => {
    mockCreateItem();
    const user = userEvent.setup();
    const { onCreated } = renderForm();

    await user.type(screen.getByLabelText("Title"), "Super Mario 64{Enter}");

    await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));
  });

  it("shows an error message when the API rejects the creation", async () => {
    mockCreateItemFailure();
    const user = userEvent.setup();
    const { onCreated } = renderForm();

    await user.type(screen.getByLabelText("Title"), "Unknown catalog item");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(
      await screen.findByText(
        "Could not create the catalog item. Please try again.",
      ),
    ).toBeInTheDocument();
    expect(onCreated).not.toHaveBeenCalled();
  });

  it("has no accessibility violations", async () => {
    const { container } = renderForm();

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations with optional fields expanded", async () => {
    const user = userEvent.setup();
    const { container } = renderForm();

    await user.click(
      screen.getByRole("button", { name: "Show optional fields" }),
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
