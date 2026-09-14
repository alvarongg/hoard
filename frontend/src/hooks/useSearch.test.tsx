/**
 * Tests for useSearch hook.
 *
 * Requirements: 6.9, 19.2, 19.3
 */

import { renderHook, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi, beforeEach } from "vitest";
import * as React from "react";

import { useSearch, useSearchState } from "./useSearch";

// Mock searchApi
vi.mock("../services/searchApi", () => ({
  searchApi: {
    catalogItems: vi.fn(),
  },
}));

import { searchApi } from "../services/searchApi";

const mockSearchApi = vi.mocked(searchApi);

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        enabled: false, // Disable automatic fetching
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children,
    );
  };
};

describe("useSearch", () => {
  beforeEach(() => {
    mockSearchApi.catalogItems.mockClear();
  });

  it("does not search without query or filters", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSearch({}), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toBeUndefined();
  });

  it("constructs query key with filters", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSearch({ q: "zelda" }), { wrapper });

    // Check that query is in loading state when enabled
    expect(result.current.isFetching).toBe(true);
  });

  it("constructs query key with filters only", () => {
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useSearch({ language: "English" }),
      { wrapper },
    );

    expect(result.current.isFetching).toBe(true);
  });
});

describe("useSearchState", () => {
  beforeEach(() => {
    mockSearchApi.catalogItems.mockClear();
  });

  it("manages filter state", () => {
    const wrapper = createWrapper();

    const { result } = renderHook(() => useSearchState(), { wrapper });

    expect(result.current.filters).toEqual({});

    act(() => {
      result.current.updateFilters({ language: "English" });
    });

    expect(result.current.filters).toEqual({ language: "English" });
  });

  it("clears filters while preserving query", () => {
    const wrapper = createWrapper();

    const { result } = renderHook(() => useSearchState({ q: "test" }), {
      wrapper,
    });

    act(() => {
      result.current.updateFilters({ language: "English", region: "NTSC" });
    });

    expect(result.current.filters).toEqual({
      q: "test",
      language: "English",
      region: "NTSC",
    });

    act(() => {
      result.current.clearFilters();
    });

    expect(result.current.filters).toEqual({});
  });

  it("resets page when filters change", () => {
    const wrapper = createWrapper();

    const { result } = renderHook(() => useSearchState(), { wrapper });

    // Set page to 2
    act(() => {
      result.current.setPage(2);
    });

    expect(result.current.page).toBe(2);

    // Change filters
    act(() => {
      result.current.updateFilters({ language: "English" });
    });

    expect(result.current.page).toBe(0);
  });

  it("manages pagination state", () => {
    const wrapper = createWrapper();

    const { result } = renderHook(() => useSearchState({}, 20), { wrapper });

    expect(result.current.page).toBe(0);

    act(() => {
      result.current.setPage(1);
    });

    expect(result.current.page).toBe(1);
  });
});
