import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { axe, toHaveNoViolations } from "jest-axe";
import { ImageUpload } from "./ImageUpload";

expect.extend(toHaveNoViolations);

vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        "images.upload": "Upload Image",
        "images.dropzone": "Drop images here or click to select",
        "images.invalidType": "Invalid file type. Allowed: JPEG, PNG, WebP",
        "images.tooLarge": "File is too large. Maximum size: 10MB",
        "images.preview": "Image preview",
        "common.loading": "Loading...",
      };
      return translations[key] ?? key;
    },
  }),
}));

function createMockFile(
  name: string,
  type: string,
  sizeBytes: number,
): File {
  const content = new Uint8Array(sizeBytes);
  return new File([content], name, { type });
}

describe("ImageUpload", () => {
  it("renders dropzone area", () => {
    render(<ImageUpload onUpload={vi.fn()} isLoading={false} />);
    expect(
      screen.getByText("Drop images here or click to select"),
    ).toBeInTheDocument();
  });

  it("renders dropzone button with aria-label", () => {
    render(<ImageUpload onUpload={vi.fn()} isLoading={false} />);
    expect(
      screen.getByRole("button", { name: "Drop images here or click to select" }),
    ).toBeInTheDocument();
  });

  it("validates invalid file type and shows error", async () => {
    render(<ImageUpload onUpload={vi.fn()} isLoading={false} />);

    const file = createMockFile("test.pdf", "application/pdf", 1024);
    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    // Use fireEvent directly since accept attribute blocks userEvent for invalid types
    fireEvent.change(input, { target: { files: [file] } });

    expect(
      await screen.findByText("Invalid file type. Allowed: JPEG, PNG, WebP"),
    ).toBeInTheDocument();
  });

  it("validates oversized file and shows error", async () => {
    render(<ImageUpload onUpload={vi.fn()} isLoading={false} />);

    // 11MB file
    const file = createMockFile(
      "big.jpg",
      "image/jpeg",
      11 * 1024 * 1024,
    );
    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    fireEvent.change(input, { target: { files: [file] } });

    expect(
      await screen.findByText("File is too large. Maximum size: 10MB"),
    ).toBeInTheDocument();
  });

  it("shows preview for valid image file", async () => {
    const user = userEvent.setup();
    render(<ImageUpload onUpload={vi.fn()} isLoading={false} />);

    const file = createMockFile("photo.jpg", "image/jpeg", 1024);
    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(input, file);

    // FileReader is async, wait for preview
    const preview = await screen.findByAltText("Image preview");
    expect(preview).toBeInTheDocument();
  });

  it("calls onUpload when upload button is clicked after selecting valid file", async () => {
    const onUpload = vi.fn();
    const user = userEvent.setup();
    render(<ImageUpload onUpload={onUpload} isLoading={false} />);

    const file = createMockFile("photo.png", "image/png", 2048);
    const input = document.querySelector(
      'input[type="file"]',
    ) as HTMLInputElement;

    await user.upload(input, file);

    // Wait for preview to appear (means file was accepted)
    await screen.findByAltText("Image preview");

    // Click the upload button (appears after file selection)
    const uploadButton = screen.getByRole("button", { name: "Upload Image" });
    await user.click(uploadButton);

    expect(onUpload).toHaveBeenCalledWith(file);
  });

  it("has no accessibility violations", async () => {
    const { container } = render(
      <ImageUpload onUpload={vi.fn()} isLoading={false} />,
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
