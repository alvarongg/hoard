import { test, expect, type Page } from '@playwright/test';

/**
 * E2E tests for the Collections CRUD flow.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 *
 * The collection form defaults to the "single_category" type, which REQUIRES
 * a sub-category. To create a collection with only a name we switch the type
 * to "Multi Category" (no sub-category required) before saving.
 */

async function gotoCollections(page: Page) {
  await page.goto('/collections');
  await expect(
    page.getByRole('heading', { name: /collections/i, level: 1 }),
  ).toBeVisible();
}

/** Create a collection via the modal and wait for it to appear in the list. */
async function createCollection(page: Page, name: string) {
  await page.getByRole('button', { name: /create collection/i }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await dialog.getByLabel('Name').fill(name);
  // Multi Category needs no sub-category, so name alone is a valid submission.
  await dialog.getByLabel('Type').selectOption({ label: 'Multi Category' });
  await dialog.getByRole('button', { name: /save/i }).click();
  await expect(dialog).toBeHidden({ timeout: 8000 });
  await expect(page.getByRole('heading', { name })).toBeVisible();
}

async function deleteCollection(page: Page, name: string) {
  page.on('dialog', (d) => d.accept());
  await page
    .getByRole('button', { name: new RegExp(`delete ${name}`, 'i') })
    .click();
  await expect(page.getByRole('heading', { name })).toHaveCount(0);
}

test.describe('Collections CRUD Flow', () => {
  test.beforeEach(async ({ page }) => {
    await gotoCollections(page);
  });

  test('can create a new collection and see it in the list', async ({ page }) => {
    const name = `Create ${Date.now()}`;
    await createCollection(page, name);
    await deleteCollection(page, name);
  });

  test('can navigate to collection detail from the list', async ({ page }) => {
    const name = `Detail ${Date.now()}`;
    await createCollection(page, name);

    await page
      .getByRole('button', { name: new RegExp(`edit ${name}`, 'i') })
      .click();
    await expect(page.getByRole('heading', { name })).toBeVisible();
    await expect(page.getByRole('button', { name: /add item/i })).toBeVisible();

    await gotoCollections(page);
    await deleteCollection(page, name);
  });

  test('can open a collection detail page', async ({ page }) => {
    const name = `Edit ${Date.now()}`;
    await createCollection(page, name);

    await page
      .getByRole('button', { name: new RegExp(`edit ${name}`, 'i') })
      .click();
    await expect(page.getByRole('heading', { name })).toBeVisible();

    await gotoCollections(page);
    await deleteCollection(page, name);
  });

  test('can delete a collection', async ({ page }) => {
    const name = `Delete ${Date.now()}`;
    await createCollection(page, name);
    await deleteCollection(page, name);
  });

  test('create collection form validates required fields', async ({ page }) => {
    await page.getByRole('button', { name: /create collection/i }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Submit without filling name.
    await dialog.getByRole('button', { name: /save/i }).click();

    // Validation error for the name field is shown, modal stays open.
    await expect(page.getByText(/name is required/i)).toBeVisible();
  });

  test('create collection modal can be cancelled', async ({ page }) => {
    await page.getByRole('button', { name: /create collection/i }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    await dialog.getByRole('button', { name: /cancel/i }).click();
    await expect(dialog).toBeHidden();
  });
});

test.describe('Collections Full Lifecycle', () => {
  test('create → verify → navigate to detail → go back → delete', async ({ page }) => {
    const name = `Lifecycle ${Date.now()}`;

    await gotoCollections(page);
    await createCollection(page, name);

    await page
      .getByRole('button', { name: new RegExp(`edit ${name}`, 'i') })
      .click();
    await expect(page.getByRole('heading', { name })).toBeVisible();

    await gotoCollections(page);
    await expect(page.getByRole('heading', { name })).toBeVisible();

    await deleteCollection(page, name);
  });
});
