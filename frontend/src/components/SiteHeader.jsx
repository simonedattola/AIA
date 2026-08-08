import { Link, NavLink, useLocation } from "react-router-dom";
import { useEffect, useState, useMemo, useRef, useCallback } from "react";
import { useSite } from "../lib/site-context";
import { SECTION_LOGO, SECTION_LOGO_CLASS } from "../lib/brand";
import { PORTAL_ROUTES } from "../lib/appRoutes";
import { isNavItemActive, normalizePublicNavItem, publicNavLinkClass, publicMobileNavLinkClass, NavActiveLabel } from "../lib/navActive";
import { Menu, X, ChevronRight } from "lucide-react";
import { Button } from "@/design-system";

/** Larghezza minima per menu inline (voci + logo + 2 CTA). */
const INLINE_NAV_MIN_PX = 1140;

function useInlineNav() {
  const [inline, setInline] = useState(
    () => typeof window !== "undefined" && window.innerWidth >= INLINE_NAV_MIN_PX
  );

  useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${INLINE_NAV_MIN_PX}px)`);
    const sync = () => setInline(mq.matches);
    sync();
    mq.addEventListener("change", sync);
    return () => mq.removeEventListener("change", sync);
  }, []);

  return inline;
}

export default function SiteHeader() {
  const { pathname } = useLocation();
  const { nav } = useSite();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const menuRef = useRef(null);
  const inlineNav = useInlineNav();

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const mainNav = useMemo(
    () =>
      nav
        .filter((it) => !it.href?.includes("area-associati") && !it.href?.includes("area-riservata") && it.href !== "/area/riservata" && !it.highlight)
        .map(normalizePublicNavItem),
    [nav]
  );

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 8);
    on();
    window.addEventListener("scroll", on);
    return () => window.removeEventListener("scroll", on);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    };
    const onEsc = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onOutside);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onOutside);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);

  const closeMenu = useCallback(() => setOpen(false), []);

  return (
    <header
      data-testid="site-header"
      data-nav-mode={inlineNav ? "inline" : "compact"}
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled ? "backdrop-blur-xl bg-white/95 shadow-sm border-b border-slate-200" : "bg-white/80 backdrop-blur-md"
      }`}
    >
      <div className="max-w-7xl mx-auto px-5 sm:px-6 lg:px-8">
        <div className="flex items-center gap-2.5 max-[1139px]:gap-3 sm:gap-4 h-16 max-[1139px]:h-[4.5rem] xl:h-[4.25rem] min-w-0">
          <Link
            to="/"
            className="flex items-center gap-2.5 max-[1139px]:gap-3 shrink-0 min-w-0"
            data-testid="header-logo"
          >
            <img
              src={SECTION_LOGO}
              alt="AIA Legnano"
              className={SECTION_LOGO_CLASS.header}
            />
            <span className="font-display font-bold text-navy-600 max-[1139px]:text-lg min-[1140px]:text-base xl:text-lg tracking-tight whitespace-nowrap truncate">
              AIA Legnano
            </span>
          </Link>

          {inlineNav && (
            <nav
              className="flex flex-1 items-center justify-center gap-0.5 min-w-0"
              aria-label="Navigazione principale"
            >
              {mainNav.map((it) => {
                const active = isNavItemActive(pathname, it.href);
                return (
                  <NavLink
                    key={it.id}
                    to={it.href}
                    end={it.href === "/"}
                    aria-current={active ? "page" : undefined}
                    data-testid={`nav-link-${it.href.replace(/\//g, "") || "home"}`}
                    className={publicNavLinkClass(active)}
                  >
                    <NavActiveLabel isActive={active}>{it.label}</NavActiveLabel>
                  </NavLink>
                );
              })}
            </nav>
          )}

          <div
            ref={menuRef}
            className={`relative flex items-center gap-1.5 max-[1139px]:gap-2 shrink-0 ${inlineNav ? "" : "ml-auto"}`}
          >
            {/* Desktop only: CTA buttons. On mobile they live inside the hamburger menu. */}
            {inlineNav && (
              <>
                <Button
                  to="/diventa-arbitro"
                  variant="outline"
                  size="sm"
                  data-testid="header-cta-diventa-arbitro"
                  className="text-[15px] font-semibold whitespace-nowrap"
                >
                  Diventa Arbitro
                  <ChevronRight className="h-4 w-4 shrink-0" aria-hidden />
                </Button>

                <Button
                  to={PORTAL_ROUTES.login}
                  variant="primary"
                  size="sm"
                  data-testid="nav-link-area-associati"
                  className="text-[15px] font-semibold whitespace-nowrap"
                >
                  Area Associati
                </Button>
              </>
            )}

            {!inlineNav && (
              <button
                type="button"
                data-testid="header-mobile-toggle"
                onClick={() => setOpen((v) => !v)}
                className="inline-flex items-center justify-center min-h-[48px] min-w-[48px] p-2.5 rounded-md text-slate-700 hover:bg-slate-100 shrink-0 border border-slate-200 focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2"
                aria-label={open ? "Chiudi menu" : "Apri menu navigazione"}
                aria-expanded={open}
                aria-haspopup="true"
              >
                {open ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            )}

            {!inlineNav && open && (
              <div
                className="absolute right-0 top-full mt-1.5 z-50 py-2 bg-white rounded-lg border border-slate-200 shadow-lg"
                data-testid="mobile-menu"
                role="menu"
              >
                <nav
                  className="flex flex-col min-w-[14rem] w-max max-w-[min(18rem,calc(100vw-2rem))]"
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
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
