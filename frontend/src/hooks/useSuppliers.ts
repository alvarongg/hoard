import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { suppliersApi } from "../services/suppliersApi";
import type {
  Supplier,
  SupplierCreate,
  SupplierUpdate,
  SupplierPurchase,
} from "../types/supplier";
import type { SupplierFilters } from "../services/suppliersApi";

const SUPPLIERS_KEY = ["suppliers"] as const;

export function useSuppliers(filters?: SupplierFilters) {
  const queryClient = useQueryClient();

  const query = useQuery<Supplier[], Error>({
    queryKey: filters ? [...SUPPLIERS_KEY, filters] : SUPPLIERS_KEY,
    queryFn: () => suppliersApi.list(filters),
  });

  const create = useMutation<Supplier, Error, SupplierCreate>({
    mutationFn: (data) => suppliersApi.create(data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: SUPPLIERS_KEY }),
  });

  const update = useMutation<
    Supplier,
    Error,
    { id: string; data: SupplierUpdate }
  >({
    mutationFn: ({ id, data }) => suppliersApi.update(id, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: SUPPLIERS_KEY }),
  });

  const remove = useMutation<void, Error, string>({
    mutationFn: (id) => suppliersApi.remove(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: SUPPLIERS_KEY }),
  });

  const toggleFavorite = useMutation<Supplier, Error, { id: string; currentFavorite: boolean }, { previousSuppliers: Supplier[] | undefined }>({
    mutationFn: ({ id, currentFavorite }) =>
      suppliersApi.update(id, { isFavorite: !currentFavorite }),
    onMutate: async ({ id, currentFavorite }) => {
      await queryClient.cancelQueries({ queryKey: SUPPLIERS_KEY });

      const previousSuppliers = queryClient.getQueryData<Supplier[]>(SUPPLIERS_KEY);

      if (previousSuppliers) {
        queryClient.setQueryData<Supplier[]>(
          SUPPLIERS_KEY,
          previousSuppliers.map((supplier) =>
            supplier.id === id
              ? { ...supplier, isFavorite: !currentFavorite }
              : supplier
          )
        );
      }

      return { previousSuppliers };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousSuppliers) {
        queryClient.setQueryData<Supplier[]>(SUPPLIERS_KEY, context.previousSuppliers);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: SUPPLIERS_KEY });
    },
  });

  return { ...query, create, update, remove, toggleFavorite };
}

export function useSupplier(id: string | undefined) {
  return useQuery<Supplier, Error>({
    queryKey: [...SUPPLIERS_KEY, id],
    queryFn: () => suppliersApi.get(id!),
    enabled: !!id,
  });
}

export function useSupplierPurchases(id: string | undefined) {
  return useQuery<SupplierPurchase[], Error>({
    queryKey: [...SUPPLIERS_KEY, id, "purchases"],
    queryFn: () => suppliersApi.purchases(id!),
    enabled: !!id,
  });
}
