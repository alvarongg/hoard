import { Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  createBrowserRouter,
  RouterProvider,
} from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import { HomePage } from "./pages/HomePage";
import { CollectionsPage } from "./pages/CollectionsPage";
import { CollectionDetailPage } from "./pages/CollectionDetailPage";
import { CatalogsPage } from "./pages/CatalogsPage";
import { CatalogDetailPage } from "./pages/CatalogDetailPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "collections", element: <CollectionsPage /> },
      { path: "collections/:id", element: <CollectionDetailPage /> },
      { path: "catalogs", element: <CatalogsPage /> },
      { path: "catalogs/:id", element: <CatalogDetailPage /> },
    ],
  },
]);

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={<div role="status">Loading...</div>}>
        <RouterProvider router={router} />
      </Suspense>
    </QueryClientProvider>
  );
}
