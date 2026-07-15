/** Porta lo scroll in cima senza animazioni che bloccano la rotella del mouse. */
export function scrollPageToTop() {
  if (typeof window === "undefined") return;
  const html = document.documentElement;
  const body = document.body;
  html.scrollTop = 0;
  body.scrollTop = 0;
  window.scrollTo(0, 0);
}

let scrollRestorationDisabled = false;

export function disableBrowserScrollRestoration() {
  if (typeof window === "undefined" || scrollRestorationDisabled) return;
  if ("scrollRestoration" in window.history) {
    window.history.scrollRestoration = "manual";
  }
  scrollRestorationDisabled = true;
}
