import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { SightingList } from "./SightingList";
import type { Sighting } from "../../types/wishlist";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "wishlist.sightings.empty": "No sightings yet. Add one to track prices.",
        "wishlist.sightings.condition": "Condition",
        "wishlist.sightings.viewListing": "View Listing",
        "wishlist.sightings.sighted": "Sighted",
        "wishlist.sightings.available": "Available",
        "wishlist.sightings.unavailable": "Unavailable",
        "wishlist.sightings.contacted": "Contacted",
        "wishlist.sightings.edit": "Edit sighting",
        "wishlist.sightings.delete": "Delete sighting",
        "wishlist.sightings.decision.buy": "Buy",
        "wishlist.sightings.decision.pass": "Pass",
        "wishlist.sightings.decision.wait": "Wait",
        "wishlist.sightings.decision.negotiate": "Negotiate",
        "common.edit": "Edit",
        "common.delete": "Delete",
      };
      return translations[key] ?? key;
    },
  }),
}));

const baseSighting: Sighting = {
  id: "1",
  wishlistItemId: "w1",
  price: 100,
  currency: "USD",
  sightedAt: "2024-01-15T10:00:00",
  condition: "Good",
  isAvailable: true,
  quantityAvailable: 1,
  contacted: false,
  createdAt: "2024-01-15T10:00:00",
  url: null,
  supplierId: null,
  locationDescription: null,
  isComplete: null,
  description: null,
  imageUrls: null,
  lastCheckedAt: null,
  contactedAt: null,
  contactMethod: null,
  responseNotes: null,
  decision: null,
  decisionNotes: null,
  decisionDate: null,
};

describe("SightingList", () => {
  it("renders empty state when no sightings", () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<SightingList sightings={[]} onEdit={onEdit} onDelete={onDelete} />);
    expect(screen.getByText(/no sightings yet/i)).toBeInTheDocument();
  });

  it("renders all sightings", () => {
    const sightings: Sighting[] = [
      { ...baseSighting, id: "1", price: 100 },
      { ...baseSighting, id: "2", price: 80 },
    ];
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<SightingList sightings={sightings} onEdit={onEdit} onDelete={onDelete} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });

  it("sorts sightings by date descending", () => {
    const sightings: Sighting[] = [
      { ...baseSighting, id: "1", price: 100, sightedAt: "2024-01-15T10:00:00" },
      { ...baseSighting, id: "2", price: 80, sightedAt: "2024-01-20T10:00:00" },
    ];
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<SightingList sightings={sightings} onEdit={onEdit} onDelete={onDelete} />);
    const items = screen.getAllByRole("listitem");
    // First item should be the more recent one (Jan 20)
    expect(items[0]).toHaveTextContent("$80.00");
  });

  it("renders price correctly", () => {
    const sightings: Sighting[] = [{ ...baseSighting, price: 100 }];
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<SightingList sightings={sightings} onEdit={onEdit} onDelete={onDelete} />);
    expect(screen.getByText("$100.00")).toBeInTheDocument();
  });

  it("renders availability badge", () => {
    const sightings: Sighting[] = [
      { ...baseSighting, isAvailable: true },
      { ...baseSighting, id: "2", isAvailable: false },
    ];
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<SightingList sightings={sightings} onEdit={onEdit} onDelete={onDelete} />);
    expect(screen.getByText("Available")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
  });

  it("renders contacted badge", () => {
    const sightings: Sighting[] = [{ ...baseSighting, contacted: true }];
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<SightingList sightings={sightings} onEdit={onEdit} onDelete={onDelete} />);
    expect(screen.getByText("Contacted")).toBeInTheDocument();
  });

  it("renders decision badge", () => {
    const sightings: Sighting[] = [{ ...baseSighting, decision: "buy" }];
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<SightingList sightings={sightings} onEdit={onEdit} onDelete={onDelete} />);
    expect(screen.getByText("Buy")).toBeInTheDocument();
  });

  it("calls onEdit when edit button clicked", async () => {
    const user = userEvent.setup();
    const sightings: Sighting[] = [{ ...baseSighting, id: "1" }];
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<SightingList sightings={sightings} onEdit={onEdit} onDelete={onDelete} />);

    await user.click(screen.getByRole("button", { name: /edit/i }));
    expect(onEdit).toHaveBeenCalledWith(sightings[0]);
  });

  it("calls onDelete when delete button clicked", async () => {
    const user = userEvent.setup();
    const sightings: Sighting[] = [{ ...baseSighting, id: "1" }];
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(<SightingList sightings={sightings} onEdit={onEdit} onDelete={onDelete} />);

    await user.click(screen.getByRole("button", { name: /delete/i }));
    expect(onDelete).toHaveBeenCalledWith("1");
  });
});
