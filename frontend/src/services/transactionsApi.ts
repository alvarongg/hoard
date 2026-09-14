import { fetchApi, toSnakeCase } from "./api";
import type {
  Transaction,
  TransactionCreate,
  TransactionUpdate,
  ItemInvestment,
} from "../types/transaction";

export const transactionsApi = {
  list: (collectionItemId: string): Promise<Transaction[]> =>
    fetchApi<Transaction[]>(
      `/collection-items/${collectionItemId}/transactions`,
    ),

  create: (
    collectionItemId: string,
    data: TransactionCreate,
  ): Promise<Transaction> =>
    fetchApi<Transaction>(
      `/collection-items/${collectionItemId}/transactions`,
      { method: "POST", body: JSON.stringify(toSnakeCase(data)) },
    ),

  update: (id: string, data: TransactionUpdate): Promise<Transaction> =>
    fetchApi<Transaction>(`/transactions/${id}`, {
      method: "PUT",
      body: JSON.stringify(toSnakeCase(data)),
    }),

  remove: (id: string): Promise<ItemInvestment> =>
    fetchApi<ItemInvestment>(`/transactions/${id}`, { method: "DELETE" }),

  investment: (collectionItemId: string): Promise<ItemInvestment> =>
    fetchApi<ItemInvestment>(
      `/collection-items/${collectionItemId}/investment`,
    ),
};
