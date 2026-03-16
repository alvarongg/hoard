import { useTranslation } from "react-i18next";

type ButtonVariant = "primary" | "secondary" | "danger";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  isLoading?: boolean;
  children: React.ReactNode;
}

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",
  secondary: "bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-400",
  danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
};

export function Button({
  variant = "primary",
  isLoading = false,
  disabled,
  children,
  className = "",
  ...props
}: ButtonProps) {
  const { t } = useTranslation();
  const isDisabled = disabled || isLoading;

  return (
    <button
      className={`inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${className}`}
      disabled={isDisabled}
      aria-busy={isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <span className="mr-2 animate-spin" aria-hidden="true">⟳</span>
          {t("common.loading")}
        </>
      ) : (
        children
      )}
    </button>
  );
}
