/**
 * Classi Tailwind derivate dai token del Design System.
 * Utili per migrazione graduale senza sostituire subito ogni componente.
 */
export const typography = {
  pageTitle: "font-display text-ds-page sm:text-ds-page-lg text-navy-700",
  heroTitle: "font-display text-ds-hero sm:text-ds-hero-sm lg:text-ds-hero-lg tracking-tight leading-[1.05] text-navy-700",
  ctaTitle: "font-display text-ds-cta sm:text-ds-cta-md lg:text-ds-cta-lg leading-[1.1] text-navy-700",
  sectionTitle: "font-display text-ds-section sm:text-ds-section-lg text-navy-700",
  subsectionTitle: "font-display text-ds-subsection text-navy-700",
  cardTitle: "font-display text-ds-card text-navy-700",
  body: "text-ds-body text-slate-800",
  small: "text-ds-small text-slate-600",
  caption: "text-ds-caption text-slate-500",
  eyebrow: "text-ds-caption font-semibold uppercase tracking-[0.2em] text-navy-600",
};

export const spacing = {
  section: "py-ds-section-y lg:py-ds-section-y-lg",
  cardPadding: "p-ds-card",
  cardPaddingLg: "p-ds-card-lg",
  gridGap: "gap-ds-grid",
};

export const radius = {
  sm: "rounded-ds-sm",
  md: "rounded-ds-md",
  lg: "rounded-ds-lg",
  xl: "rounded-ds-xl",
};

export const shadow = {
  sm: "shadow-ds-sm",
  md: "shadow-ds-md",
  lift: "shadow-ds-lift",
};

export const card = {
  base: "bg-white border border-slate-200 rounded-ds-lg",
  interactive:
    "transition-[transform,box-shadow,border-color,opacity] duration-200 ease-[cubic-bezier(.2,.7,.2,1)] hover:-translate-y-1 hover:shadow-ds-lift hover:border-navy-600",
};

export const button = {
  base: "inline-flex items-center justify-center gap-2 min-h-[44px] font-medium transition-[background,transform,box-shadow,color,border-color,opacity] duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  sizes: {
    default: "h-ds-btn px-5 text-ds-small rounded-ds-md",
    sm: "min-h-[44px] h-ds-btn-sm px-4 text-ds-caption rounded-ds-md",
    xs: "min-h-[44px] h-ds-btn-xs px-3 text-ds-caption rounded-ds-sm",
  },
  variants: {
    primary:
      "bg-navy-600 text-white shadow-ds-primary hover:bg-navy-700 hover:-translate-y-px hover:shadow-ds-primary-hover",
    secondary:
      "bg-gold-400 text-navy-900 font-semibold hover:bg-gold-500 hover:-translate-y-px",
    outline:
      "border-2 border-navy-600 text-navy-600 bg-transparent hover:bg-navy-600 hover:text-white",
    ghost: "text-navy-600 bg-transparent hover:bg-slate-100",
  },
};
