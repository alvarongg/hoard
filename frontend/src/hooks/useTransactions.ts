import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { transactionsApi } from "../services/transactionsApi";
import type {
  Transaction,
  TransactionCreate,
  TransactionUpdate,
  ItemInvestment,
} from "../types/transaction";

const TRANSACTIONS_KEY = ["transactions"] as const;

export function useTransactions(collectionItemId: string | undefined) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    queryClient.invalidateQueries({
      queryKey: [...TRANSACTIONS_KEY, collectionItemId],
    });
    queryClient.invalidateQueries({
      queryKey: ["investment", collectionItemId],
    });
    queryClient.invalidateQueries({ queryKey: ["collection-stats"] });
  };

  const query = useQuery<Transaction[], Error>({
    queryKey: [...TRANSACTIONS_KEY, collectionItemId],
    queryFn: () => transactionsApi.list(collectionItemId!),
    enabled: !!collectionItemId,
  });

  const create = useMutation<Transaction, Error, TransactionCreate>({
    mutationFn: (data) => transactionsApi.create(collectionItemId!, data),
    onSuccess: invalidate,
  });

  const update = useMutation<
    Transaction,
    Error,
    { id: string; data: TransactionUpdate }
  >({
    mutationFn: ({ id, data }) => transactionsApi.update(id, data),
    onSuccess: invalidate,
  });

  const remove = useMutation<ItemInvestment, Error, string>({
    mutationFn: (id) => transactionsApi.remove(id),
    onSuccess: invalidate,
  });

  return { ...query, create, update, remove };
}

export function useItemInvestment(collectionItemId: string | undefined) {
  return useQuery<ItemInvestment, Error>({
    queryKey: ["investment", collectionItemId],
    queryFn: () => transactionsApi.investment(collectionItemId!),
    enabled: !!collectionItemId,
  });
}
