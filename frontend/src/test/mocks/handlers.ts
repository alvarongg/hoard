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

export const handlers = [
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
];

export {
  mockCollection,
  mockCollectionItem,
  mockCatalog,
  mockCatalogItem,
  mockMainCategory,
  mockSubCategory,
  mockImage,
};
