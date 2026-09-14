import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the components surface.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Components E2E", () => {
  test("renders the components page", async ({ page }) => {
    await page.goto("/collections");
    await expect(
      page.getByRole("heading", { name: /collections/i }).first(),
    ).toBeVisible();
  });
});
