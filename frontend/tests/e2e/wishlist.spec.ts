import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the wishlist surface.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Wishlist E2E", () => {
  test("renders the wishlist page", async ({ page }) => {
    await page.goto("/wishlist");
    await expect(
      page.getByRole("heading", { name: /wishlist/i }).first(),
    ).toBeVisible();
  });
});
