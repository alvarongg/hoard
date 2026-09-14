import { http, HttpResponse } from "msw";

const API_URL = "http://localhost:8000/api";

const mockCollection = {
  id: "col-1",
  name: "My N64 Collection",
  description: "Nintendo 64 games",
  collection_type: "single_category",
  theme: null,
  theme_description: null,
  restricted_to_sub_category_id: "sub-1",
  goal_description: null,
  goal_items_count: null,
  display_order: "custom",
  is_public: false,
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockCollectionItem = {
  id: "item-1",
  collection_id: "col-1",
  catalog_item_id: "cat-item-1",
  condition: "excellent",
  is_complete: true,
  notes: null,
  purchase_price: 45.0,
  purchase_currency: "USD",
  purchase_date: null,
  acquisition_type: "purchase",
  storage_location: null,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockCatalog = {
  id: "catalog-1",
  sub_category_id: "sub-1",
  name: "N64 Games Catalog",
  description: "All N64 games",
  total_items: 296,
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockCatalogItem = {
  id: "cat-item-1",
  catalog_id: "catalog-1",
  title: "The Legend of Zelda: Ocarina of Time",
  subtitle: null,
  description: "Action-adventure game",
  release_date: "1998-11-21",
  manufacturer: "Nintendo",
  publisher: "Nintendo",
  developer: "Nintendo EAD",
  brand: "Nintendo",
  language: "en",
  region: "NTSC",
  rarity: "common",
  custom_fields: {},
  cover_image_url: null,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockMainCategory = {
  id: "main-1",
  name: "Video Games",
  description: "Video game collections",
  icon: "gamepad",
  display_order: 1,
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockSubCategory = {
  id: "sub-1",
  main_category_id: "main-1",
  name: "Nintendo 64",
  description: "N64 games and accessories",
  icon: null,
  display_order: 1,
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const mockImage = {
  id: "img-1",
  collection_item_id: "item-1",
  file_path: "/uploads/item-1/abc.jpg",
  file_name: "zelda_front.jpg",
  file_size: 102400,
  mime_type: "image/jpeg",
  image_type: "front",
  description: null,
  is_primary: true,
  uploaded_at: "2024-01-01T00:00:00Z",
};

const mockWishlistItem = {
  id: "wish-1",
  collection_id: "col-1",
  catalog_item_id: "cat-item-1",
  desired_condition: "excellent",
  desired_condition_min: null,
  must_be_complete: true,
  desired_completeness_description: null,
  max_price: 120.0,
  currency: "USD",
  specific_variant_required: false,
  variant_description: null,
  priority: 2,
  urgency: "high",
  notes: "Looking for a boxed copy",
  search_notes: null,
  tags: null,
  is_active: true,
  is_acquired: false,
  acquired_date: null,
  acquired_collection_item_id: null,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

export const handlers = [
  // Wishlist
  http.get(`${API_URL}/wishlist`, () => {
    return HttpResponse.json([mockWishlistItem]);
  }),

  http.get(`${API_URL}/wishlist/:id`, ({ params }) => {
    if (params.id === "not-found") {
      return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    }
    return HttpResponse.json({
      ...mockWishlistItem,
      price_aggregates: {
        avg_price: 100.0,
        min_price: 80.0,
        max_price: 120.0,
        total_sightings: 3,
        available_sightings: 2,
      },
    });
  }),

  http.post(`${API_URL}/wishlist`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockWishlistItem, ...body }, { status: 201 });
  }),

  http.put(`${API_URL}/wishlist/:id`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockWishlistItem, ...body });
  }),

  http.delete(`${API_URL}/wishlist/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Collections
  http.get(`${API_URL}/collections`, () => {
    return HttpResponse.json([mockCollection]);
  }),

  http.get(`${API_URL}/collections/:id`, ({ params }) => {
    if (params.id === "not-found") {
      return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    }
    return HttpResponse.json(mockCollection);
  }),

  http.post(`${API_URL}/collections`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockCollection, ...body },
      { status: 201 },
    );
  }),

  http.put(`${API_URL}/collections/:id`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockCollection, ...body });
  }),

  http.delete(`${API_URL}/collections/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Collection Items
  http.get(`${API_URL}/collections/:id/items`, () => {
    return HttpResponse.json([mockCollectionItem]);
  }),

  http.get(`${API_URL}/collections/:id/catalogs`, () => {
    return HttpResponse.json([mockCatalog]);
  }),

  http.post(`${API_URL}/collections/:id/items`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockCollectionItem, ...body },
      { status: 201 },
    );
  }),

  http.put(`${API_URL}/items/:id`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json({ ...mockCollectionItem, ...body });
  }),

  http.delete(`${API_URL}/items/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Catalogs
  http.get(`${API_URL}/catalogs`, () => {
    return HttpResponse.json([mockCatalog]);
  }),

  http.get(`${API_URL}/catalogs/:id`, () => {
    return HttpResponse.json(mockCatalog);
  }),

  http.post(`${API_URL}/catalogs`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockCatalog, ...body },
      { status: 201 },
    );
  }),

  http.get(`${API_URL}/catalogs/:id/items`, () => {
    return HttpResponse.json([mockCatalogItem]);
  }),

  http.get(`${API_URL}/catalog-items/search`, () => {
    return HttpResponse.json([mockCatalogItem]);
  }),

  // Categories
  http.get(`${API_URL}/categories`, () => {
    return HttpResponse.json([mockMainCategory]);
  }),

  http.post(`${API_URL}/categories`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockMainCategory, ...body },
      { status: 201 },
    );
  }),

  http.get(`${API_URL}/categories/:id/subcategories`, () => {
    return HttpResponse.json([mockSubCategory]);
  }),

  http.post(`${API_URL}/categories/:id/subcategories`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      { ...mockSubCategory, ...body },
      { status: 201 },
    );
  }),

  // Images
  http.get(`${API_URL}/items/:id/images`, () => {
    return HttpResponse.json([mockImage]);
  }),

  http.post(`${API_URL}/items/:id/images`, () => {
    return HttpResponse.json(mockImage, { status: 201 });
  }),

  http.delete(`${API_URL}/images/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Suppliers
  http.get(`${API_URL}/suppliers`, ({ request }) => {
    const url = new URL(request.url);
    const type = url.searchParams.get("type");
    const country = url.searchParams.get("country");
    const isFavorite = url.searchParams.get("is_favorite");

    let filtered = [...mockSuppliers];
    if (type) {
      filtered = filtered.filter((s) => s.type === type);
    }
    if (country) {
      filtered = filtered.filter((s) => s.country === country);
    }
    if (isFavorite === "true") {
      filtered = filtered.filter((s) => s.is_favorite === true);
    }

    return HttpResponse.json(filtered);
  }),

  http.get(`${API_URL}/suppliers/:id`, ({ params }) => {
    if (params.id === "not-found") {
      return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    }
    const supplier = mockSuppliers.find((s) => s.id === params.id);
    if (!supplier) {
      return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    }
    return HttpResponse.json(supplier);
  }),

  http.post(`${API_URL}/suppliers`, async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    const newSupplier = {
      ...mockSuppliers[0],
      id: `supplier-${Date.now()}`,
      ...body,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    return HttpResponse.json(newSupplier, { status: 201 });
  }),

  http.patch(`${API_URL}/suppliers/:id`, async ({ request, params }) => {
    const body = (await request.json()) as Record<string, unknown>;
    const supplier = mockSuppliers.find((s) => s.id === params.id);
    if (!supplier) {
      return HttpResponse.json({ detail: "Not found" }, { status: 404 });
    }
    // Return the updated supplier with the body changes applied
    const updated = { ...supplier, ...body, updated_at: new Date().toISOString() };
    return HttpResponse.json(updated);
  }),

  http.delete(`${API_URL}/suppliers/:id`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${API_URL}/suppliers/:id/purchases`, () => {
    return HttpResponse.json(mockSupplierPurchases);
  }),
];

const mockSupplierPurchases = [
  {
    id: "purchase-1",
    collection_item_id: "item-1",
    purchase_date: "2024-01-15",
    purchase_price: 45.0,
    purchase_currency: "USD",
  },
];

const mockSuppliers = [
  {
    id: "supplier-1",
    name: "GameStop",
    type: "store",
    country: "USA",
    state_province: "Texas",
    city: "Dallas",
    address: "123 Main St",
    postal_code: "75001",
    website: "https://gamestop.com",
    email: "contact@gamestop.com",
    phone: "+1-555-123-4567",
    marketplace_url: null,
    social_media: null,
    rating: 4.5,
    notes: "Local game store",
    is_favorite: true,
    is_active: true,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: "supplier-2",
    name: "eBay Seller",
    type: "marketplace",
    country: "USA",
    state_province: null,
    city: null,
    address: null,
    postal_code: null,
    website: null,
    email: null,
    phone: null,
    marketplace_url: "https://ebay.com/user/seller123",
    social_media: null,
    rating: 4.8,
    notes: "Reliable eBay seller",
    is_favorite: false,
    is_active: true,
    created_at: "2024-01-02T00:00:00Z",
    updated_at: "2024-01-02T00:00:00Z",
  },
];

export {
  mockCollection,
  mockCollectionItem,
  mockCatalog,
  mockCatalogItem,
  mockMainCategory,
  mockSubCategory,
  mockImage,
  mockSuppliers,
  mockSupplierPurchases,
  mockWishlistItem,
};
