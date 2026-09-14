import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { imagesApi } from "./imagesApi";

// Mock fetchApi
vi.mock("./api", () => ({
  fetchApi: vi.fn(),
}));

import { fetchApi } from "./api";

const mockFetchApi = vi.mocked(fetchApi);

describe("imagesApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe("list", () => {
    it("calls the correct endpoint", async () => {
      const mockImages = [
        { id: "img-1", collectionItemId: "item-1", filename: "test.jpg" },
      ];
      mockFetchApi.mockResolvedValueOnce(mockImages);

      const result = await imagesApi.list("item-1");

      expect(mockFetchApi).toHaveBeenCalledWith("/items/item-1/images");
      expect(result).toEqual(mockImages);
    });
  });

  describe("upload", () => {
    it("uploads a file with FormData", async () => {
      const mockImage = { id: "img-1", collectionItemId: "item-1", filename: "test.jpg" };
      mockFetchApi.mockResolvedValueOnce(mockImage);

      const file = new File(["test"], "test.jpg", { type: "image/jpeg" });
      const result = await imagesApi.upload("item-1", file);

      expect(mockFetchApi).toHaveBeenCalledWith(
        "/items/item-1/images",
        expect.objectContaining({
          method: "POST",
          body: expect.any(FormData),
        })
      );
      expect(result).toEqual(mockImage);
    });
  });

  describe("delete", () => {
    it("calls delete endpoint", async () => {
      mockFetchApi.mockResolvedValueOnce(undefined);

      await imagesApi.delete("img-1");

      expect(mockFetchApi).toHaveBeenCalledWith("/images/img-1", {
        method: "DELETE",
      });
    });
  });
});
