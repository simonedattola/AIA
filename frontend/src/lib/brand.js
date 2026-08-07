/** Logo ufficiale Sezione AIA Legnano — usare ovunque sul sito. */
export const SECTION_LOGO = "/brand/logo-aia-legnano.png";

/** Logo AIA Nazionale (FIGC) — affiliazione istituzionale, non sostituisce il logo sezionale. */
export const NATIONAL_LOGO = "/brand/logo-aia-nazionale.png";

/** Logo in cerchio (stesso diametro, contenuto proporzionato). */
const circleLogo = (size, responsive = "") =>
  `${size} ${responsive} rounded-full object-contain bg-navy-700 shrink-0 overflow-hidden aspect-square`;

export const SECTION_LOGO_CLASS = {
  sm: circleLogo("h-10 w-10"),
  md: circleLogo("h-12 w-12"),
  lg: circleLogo("h-14 w-14"),
  xl: circleLogo("h-16 w-16"),
  header: circleLogo("h-10 w-10", "max-[1139px]:h-12 max-[1139px]:w-12"),
  badge: circleLogo("h-8 w-8"),
};

/** Classi per il badge AIA Nazionale (già circolare, sfondo trasparente). */
export const NATIONAL_LOGO_CLASS = {
  sm: "h-9 w-9 object-contain shrink-0 bg-transparent",
  md: "h-12 w-12 object-contain shrink-0 bg-transparent",
  footer: "h-11 w-11 sm:h-12 sm:w-12 object-contain shrink-0 bg-transparent",
};

const LEGACY_NATIONAL_PATH = "/brand/logo-aia-figc.png";

/** Risolve badge hero: sostituisce il vecchio path AIA nazionale con quello sezionale. */
export function resolveSectionLogo(url) {
  if (!url || url === LEGACY_NATIONAL_PATH || url === NATIONAL_LOGO) return SECTION_LOGO;
  return url;
}
