/**
 * Script to check i18n key parity across all 5 supported languages.
 * Ensures all languages have the same set of keys and no empty values.
 */
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const LOCALES_DIR = join(__dirname, "../public/locales");
const SUPPORTED_LANGUAGES = ["es", "en", "pt", "fr", "de"];

interface TranslationFile {
  [key: string]: string | TranslationFile;
}

function flattenKeys(obj: TranslationFile, prefix = ""): Set<string> {
  const keys = new Set<string>();

  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;

    if (typeof value === "object" && value !== null) {
      for (const subKey of flattenKeys(value, fullKey)) {
        keys.add(subKey);
      }
    } else {
      keys.add(fullKey);
    }
  }

  return keys;
}

function getEmptyKeys(obj: TranslationFile, prefix = ""): string[] {
  const emptyKeys: string[] = [];

  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;

    if (typeof value === "object" && value !== null) {
      emptyKeys.push(...getEmptyKeys(value, fullKey));
    } else if (value === "" || value === null || value === undefined) {
      emptyKeys.push(fullKey);
    }
  }

  return emptyKeys;
}

function main(): void {
  console.log("🔍 Checking i18n key parity across languages...\n");

  const translationsByLang: Map<string, TranslationFile> = new Map();
  const keysByLang: Map<string, Set<string>> = new Map();

  // Load all translation files
  for (const lang of SUPPORTED_LANGUAGES) {
    const filePath = join(LOCALES_DIR, lang, "translation.json");

    try {
      const content = readFileSync(filePath, "utf-8");
      const json = JSON.parse(content) as TranslationFile;
      translationsByLang.set(lang, json);
      keysByLang.set(lang, flattenKeys(json));
      console.log(`✅ Loaded ${lang}: ${keysByLang.get(lang)?.size} keys`);
    } catch (error) {
      console.error(`❌ Failed to load ${filePath}: ${error}`);
      process.exit(1);
    }
  }

  console.log("\n📋 Checking for missing and extra keys...\n");

  // Get union of all keys
  const allKeys = new Set<string>();
  for (const keys of keysByLang.values()) {
    for (const key of keys) {
      allKeys.add(key);
    }
  }

  let hasErrors = false;

  // Check each language for missing/extra keys
  for (const lang of SUPPORTED_LANGUAGES) {
    const langKeys = keysByLang.get(lang) ?? new Set();

    const missingKeys: string[] = [];
    const extraKeys: string[] = [];

    for (const key of allKeys) {
      if (!langKeys.has(key)) {
        missingKeys.push(key);
      }
    }

    for (const key of langKeys) {
      if (!allKeys.has(key) && !extraKeys.includes(key)) {
        extraKeys.push(key);
      }
    }

    if (missingKeys.length > 0) {
      console.error(`❌ ${lang}: Missing ${missingKeys.length} keys:`);
      for (const key of missingKeys.slice(0, 10)) {
        console.error(`   - ${key}`);
      }
      if (missingKeys.length > 10) {
        console.error(`   ... and ${missingKeys.length - 10} more`);
      }
      hasErrors = true;
    }

    if (extraKeys.length > 0) {
      console.error(`❌ ${lang}: Extra ${extraKeys.length} keys:`);
      for (const key of extraKeys.slice(0, 10)) {
        console.error(`   - ${key}`);
      }
      if (extraKeys.length > 10) {
        console.error(`   ... and ${extraKeys.length - 10} more`);
      }
      hasErrors = true;
    }
  }

  console.log("\n📋 Checking for empty values...\n");

  // Check for empty values
  for (const lang of SUPPORTED_LANGUAGES) {
    const translations = translationsByLang.get(lang);
    if (translations) {
      const emptyKeys = getEmptyKeys(translations);
      if (emptyKeys.length > 0) {
        console.error(`❌ ${lang}: ${emptyKeys.length} empty values:`);
        for (const key of emptyKeys.slice(0, 10)) {
          console.error(`   - ${key}`);
        }
        if (emptyKeys.length > 10) {
          console.error(`   ... and ${emptyKeys.length - 10} more`);
        }
        hasErrors = true;
      }
    }
  }

  if (!hasErrors) {
    console.log("✅ All languages have matching keys with non-empty values!\n");
    console.log(`   Total keys: ${allKeys.size}`);
    console.log(`   Languages: ${SUPPORTED_LANGUAGES.join(", ")}`);
    process.exit(0);
  } else {
    console.log("\n❌ i18n key parity check failed!");
    process.exit(1);
  }
}

main();
