/**
 * Tests for useDebouncedValue hook.
 *
 * Requirements: 6.9, 19.2, 19.3
 */

import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import { useDebouncedValue } from "./useDebouncedValue";

describe("useDebouncedValue", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns initial value immediately", () => {
    const { result } = renderHook(() => useDebouncedValue("initial", 300));

    expect(result.current).toBe("initial");
  });

  it("debounces value changes", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebouncedValue(value, delay),
      { initialProps: { value: "initial", delay: 300 } },
    );

    expect(result.current).toBe("initial");

    // Change the value
    rerender({ value: "changed", delay: 300 });

    // Value should still be the old one immediately after change
    expect(result.current).toBe("initial");

    // Advance time by 150ms (not enough)
    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(result.current).toBe("initial");

    // Advance time by another 150ms (total 300ms)
    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(result.current).toBe("changed");
  });

  it("resets timer on rapid changes", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebouncedValue(value, delay),
      { initialProps: { value: "initial", delay: 300 } },
    );

    // First change
    rerender({ value: "first", delay: 300 });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe("initial");

    // Second change before timer completes
    rerender({ value: "second", delay: 300 });
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(result.current).toBe("initial");

    // Wait for timer to complete after last change
    act(() => {
      vi.advanceTimersByTime(100);
    });
    expect(result.current).toBe("second");
  });

  it("returns latest value after delay", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebouncedValue(value, delay),
      { initialProps: { value: "initial", delay: 500 } },
    );

    rerender({ value: "updated", delay: 500 });

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current).toBe("updated");
  });

  it("handles delay changes", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebouncedValue(value, delay),
      { initialProps: { value: "initial", delay: 300 } },
    );

    rerender({ value: "changed", delay: 100 });

    act(() => {
      vi.advanceTimersByTime(100);
    });

    expect(result.current).toBe("changed");
  });

  it("works with numeric values", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebouncedValue(value, delay),
      { initialProps: { value: 0, delay: 300 } },
    );

    rerender({ value: 42, delay: 300 });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current).toBe(42);
  });

  it("works with object values", () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebouncedValue(value, delay),
      { initialProps: { value: { name: "initial" }, delay: 300 } },
    );

    rerender({ value: { name: "updated" }, delay: 300 });

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(result.current).toEqual({ name: "updated" });
  });

  it("cleans up timer on unmount", () => {
    const { unmount } = renderHook(() => useDebouncedValue("test", 300));

    // Should not throw when unmounting
    expect(() => unmount()).not.toThrow();
  });
});
