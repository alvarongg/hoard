import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the accessories surface.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Accessories E2E", () => {
  test("renders the accessories page", async ({ page }) => {
    await page.goto("/accessories");
    await expect(
      page.getByRole("heading", { name: /accessories/i }).first(),
    ).toBeVisible();
  });
});
