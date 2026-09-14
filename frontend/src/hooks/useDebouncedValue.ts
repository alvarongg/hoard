/**
 * Hook for debouncing a value.
 *
 * Returns a debounced version of the input value that only updates
 * after the specified delay has passed without the value changing.
 *
 * Requirements: 6.9
 */

import { useEffect, useState } from "react";

/**
 * Debounce a value by the specified delay.
 *
 * @param value - The value to debounce
 * @param delayMs - The debounce delay in milliseconds
 * @returns The debounced value
 */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delayMs);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delayMs]);

  return debouncedValue;
}
