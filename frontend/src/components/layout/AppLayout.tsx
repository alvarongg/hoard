import { Outlet, NavLink } from "react-router-dom";
import { LanguageSelector } from "./LanguageSelector";
import { Navigation } from "./Navigation";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <NavLink to="/" className="text-xl font-bold text-blue-600">
              H.O.A.R.D.
            </NavLink>
            <Navigation />
          </div>
          <LanguageSelector />
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
