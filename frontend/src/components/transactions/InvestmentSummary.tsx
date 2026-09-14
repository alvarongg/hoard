import { useTranslation } from "react-i18next";
import type { ItemInvestment } from "../../types/transaction";

interface InvestmentSummaryProps {
  investment: ItemInvestment;
}

/** InvestmentSummary - shows invested / ROI, with null ROI rendered as text. */
export function InvestmentSummary({ investment }: InvestmentSummaryProps) {
  const { t } = useTranslation();

  const rows: Array<{ label: string; value: string }> = [
    {
      label: t("transactions.investment.realInvested"),
      value: investment.realInvested,
    },
    {
      label: t("transactions.investment.totalOutflow"),
      value: investment.totalOutflow,
    },
    {
      label: t("transactions.investment.totalInflow"),
      value: investment.totalInflow,
    },
    {
      label: t("transactions.investment.roi"),
      value:
        investment.roiPercentage === null
          ? t("transactions.investment.roiUnavailable")
          : `${investment.roiPercentage}%`,
    },
  ];

  return (
    <section aria-labelledby="investment-heading">
      <h3
        id="investment-heading"
        className="mb-2 text-sm font-semibold text-gray-900 dark:text-white"
      >
        {t("transactions.investment.title")}
      </h3>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
        {rows.map((row) => (
          <div key={row.label} className="contents">
            <dt className="text-gray-500 dark:text-gray-400">{row.label}</dt>
            <dd className="text-right font-medium text-gray-900 dark:text-white">
              {row.value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
