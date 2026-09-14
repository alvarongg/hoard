import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { OfflineBanner } from "./OfflineBanner";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) =>
      key === "offline.banner" ? "You are offline" : key,
  }),
}));

function setOnline(value: boolean) {
  Object.defineProperty(navigator, "onLine", {
    configurable: true,
    value,
  });
}

describe("OfflineBanner", () => {
  afterEach(() => setOnline(true));

  it("renders nothing when online", () => {
    setOnline(true);
    const { container } = render(<OfflineBanner />);
    expect(container).toBeEmptyDOMElement();
  });

  it("announces offline mode via aria-live status", () => {
    setOnline(false);
    render(<OfflineBanner />);
    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("You are offline");
    expect(status).toHaveAttribute("aria-live", "polite");
  });

  it("reacts to the online/offline events", () => {
    setOnline(true);
    render(<OfflineBanner />);
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    act(() => {
      setOnline(false);
      window.dispatchEvent(new Event("offline"));
    });
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("has no accessibility violations when offline", async () => {
    setOnline(false);
    const { container } = render(<OfflineBanner />);
    expect(await axe(container)).toHaveNoViolations();
  });
});
