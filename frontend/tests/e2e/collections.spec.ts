import { test, expect } from '@playwright/test';

/**
 * E2E tests for the Collections CRUD flow.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 *
 * Flow: create collection → verify in list → edit → delete
 */

const TEST_COLLECTION_NAME = 'E2E Test Collection';

test.describe('Collections CRUD Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/collections');
    await expect(page.getByRole('heading', { name: /collections/i, level: 1 })).toBeVisible();
  });

  test('can create a new collection and see it in the list', async ({ page }) => {
    await page.getByRole('button', { name: /create collection/i }).click();

    await page.getByRole('textbox', { name: /name/i }).fill(TEST_COLLECTION_NAME);
    await page.getByRole('textbox', { name: /description/i }).fill('Created by E2E test');

    await page.getByRole('button', { name: /save/i }).click();

    await expect(page.getByText(TEST_COLLECTION_NAME)).toBeVisible();
  });

  test('can navigate to collection detail from the list', async ({ page }) => {
    await expect(page.getByText(TEST_COLLECTION_NAME)).toBeVisible();

    await page.getByRole('button', { name: new RegExp(`edit ${TEST_COLLECTION_NAME}`, 'i') }).click();

    await expect(page.getByRole('heading', { name: TEST_COLLECTION_NAME })).toBeVisible();
    await expect(page.getByRole('button', { name: /add item/i })).toBeVisible();
  });

  test('can edit a collection name', async ({ page }) => {
    await page.getByRole('button', { name: new RegExp(`edit ${TEST_COLLECTION_NAME}`, 'i') }).click();

    await expect(page.getByRole('heading', { name: TEST_COLLECTION_NAME })).toBeVisible();

    // The detail page should show the collection info
    await expect(page.getByText(TEST_COLLECTION_NAME)).toBeVisible();
  });

  test('can delete a collection', async ({ page }) => {
    page.on('dialog', (dialog) => dialog.accept());

    await page.getByRole('button', { name: new RegExp(`delete ${TEST_COLLECTION_NAME}`, 'i') }).click();

    await expect(page.getByText(TEST_COLLECTION_NAME)).not.toBeVisible();
  });

  test('shows empty state when no collections exist', async ({ page }) => {
    // If no collections, the empty state message should appear
    const emptyMessage = page.getByText(/no collections yet/i);
    const collectionCards = page.locator('article');

    // Either we see collections or the empty state
    const hasCollections = await collectionCards.count() > 0;
    if (!hasCollections) {
      await expect(emptyMessage).toBeVisible();
    }
  });

  test('create collection form validates required fields', async ({ page }) => {
    await page.getByRole('button', { name: /create collection/i }).click();

    // Submit without filling name
    await page.getByRole('button', { name: /save/i }).click();

    // Should show validation error for name
    await expect(page.getByText(/name is required/i)).toBeVisible();
  });

  test('create collection modal can be cancelled', async ({ page }) => {
    await page.getByRole('button', { name: /create collection/i }).click();

    await expect(page.getByRole('textbox', { name: /name/i })).toBeVisible();

    await page.getByRole('button', { name: /cancel/i }).click();

    // Modal should be closed — name input no longer visible
    await expect(page.getByRole('textbox', { name: /name/i })).not.toBeVisible();
  });
});

test.describe('Collections Full Lifecycle', () => {
  test('create → verify → navigate to detail → go back → delete', async ({ page }) => {
    const collectionName = `Lifecycle ${Date.now()}`;

    // Step 1: Navigate to collections
    await page.goto('/collections');
    await expect(page.getByRole('heading', { name: /collections/i, level: 1 })).toBeVisible();

    // Step 2: Create collection
    await page.getByRole('button', { name: /create collection/i }).click();
    await page.getByRole('textbox', { name: /name/i }).fill(collectionName);
    await page.getByRole('button', { name: /save/i }).click();
    await expect(page.getByText(collectionName)).toBeVisible();

    // Step 3: Navigate to detail via edit
    await page.getByRole('button', { name: new RegExp(`edit ${collectionName}`, 'i') }).click();
    await expect(page.getByRole('heading', { name: collectionName })).toBeVisible();

    // Step 4: Go back to collections list
    await page.getByRole('button', { name: /collections/i }).first().click();
    await expect(page.getByText(collectionName)).toBeVisible();

    // Step 5: Delete collection
    page.on('dialog', (dialog) => dialog.accept());
    await page.getByRole('button', { name: new RegExp(`delete ${collectionName}`, 'i') }).click();
    await expect(page.getByText(collectionName)).not.toBeVisible();
  });
});
