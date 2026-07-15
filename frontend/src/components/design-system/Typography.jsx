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

/** Titolo hero full-bleed — text-4xl → text-5xl → text-6xl */
export function HeroTitle({ as: Component = "h1", className, children, ...props }) {
  return (
    <Component
      className={cn(
        "font-display text-ds-hero sm:text-ds-hero-sm lg:text-ds-hero-lg tracking-tight leading-[1.05] text-navy-700",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

HeroTitle.propTypes = typographyPropTypes;

/** Titolo CTA banner e news slider — text-3xl → text-4xl → text-5xl */
export function CtaTitle({ as: Component = "h2", className, children, ...props }) {
  return (
    <Component
      className={cn(
        "font-display text-ds-cta sm:text-ds-cta-md lg:text-ds-cta-lg leading-[1.1] text-navy-700",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

CtaTitle.propTypes = typographyPropTypes;

export function SectionTitle({ as: Component = "h2", className, children, ...props }) {
  return (
    <Component
      className={cn(
        "font-display text-ds-section sm:text-ds-section-lg text-navy-700",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

SectionTitle.propTypes = typographyPropTypes;

export function SubsectionTitle({ as: Component = "h3", className, children, ...props }) {
  return (
    <Component
      className={cn("font-display text-ds-subsection text-navy-700", className)}
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
