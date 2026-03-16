import { describe, it, expect } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import * as fc from "fast-check";
import { server } from "../test/mocks/server";
import { createWrapper } from "../test/hookWrapper";
import { useCollections } from "./useCollections";

const API_URL = "http://localhost:8000/api";

/**
 * **Validates: Requirements REQ-013**
 * Property 9: Mutually exclusive states — exactly one of {isLoading, isError, isSuccess} is true
 */
describe("Property 9: Mutually exclusive states", () => {
  it("exactly one of isLoading, isError, isSuccess is true after settling (success)", async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            id: fc.uuid(),
            name: fc.string({ minLength: 1, maxLength: 50 }),
            collection_type: fc.constantFrom("single_category", "multi_category", "mixed"),
            is_active: fc.boolean(),
            created_at: fc.constant("2024-01-01T00:00:00Z"),
            updated_at: fc.constant("2024-01-01T00:00:00Z"),
            description: fc.constant(null),
            theme: fc.constant(null),
            theme_description: fc.constant(null),
            restricted_to_sub_category_id: fc.constant(null),
            goal_description: fc.constant(null),
            goal_items_count: fc.constant(null),
            display_order: fc.constant("custom"),
            is_public: fc.constant(false),
          }),
          { minLength: 0, maxLength: 5 },
        ),
        async (collections) => {
          server.use(
            http.get(`${API_URL}/collections`, () =>
              HttpResponse.json(collections),
            ),
          );

          const { wrapper } = createWrapper();
          const { result } = renderHook(() => useCollections(), { wrapper });

          await waitFor(() => expect(result.current.isLoading).toBe(false));

          const states = [
            result.current.isLoading,
            result.current.isError,
            result.current.isSuccess,
          ];
          const trueCount = states.filter(Boolean).length;

          expect(trueCount).toBe(1);
        },
      ),
      { numRuns: 10 },
    );
  });

  it("exactly one of isLoading, isError, isSuccess is true after settling (error)", async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.constantFrom(400, 404, 422, 500),
        async (statusCode) => {
          server.use(
            http.get(`${API_URL}/collections`, () =>
              HttpResponse.json({ detail: "Error" }, { status: statusCode }),
            ),
          );

          const { wrapper } = createWrapper();
          const { result } = renderHook(() => useCollections(), { wrapper });

          await waitFor(() => expect(result.current.isLoading).toBe(false));

          const states = [
            result.current.isLoading,
            result.current.isError,
            result.current.isSuccess,
          ];
          const trueCount = states.filter(Boolean).length;

          expect(trueCount).toBe(1);
        },
      ),
      { numRuns: 4 },
    );
  });
});

/**
 * **Validates: Requirements REQ-013**
 * Property 12: Cache invalidation — ∀ successful mutation: corresponding query is invalidated
 */
describe("Property 12: Cache invalidation", () => {
  it("create mutation invalidates collections query", async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          name: fc.string({ minLength: 1, maxLength: 50 }),
          collectionType: fc.constantFrom("single_category", "multi_category", "mixed") as fc.Arbitrary<"single_category" | "multi_category" | "mixed">,
        }),
        async (createData) => {
          let fetchCount = 0;

          server.use(
            http.get(`${API_URL}/collections`, () => {
              fetchCount++;
              return HttpResponse.json([
                {
                  id: "col-1",
                  name: "Existing",
                  collection_type: "mixed",
                  is_active: true,
                  created_at: "2024-01-01T00:00:00Z",
                  updated_at: "2024-01-01T00:00:00Z",
                  description: null,
                  theme: null,
                  theme_description: null,
                  restricted_to_sub_category_id: null,
                  goal_description: null,
                  goal_items_count: null,
                  display_order: "custom",
                  is_public: false,
                },
              ]);
            }),
          );

          const { wrapper } = createWrapper();
          const { result } = renderHook(() => useCollections(), { wrapper });

          await waitFor(() => expect(result.current.isSuccess).toBe(true));

          const fetchCountBeforeMutation = fetchCount;

          await act(async () => {
            result.current.create.mutate(createData);
          });

          await waitFor(() =>
            expect(result.current.create.isSuccess).toBe(true),
          );

          // Cache should have been invalidated, triggering a refetch
          await waitFor(() => {
            expect(fetchCount).toBeGreaterThan(fetchCountBeforeMutation);
          });
        },
      ),
      { numRuns: 5 },
    );
  });
});
