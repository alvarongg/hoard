import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const configSource = readFileSync(
  resolve(__dirname, "../../vite.config.ts"),
  "utf-8",
);

/**
 * Validates the PWA configuration shape declared in vite.config.ts.
 * This checks the config object, not Workbox behaviour itself.
 */
describe("PWA config", () => {
  it("registers the VitePWA plugin", () => {
    expect(configSource).toContain("VitePWA");
  });

  it("declares a manifest with the required fields", () => {
    for (const field of [
      "name",
      "short_name",
      "theme_color",
      "icons",
      '"standalone"',
    ]) {
      expect(configSource).toContain(field);
    }
    expect(configSource).toContain("HOARD");
  });

  it("declares runtime caching strategies per URL pattern", () => {
    expect(configSource).toContain("StaleWhileRevalidate");
    expect(configSource).toContain("NetworkFirst");
    expect(configSource).toContain("CacheFirst");
    expect(configSource).toContain("translation");
    expect(configSource).toContain("networkTimeoutSeconds");
  });

  it("declares the three PWA icon sizes", () => {
    expect(configSource).toContain("pwa-192x192.png");
    expect(configSource).toContain("pwa-512x512.png");
    expect(configSource).toContain("maskable");
  });
});
