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
            end
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.catalogs")}
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/catalogs/manage"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.catalogManagement")}
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/suppliers"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.suppliers")}
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/wishlist"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.wishlist")}
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/search"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.search")}
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/stats"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.stats")}
          </NavLink>
        </li>
        <li>
          <NavLink
            to="/accessories"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-semibold text-blue-600" : "text-gray-600 hover:text-gray-900"}`
            }
          >
            {t("navigation.accessories")}
          </NavLink>
        </li>
      </ul>
    </nav>
  );
}
