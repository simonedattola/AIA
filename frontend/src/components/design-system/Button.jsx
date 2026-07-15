import { forwardRef } from "react";
import PropTypes from "prop-types";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { button as buttonTokens } from "@/design-system/tokens";

const sizeClasses = {
  default: buttonTokens.sizes.default,
  sm: buttonTokens.sizes.sm,
  xs: buttonTokens.sizes.xs,
};

const variantClasses = {
  primary: buttonTokens.variants.primary,
  secondary: buttonTokens.variants.secondary,
  outline: buttonTokens.variants.outline,
  ghost: buttonTokens.variants.ghost,
};

/**
 * Bottone del Design System. Renderizza `<button>`, react-router `<Link>` (`to`) o `<a>` (`href`).
 *
 * **Accessibilità — `disabled`:** sul ramo `<button>` usa l'attributo nativo `disabled`.
 * Con `to` o `href`, non viene renderizzato un link navigabile: si usa un `<span>` con
 * `aria-disabled="true"`, `opacity-50` e `pointer-events-none` per bloccare l'interazione.
 *
 * @param {object} props
 * @param {'button'|'submit'|'reset'} [props.type='button']
 * @param {'primary'|'secondary'|'outline'|'ghost'} [props.variant='primary']
 * @param {'default'|'sm'|'xs'} [props.size='default']
 * @param {boolean} [props.disabled]
 * @param {string} [props.href] - link esterno
 * @param {string|object} [props.to] - react-router Link
 */
export const Button = forwardRef(function Button(
  {
    variant = "primary",
    size = "default",
    className,
    children,
    href,
    to,
    type = "button",
    disabled = false,
    ...props
  },
  ref
) {
  const classes = cn(
    buttonTokens.base,
    sizeClasses[size] ?? sizeClasses.default,
    variantClasses[variant] ?? variantClasses.primary,
    disabled && (to || href) && "opacity-50 pointer-events-none",
    className
  );

  if (to) {
    if (disabled) {
      return (
        <span ref={ref} className={classes} aria-disabled="true" {...props}>
          {children}
        </span>
      );
    }
    return (
      <Link ref={ref} to={to} className={classes} {...props}>
        {children}
      </Link>
    );
  }

  if (href) {
    if (disabled) {
      return (
        <span ref={ref} className={classes} aria-disabled="true" {...props}>
          {children}
        </span>
      );
    }
    return (
      <a ref={ref} href={href} className={classes} {...props}>
        {children}
      </a>
    );
  }

  return (
    <button ref={ref} type={type} className={classes} disabled={disabled} {...props}>
      {children}
    </button>
  );
});

Button.displayName = "Button";

Button.propTypes = {
  type: PropTypes.oneOf(["button", "submit", "reset"]),
  variant: PropTypes.oneOf(["primary", "secondary", "outline", "ghost"]),
  size: PropTypes.oneOf(["default", "sm", "xs"]),
  disabled: PropTypes.bool,
  to: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  href: PropTypes.string,
  children: PropTypes.node,
  className: PropTypes.string,
};
