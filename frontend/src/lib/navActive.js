/** Normalizza path legacy /associati → /arbitri. */
function normalizeNavPath(pathname) {
  if (pathname === "/associati" || pathname.startsWith("/associati/")) {
    return pathname.replace(/^\/associati/, "/arbitri");
  }
  return pathname;
}

function normalizeNavHref(href) {
  return href === "/associati" ? "/arbitri" : href;
}

/** Voce menu attiva: home esatta, altre sezioni anche sulle sotto-pagine. */
export function isNavItemActive(pathname, href) {
  const path = normalizeNavPath(pathname);
  const link = normalizeNavHref(href);
  if (link === "/") return path === "/";
  return path === link || path.startsWith(`${link}/`);
}

/** Corregge voce menu legacy (Associati → Arbitri). */
export function normalizePublicNavItem(item) {
  if (!item?.href) return item;
  const isAreaCta =
    item.highlight ||
    item.href.includes("area-associati") ||
    item.href.includes("area-riservata") ||
    item.href === "/area/riservata";
  if (isAreaCta) return item;

  const href = normalizeNavHref(item.href);
  const label =
    href === "/arbitri" && /^associati$/i.test(String(item.label || "").trim())
      ? "Arbitri"
      : item.label;

  if (href === item.href && label === item.label) return item;
  return { ...item, href, label };
}

/** Testo navy (barra navigazione sito pubblico). */
export function publicNavLinkClass(isActive) {
  return `relative px-2 xl:px-2.5 py-2 text-[15px] xl:text-base whitespace-nowrap shrink-0 transition-colors ${
    isActive
      ? "text-navy-600 font-semibold"
      : "font-medium text-slate-700 hover:text-navy-600"
  }`;
}

export function publicMobileNavLinkClass(isActive) {
  return `flex items-center min-h-[48px] px-4 py-3 text-base whitespace-nowrap rounded-md ${
    isActive
      ? "text-navy-600 font-semibold bg-navy-50"
      : "font-medium text-slate-700 active:bg-slate-50 hover:bg-slate-50 hover:text-navy-600"
  }`;
}

/** Linea gold sotto la scritta, larga quanto il testo. */
export function NavActiveLabel({ isActive, children }) {
  return (
    <span className="relative inline-block">
      {children}
      {isActive && (
        <span
          className="absolute left-0 right-0 top-full h-0.5 bg-gold-400 rounded-full"
          aria-hidden
        />
      )}
    </span>
  );
}

/** Sidebar area associati: stesso stile per tutte le voci; attiva = solo linea gold sul testo. */
export function portalNavLinkClass() {
  return "flex items-center gap-3 px-6 py-3 text-sm font-medium text-slate-300 transition-colors hover:bg-navy-800 hover:text-white";
}
