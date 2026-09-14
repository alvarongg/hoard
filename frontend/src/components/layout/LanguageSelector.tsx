import { useTranslation } from "react-i18next";
import { useReducedMotion } from "../../hooks/useReducedMotion";

const languages = [
  { code: "es", label: "Español" },
  { code: "en", label: "English" },
  { code: "pt", label: "Português" },
  { code: "fr", label: "Français" },
  { code: "de", label: "Deutsch" },
];

export function LanguageSelector() {
  const { i18n, t } = useTranslation();
  const reducedMotion = useReducedMotion();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  const isActive = (code: string) => i18n.language.startsWith(code);

  return (
    <div role="group" aria-label={t("languageSelector.label")} className="flex gap-1">
      {languages.map((lang) => (
        <button
          key={lang.code}
          onClick={() => changeLanguage(lang.code)}
          aria-pressed={isActive(lang.code)}
          aria-label={lang.label}
          className={[
            "rounded px-2 py-1 text-sm font-medium transition-colors",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2",
            reducedMotion ? "duration-0" : "duration-150",
            isActive(lang.code)
              ? "bg-accent text-white"
              : "bg-surface-muted text-content-muted hover:text-content hover:bg-surface-muted/80",
          ].join(" ")}
        >
          {lang.code.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
