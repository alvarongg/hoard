const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly statusText: string,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

interface ApiErrorBody {
  detail?: string;
}

function isApiErrorBody(value: unknown): value is ApiErrorBody {
  return (
    typeof value === "object" &&
    value !== null &&
    ("detail" in value ? typeof (value as ApiErrorBody).detail === "string" : true)
  );
}

function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase());
}

function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

export function transformKeys<T>(
  obj: unknown,
  transformer: (key: string) => string,
): T {
  if (Array.isArray(obj)) {
    return obj.map((item) => transformKeys(item, transformer)) as T;
  }
  if (obj !== null && typeof obj === "object" && !(obj instanceof Date)) {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj)) {
      result[transformer(key)] = transformKeys(value, transformer);
    }
    return result as T;
  }
  return obj as T;
}

export function toCamelCase<T>(obj: unknown): T {
  return transformKeys<T>(obj, snakeToCamel);
}

export function toSnakeCase<T>(obj: unknown): T {
  return transformKeys<T>(obj, camelToSnake);
}

export async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: HeadersInit = {
    ...options.headers,
  };

  if (!(options.body instanceof FormData)) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body: unknown = await response.json();
      if (isApiErrorBody(body) && body.detail) {
        detail = body.detail;
      }
    } catch {
      // Use statusText as fallback
    }
    throw new ApiError(response.status, response.statusText, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const data: unknown = await response.json();
  return toCamelCase<T>(data);
}
