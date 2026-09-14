import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { accessoriesApi } from "../services/accessoriesApi";
import type {
  Accessory,
  AccessoryCreate,
  AccessoryUpdate,
  LowStockEntry,
  ItemAccessoryAssignment,
} from "../types/accessory";

const ACCESSORIES_KEY = ["accessories"] as const;

export function useAccessories(category?: string) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ACCESSORIES_KEY });
    queryClient.invalidateQueries({ queryKey: ["accessories", "low-stock"] });
  };

  const query = useQuery<Accessory[], Error>({
    queryKey: [...ACCESSORIES_KEY, category],
    queryFn: () => accessoriesApi.list(category),
  });

  const create = useMutation<Accessory, Error, AccessoryCreate>({
    mutationFn: (data) => accessoriesApi.create(data),
    onSuccess: invalidate,
  });

  const update = useMutation<
    Accessory,
    Error,
    { id: string; data: AccessoryUpdate }
  >({
    mutationFn: ({ id, data }) => accessoriesApi.update(id, data),
    onSuccess: invalidate,
  });

  const remove = useMutation<void, Error, string>({
    mutationFn: (id) => accessoriesApi.remove(id),
    onSuccess: invalidate,
  });

  return { ...query, create, update, remove };
}

export function useLowStock() {
  return useQuery<LowStockEntry[], Error>({
    queryKey: ["accessories", "low-stock"],
    queryFn: () => accessoriesApi.lowStock(),
  });
}

export function useItemAccessories(collectionItemId: string | undefined) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({
      queryKey: ["item-accessories", collectionItemId],
    });
    queryClient.invalidateQueries({ queryKey: ACCESSORIES_KEY });
    queryClient.invalidateQueries({ queryKey: ["accessories", "low-stock"] });
  };

  const query = useQuery<ItemAccessoryAssignment[], Error>({
    queryKey: ["item-accessories", collectionItemId],
    queryFn: () => accessoriesApi.listAssignments(collectionItemId!),
    enabled: !!collectionItemId,
  });

  const assign = useMutation<
    ItemAccessoryAssignment,
    Error,
    { accessoryId: string; quantityUsed: number }
  >({
    mutationFn: ({ accessoryId, quantityUsed }) =>
      accessoriesApi.assign(collectionItemId!, accessoryId, quantityUsed),
    onSuccess: invalidate,
  });

  const unassign = useMutation<void, Error, string>({
    mutationFn: (id) => accessoriesApi.unassign(id),
    onSuccess: invalidate,
  });

  return { ...query, assign, unassign };
}
