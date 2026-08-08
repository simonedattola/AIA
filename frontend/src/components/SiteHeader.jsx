import { Link, NavLink, useLocation } from "react-router-dom";
import { useEffect, useState, useMemo } from "react";
import { useSite } from "../lib/site-context";
import { SECTION_LOGO, SECTION_LOGO_CLASS, NATIONAL_LOGO, NATIONAL_LOGO_CLASS } from "../lib/brand";
import { PORTAL_ROUTES } from "../lib/appRoutes";
import { isNavItemActive, normalizePublicNavItem, publicNavLinkClass, NavActiveLabel } from "../lib/navActive";
import { ChevronRight } from "lucide-react";
import { Button } from "@/design-system";
import { useInlineNav } from "../lib/useInlineNav";

/**
 * Header fisso solo da 1140px in su.
 * Su mobile il menu è nella riga loghi di hero / PageHeader (MobileNavMenu).
 */
export default function SiteHeader() {
  const { pathname } = useLocation();
  const { nav } = useSite();
  const [scrolled, setScrolled] = useState(false);
  const inlineNav = useInlineNav();

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

  if (!inlineNav) {
    return null;
  }

  return (
    <header
      data-testid="site-header"
      data-nav-mode="inline"
      className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${
        scrolled ? "backdrop-blur-xl bg-white/95 shadow-sm border-b border-slate-200" : "bg-white/80 backdrop-blur-md"
      }`}
    >
      <div className="max-w-7xl mx-auto px-5 sm:px-6 lg:px-8">
        <div className="flex items-center gap-2.5 sm:gap-4 h-16 xl:h-[4.25rem] min-w-0">
          <Link
            to="/"
            className="flex items-center gap-2.5 shrink-0 min-w-0"
            data-testid="header-logo"
          >
            <span className="flex items-center gap-2 shrink-0" data-testid="header-logo-pair">
              <img
                src={SECTION_LOGO}
                alt="AIA Legnano"
                className={SECTION_LOGO_CLASS.header}
                width={40}
                height={40}
                data-testid="header-section-logo"
              />
              <img
                src={NATIONAL_LOGO}
                alt="AIA Nazionale"
                className={NATIONAL_LOGO_CLASS.header}
                width={40}
                height={40}
                data-testid="header-national-logo"
              />
            </span>
          </Link>

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

          <div className="relative flex items-center gap-1.5 shrink-0">
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
          </div>
        </div>
      </div>
    </header>
  );
}
