import { describe, it, expect, beforeEach, vi } from "vitest";
import { readPreference, writePreference, clearPreference, STORAGE_KEY } from "./storage";

describe("theme storage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe("readPreference", () => {
    it("returns 'auto' when no preference is stored", () => {
      expect(readPreference()).toBe("auto");
    });

    it("returns 'light' when light is stored", () => {
      localStorage.setItem(STORAGE_KEY, "light");
      expect(readPreference()).toBe("light");
    });

    it("returns 'dark' when dark is stored", () => {
      localStorage.setItem(STORAGE_KEY, "dark");
      expect(readPreference()).toBe("dark");
    });

    it("returns 'auto' when auto is stored", () => {
      localStorage.setItem(STORAGE_KEY, "auto");
      expect(readPreference()).toBe("auto");
    });

    it("returns 'auto' for invalid stored values", () => {
      localStorage.setItem(STORAGE_KEY, "invalid");
      expect(readPreference()).toBe("auto");
    });

    it("returns 'auto' when localStorage throws", () => {
      const getItemSpy = vi.spyOn(Storage.prototype, "getItem");
      getItemSpy.mockImplementation(() => {
        throw new Error("localStorage not available");
      });

      expect(readPreference()).toBe("auto");
      getItemSpy.mockRestore();
    });
  });

  describe("writePreference", () => {
    it("writes preference to localStorage", () => {
      writePreference("dark");
      expect(localStorage.getItem(STORAGE_KEY)).toBe("dark");
    });

    it("does not throw when localStorage throws", () => {
      const setItemSpy = vi.spyOn(Storage.prototype, "setItem");
      setItemSpy.mockImplementation(() => {
        throw new Error("localStorage not available");
      });

      expect(() => writePreference("dark")).not.toThrow();
      setItemSpy.mockRestore();
    });
  });

  describe("clearPreference", () => {
    it("removes preference from localStorage", () => {
      localStorage.setItem(STORAGE_KEY, "dark");
      clearPreference();
      expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });

    it("does not throw when localStorage throws", () => {
      const removeItemSpy = vi.spyOn(Storage.prototype, "removeItem");
      removeItemSpy.mockImplementation(() => {
        throw new Error("localStorage not available");
      });

      expect(() => clearPreference()).not.toThrow();
      removeItemSpy.mockRestore();
    });
  });
});
