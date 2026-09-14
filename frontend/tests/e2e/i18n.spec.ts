import { test, expect } from '@playwright/test';

/**
 * E2E tests for internationalization (i18n) — language switching ES ↔ EN.
 * Runs against the full Docker stack (backend + frontend + nginx + db).
 *
 * Verifies that the entire UI changes when switching languages.
 */

test.describe('i18n Language Switching', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for hydration: the language selector is part of the header shell.
    await expect(
      page.getByRole('group', { name: /language|idioma/i }),
    ).toBeVisible();
  });

  test('language selector is visible with ES and EN buttons', async ({ page }) => {
    const languageGroup = page.getByRole('group', { name: /language/i });
    await expect(languageGroup).toBeVisible();

    await expect(languageGroup.getByRole('button', { name: 'ES' })).toBeVisible();
    await expect(languageGroup.getByRole('button', { name: 'EN' })).toBeVisible();
  });

  test('switching to EN shows English navigation labels', async ({ page }) => {
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    const nav = page.getByRole('navigation', { name: /main navigation/i });
    await expect(nav.getByRole('link', { name: 'Home' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Collections' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Catalogs', exact: true })).toBeVisible();
  });

  test('switching to ES shows Spanish navigation labels', async ({ page }) => {
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'ES' }).click();

    const nav = page.getByRole('navigation', { name: /navegación principal/i });
    await expect(nav.getByRole('link', { name: 'Inicio' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Colecciones' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Catálogos', exact: true })).toBeVisible();
  });

  test('switching to EN shows English home page content', async ({ page }) => {
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    await expect(page.getByRole('heading', { name: /welcome to h\.o\.a\.r\.d\./i })).toBeVisible();
    await expect(page.getByText(/total collections/i)).toBeVisible();
    await expect(page.getByText(/total catalogs/i)).toBeVisible();
  });

  test('switching to ES shows Spanish home page content', async ({ page }) => {
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'ES' }).click();

    await expect(page.getByRole('heading', { name: /bienvenido a h\.o\.a\.r\.d\./i })).toBeVisible();
    await expect(page.getByText(/total de colecciones/i)).toBeVisible();
    await expect(page.getByText(/total de catálogos/i)).toBeVisible();
  });

  test('language switch persists when navigating to collections page', async ({ page }) => {
    // Switch to ES
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'ES' }).click();
    await expect(page.getByRole('heading', { name: /bienvenido/i })).toBeVisible();

    // Navigate to collections
    await page.goto('/collections');

    await expect(page.getByRole('heading', { name: 'Colecciones', level: 1 })).toBeVisible();
    await expect(page.getByRole('button', { name: /crear colección/i })).toBeVisible();
  });

  test('language switch persists when navigating to catalogs page', async ({ page }) => {
    // Switch to EN
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    await page.goto('/catalogs');

    await expect(page.getByRole('heading', { name: 'Catalogs' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /search items/i })).toBeVisible();
  });

  test('can toggle between ES and EN multiple times', async ({ page }) => {
    // Start with EN
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();
    await expect(page.getByRole('heading', { name: /welcome/i })).toBeVisible();

    // Switch to ES
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'ES' }).click();
    await expect(page.getByRole('heading', { name: /bienvenido/i })).toBeVisible();

    // Back to EN
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();
    await expect(page.getByRole('heading', { name: /welcome/i })).toBeVisible();
  });

  test('active language button has aria-pressed=true', async ({ page }) => {
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();

    await expect(page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' })).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'ES' })).toHaveAttribute('aria-pressed', 'false');

    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'ES' }).click();

    await expect(page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'ES' })).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' })).toHaveAttribute('aria-pressed', 'false');
  });

  test('collections page buttons change language', async ({ page }) => {
    await page.goto('/collections');

    // EN
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'EN' }).click();
    await expect(page.getByRole('button', { name: /create collection/i })).toBeVisible();

    // ES
    await page.getByRole('group', { name: /language|idioma/i }).getByRole('button', { name: 'ES' }).click();
    await expect(page.getByRole('button', { name: /crear colección/i })).toBeVisible();
  });
});
