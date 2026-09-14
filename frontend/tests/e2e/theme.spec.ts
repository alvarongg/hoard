import { test, expect } from "@playwright/test";

/**
 * E2E smoke test for the theme surface.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Theme E2E", () => {
  test("renders the theme page", async ({ page }) => {
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: /welcome/i }).first(),
    ).toBeVisible();
  });
});

test.describe("Theme toggle E2E", () => {
  test("switches between light and dark", async ({ page }) => {
    await page.goto("/");
    const dark = page.getByRole("radio", { name: /dark/i });
    await dark.click();
    await expect(page.locator("html")).toHaveClass(/dark/);
  });
});
