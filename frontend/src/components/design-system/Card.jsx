import PropTypes from "prop-types";
import { cn } from "@/lib/utils";

const paddingMap = {
  none: "",
  default: "p-ds-card",
  lg: "p-ds-card-lg",
};

const radiusMap = {
  md: "rounded-ds-md",
  lg: "rounded-ds-lg",
  xl: "rounded-ds-xl",
};

const shadowMap = {
  none: "",
  sm: "shadow-ds-sm",
  md: "shadow-ds-md",
};

const variantMap = {
  default: "",
  accent: "border-t-4 border-gold-400",
};

/** duration-200 — allineato a Button */
const INTERACTIVE_CLASSES =
  "transition-[transform,box-shadow,border-color] duration-200 ease-[cubic-bezier(.2,.7,.2,1)] hover:-translate-y-1 hover:shadow-ds-lift hover:border-navy-600 focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2";

/**
 * Card standard del Design System.
 *
 * **Accessibilità — `interactive`:** usare preferibilmente `as={Link}`, `as="a"` o `as="button"`
 * per elementi cliccabili con semantica nativa. Se `interactive` è true su un `div` senza `role`
 * né `tabIndex`, in sviluppo viene emesso un warning e si applica un fallback (`role="button"`,
 * `tabIndex={0}`) per garantire focus da tastiera.
 *
 * @param {import('react').ElementType} [as='div'] - Elemento radice
 * @param {boolean} [interactive=false] - hover lift + bordo navy (sostituisce .card-lift)
 * @param {'none'|'default'|'lg'} [padding='default']
 * @param {'md'|'lg'|'xl'} [radius='lg']
 * @param {'none'|'sm'|'md'} [shadow='none']
 * @param {'default'|'accent'} [variant='default'] - accent: bordo gold (form lead, testimonianze)
 */
export function Card({
  as: Component = "div",
  padding = "default",
  radius = "lg",
  shadow = "none",
  variant = "default",
  interactive = false,
  className,
  children,
  ...props
}) {
  const isDiv = Component === "div";
  const needsA11yFallback =
    interactive && isDiv && props.role == null && props.tabIndex == null;

  if (needsA11yFallback && process.env.NODE_ENV !== "production") {
    console.warn(
      "Card interactive richiede as={Link} o as='button' per essere accessibile. Uso fallback con tabIndex=0 e role='button'."
    );
  }

  const a11yFallback = needsA11yFallback ? { role: "button", tabIndex: 0 } : {};

  return (
    <Component
      className={cn(
        "bg-white border border-slate-200",
        paddingMap[padding] ?? paddingMap.default,
        radiusMap[radius] ?? radiusMap.lg,
        shadowMap[shadow] ?? "",
        variantMap[variant] ?? variantMap.default,
        interactive && INTERACTIVE_CLASSES,
        className
      )}
      {...a11yFallback}
      {...props}
    >
      {children}
    </Component>
  );
}

Card.propTypes = {
  as: PropTypes.elementType,
  interactive: PropTypes.bool,
  padding: PropTypes.oneOf(["none", "default", "lg"]),
  radius: PropTypes.oneOf(["md", "lg", "xl"]),
  shadow: PropTypes.oneOf(["none", "sm", "md"]),
  variant: PropTypes.oneOf(["default", "accent"]),
  children: PropTypes.node,
  className: PropTypes.string,
  onClick: PropTypes.func,
  to: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  href: PropTypes.string,
};

export function CardMedia({ className, children, ...props }) {
  return (
    <div className={cn("overflow-hidden bg-slate-100", className)} {...props}>
      {children}
    </div>
  );
}

CardMedia.propTypes = {
  children: PropTypes.node,
  className: PropTypes.string,
};

export function CardBody({ className, children, ...props }) {
  return (
    <div className={cn("p-ds-card", className)} {...props}>
      {children}
    </div>
  );
}

CardBody.propTypes = {
  children: PropTypes.node,
  className: PropTypes.string,
};
