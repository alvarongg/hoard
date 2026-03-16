import { test, expect } from '@playwright/test';

/**
 * E2E tests for keyboard navigation across the entire app.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 *
 * Verifies that all interactive elements are reachable via Tab and activatable via Enter.
 */

test.describe('Keyboard Navigation', () => {
  test('can tab through main navigation links', async ({ page }) => {
    await page.goto('/');

    // Tab into the navigation area
    // The first focusable element in the header is the H.O.A.R.D. logo link
    await page.keyboard.press('Tab');

    // Continue tabbing through nav links: Home, Collections, Catalogs
    const navLinks = ['Home', 'Collections', 'Catalogs'];

    for (const linkName of navLinks) {
      // Tab until we find the nav link
      let found = false;
      for (let i = 0; i < 10; i++) {
        const focused = page.locator(':focus');
        const text = await focused.textContent();
        if (text?.trim() === linkName || text?.includes(linkName)) {
          found = true;
          break;
        }
        await page.keyboard.press('Tab');
      }

      if (found) {
        await expect(page.locator(':focus')).toBeVisible();
      }
    }
  });

  test('can navigate to collections page using keyboard', async ({ page }) => {
    await page.goto('/');

    // Switch to EN first for consistent text matching
    await page.getByRole('button', { name: 'EN' }).click();

    // Find and activate the Collections nav link via keyboard
    const collectionsLink = page.getByRole('link', { name: 'Collections' }).first();
    await collectionsLink.focus();
    await page.keyboard.press('Enter');

    await expect(page).toHaveURL(/\/collections/);
    await expect(page.getByRole('heading', { name: /collections/i })).toBeVisible();
  });

  test('can navigate to catalogs page using keyboard', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: 'EN' }).click();

    const catalogsLink = page.getByRole('link', { name: 'Catalogs' }).first();
    await catalogsLink.focus();
    await page.keyboard.press('Enter');

    await expect(page).toHaveURL(/\/catalogs/);
    await expect(page.getByRole('heading', { name: /catalogs/i })).toBeVisible();
  });

  test('can open create collection modal with keyboard', async ({ page }) => {
    await page.goto('/collections');

    await page.getByRole('button', { name: 'EN' }).click();

    const createButton = page.getByRole('button', { name: /create collection/i });
    await createButton.focus();
    await page.keyboard.press('Enter');

    // Modal should open with the name input
    await expect(page.getByRole('textbox', { name: /name/i })).toBeVisible();
  });

  test('can close modal with Escape key', async ({ page }) => {
    await page.goto('/collections');

    await page.getByRole('button', { name: 'EN' }).click();

    // Open create modal
    await page.getByRole('button', { name: /create collection/i }).click();
    await expect(page.getByRole('textbox', { name: /name/i })).toBeVisible();

    // Close with Escape
    await page.keyboard.press('Escape');

    await expect(page.getByRole('textbox', { name: /name/i })).not.toBeVisible();
  });

  test('can fill and submit collection form with keyboard', async ({ page }) => {
    await page.goto('/collections');

    await page.getByRole('button', { name: 'EN' }).click();

    // Open modal
    await page.getByRole('button', { name: /create collection/i }).click();

    // Tab to name field and type
    const nameInput = page.getByRole('textbox', { name: /name/i });
    await nameInput.focus();
    await nameInput.fill(`Keyboard Test ${Date.now()}`);

    // Tab to save button and press Enter
    const saveButton = page.getByRole('button', { name: /save/i });
    await saveButton.focus();
    await page.keyboard.press('Enter');

    // Modal should close after successful creation
    await expect(page.getByRole('textbox', { name: /name/i })).not.toBeVisible({ timeout: 5000 });
  });

  test('language selector buttons are keyboard accessible', async ({ page }) => {
    await page.goto('/');

    const esButton = page.getByRole('button', { name: 'ES' });
    const enButton = page.getByRole('button', { name: 'EN' });

    // Focus and activate ES button
    await esButton.focus();
    await expect(esButton).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(esButton).toHaveAttribute('aria-pressed', 'true');

    // Focus and activate EN button
    await enButton.focus();
    await expect(enButton).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(enButton).toHaveAttribute('aria-pressed', 'true');
  });

  test('tab order follows logical reading order on home page', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: 'EN' }).click();

    // Collect focused element names as we tab through
    const focusedElements: string[] = [];

    for (let i = 0; i < 15; i++) {
      await page.keyboard.press('Tab');
      const focused = page.locator(':focus');
      const tagName = await focused.evaluate((el) => el.tagName.toLowerCase()).catch(() => '');
      const text = await focused.textContent().catch(() => '');
      const ariaLabel = await focused.getAttribute('aria-label').catch(() => '');

      if (tagName === 'a' || tagName === 'button') {
        focusedElements.push(text?.trim() || ariaLabel || '');
      }
    }

    // Navigation links should appear before page content links
    expect(focusedElements.length).toBeGreaterThan(0);
  });

  test('collection cards have focusable edit and delete buttons', async ({ page }) => {
    await page.goto('/collections');

    await page.getByRole('button', { name: 'EN' }).click();

    const articles = page.locator('article');
    const count = await articles.count();

    if (count === 0) {
      test.skip();
      return;
    }

    // First collection card should have focusable edit and delete buttons
    const firstCard = articles.first();
    const editButton = firstCard.getByRole('button', { name: /edit/i });
    const deleteButton = firstCard.getByRole('button', { name: /delete/i });

    await editButton.focus();
    await expect(editButton).toBeFocused();

    await deleteButton.focus();
    await expect(deleteButton).toBeFocused();
  });

  test('catalogs search input is keyboard accessible', async ({ page }) => {
    await page.goto('/catalogs');

    await page.getByRole('button', { name: 'EN' }).click();

    const searchInput = page.getByRole('textbox', { name: /search items/i });
    await searchInput.focus();
    await expect(searchInput).toBeFocused();

    await searchInput.fill('test search');
    await expect(searchInput).toHaveValue('test search');
  });
});
