import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the backups surface.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Backups E2E", () => {
  test("renders the backups page", async ({ page }) => {
    await page.goto("/settings/backups");
    await expect(
      page.getByRole("heading", { name: /backups/i }).first(),
    ).toBeVisible();
  });
});
