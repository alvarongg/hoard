import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the transfer surface.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Transfer E2E", () => {
  test("renders the transfer page", async ({ page }) => {
    await page.goto("/export");
    await expect(
      page.getByRole("heading", { name: /export/i }).first(),
    ).toBeVisible();
  });
});

test.describe("Import wizard E2E", () => {
  test("shows the import page and file selector", async ({ page }) => {
    await page.goto("/import");
    await expect(
      page.getByRole("heading", { name: /import/i }).first(),
    ).toBeVisible();
    // The file selector is a styled <input type="file"> (may be visually
    // hidden), so assert its presence in the DOM rather than visible text.
    await expect(page.locator('input[type="file"]')).toHaveCount(1);
  });
});
