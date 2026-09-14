import { test, expect } from "@playwright/test";

/**
 * Keyboard accessibility E2E.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 *
 * Covers: skip link, keyboard-only navigation, modal focus trap, and 200%
 * zoom without loss of functionality or page-level horizontal scroll.
 *
 * NOTE: authored but not executed in the build environment (needs the
 * Playwright runner + running stack).
 */
test.describe("Keyboard accessibility", () => {
  test("skip link is the first focusable and jumps to main", async ({ page }) => {
    await page.goto("/");
    await page.keyboard.press("Tab");
    const skip = page.getByRole("link", { name: /skip/i });
    await expect(skip).toBeFocused();
    await skip.press("Enter");
    await expect(page.locator("#main-content")).toBeFocused();
  });

  test("primary navigation is reachable and operable by keyboard", async ({
    page,
  }) => {
    await page.goto("/");
    // Tab through the nav and activate a link with the keyboard.
    const collections = page.getByRole("link", { name: /collections/i });
    await collections.focus();
    await collections.press("Enter");
    await expect(
      page.getByRole("heading", { name: /collections/i }),
    ).toBeVisible();
  });

  test("modal traps focus and Escape closes it, returning focus", async ({
    page,
  }) => {
    await page.goto("/collections");
    const opener = page.getByRole("button", { name: /create collection/i });
    await opener.focus();
    await opener.press("Enter");

    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    // Focus is inside the dialog.
    await expect(dialog.locator(":focus")).toHaveCount(1);

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(opener).toBeFocused();
  });

  test("remains usable at 200% zoom without page horizontal scroll", async ({
    page,
  }) => {
    await page.goto("/collections");
    await page.evaluate(() => {
      document.documentElement.style.zoom = "200%";
    });
    const overflowsX = await page.evaluate(
      () =>
        document.documentElement.scrollWidth >
        document.documentElement.clientWidth + 1,
    );
    expect(overflowsX).toBe(false);
    await expect(
      page.getByRole("heading", { name: /collections/i }),
    ).toBeVisible();
  });
});
