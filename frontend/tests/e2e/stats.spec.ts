import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the stats surface.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Stats E2E", () => {
  test("renders the stats page", async ({ page }) => {
    await page.goto("/stats");
    await expect(
      page.getByRole("heading", { name: /statistics|stats/i }).first(),
    ).toBeVisible();
  });
});
