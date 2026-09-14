export type TransactionType =
  | "purchase"
  | "sale"
  | "trade_in"
  | "trade_out"
  | "gift_received"
  | "gift_given"
  | "grading_fee"
  | "repair"
  | "appraisal"
  | "other";

export interface Transaction {
  id: string;
  collectionItemId: string;
  transactionType: TransactionType;
  transactionDate: string;
  amount: string | null;
  currency: string;
  shippingCost: string | null;
  taxAmount: string | null;
  otherFees: string | null;
  readonly totalAmount: string;
  supplierId: string | null;
  counterpartName: string | null;
  invoiceNumber: string | null;
  receiptPath: string | null;
  paymentMethod: string | null;
  notes: string | null;
  createdAt: string;
}

export interface TransactionCreate {
  transactionType: TransactionType;
  transactionDate: string;
  amount?: string | null;
  currency?: string;
  shippingCost?: string | null;
  taxAmount?: string | null;
  otherFees?: string | null;
  supplierId?: string | null;
  counterpartName?: string | null;
  invoiceNumber?: string | null;
  paymentMethod?: string | null;
  notes?: string | null;
}

export type TransactionUpdate = Partial<TransactionCreate>;

export interface ItemInvestment {
  realInvested: string;
  totalOutflow: string;
  totalInflow: string;
  currentMarketValue: string | null;
  roiPercentage: string | null;
  source: string;
}
