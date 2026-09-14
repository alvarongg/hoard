import { describe, it, expect } from "vitest";
import fc from "fast-check";
import {
  createInstance,
  type i18n as I18nInstance,
  type ResourceKey,
} from "i18next";
import enTranslation from "../../../public/locales/en/translation.json";
import esTranslation from "../../../public/locales/es/translation.json";

/**
 * Locales soportados por la aplicación (ver src/i18n/config.ts).
 * Las traducciones se cargan en runtime vía i18next-http-backend, por lo que en
 * el test se importan los JSON directamente y se inyectan como `resources`.
 */
const LOCALE_RESOURCES: Record<string, ResourceKey> = {
  en: enTranslation,
  es: esTranslation,
};

const SUPPORTED_LOCALES = Object.keys(LOCALE_RESOURCES);

/**
 * Claves de traducción utilizadas por `InlineCatalogItemForm`.
 * Mantener sincronizado con el componente.
 */
const INLINE_FORM_KEYS = [
  "items.inline.createNew",
  "items.inline.title",
  "items.inline.titleRequired",
  "items.inline.titleWhitespace",
  "items.inline.showOptional",
  "items.inline.hideOptional",
  "items.inline.optionalFields",
  "items.inline.creating",
  "items.inline.createError",
  "items.inline.subtitle",
  "items.inline.description",
  "items.inline.manufacturer",
  "items.inline.publisher",
  "items.inline.developer",
  "items.inline.brand",
  "items.inline.language",
  "items.inline.region",
  "items.inline.rarity",
  "common.save",
  "common.cancel",
];

function createIsolatedInstance(locale: string): I18nInstance {
  const instance = createInstance();
  instance.init({
    lng: locale,
    // Sin fallback: cada locale debe resolver sus propias claves.
    fallbackLng: false,
    supportedLngs: SUPPORTED_LOCALES,
    defaultNS: "translation",
    ns: ["translation"],
    resources: {
      [locale]: { translation: LOCALE_RESOURCES[locale] as ResourceKey },
    },
    interpolation: { escapeValue: false },
  });
  return instance;
}

const instances = new Map<string, I18nInstance>(
  SUPPORTED_LOCALES.map((locale) => [locale, createIsolatedInstance(locale)]),
);

// Feature: inline-catalog-item-creation, Property 4: Completitud de traducciones i18n
describe("InlineCatalogItemForm i18n properties", () => {
  it("resolves every translation key to a non-empty string in every supported locale", () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...SUPPORTED_LOCALES),
        fc.constantFrom(...INLINE_FORM_KEYS),
        (locale, key) => {
          const instance = instances.get(locale)!;

          expect(instance.exists(key)).toBe(true);

          const value = instance.t(key);
          expect(typeof value).toBe("string");
          expect(value).not.toBe(key);
          expect(value.trim().length).toBeGreaterThan(0);
        },
      ),
      { numRuns: 100 },
    );
  });

  it("keeps the same key set defined across every supported locale", () => {
    fc.assert(
      fc.property(fc.constantFrom(...INLINE_FORM_KEYS), (key) => {
        const definedIn = SUPPORTED_LOCALES.filter((locale) =>
          instances.get(locale)!.exists(key),
        );
        expect(definedIn).toEqual(SUPPORTED_LOCALES);
      }),
      { numRuns: 100 },
    );
  });
});
