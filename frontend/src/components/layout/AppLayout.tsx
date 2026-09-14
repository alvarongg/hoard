import { Outlet, NavLink } from "react-router-dom";
import { LanguageSelector } from "./LanguageSelector";
import { Navigation } from "./Navigation";
import { SkipLink } from "../ui/SkipLink";
import { ThemeToggle } from "../ui/ThemeToggle";
import { AnnouncementProvider } from "../../hooks/useAnnouncement";

export function AppLayout() {
  return (
    <AnnouncementProvider>
      <div className="min-h-screen bg-surface">
        <SkipLink targetId="main-content" />
        <header className="border-b border-border bg-surface shadow-sm">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
            <div className="flex items-center gap-6">
              <NavLink to="/" className="text-xl font-bold text-accent">
                H.O.A.R.D.
              </NavLink>
              <Navigation />
            </div>
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <LanguageSelector />
            </div>
          </div>
        </header>
        <main id="main-content" className="mx-auto max-w-7xl px-4 py-6" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </AnnouncementProvider>
  );
}
