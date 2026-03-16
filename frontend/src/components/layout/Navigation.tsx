import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function Navigation() {
  const { t } = useTranslation();

  return (
    <nav aria-label={t("navigation.main")}>
      <ul className="flex gap-4">
        <li>
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.home")}
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/collections"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.collections")}
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/catalogs"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.catalogs")}
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}
