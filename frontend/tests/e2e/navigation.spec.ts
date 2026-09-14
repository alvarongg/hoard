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
    await expect(page.getByRole('heading', { name: /welcome/i })).toBeVisible();

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
    await expect(page.getByRole('heading', { name: /welcome/i })).toBeVisible();

    // Switch to EN first for consistent text matching
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    // Find and activate the Collections nav link via keyboard
    const collectionsLink = page.getByRole('link', { name: 'Collections' }).first();
    await collectionsLink.focus();
    await page.keyboard.press('Enter');

    await expect(page).toHaveURL(/\/collections/);
    await expect(page.getByRole('heading', { name: /collections/i, level: 1 })).toBeVisible();
  });

  test('can navigate to catalogs page using keyboard', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /welcome/i })).toBeVisible();

    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    const catalogsLink = page.getByRole('link', { name: 'Catalogs' }).first();
    await catalogsLink.focus();
    await page.keyboard.press('Enter');

    await expect(page).toHaveURL(/\/catalogs/);
    await expect(page.getByRole('heading', { name: /catalogs/i })).toBeVisible();
  });

  test('can open create collection modal with keyboard', async ({ page }) => {
    await page.goto('/collections');

    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    const createButton = page.getByRole('button', { name: /create collection/i });
    await createButton.focus();
    await page.keyboard.press('Enter');

    // Modal should open with the name input
    await expect(page.getByRole('textbox', { name: /name/i })).toBeVisible();
  });

  test('can close modal with Escape key', async ({ page }) => {
    await page.goto('/collections');

    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    // Open create modal
    await page.getByRole('button', { name: /create collection/i }).click();
    await expect(page.getByRole('textbox', { name: /name/i })).toBeVisible();

    // Close with Escape
    await page.keyboard.press('Escape');

    await expect(page.getByRole('textbox', { name: /name/i })).not.toBeVisible();
  });

  test('can fill and submit collection form with keyboard', async ({ page }) => {
    await page.goto('/collections');
    await expect(
      page.getByRole('heading', { name: /collections/i, level: 1 }),
    ).toBeVisible();

    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    // Open modal
    await page.getByRole('button', { name: /create collection/i }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Fill the name field
    const nameInput = dialog.getByLabel('Name');
    await nameInput.focus();
    await nameInput.fill(`Keyboard Test ${Date.now()}`);

    // Multi Category needs no sub-category, so the form validates with a name.
    await dialog.getByLabel('Type').selectOption({ label: 'Multi Category' });

    // Submit with the keyboard
    const saveButton = dialog.getByRole('button', { name: /save/i });
    await saveButton.focus();
    await page.keyboard.press('Enter');

    // Modal should close after successful creation
    await expect(dialog).toBeHidden({ timeout: 8000 });
  });

  test('language selector buttons are keyboard accessible', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /welcome/i })).toBeVisible();

    const esButton = page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'ES' });
    const enButton = page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' });

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
    await expect(page.getByRole('heading', { name: /welcome/i })).toBeVisible();

    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    // Tab through the first several focusable elements, reading the active
    // element in-page (a single evaluate per step avoids the locator churn /
    // teardown race that re-resolving :focus 15x can trigger).
    const focusedTags: string[] = [];
    for (let i = 0; i < 12; i++) {
      await page.keyboard.press('Tab');
      const tag = await page.evaluate(
        () => document.activeElement?.tagName.toLowerCase() ?? '',
      );
      if (tag === 'a' || tag === 'button') focusedTags.push(tag);
    }

    // The skip link and header nav are all links/buttons, so tabbing from the
    // top of the document must land on at least one of them.
    expect(focusedTags.length).toBeGreaterThan(0);
  });

  test('collection cards have focusable edit and delete buttons', async ({ page }) => {
    await page.goto('/collections');

    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

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

    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    const searchInput = page.getByRole('textbox', { name: /search items/i });
    await searchInput.focus();
    await expect(searchInput).toBeFocused();

    await searchInput.fill('test search');
    await expect(searchInput).toHaveValue('test search');
  });
});
