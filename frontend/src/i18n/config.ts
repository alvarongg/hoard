import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import HttpBackend from "i18next-http-backend";

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: "en",
    supportedLngs: ["es", "en", "pt", "fr", "de"],
    debug: false,
    interpolation: {
      escapeValue: false,
    },
    backend: {
      loadPath: "/locales/{{lng}}/{{ns}}.json",
    },
    detection: {
      order: ["localStorage", "navigator", "htmlTag"],
      caches: ["localStorage"],
    },
  });

// Update document language when i18n language changes
i18n.on("languageChanged", (lng) => {
  document.documentElement.lang = lng;
});

// Set initial language on document
if (typeof document !== "undefined") {
  document.documentElement.lang = i18n.language || "en";
}

export { i18n };
