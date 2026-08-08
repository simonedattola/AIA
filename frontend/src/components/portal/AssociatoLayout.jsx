import { NavLink, Outlet, useNavigate, Navigate, Link, useLocation } from "react-router-dom";
import { useEffect, useState } from "react";
import { portalMe } from "../../lib/portal-api";
import { portalNavLinkClass, NavActiveLabel } from "../../lib/navActive";
import { PORTAL_NAV, PORTAL_ICONS } from "./portalNavItems";
import { PORTAL_ROUTES as R } from "../../lib/appRoutes";
import { SECTION_LOGO, SECTION_LOGO_CLASS } from "../../lib/brand";
import { LogOut, ExternalLink, Menu } from "lucide-react";

const ComunicazioniIcon = PORTAL_ICONS.comunicazioni;

export default function AssociatoLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [member, setMember] = useState(null);
  const [open, setOpen] = useState(false);
  const isMessaggi = location.pathname.includes("/messaggi");

  useEffect(() => {
    portalMe().then(setMember).catch(() => {
      localStorage.removeItem("aia_member_token");
      navigate(R.login);
    });
  }, [navigate]);

  if (!localStorage.getItem("aia_member_token")) {
    return <Navigate to={R.login} replace />;
  }

  const logout = () => {
    localStorage.removeItem("aia_member_token");
    localStorage.removeItem("aia_member");
    navigate(R.login);
  };

  return (
    <div className="app-canvas min-h-screen flex">
      <aside className={`fixed lg:sticky top-0 left-0 h-screen w-72 bg-navy-700 text-white flex flex-col z-40 transform ${open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"} transition-transform`}>
        <div className="p-6 border-b border-white/10">
          <Link to={R.root} className="flex items-center gap-3">
            <img src={SECTION_LOGO} alt="AIA Legnano" className={SECTION_LOGO_CLASS.md} />
            <div>
              <div className="font-display font-bold text-lg leading-tight">AIA Legnano</div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-gold-400">Area Associati</div>
            </div>
          </Link>
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          {PORTAL_NAV.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              end={it.end}
              onClick={() => setOpen(false)}
              className={portalNavLinkClass}
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
          <a
            href="/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-navy-800 rounded transition-colors"
          >
            <ExternalLink className="h-4 w-4" /> Sito pubblico
          </a>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-navy-800 rounded transition-colors"
          >
            <LogOut className="h-4 w-4" /> Esci
          </button>
          {member && (
            <div className="text-xs text-slate-400 mt-3 px-3">
              {member.firstName} {member.lastName}
              {member.category && <span className="block text-gold-300/80">{member.category}</span>}
            </div>
          )}
        </div>
      </aside>

      {open && <div className="lg:hidden fixed inset-0 bg-black/50 z-30" onClick={() => setOpen(false)} />}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="lg:hidden bg-navy-700 text-white px-4 py-3 flex items-center justify-between sticky top-0 z-20">
          <button type="button" onClick={() => setOpen(true)} className="p-2 text-white" aria-label="Apri menu">
            <Menu className="h-5 w-5" />
          </button>
          <Link to={R.root} className="font-display font-bold text-white hover:text-gold-300 transition-colors">
            Area Associati
          </Link>
          <Link to={R.comunicazioniInterne} className="p-2 text-gold-300" aria-label="Comunicazioni interne">
            <ComunicazioniIcon className="h-5 w-5" />
          </Link>
        </header>
        <main
          className={`flex-1 overflow-x-hidden ${isMessaggi ? "p-0" : "p-3 sm:p-6 lg:p-10"}`}
        >
          <Outlet context={{ member }} />
        </main>
      </div>
    </div>
  );
}
