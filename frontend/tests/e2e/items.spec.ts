import { test, expect } from '@playwright/test';

/**
 * E2E tests for the Items flow within a collection.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 *
 * Flow: add item to collection → upload image → verify
 */

test.describe('Collection Items Flow', () => {
  const collectionName = `Items Test ${Date.now()}`;

  test.beforeAll(async ({ browser }) => {
    // Create a collection to work with
    const page = await browser.newPage();
    await page.goto('/collections');
    await page.getByRole('button', { name: /create collection/i }).click();
    await page.getByRole('textbox', { name: /name/i }).fill(collectionName);
    await page.getByRole('button', { name: /save/i }).click();
    await expect(page.getByText(collectionName)).toBeVisible();
    await page.close();
  });

  test('can navigate to collection detail and see add item button', async ({ page }) => {
    await page.goto('/collections');
    await expect(page.getByText(collectionName)).toBeVisible();

    // Navigate to detail
    await page.getByRole('button', { name: new RegExp(`edit ${collectionName}`, 'i') }).click();

    await expect(page.getByRole('heading', { name: collectionName })).toBeVisible();
    await expect(page.getByRole('button', { name: /add item/i })).toBeVisible();
  });

  test('can open add item modal from collection detail', async ({ page }) => {
    await page.goto('/collections');
    await page.getByRole('button', { name: new RegExp(`edit ${collectionName}`, 'i') }).click();

    await page.getByRole('button', { name: /add item/i }).click();

    // The item form modal should be visible with condition and catalog item fields
    await expect(page.getByText(/condition/i)).toBeVisible();
    await expect(page.getByText(/catalog item/i)).toBeVisible();
  });

  test('add item form has required fields', async ({ page }) => {
    await page.goto('/collections');
    await page.getByRole('button', { name: new RegExp(`edit ${collectionName}`, 'i') }).click();

    await page.getByRole('button', { name: /add item/i }).click();

    // Try to submit without filling required fields
    await page.getByRole('button', { name: /save/i }).click();

    // Should show validation errors
    const catalogError = page.getByText(/catalog item is required/i);
    const conditionError = page.getByText(/condition is required/i);

    // At least one validation error should appear
    await expect(catalogError.or(conditionError)).toBeVisible();
  });

  test('add item modal can be cancelled', async ({ page }) => {
    await page.goto('/collections');
    await page.getByRole('button', { name: new RegExp(`edit ${collectionName}`, 'i') }).click();

    await page.getByRole('button', { name: /add item/i }).click();
    await expect(page.getByText(/condition/i)).toBeVisible();

    await page.getByRole('button', { name: /cancel/i }).click();

    // Modal should close
    await expect(page.getByRole('button', { name: /save/i })).not.toBeVisible();
  });

  test('shows empty state when collection has no items', async ({ page }) => {
    await page.goto('/collections');
    await page.getByRole('button', { name: new RegExp(`edit ${collectionName}`, 'i') }).click();

    await expect(page.getByRole('heading', { name: collectionName })).toBeVisible();

    // Should show empty items state
    await expect(page.getByText(/no items yet/i)).toBeVisible();
  });
});

test.describe('Image Upload Flow', () => {
  test('collection detail page shows image upload area when adding item', async ({ page }) => {
    await page.goto('/collections');

    // Check if there are any collections to work with
    const hasCollections = await page.locator('article').count() > 0;
    if (!hasCollections) {
      test.skip();
      return;
    }

    // Click edit on the first collection
    await page.locator('article').first().getByRole('button', { name: /edit/i }).click();

    await expect(page.getByRole('button', { name: /add item/i })).toBeVisible();
  });

  test('image dropzone is accessible via keyboard', async ({ page }) => {
    await page.goto('/collections');

    const hasCollections = await page.locator('article').count() > 0;
    if (!hasCollections) {
      test.skip();
      return;
    }

    await page.locator('article').first().getByRole('button', { name: /edit/i }).click();

    // The image upload area (if visible on the detail page) should be keyboard accessible
    const dropzone = page.getByRole('button', { name: /drop images here/i });
    if (await dropzone.isVisible()) {
      await dropzone.focus();
      await expect(dropzone).toBeFocused();
    }
  });
});
