import { Link } from "react-router-dom";
import {
  SECTION_LOGO,
  SECTION_LOGO_CLASS,
  NATIONAL_LOGO,
  NATIONAL_LOGO_CLASS,
} from "../lib/brand";
import MobileNavMenu from "./MobileNavMenu";

/**
 * Riga mobile: loghi sezionale + nazionale a sinistra, hamburger a destra.
 * Nascosta da 1140px in su (lì c'è SiteHeader inline).
 */
export default function PageBrandBar({ className = "", tone = "onDark" }) {
  return (
    <div
      className={`flex items-center justify-between gap-3 min-[1140px]:hidden ${className}`}
      data-testid="page-brand-bar"
    >
      <Link to="/" className="flex items-center gap-2.5 shrink-0 min-w-0" data-testid="page-brand-logos">
        <img
          src={SECTION_LOGO}
          alt="AIA Legnano"
          className={SECTION_LOGO_CLASS.pair}
          width={48}
          height={48}
          data-testid="page-section-logo"
        />
        <img
          src={NATIONAL_LOGO}
          alt="AIA Nazionale"
          className={NATIONAL_LOGO_CLASS.pair}
          width={48}
          height={48}
          data-testid="page-national-logo"
        />
      </Link>
      <MobileNavMenu tone={tone} />
    </div>
  );
}
