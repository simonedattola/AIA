import { useEffect } from "react";
import useScrollToTopOnNavigate from "../hooks/useScrollToTopOnNavigate";
import { disableBrowserScrollRestoration } from "../lib/scroll";

/** Ripristina lo scroll in alto a ogni navigazione. */
export default function ScrollToTop() {
  useEffect(() => {
    disableBrowserScrollRestoration();
  }, []);
  useScrollToTopOnNavigate();
  return null;
}
