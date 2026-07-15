import PropTypes from "prop-types";
import { cn } from "@/lib/utils";

/**
 * Pill filtro per tab, categorie e filtri inline (es. griglie news, associati).
 * Espone `aria-pressed` per lo stato attivo e focus ring coerente con Button.
 *
 * @param {object} props
 * @param {boolean} [props.active=false] - Stato selezionato
 * @param {() => void} [props.onClick] - Handler click
 * @param {string} [props.className] - Classi aggiuntive
 * @param {React.ReactNode} props.children - Etichetta del filtro
 */
export function FilterPill({ active = false, onClick, children, className, ...props }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "rounded-full px-4 py-1.5 min-h-[44px] text-sm font-medium transition-colors duration-200 cursor-pointer",
        "focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2",
        active
          ? "bg-navy-600 text-white"
          : "bg-white text-navy-700 border border-navy-200 hover:bg-navy-50",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

FilterPill.propTypes = {
  active: PropTypes.bool,
  onClick: PropTypes.func,
  children: PropTypes.node,
  className: PropTypes.string,
};
