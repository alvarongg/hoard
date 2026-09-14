import { test, expect } from "@playwright/test";

// End-to-end smoke of the collector-workflow flows against the live stack.
// Assumes the NES official catalog has been loaded (many catalog items exist).

const uniq = () => `E2E ${Date.now()}-${Math.floor(Math.random() * 1e4)}`;

test.describe("Collector workflow E2E", () => {
  test("create a collection (choose Multi Category, no modal auto-close)", async ({
    page,
  }) => {
    await page.goto("/collections");
    await page.getByRole("button", { name: /new collection|nueva/i }).click();

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();

    const name = uniq();
    await dialog.getByLabel(/name|nombre/i).fill(name);
    // Selecting the type must NOT close the modal (regression guard).
    await dialog
      .getByLabel(/type|tipo/i)
      .selectOption({ label: /multi/i });
    await expect(dialog).toBeVisible();

    await dialog.getByRole("button", { name: /save|guardar/i }).click();
    await expect(dialog).toBeHidden();
    await expect(
      page.getByRole("heading", { name, level: 3 }),
    ).toBeVisible();
  });

  test("navigate catalog -> item detail -> add to collection", async ({
    page,
  }) => {
    // Ensure a collection exists.
    await page.goto("/collections");
    await page.getByRole("button", { name: /new collection|nueva/i }).click();
    const dialog = page.getByRole("dialog");
    const colName = uniq();
    await dialog.getByLabel(/name|nombre/i).fill(colName);
    await dialog.getByLabel(/type|tipo/i).selectOption({ label: /multi/i });
    await dialog.getByRole("button", { name: /save|guardar/i }).click();
    await expect(dialog).toBeHidden();

    // Open the first catalog.
    await page.goto("/catalogs");
    const firstCatalog = page.getByRole("link").filter({ hasText: /.+/ });
    // Catalogs list renders cards; click the first "view" affordance.
    await page.goto("/catalogs");
    await page.waitForLoadState("networkidle");

    // Go straight to a catalog detail by clicking the first catalog card link.
    const catalogCard = page.locator("a[href^='/catalogs/']").first();
    if ((await catalogCard.count()) > 0) {
      await catalogCard.click();
    }

    // From catalog detail, click "View item" on the first item.
    const viewItem = page
      .getByRole("button", { name: /view item|ver ítem|ver item/i })
      .first();
    await expect(viewItem).toBeVisible({ timeout: 15000 });
    await viewItem.click();

    // On the item detail, open "Add to collection".
    await page
      .getByRole("button", { name: /add to collection|agregar a colección/i })
      .click();
    const addDialog = page.getByRole("dialog");
    await expect(addDialog).toBeVisible();

    // Choose the collection we just created and save.
    await addDialog
      .getByLabel(/collection|colección/i)
      .first()
      .selectOption({ label: colName });
    await addDialog
      .getByRole("button", { name: /^save$|^guardar$/i })
      .click();
    await expect(addDialog).toBeHidden({ timeout: 15000 });
  });

  test("pending page renders", async ({ page }) => {
    await page.goto("/pending");
    await expect(
      page.getByRole("heading", { name: /pending|pendientes/i, level: 1 }),
    ).toBeVisible();
  });
});
