import { Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createBrowserRouter,
  RouterProvider,
  type RouteObject,
} from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { HomePage } from "./pages/HomePage";
import { CollectionsPage } from "./pages/CollectionsPage";
import { CollectionDetailPage } from "./pages/CollectionDetailPage";
import { CatalogsPage } from "./pages/CatalogsPage";
import { CatalogDetailPage } from "./pages/CatalogDetailPage";
import { CatalogManagementPage } from "./pages/CatalogManagementPage";
import { SuppliersPage } from "./pages/SuppliersPage";
import { WishlistPage } from "./pages/WishlistPage";
import { WishlistDetailPage } from "./pages/WishlistDetailPage";
import { SearchPage } from "./pages/SearchPage";
import { StatsPage } from "./pages/StatsPage";
import { AccessoriesPage } from "./pages/AccessoriesPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

export const appRoutes: RouteObject[] = [
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "collections", element: <CollectionsPage /> },
      { path: "collections/:id", element: <CollectionDetailPage /> },
      { path: "catalogs", element: <CatalogsPage /> },
      { path: "catalogs/manage", element: <CatalogManagementPage /> },
      { path: "catalogs/:id", element: <CatalogDetailPage /> },
      { path: "suppliers", element: <SuppliersPage /> },
      { path: "wishlist", element: <WishlistPage /> },
      { path: "wishlist/:id", element: <WishlistDetailPage /> },
      { path: "search", element: <SearchPage /> },
      { path: "stats", element: <StatsPage /> },
      { path: "accessories", element: <AccessoriesPage /> },
    ],
  },
];

const router = createBrowserRouter(appRoutes);

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={<div role="status">Loading...</div>}>
        <RouterProvider router={router} />
      </Suspense>
    </QueryClientProvider>
  );
}
