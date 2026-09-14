import { useTranslation } from "react-i18next";
import { NavLink } from "react-router-dom";
import { ThemeToggle } from "../components/ui/ThemeToggle";
import { LanguageSelector } from "../components/layout/LanguageSelector";
import { OfficialCatalogList } from "../components/catalog/OfficialCatalogList";

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg border border-border p-4">
      <h2 className="text-lg font-semibold text-content">{title}</h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

export function SettingsPage() {
  const { t } = useTranslation();

  return (
    <main>
      <h1 className="text-2xl font-bold text-content">{t("settings.title")}</h1>
      <p className="mt-1 text-content-muted">{t("settings.subtitle")}</p>

      <div className="mt-6 grid gap-6">
        <Section title={t("settings.general")}>
          <div className="flex flex-col gap-4">
            <div>
              <p className="mb-1 text-sm font-medium text-content">
                {t("theme.label")}
              </p>
              <ThemeToggle />
            </div>
            <div>
              <p className="mb-1 text-sm font-medium text-content">
                {t("settings.language")}
              </p>
              <LanguageSelector />
            </div>
          </div>
        </Section>

        <Section title={t("settings.catalogs")}>
          <h3 className="text-sm font-semibold text-content">
            {t("catalogLibrary.title")}
          </h3>
          <p className="mb-3 text-sm text-content-muted">
            {t("catalogLibrary.description")}
          </p>
          <OfficialCatalogList />

          <div className="mt-4 flex flex-wrap gap-3 text-sm">
            <NavLink to="/catalogs/manage" className="text-accent underline">
              {t("settings.createCatalog")}
            </NavLink>
            <NavLink to="/settings/catalog-import" className="text-accent underline">
              {t("settings.importCatalog")}
            </NavLink>
          </div>
          <p className="mt-3 text-xs text-content-muted">
            {t("catalogLibrary.generateNote")}
          </p>
        </Section>

        <Section title={t("settings.data")}>
          <div className="flex flex-wrap gap-3 text-sm">
            <NavLink to="/import" className="text-accent underline">
              {t("navigation.import")}
            </NavLink>
            <NavLink to="/export" className="text-accent underline">
              {t("navigation.export")}
            </NavLink>
            <NavLink to="/settings/backups" className="text-accent underline">
              {t("navigation.backups")}
            </NavLink>
          </div>
        </Section>
      </div>
    </main>
  );
}
