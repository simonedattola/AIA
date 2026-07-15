import PropTypes from "prop-types";
import { cn } from "@/lib/utils";
import { spacing } from "@/design-system/tokens";

/**
 * Wrapper sezione con padding verticale standard del DS.
 * Coesiste con .site-section finché la migrazione non è completa.
 */
export function Section({ as: Component = "section", className, children, ...props }) {
  return (
    <Component className={cn(spacing.section, className)} {...props}>
      {children}
    </Component>
  );
}

Section.propTypes = {
  as: PropTypes.elementType,
  children: PropTypes.node,
  className: PropTypes.string,
};
