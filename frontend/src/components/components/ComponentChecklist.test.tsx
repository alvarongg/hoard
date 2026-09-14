/**
 * Tests for ComponentChecklist component.
 *
 * Verifies:
 * - Renders loading state
 * - Renders error state
 * - Renders empty state
 * - Renders component list with required/optional sections
 * - Accessibility with axe-core
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ComponentChecklist } from "./ComponentChecklist";
import type { ComponentTemplateEntry } from "../../types/itemComponent";
import { axe, toHaveNoViolations } from "jest-axe";

expect.extend(toHaveNoViolations);

// Mock i18next
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      const translations: Record<string, string> = {
        "components.title": "Components",
        "components.requiredComponents": "Required Components",
        "components.optionalComponents": "Optional Components",
        "components.template.empty": "No components defined for this category",
        "components.completenessAnnouncement.complete": "Item is now complete",
        "components.completenessAnnouncement.incomplete": `Item is incomplete. Missing: ${params?.missing}`,
        "errors.loadFailed": "Failed to load",
      };
      return translations[key] || key;
    },
  }),
}));

// Mock useAnnouncement
vi.mock("../../hooks/useAnnouncement", () => ({
  useAnnouncement: () => vi.fn(),
}));

// Mock hooks
const mockRefetch = vi.fn();
vi.mock("../../hooks/useItemComponents", () => ({
  useComponentTemplate: vi.fn(),
  useItemComponentMutations: () => ({
    upsert: { mutateAsync: vi.fn() },
    remove: { mutateAsync: vi.fn() },
  }),
}));

import { useComponentTemplate } from "../../hooks/useItemComponents";

const mockUseComponentTemplate = vi.mocked(useComponentTemplate);

describe("ComponentChecklist", () => {
  const mockTemplate: ComponentTemplateEntry[] = [
    {
      standardComponentId: "std-1",
      componentName: "Box",
      componentType: "required",
      description: "Original box",
      sortOrder: 0,
      isPresent: false,
      recordedComponentId: null,
    },
    {
      standardComponentId: "std-2",
      componentName: "Manual",
      componentType: "required",
      description: null,
      sortOrder: 1,
      isPresent: true,
      recordedComponentId: "comp-2",
    },
    {
      standardComponentId: "std-3",
      componentName: "Insert",
      componentType: "optional",
      description: "Promotional insert",
      sortOrder: 2,
      isPresent: false,
      recordedComponentId: null,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders loading state", () => {
      mockUseComponentTemplate.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof useComponentTemplate>);

      render(<ComponentChecklist collectionItemId="item-1" />);

      // LoadingSpinner has role="status"
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("renders error state", () => {
      mockUseComponentTemplate.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Failed to load"),
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof useComponentTemplate>);

      render(<ComponentChecklist collectionItemId="item-1" />);

      expect(screen.getByText("Failed to load")).toBeInTheDocument();
    });

    it("renders empty state when no template", () => {
      mockUseComponentTemplate.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof useComponentTemplate>);

      render(<ComponentChecklist collectionItemId="item-1" />);

      expect(screen.getByText("No components defined for this category")).toBeInTheDocument();
    });

    it("renders component list with required and optional sections", () => {
      mockUseComponentTemplate.mockReturnValue({
        data: mockTemplate,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof useComponentTemplate>);

      render(<ComponentChecklist collectionItemId="item-1" />);

      expect(screen.getByText("Required Components")).toBeInTheDocument();
      expect(screen.getByText("Optional Components")).toBeInTheDocument();
      expect(screen.getByText("Box")).toBeInTheDocument();
      expect(screen.getByText("Manual")).toBeInTheDocument();
      expect(screen.getByText("Insert")).toBeInTheDocument();
    });

    it("renders only required section when no optional components", () => {
      mockUseComponentTemplate.mockReturnValue({
        data: mockTemplate.filter((e) => e.componentType === "required"),
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof useComponentTemplate>);

      render(<ComponentChecklist collectionItemId="item-1" />);

      expect(screen.getByText("Required Components")).toBeInTheDocument();
      expect(screen.queryByText("Optional Components")).not.toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("has no accessibility violations", async () => {
      mockUseComponentTemplate.mockReturnValue({
        data: mockTemplate,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof useComponentTemplate>);

      const { container } = render(<ComponentChecklist collectionItemId="item-1" />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    it("has accessible section heading", () => {
      mockUseComponentTemplate.mockReturnValue({
        data: mockTemplate,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof useComponentTemplate>);

      render(<ComponentChecklist collectionItemId="item-1" />);

      // Screen reader only heading
      expect(screen.getByText("Components")).toBeInTheDocument();
    });

    it("has no accessibility violations in empty state", async () => {
      mockUseComponentTemplate.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      } as unknown as ReturnType<typeof useComponentTemplate>);

      const { container } = render(<ComponentChecklist collectionItemId="item-1" />);

      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });
});
