import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the search surface.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Search E2E", () => {
  test("renders the search page", async ({ page }) => {
    await page.goto("/search");
    await expect(
      page.getByRole("heading", { name: /search/i }).first(),
    ).toBeVisible();
  });
});
