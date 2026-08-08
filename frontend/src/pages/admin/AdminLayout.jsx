import { NavLink, Outlet, useNavigate, Navigate, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { adminMe } from "../../lib/api";
import { portalNavLinkClass, NavActiveLabel } from "../../lib/navActive";
import { ADMIN_NAV } from "../../components/admin/adminNavItems";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { SECTION_LOGO, SECTION_LOGO_CLASS } from "../../lib/brand";
import { LogOut, Menu } from "lucide-react";

export default function AdminLayout() {
  const navigate = useNavigate();
  const [admin, setAdmin] = useState(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    adminMe().then(setAdmin).catch(() => {
      localStorage.removeItem("aia_token");
      navigate(R.login);
    });
  }, [navigate]);

  if (!localStorage.getItem("aia_token")) {
    return <Navigate to={R.login} replace />;
  }

  const logout = () => {
    localStorage.removeItem("aia_token");
    localStorage.removeItem("aia_admin");
    navigate(R.login);
  };

  return (
    <div className="app-canvas min-h-screen flex">
      <aside
        className={`fixed lg:sticky top-0 left-0 h-screen w-72 max-w-[85vw] bg-navy-700 text-white flex flex-col z-40 transform ${
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        } transition-transform`}
      >
        <div className="p-6 border-b border-white/10">
          <Link to={R.dashboard} className="flex items-center gap-3" onClick={() => setOpen(false)}>
            <img src={SECTION_LOGO} alt="AIA Legnano" className={SECTION_LOGO_CLASS.md} />
            <div>
              <div className="font-display font-bold text-lg leading-tight">AIA Legnano</div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-gold-400">Amministrazione</div>
            </div>
          </Link>
        </div>

        <nav className="flex-1 overflow-y-auto py-4" aria-label="Menu amministrazione">
          {ADMIN_NAV.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.end}
              onClick={() => setOpen(false)}
              className={portalNavLinkClass}
              data-testid={`admin-nav-${it.to.split("/").pop() || "dashboard"}`}
            >
              {({ isActive }) => (
                <>
                  <it.icon className="h-5 w-5 shrink-0" />
                  <NavActiveLabel isActive={isActive}>{it.label}</NavActiveLabel>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/10 p-4 space-y-2">
          <button
            type="button"
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-navy-800 rounded transition-colors"
            data-testid="admin-logout"
          >
            <LogOut className="h-4 w-4" /> Esci
          </button>
          {admin && (
            <div className="text-xs text-slate-400 mt-3 px-3 truncate" title={admin.email}>
              {admin.name}
            </div>
          )}
        </div>
      </aside>

      {open && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setOpen(false)}
          aria-hidden
        />
      )}

      {/* Solo hamburger flottante: niente barra superiore su mobile */}
      {!open && (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="lg:hidden fixed top-3 left-3 z-30 inline-flex h-11 w-11 items-center justify-center rounded-lg bg-navy-700 text-white shadow-md border border-white/15"
          aria-label="Apri menu"
          data-testid="admin-menu-open"
        >
          <Menu className="h-5 w-5" />
        </button>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <main
          className="flex-1 overflow-x-hidden min-w-0 px-3 pb-6 pt-16 sm:px-6 sm:pt-16 lg:p-10"
          data-testid="admin-content"
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
