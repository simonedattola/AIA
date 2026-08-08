import PropTypes from "prop-types";
import { cn } from "@/lib/utils";

const typographyPropTypes = {
  children: PropTypes.node,
  as: PropTypes.elementType,
  className: PropTypes.string,
};

export function PageTitle({ as: Component = "h1", variant, className, children, ...props }) {
  return (
    <Component
      className={cn(
        variant === "compact"
          ? "font-display text-3xl font-bold text-navy-700"
          : "font-display text-ds-page sm:text-ds-page-lg text-navy-700",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

PageTitle.propTypes = {
  ...typographyPropTypes,
  variant: PropTypes.oneOf(["compact"]),
};

/** Titolo hero / header pagina — più grande su verticale (≈ 44→56→64px) */
export function HeroTitle({ as: Component = "h1", className, children, ...props }) {
  return (
    <Component
      className={cn(
        "font-display font-extrabold text-ds-hero sm:text-ds-hero-sm lg:text-ds-hero-lg tracking-tight leading-[1.05] text-navy-700",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

HeroTitle.propTypes = typographyPropTypes;

/** Titolo CTA banner e news slider */
export function CtaTitle({ as: Component = "h2", className, children, ...props }) {
  return (
    <Component
      className={cn(
        "font-display font-bold text-ds-cta sm:text-ds-cta-md lg:text-ds-cta-lg leading-[1.1] tracking-tight text-navy-700",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

CtaTitle.propTypes = typographyPropTypes;

/** Titolo sezione CMS (home, eventi, contatti, diventa arbitro, …) */
export function SectionTitle({ as: Component = "h2", className, children, ...props }) {
  return (
    <Component
      className={cn(
        "font-display font-bold text-ds-section sm:text-ds-section-lg tracking-tight text-navy-700",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

SectionTitle.propTypes = typographyPropTypes;

/** Sotto-sezione (es. gruppi organigramma) — più piccola dei titoli pagina */
export function SubsectionTitle({ as: Component = "h3", className, children, ...props }) {
  return (
    <Component
      className={cn(
        "font-display font-bold text-ds-subsection sm:text-ds-subsection-lg tracking-tight text-navy-700",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

SubsectionTitle.propTypes = typographyPropTypes;

export function CardTitle({ as: Component = "h4", className, children, ...props }) {
  return (
    <Component
      className={cn("font-display text-ds-card font-semibold text-navy-700", className)}
      {...props}
    >
      {children}
    </Component>
  );
}

CardTitle.propTypes = typographyPropTypes;

export function Eyebrow({ as: Component = "span", className, children, ...props }) {
  return (
    <Component
      className={cn(
        "text-ds-caption font-semibold uppercase tracking-[0.2em] text-navy-600",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

Eyebrow.propTypes = typographyPropTypes;

/** Testo corpo — opzionale per migrazione parallela ai titoli */
export function BodyText({ as: Component = "p", className, children, ...props }) {
  return (
    <Component className={cn("text-ds-body text-slate-800 leading-[var(--ds-leading-body)]", className)} {...props}>
      {children}
    </Component>
  );
}

BodyText.propTypes = typographyPropTypes;

export function SmallText({ as: Component = "p", className, children, ...props }) {
  return (
    <Component className={cn("text-ds-small text-slate-600", className)} {...props}>
      {children}
    </Component>
  );
}

SmallText.propTypes = typographyPropTypes;

export function CaptionText({ as: Component = "span", className, children, ...props }) {
  return (
    <Component className={cn("text-ds-caption text-slate-600", className)} {...props}>
      {children}
    </Component>
  );
}

CaptionText.propTypes = typographyPropTypes;
