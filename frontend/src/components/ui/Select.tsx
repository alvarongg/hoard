import { useId } from "react";

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "children"> {
  label: string;
  options: SelectOption[];
  placeholder?: string;
  error?: string;
}

export function Select({
  label,
  options,
  placeholder,
  error,
  className = "",
  id: externalId,
  ...props
}: SelectProps) {
  const generatedId = useId();
  const selectId = externalId ?? generatedId;
  const errorId = `${selectId}-error`;

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={selectId} className="text-sm font-medium text-gray-700">
        {label}
      </label>
      <select
        id={selectId}
        className={`rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? "border-red-500" : "border-gray-300"
        } ${className}`}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p id={errorId} className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
