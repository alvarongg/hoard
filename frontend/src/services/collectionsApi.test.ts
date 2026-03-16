import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { collectionsApi } from "./collectionsApi";
import { ApiError } from "./api";

const API_URL = "http://localhost:8000/api";

describe("collectionsApi", () => {
  describe("list", () => {
    it("returns array of collections with camelCase keys", async () => {
      const result = await collectionsApi.list();

      expect(Array.isArray(result)).toBe(true);
      expect(result.length).toBeGreaterThan(0);
      expect(result[0]).toHaveProperty("collectionType");
      expect(result[0]).toHaveProperty("isActive");
      expect(result[0]).toHaveProperty("createdAt");
    });

    it("passes skip and limit as query params", async () => {
      let capturedUrl = "";

      server.use(
        http.get(`${API_URL}/collections`, ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json([]);
        }),
      );

      await collectionsApi.list(10, 50);

      expect(capturedUrl).toContain("skip=10");
      expect(capturedUrl).toContain("limit=50");
    });
  });

  describe("getById", () => {
    it("returns a single collection with camelCase keys", async () => {
      const result = await collectionsApi.getById("col-1");

      expect(result.id).toBe("col-1");
      expect(result.collectionType).toBe("single_category");
      expect(result.name).toBe("My N64 Collection");
    });

    it("throws ApiError on 404", async () => {
      await expect(collectionsApi.getById("not-found")).rejects.toThrow(ApiError);
    });
  });

  describe("create", () => {
    it("sends POST with snake_case body and returns camelCase response", async () => {
      let capturedBody: Record<string, unknown> = {};

      server.use(
        http.post(`${API_URL}/collections`, async ({ request }) => {
          capturedBody = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json(
            {
              id: "new-col",
              name: capturedBody.name,
              collection_type: capturedBody.collection_type,
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
            { status: 201 },
          );
        }),
      );

      const result = await collectionsApi.create({
        name: "New Collection",
        collectionType: "multi_category",
      });

      expect(capturedBody.name).toBe("New Collection");
      expect(capturedBody.collection_type).toBe("multi_category");
      expect(result.collectionType).toBe("multi_category");
    });
  });

  describe("update", () => {
    it("sends PUT with snake_case body", async () => {
      let capturedBody: Record<string, unknown> = {};

      server.use(
        http.put(`${API_URL}/collections/:id`, async ({ request }) => {
          capturedBody = (await request.json()) as Record<string, unknown>;
          return HttpResponse.json({
            id: "col-1",
            name: capturedBody.name ?? "My N64 Collection",
            collection_type: "single_category",
            is_active: capturedBody.is_active ?? true,
            created_at: "2024-01-01T00:00:00Z",
            updated_at: "2024-01-02T00:00:00Z",
            description: null,
            theme: null,
            theme_description: null,
            restricted_to_sub_category_id: "sub-1",
            goal_description: null,
            goal_items_count: null,
            display_order: "custom",
            is_public: false,
          });
        }),
      );

      const result = await collectionsApi.update("col-1", {
        name: "Updated Name",
        isPublic: true,
      });

      expect(capturedBody.name).toBe("Updated Name");
      expect(capturedBody.is_public).toBe(true);
      expect(result.name).toBe("Updated Name");
    });
  });

  describe("delete", () => {
    it("sends DELETE and returns void", async () => {
      const result = await collectionsApi.delete("col-1");
      expect(result).toBeUndefined();
    });
  });
});
