import { readFileSync } from "fs";
import { resolve } from "path";
import { describe, it, expect } from "vitest";
import * as fc from "fast-check";

/**
 * **Validates: Requirements REQ-014.1, REQ-014.2**
 * Property 11: i18n completo — ∀ string visible: proviene de t() y existe en es/ y en/
 *
 * Verifies structural completeness of translation files:
 * - Every key in EN exists in ES and vice versa
 * - No empty string values in either locale
 * - Random key paths resolve to non-empty strings in both locales
 */

type TranslationObject = Record<string, unknown>;

function loadTranslations(locale: string): TranslationObject {
  const filePath = resolve(__dirname, `../../public/locales/${locale}/translation.json`);
  const content = readFileSync(filePath, "utf-8");
  return JSON.parse(content) as TranslationObject;
}

function flattenKeys(obj: TranslationObject, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([key, value]) => {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (typeof value === "object" && value !== null && !Array.isArray(value)) {
      return flattenKeys(value as TranslationObject, fullKey);
    }
    return [fullKey];
  });
}

function getNestedValue(obj: TranslationObject, keyPath: string): unknown {
  return keyPath.split(".").reduce<unknown>((current, segment) => {
    if (typeof current === "object" && current !== null) {
      return (current as TranslationObject)[segment];
    }
    return undefined;
  }, obj);
}

describe("Property 11: i18n completeness", () => {
  const en = loadTranslations("en");
  const es = loadTranslations("es");
  const enKeys = flattenKeys(en);
  const esKeys = flattenKeys(es);

  it("every EN key exists in ES", () => {
    const esKeySet = new Set(esKeys);
    for (const key of enKeys) {
      expect(esKeySet.has(key), `Missing ES translation for: ${key}`).toBe(true);
    }
  });

  it("every ES key exists in EN", () => {
    const enKeySet = new Set(enKeys);
    for (const key of esKeys) {
      expect(enKeySet.has(key), `Missing EN translation for: ${key}`).toBe(true);
    }
  });

  it("no translation value is empty in either locale", () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...enKeys),
        (key) => {
          const enValue = getNestedValue(en, key);
          const esValue = getNestedValue(es, key);
          return (
            typeof enValue === "string" &&
            enValue.length > 0 &&
            typeof esValue === "string" &&
            esValue.length > 0
          );
        },
      ),
      { numRuns: enKeys.length },
    );
  });

  it("both locales have the same number of keys", () => {
    expect(enKeys.length).toBe(esKeys.length);
  });

  it("random key subsets exist in both locales", () => {
    fc.assert(
      fc.property(
        fc.constantFrom(...enKeys),
        (key) => {
          const enValue = getNestedValue(en, key);
          const esValue = getNestedValue(es, key);
          return enValue !== undefined && esValue !== undefined;
        },
      ),
      { numRuns: Math.min(enKeys.length, 100) },
    );
  });
});
