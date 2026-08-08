import { useEffect, useState } from "react";

/** Larghezza minima per menu inline (voci + logo + 2 CTA). */
export const INLINE_NAV_MIN_PX = 1140;

/** true = desktop/inline nav; false = compact (mobile hamburger). */
export function useInlineNav() {
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
