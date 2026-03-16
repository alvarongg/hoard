import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../test/mocks/server";
import { fetchApi, ApiError, toCamelCase, toSnakeCase } from "./api";

const API_URL = "http://localhost:8000/api";

describe("fetchApi", () => {
  it("returns parsed JSON with camelCase keys on 200", async () => {
    server.use(
      http.get(`${API_URL}/test`, () => {
        return HttpResponse.json({ some_key: "value", nested_obj: { inner_key: 1 } });
      }),
    );

    const result = await fetchApi<{ someKey: string; nestedObj: { innerKey: number } }>(
      "/test",
    );

    expect(result.someKey).toBe("value");
    expect(result.nestedObj.innerKey).toBe(1);
  });

  it("returns undefined on 204 No Content", async () => {
    server.use(
      http.delete(`${API_URL}/test/1`, () => {
        return new HttpResponse(null, { status: 204 });
      }),
    );

    const result = await fetchApi<void>("/test/1", { method: "DELETE" });
    expect(result).toBeUndefined();
  });

  it("throws ApiError with detail on 404", async () => {
    server.use(
      http.get(`${API_URL}/test/missing`, () => {
        return HttpResponse.json({ detail: "Not found" }, { status: 404 });
      }),
    );

    await expect(fetchApi("/test/missing")).rejects.toThrow(ApiError);

    try {
      await fetchApi("/test/missing");
    } catch (error) {
      const apiError = error as ApiError;
      expect(apiError.status).toBe(404);
      expect(apiError.detail).toBe("Not found");
    }
  });

  it("throws ApiError with detail on 422 validation error", async () => {
    server.use(
      http.post(`${API_URL}/test`, () => {
        return HttpResponse.json(
          { detail: "Validation failed" },
          { status: 422 },
        );
      }),
    );

    await expect(
      fetchApi("/test", { method: "POST", body: JSON.stringify({}) }),
    ).rejects.toThrow(ApiError);

    try {
      await fetchApi("/test", { method: "POST", body: JSON.stringify({}) });
    } catch (error) {
      const apiError = error as ApiError;
      expect(apiError.status).toBe(422);
      expect(apiError.detail).toBe("Validation failed");
    }
  });

  it("throws ApiError on 500 server error", async () => {
    server.use(
      http.get(`${API_URL}/test/error`, () => {
        return HttpResponse.json(
          { detail: "Internal server error" },
          { status: 500 },
        );
      }),
    );

    await expect(fetchApi("/test/error")).rejects.toThrow(ApiError);

    try {
      await fetchApi("/test/error");
    } catch (error) {
      const apiError = error as ApiError;
      expect(apiError.status).toBe(500);
      expect(apiError.detail).toBe("Internal server error");
    }
  });

  it("sets Content-Type to application/json for non-FormData bodies", async () => {
    let capturedContentType: string | null = null;

    server.use(
      http.post(`${API_URL}/test`, async ({ request }) => {
        capturedContentType = request.headers.get("Content-Type");
        return HttpResponse.json({ id: "1" }, { status: 201 });
      }),
    );

    await fetchApi("/test", {
      method: "POST",
      body: JSON.stringify({ name: "test" }),
    });

    expect(capturedContentType).toBe("application/json");
  });

  it("does not set Content-Type for FormData bodies", async () => {
    let capturedContentType: string | null = null;

    server.use(
      http.post(`${API_URL}/test/upload`, async ({ request }) => {
        capturedContentType = request.headers.get("Content-Type");
        return HttpResponse.json({ id: "1" }, { status: 201 });
      }),
    );

    const formData = new FormData();
    formData.append("file", new Blob(["test"]), "test.txt");

    await fetchApi("/test/upload", {
      method: "POST",
      body: formData,
    });

    expect(capturedContentType).toContain("multipart/form-data");
  });
});

describe("toCamelCase", () => {
  it("converts snake_case keys to camelCase", () => {
    const input = { some_key: "value", another_key: 42 };
    const result = toCamelCase<{ someKey: string; anotherKey: number }>(input);
    expect(result).toEqual({ someKey: "value", anotherKey: 42 });
  });

  it("converts nested objects recursively", () => {
    const input = { outer_key: { inner_key: "value" } };
    const result = toCamelCase<{ outerKey: { innerKey: string } }>(input);
    expect(result).toEqual({ outerKey: { innerKey: "value" } });
  });

  it("converts arrays of objects", () => {
    const input = [{ some_key: 1 }, { some_key: 2 }];
    const result = toCamelCase<Array<{ someKey: number }>>(input);
    expect(result).toEqual([{ someKey: 1 }, { someKey: 2 }]);
  });

  it("returns primitives unchanged", () => {
    expect(toCamelCase<string>("hello")).toBe("hello");
    expect(toCamelCase<number>(42)).toBe(42);
    expect(toCamelCase<null>(null)).toBeNull();
  });
});

describe("toSnakeCase", () => {
  it("converts camelCase keys to snake_case", () => {
    const input = { someKey: "value", anotherKey: 42 };
    const result = toSnakeCase<{ some_key: string; another_key: number }>(input);
    expect(result).toEqual({ some_key: "value", another_key: 42 });
  });

  it("converts nested objects recursively", () => {
    const input = { outerKey: { innerKey: "value" } };
    const result = toSnakeCase<{ outer_key: { inner_key: string } }>(input);
    expect(result).toEqual({ outer_key: { inner_key: "value" } });
  });
});
