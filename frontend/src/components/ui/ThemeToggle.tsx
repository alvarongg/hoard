import { useTranslation } from "react-i18next";
import { useTheme } from "../../theme";
import { useReducedMotion } from "../../hooks/useReducedMotion";
import { SunIcon } from "../icons/SunIcon";
import { MoonIcon } from "../icons/MoonIcon";
import { ComputerIcon } from "../icons/ComputerIcon";
import type { ThemePreference } from "../../theme/types";

/**
 * Theme toggle component with three options: light, dark, and auto.
 * Uses a radio group pattern for accessibility.
 */
export function ThemeToggle(): React.ReactNode {
  const { t } = useTranslation();
  const { preference, setPreference } = useTheme();
  const reducedMotion = useReducedMotion();

  const options: Array<{ value: ThemePreference; label: string; icon: React.ReactNode }> = [
    { value: "light", label: t("theme.light"), icon: <SunIcon className="h-4 w-4" aria-hidden /> },
    { value: "dark", label: t("theme.dark"), icon: <MoonIcon className="h-4 w-4" aria-hidden /> },
    { value: "auto", label: t("theme.auto"), icon: <ComputerIcon className="h-4 w-4" aria-hidden /> },
  ];

  const handleChange = (value: ThemePreference): void => {
    setPreference(value);
  };

  const handleKeyDown = (e: React.KeyboardEvent, currentIndex: number): void => {
    const nextIndex = {
      ArrowRight: (currentIndex + 1) % options.length,
      ArrowDown: (currentIndex + 1) % options.length,
      ArrowLeft: (currentIndex - 1 + options.length) % options.length,
      ArrowUp: (currentIndex - 1 + options.length) % options.length,
      Home: 0,
      End: options.length - 1,
    }[e.key];

    if (nextIndex === undefined) {
      return;
    }

    const nextOption = options[nextIndex];
    if (!nextOption) {
      return;
    }

    e.preventDefault();
    const button = e.currentTarget.parentElement?.querySelectorAll("button")[nextIndex];
    button?.focus();
    handleChange(nextOption.value);
  };

  return (
    <div
      role="radiogroup"
      aria-label={t("theme.label")}
      className="flex items-center gap-1 rounded-lg bg-surface-muted p-1"
    >
      {options.map((option, index) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={preference === option.value}
          aria-label={option.label}
          onClick={() => handleChange(option.value)}
          onKeyDown={(e) => handleKeyDown(e, index)}
          className={[
            "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors",
            "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2",
            reducedMotion ? "duration-0" : "duration-150",
            preference === option.value
              ? "bg-surface text-content shadow-sm"
              : "text-content-muted hover:text-content",
          ].join(" ")}
        >
          {option.icon}
          <span className="sr-only">{option.label}</span>
          <span aria-hidden="true">{option.label}</span>
        </button>
      ))}
    </div>
  );
}
