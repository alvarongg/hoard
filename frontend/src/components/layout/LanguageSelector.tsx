import { useTranslation } from "react-i18next";

export function LanguageSelector() {
  const { i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <div role="group" aria-label="Language selector" className="flex gap-1">
      <button
        onClick={() => changeLanguage("es")}
        aria-pressed={i18n.language.startsWith("es")}
        className={`rounded px-2 py-1 text-sm ${
          i18n.language.startsWith("es")
            ? "bg-blue-600 text-white"
            : "bg-gray-200 text-gray-700 hover:bg-gray-300"
        }`}
      >
        ES
      </button>
      <button
        onClick={() => changeLanguage("en")}
        aria-pressed={i18n.language.startsWith("en")}
        className={`rounded px-2 py-1 text-sm ${
          i18n.language.startsWith("en")
            ? "bg-blue-600 text-white"
            : "bg-gray-200 text-gray-700 hover:bg-gray-300"
        }`}
      >
        EN
      </button>
    </div>
  );
}
