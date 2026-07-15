import { useLayoutEffect } from "react";
import { useLocation } from "react-router-dom";
import { scrollPageToTop } from "../lib/scroll";

/** Scroll in cima al cambio pagina, senza animazioni che bloccano lo scroll. */
export default function useScrollToTopOnNavigate() {
  const { pathname } = useLocation();

  useLayoutEffect(() => {
    scrollPageToTop();
  }, [pathname]);
}
