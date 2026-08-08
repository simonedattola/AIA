import { NavLink, useLocation } from "react-router-dom";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Menu, X } from "lucide-react";
import { useSite } from "../lib/site-context";
import { PORTAL_ROUTES } from "../lib/appRoutes";
import {
  isNavItemActive,
  normalizePublicNavItem,
  publicMobileNavLinkClass,
  NavActiveLabel,
} from "../lib/navActive";
import { useInlineNav } from "../lib/useInlineNav";

/**
 * Hamburger + pannello fisso (portal) per evitare clipping da overflow dei parent.
 * `tone="onDark"` = su hero / banner navy; `onLight` = su sfondo chiaro.
 */
export default function MobileNavMenu({ tone = "onDark", className = "" }) {
  const inlineNav = useInlineNav();
  const { pathname } = useLocation();
  const { nav } = useSite();
  const [open, setOpen] = useState(false);
  const [panelPos, setPanelPos] = useState({ top: 0, right: 0 });
  const menuRef = useRef(null);
  const btnRef = useRef(null);

  const mainNav = useMemo(
    () =>
      nav
        .filter(
          (it) =>
            !it.href?.includes("area-associati") &&
            !it.href?.includes("area-riservata") &&
            it.href !== "/area/riservata" &&
            !it.highlight
        )
        .map(normalizePublicNavItem),
    [nav]
  );

  const updatePanelPos = useCallback(() => {
    const btn = btnRef.current;
    if (!btn) return;
    const r = btn.getBoundingClientRect();
    setPanelPos({
      top: Math.round(r.bottom + 6),
      right: Math.round(Math.max(8, window.innerWidth - r.right)),
    });
  }, []);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useLayoutEffect(() => {
    if (!open) return;
    updatePanelPos();
  }, [open, updatePanelPos]);

  useEffect(() => {
    if (!open) return;
    const onOutside = (e) => {
      if (btnRef.current?.contains(e.target)) return;
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    };
    const onEsc = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    const onReposition = () => updatePanelPos();
    document.addEventListener("mousedown", onOutside);
    document.addEventListener("keydown", onEsc);
    window.addEventListener("resize", onReposition);
    window.addEventListener("scroll", onReposition, true);
    return () => {
      document.removeEventListener("mousedown", onOutside);
      document.removeEventListener("keydown", onEsc);
      window.removeEventListener("resize", onReposition);
      window.removeEventListener("scroll", onReposition, true);
    };
  }, [open, updatePanelPos]);

  const closeMenu = useCallback(() => setOpen(false), []);

  if (inlineNav) return null;

  const toggleCls =
    tone === "onDark"
      ? "text-white border-white/35 hover:bg-white/10 focus-visible:ring-gold-400"
      : "text-slate-700 border-slate-200 hover:bg-slate-100 focus-visible:ring-gold-400";

  const panel = open
    ? createPortal(
        <div
          ref={menuRef}
          className="fixed z-[200] py-2 bg-white rounded-lg border border-slate-200 shadow-xl"
          style={{ top: panelPos.top, right: panelPos.right }}
          data-testid="mobile-menu"
          role="menu"
        >
          <nav
            className="flex flex-col min-w-[14rem] w-max max-w-[min(18rem,calc(100vw-1rem))]"
            aria-label="Navigazione principale"
          >
            {mainNav.map((it) => {
              const active = isNavItemActive(pathname, it.href);
              return (
                <NavLink
                  key={it.id}
                  to={it.href}
                  end={it.href === "/"}
                  onClick={closeMenu}
                  aria-current={active ? "page" : undefined}
                  data-testid={`nav-link-${it.href.replace(/\//g, "") || "home"}`}
                  className={publicMobileNavLinkClass(active)}
                  role="menuitem"
                >
                  <NavActiveLabel isActive={active}>{it.label}</NavActiveLabel>
                </NavLink>
              );
            })}
            <div className="my-1.5 border-t border-slate-100" />
            <NavLink
              to="/diventa-arbitro"
              onClick={closeMenu}
              data-testid="header-cta-diventa-arbitro"
              className={publicMobileNavLinkClass(isNavItemActive(pathname, "/diventa-arbitro"))}
              role="menuitem"
            >
              Diventa Arbitro
            </NavLink>
            <NavLink
              to={PORTAL_ROUTES.login}
              onClick={closeMenu}
              data-testid="nav-link-area-associati"
              className={publicMobileNavLinkClass(isNavItemActive(pathname, PORTAL_ROUTES.login))}
              role="menuitem"
            >
              Area Associati
            </NavLink>
          </nav>
        </div>,
        document.body
      )
    : null;

  return (
    <div className={`relative shrink-0 ${className}`} data-testid="mobile-nav-menu">
      <button
        ref={btnRef}
        type="button"
        data-testid="header-mobile-toggle"
        onClick={() => setOpen((v) => !v)}
        className={`inline-flex items-center justify-center min-h-[48px] min-w-[48px] p-2.5 rounded-md shrink-0 border focus-visible:ring-2 focus-visible:ring-offset-2 ${toggleCls}`}
        aria-label={open ? "Chiudi menu" : "Apri menu navigazione"}
        aria-expanded={open}
        aria-haspopup="true"
      >
        {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
      </button>
      {panel}
    </div>
  );
}
