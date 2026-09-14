import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the suppliers surface.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Suppliers E2E", () => {
  test("renders the suppliers page", async ({ page }) => {
    await page.goto("/suppliers");
    await expect(
      page.getByRole("heading", { name: /suppliers/i }).first(),
    ).toBeVisible();
  });
});
