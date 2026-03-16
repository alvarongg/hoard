import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { ImageGallery } from "./ImageGallery";
import type { ItemImage } from "../../types/image";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "images.gallery": "Image Gallery",
        "images.primary": "Primary",
        "images.delete": "Delete Image",
        "images.empty": "No images yet",
        "ui.close": "Close",
        "ui.emptyTitle": "Nothing here yet",
        "ui.emptyDescription": "Get started by creating your first item",
      };
      return translations[key] ?? key;
    },
  }),
}));

const mockImages: ItemImage[] = [
  {
    id: "img-1",
    collectionItemId: "item-1",
    filePath: "/uploads/item-1/abc.jpg",
    fileName: "zelda_front.jpg",
    fileSize: 102400,
    mimeType: "image/jpeg",
    imageType: "front",
    description: "Front cover",
    isPrimary: true,
    uploadedAt: "2024-01-01T00:00:00Z",
  },
  {
    id: "img-2",
    collectionItemId: "item-1",
    filePath: "/uploads/item-1/def.jpg",
    fileName: "zelda_back.jpg",
    fileSize: 98000,
    mimeType: "image/jpeg",
    imageType: "back",
    description: null,
    isPrimary: false,
    uploadedAt: "2024-01-02T00:00:00Z",
  },
];

describe("ImageGallery", () => {
  it("renders grid of images", () => {
    render(<ImageGallery images={mockImages} />);
    const images = screen.getAllByRole("img");
    expect(images).toHaveLength(2);
  });

  it("renders image list with aria-label", () => {
    render(<ImageGallery images={mockImages} />);
    expect(
      screen.getByRole("list", { name: "Image Gallery" }),
    ).toBeInTheDocument();
  });

  it("shows primary badge on primary image", () => {
    render(<ImageGallery images={mockImages} />);
    expect(screen.getByText("Primary")).toBeInTheDocument();
  });

  it("renders empty state when no images", () => {
    render(<ImageGallery images={[]} />);
    expect(screen.getByText("No images yet")).toBeInTheDocument();
  });

  it("renders delete buttons when onDelete is provided", () => {
    render(<ImageGallery images={mockImages} onDelete={vi.fn()} />);
    const deleteButtons = screen.getAllByRole("button", {
      name: "Delete Image",
    });
    expect(deleteButtons).toHaveLength(2);
  });

  it("does not render delete buttons when onDelete is not provided", () => {
    render(<ImageGallery images={mockImages} />);
    expect(
      screen.queryByRole("button", { name: "Delete Image" }),
    ).not.toBeInTheDocument();
  });

  it("uses description as alt text when available", () => {
    render(<ImageGallery images={mockImages} />);
    expect(screen.getByAltText("Front cover")).toBeInTheDocument();
  });

  it("uses fileName as alt text when description is null", () => {
    render(<ImageGallery images={mockImages} />);
    expect(screen.getByAltText("zelda_back.jpg")).toBeInTheDocument();
  });

  it("has no accessibility violations with images", async () => {
    const { container } = render(
      <ImageGallery images={mockImages} onDelete={vi.fn()} />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it("has no accessibility violations when empty", async () => {
    const { container } = render(<ImageGallery images={[]} />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
