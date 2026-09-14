/**
 * Tests for ComponentRow component.
 *
 * Verifies:
 * - Renders component with checkbox
 * - Toggles presence on click
 * - Keyboard navigation (Enter, Space)
 * - ARIA labels
 * - Accessibility with axe-core
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ComponentRow } from "./ComponentRow";
import type { ComponentTemplateEntry } from "../../types/itemComponent";
import { axe, toHaveNoViolations } from "jest-axe";

expect.extend(toHaveNoViolations);

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "components.present": `${params?.name} marked as present`,
        "components.absent": `${params?.name} marked as absent`,
        "components.toggleComponent": `Toggle ${params?.name}`,
        "components.required": "required",
        "components.hideDetails": "Hide details",
        "components.addDetails": "Add details",
        "components.condition": "Condition",
        "components.conditionNotes": "Notes",
      };
      return translations[key] || key;
    },
  }),
}));

// Mock useAnnouncement
vi.mock("../../hooks/useAnnouncement", () => ({
  useAnnouncement: () => vi.fn(),
}));

// Mock useItemComponentMutations
const mockUpsert = vi.fn();
const mockRemove = vi.fn();
vi.mock("../../hooks/useItemComponents", () => ({
  useItemComponentMutations: () => ({
    upsert: {
      mutateAsync: mockUpsert,
    },
    remove: {
      mutateAsync: mockRemove,
    },
  }),
}));

describe("ComponentRow", () => {
  const mockEntry: ComponentTemplateEntry = {
    standardComponentId: "std-1",
    componentName: "Box",
    componentType: "required",
    description: "Original box",
    sortOrder: 0,
    isPresent: false,
    recordedComponentId: null,
  };

  const mockOnCompletenessChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUpsert.mockResolvedValue({
      component: { id: "comp-1" },
      completeness: { isComplete: true, requiredCount: 1, presentCount: 1, missingNames: [] },
    });
    mockRemove.mockResolvedValue({
      isComplete: false,
      requiredCount: 1,
      presentCount: 0,
      missingNames: ["Box"],
    });
  });

  describe("rendering", () => {
    it("renders component name as label", () => {
      render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      expect(screen.getByText("Box")).toBeInTheDocument();
    });

    it("renders required badge for required components", () => {
      render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      expect(screen.getByText("(required)")).toBeInTheDocument();
    });

    it("renders description when provided", () => {
      render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      expect(screen.getByText("Original box")).toBeInTheDocument();
    });

    it("renders unchecked checkbox when not present", () => {
      render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      const checkbox = screen.getByRole("checkbox");
      expect(checkbox).not.toBeChecked();
    });

    it("renders checked checkbox when present", () => {
      const presentEntry = { ...mockEntry, isPresent: true, recordedComponentId: "comp-1" };
      render(
        <ComponentRow
          entry={presentEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      const checkbox = screen.getByRole("checkbox");
      expect(checkbox).toBeChecked();
    });
  });

  describe("interactions", () => {
    it("calls upsert when checking an unchecked component", async () => {
      const user = userEvent.setup();
      render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      await user.click(screen.getByRole("checkbox"));

      expect(mockUpsert).toHaveBeenCalledWith({
        standardComponentId: "std-1",
        componentName: "Box",
        componentType: "required",
        isPresent: true,
        condition: undefined,
        conditionNotes: undefined,
      });
    });

    it("calls remove when unchecking a checked component", async () => {
      const user = userEvent.setup();
      const presentEntry = { ...mockEntry, isPresent: true, recordedComponentId: "comp-1" };
      render(
        <ComponentRow
          entry={presentEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      await user.click(screen.getByRole("checkbox"));

      expect(mockRemove).toHaveBeenCalledWith("comp-1");
    });

    it("calls onCompletenessChange after toggle", async () => {
      const user = userEvent.setup();
      render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      await user.click(screen.getByRole("checkbox"));

      expect(mockOnCompletenessChange).toHaveBeenCalled();
    });

    it("toggles with keyboard Enter key", async () => {
      const user = userEvent.setup();
      render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      const checkbox = screen.getByRole("checkbox");
      checkbox.focus();
      await user.keyboard("{Enter}");

      expect(mockUpsert).toHaveBeenCalled();
    });

    it("toggles with keyboard Space key", async () => {
      const user = userEvent.setup();
      render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      const checkbox = screen.getByRole("checkbox");
      checkbox.focus();
      await user.keyboard(" ");

      expect(mockUpsert).toHaveBeenCalled();
    });
  });

  describe("accessibility", () => {
    it("has accessible checkbox label", () => {
      render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      expect(screen.getByLabelText("Toggle Box")).toBeInTheDocument();
    });

    it("has no accessibility violations", async () => {
      const { container } = render(
        <ComponentRow
          entry={mockEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("has no accessibility violations when present", async () => {
      const presentEntry = { ...mockEntry, isPresent: true, recordedComponentId: "comp-1" };
      const { container } = render(
        <ComponentRow
          entry={presentEntry}
          collectionItemId="item-1"
          onCompletenessChange={mockOnCompletenessChange}
        />
      );

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});
