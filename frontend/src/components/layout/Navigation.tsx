import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

const linkClass = ({ isActive }: { isActive: boolean }): string =>
  `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`;

export function Navigation() {
  const { t } = useTranslation();

  return (
    <nav aria-label={t("navigation.main")}>
      <ul className="flex gap-4">
        <li>
          <NavLink to="/" end className={linkClass}>
            {t("navigation.home")}
          </NavLink>
        </li>
        <li>
          <NavLink to="/collections" className={linkClass}>
            {t("navigation.collections")}
          </NavLink>
        </li>
        <li>
          <NavLink to="/catalogs" end className={linkClass}>
            {t("navigation.catalogs")}
          </NavLink>
        </li>
        <li>
          <NavLink to="/wishlist" className={linkClass}>
            {t("navigation.wishlist")}
          </NavLink>
        </li>
        <li>
          <NavLink to="/search" className={linkClass}>
            {t("navigation.search")}
          </NavLink>
        </li>
        <li>
          <NavLink to="/stats" className={linkClass}>
            {t("navigation.stats")}
          </NavLink>
        </li>
        <li>
          <NavLink to="/accessories" className={linkClass}>
            {t("navigation.accessories")}
          </NavLink>
        </li>
        <li>
          <NavLink to="/settings" className={linkClass}>
            {t("navigation.settings")}
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}
