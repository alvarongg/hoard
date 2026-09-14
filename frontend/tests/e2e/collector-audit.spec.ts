import { test, expect, type Page, type Locator } from "@playwright/test";

/**
 * Collector-workflow deep audit E2E suite for H.O.A.R.D.
 *
 * Runs against an ALREADY-RUNNING stack. baseURL comes from PLAYWRIGHT_BASE_URL
 * (configured in playwright.config). Each test is self-contained: it creates its
 * own collection with a unique name (`E2E ${Date.now()}`) so tests never depend
 * on ordering or on data left behind by a sibling.
 *
 * App notes:
 *  - React + react-i18next, default language EN in a fresh Chromium context.
 *  - selectOption is always called with an EXACT label string (never a regex),
 *    e.g. { label: "Multi Category" }.
 *  - Every dialog interaction is scoped through page.getByRole("dialog").
 */

const NAV_TIMEOUT = 15_000;
const UUID_HEAD = /^[0-9a-f]{8}-[0-9a-f]{4}/i;

/** Wait for the SPA shell to hydrate: the home heading is the first reliable signal. */
async function waitForAppReady(page: Page): Promise<void> {
  await page.goto("/", { timeout: NAV_TIMEOUT });
  await expect(
    page.getByRole("heading", { level: 1, name: /welcome to h\.o\.a\.r\.d\./i }),
  ).toBeVisible({ timeout: NAV_TIMEOUT });
}

/** Navigate through the top nav landmark by accessible link name. */
async function navTo(page: Page, linkName: string): Promise<void> {
  const nav = page.getByRole("navigation");
  await nav.getByRole("link", { name: linkName, exact: true }).first().click();
}

/**
 * Create a Multi Category collection with a unique name and return that name.
 * Multi Category is chosen so the form validates with only a name
 * (single_category would require a sub-category).
 */
async function createMultiCategoryCollection(page: Page): Promise<string> {
  const name = `E2E ${Date.now()}`;

  await page.goto("/collections", { timeout: NAV_TIMEOUT });
  await page.getByRole("button", { name: "Create Collection" }).click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible({ timeout: NAV_TIMEOUT });

  await dialog.getByLabel("Name").fill(name);
  await dialog.getByLabel("Type").selectOption({ label: "Multi Category" });

  // Choosing the Type must NOT close the dialog (regression guard).
  await expect(dialog).toBeVisible();

  await dialog.getByRole("button", { name: "Save" }).click();
  await expect(dialog).toBeHidden({ timeout: NAV_TIMEOUT });

  // The created collection shows up as a level-3 heading with its name.
  await expect(
    page.getByRole("heading", { level: 3, name }),
  ).toBeVisible({ timeout: NAV_TIMEOUT });

  return name;
}

/** Open the first catalog and drill into the first item's detail page ("View item"). */
async function openFirstCatalogItemDetail(page: Page): Promise<void> {
  await page.goto("/catalogs", { timeout: NAV_TIMEOUT });

  const catalogLink = page.locator('a[href^="/catalogs/"]').first();
  await expect(catalogLink).toBeVisible({ timeout: NAV_TIMEOUT });
  await catalogLink.click();

  await expect(page).toHaveURL(/\/catalogs\/[^/]+$/, { timeout: NAV_TIMEOUT });

  const viewItem = page.getByRole("button", { name: "View item" }).first();
  await expect(viewItem).toBeVisible({ timeout: NAV_TIMEOUT });
  await viewItem.click();

  await expect(page).toHaveURL(/\/catalogs\/[^/]+\/items\/[^/]+$/, {
    timeout: NAV_TIMEOUT,
  });
}

/** Pick the first non-placeholder option label from a select and select it. Returns the label. */
async function selectFirstRealOption(select: Locator): Promise<string> {
  const optionValues = await select.locator("option").evaluateAll((opts) =>
    (opts as HTMLOptionElement[]).map((o) => ({
      value: o.value,
      label: o.textContent?.trim() ?? "",
      disabled: o.disabled,
    })),
  );

  const real = optionValues.find(
    (o) => o.value !== "" && !o.disabled && o.label !== "",
  );
  if (!real) {
    throw new Error("Select has no real (non-placeholder) option");
  }

  await select.selectOption(real.value);
  return real.label;
}

test.describe("H.O.A.R.D. collector workflow — deep audit", () => {
  test.beforeEach(async ({ page }) => {
    await waitForAppReady(page);
  });

  test("creates a Multi Category collection without the dialog auto-closing", async ({
    page,
  }) => {
    const name = await createMultiCategoryCollection(page);
    // Sanity: the collection persists in the list after creation.
    await expect(
      page.getByRole("heading", { level: 3, name }),
    ).toBeVisible({ timeout: NAV_TIMEOUT });
  });

  test("adds a catalog item to a collection from the item detail page", async ({
    page,
  }) => {
    const collectionName = await createMultiCategoryCollection(page);

    await openFirstCatalogItemDetail(page);

    await page.getByRole("button", { name: "Add to collection" }).click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible({ timeout: NAV_TIMEOUT });

    await dialog.getByLabel("Collection").selectOption({ label: collectionName });
    await dialog.getByRole("button", { name: "Save" }).click();

    await expect(dialog).toBeHidden({ timeout: NAV_TIMEOUT });
  });

  test("adds a catalog item to the wishlist and it appears in /wishlist", async ({
    page,
  }) => {
    const collectionName = await createMultiCategoryCollection(page);

    await openFirstCatalogItemDetail(page);

    await page.getByRole("button", { name: "Add to wishlist" }).click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible({ timeout: NAV_TIMEOUT });

    await dialog.getByLabel("Collection").selectOption({ label: collectionName });
    await dialog.getByRole("button", { name: "Add to wishlist" }).click();

    await expect(dialog).toBeHidden({ timeout: NAV_TIMEOUT });

    await page.goto("/wishlist", { timeout: NAV_TIMEOUT });
    // At least one wishlist link/entry must render.
    await expect(
      page.locator('a[href^="/wishlist/"]').first(),
    ).toBeVisible({ timeout: NAV_TIMEOUT });
  });

  test("edits a catalog item title and the heading reflects the change", async ({
    page,
  }) => {
    await openFirstCatalogItemDetail(page);

    const heading = page.getByRole("heading", { level: 1 }).first();
    await expect(heading).toBeVisible({ timeout: NAV_TIMEOUT });
    const originalTitle = ((await heading.textContent()) ?? "").trim();
    const newTitle = `${originalTitle} EDITED`;

    await page.getByRole("button", { name: "Edit item" }).click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible({ timeout: NAV_TIMEOUT });

    const titleField = dialog.getByLabel("Title");
    await titleField.fill(newTitle);
    await dialog.getByRole("button", { name: "Save" }).click();

    await expect(dialog).toBeHidden({ timeout: NAV_TIMEOUT });

    await expect(
      page.getByRole("heading", { name: newTitle }),
    ).toBeVisible({ timeout: NAV_TIMEOUT });
  });

  test("Add Item on a collection with an associated catalog offers real catalog-item options", async ({
    page,
  }) => {
    const collectionName = await createMultiCategoryCollection(page);

    // Associate a catalog item with the collection first (populates "Catalog Item").
    await openFirstCatalogItemDetail(page);
    await page.getByRole("button", { name: "Add to collection" }).click();
    let dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible({ timeout: NAV_TIMEOUT });
    await dialog.getByLabel("Collection").selectOption({ label: collectionName });
    await dialog.getByRole("button", { name: "Save" }).click();
    await expect(dialog).toBeHidden({ timeout: NAV_TIMEOUT });

    // Open the collection and its "Add Item" dialog.
    await page.goto("/collections", { timeout: NAV_TIMEOUT });
    await page.getByRole("heading", { level: 3, name: collectionName }).click();
    await expect(page).toHaveURL(/\/collections\/[^/]+$/, { timeout: NAV_TIMEOUT });

    await page.getByRole("button", { name: "Add Item" }).click();
    dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible({ timeout: NAV_TIMEOUT });

    const catalogItemSelect = dialog.getByLabel("Catalog Item");
    await expect(catalogItemSelect).toBeVisible({ timeout: NAV_TIMEOUT });

    const optionCount = await catalogItemSelect.locator("option").count();
    // More than 1 => a real option beyond the empty placeholder.
    expect(optionCount).toBeGreaterThan(1);
  });

  test("adding an item via Add Item shows a human title, not a raw UUID", async ({
    page,
  }) => {
    const collectionName = await createMultiCategoryCollection(page);

    // Associate a catalog with the collection so "Add Item" has choices.
    await openFirstCatalogItemDetail(page);
    await page.getByRole("button", { name: "Add to collection" }).click();
    let dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible({ timeout: NAV_TIMEOUT });
    await dialog.getByLabel("Collection").selectOption({ label: collectionName });
    await dialog.getByRole("button", { name: "Save" }).click();
    await expect(dialog).toBeHidden({ timeout: NAV_TIMEOUT });

    // Open the collection and add an item through the "Add Item" dialog.
    await page.goto("/collections", { timeout: NAV_TIMEOUT });
    await page.getByRole("heading", { level: 3, name: collectionName }).click();
    await expect(page).toHaveURL(/\/collections\/[^/]+$/, { timeout: NAV_TIMEOUT });

    await page.getByRole("button", { name: "Add Item" }).click();
    dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible({ timeout: NAV_TIMEOUT });

    await selectFirstRealOption(dialog.getByLabel("Catalog Item"));
    await dialog.getByLabel("Condition").selectOption({ label: "Mint" });
    await dialog.getByRole("button", { name: "Save" }).click();

    await expect(dialog).toBeHidden({ timeout: NAV_TIMEOUT });

    // Inspect every heading rendered in the items list; none may be a raw UUID.
    const headingTexts = await page
      .getByRole("heading")
      .allTextContents();
    for (const text of headingTexts) {
      expect(UUID_HEAD.test(text.trim())).toBe(false);
    }
  });

  test("renders the Pending page heading", async ({ page }) => {
    await page.goto("/pending", { timeout: NAV_TIMEOUT });
    await expect(
      page.getByRole("heading", { level: 1 }).first(),
    ).toBeVisible({ timeout: NAV_TIMEOUT });
  });
});
