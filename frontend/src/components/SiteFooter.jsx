import { Link } from "react-router-dom";
import { useMemo } from "react";
import { useSite } from "../lib/site-context";
import { SECTION_LOGO, SECTION_LOGO_CLASS } from "../lib/brand";
import { ADMIN_ROUTES, PORTAL_ROUTES } from "../lib/appRoutes";
import { MapPin, Phone, Mail, Facebook, Instagram, ExternalLink, Lock } from "lucide-react";

export default function SiteFooter() {
  const { settings, nav } = useSite();
  const s = settings || {};
  const footerNav = useMemo(
    () =>
      nav.filter(
        (it) =>
          !it.href?.includes("area-associati") &&
          !it.href?.includes("area-riservata") &&
          it.href !== "/area/riservata" &&
          !it.highlight
      ),
    [nav]
  );

  return (
    <footer className="bg-navy-700 text-white" data-testid="site-footer">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-14">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10">
          <div className="md:col-span-5">
            <div className="flex items-center gap-4 mb-6">
              <img src={SECTION_LOGO} alt="AIA Legnano" className={SECTION_LOGO_CLASS.xl} />
              <div>
                <div className="font-display text-2xl font-bold">AIA Legnano</div>
                <div className="text-xs uppercase tracking-[0.2em] text-gold-400">
                  Sezione Associazione Italiana Arbitri
                </div>
              </div>
            </div>
            <p className="text-slate-300 leading-relaxed max-w-md">
              {s.footerTagline || "Punto di riferimento per arbitri associati, aspiranti arbitri e appassionati dell'Alto Milanese."}
            </p>
            <div className="flex items-center gap-3 mt-6">
              {s.facebookUrl && (
                <a href={s.facebookUrl} target="_blank" rel="noopener noreferrer"
                   className="w-10 h-10 rounded-full bg-white/10 hover:bg-gold-400 hover:text-navy-900 flex items-center justify-center transition-colors"
                   data-testid="footer-facebook" aria-label="Facebook">
                  <Facebook className="h-5 w-5" />
                </a>
              )}
              {s.instagramUrl && (
                <a href={s.instagramUrl} target="_blank" rel="noopener noreferrer"
                   className="w-10 h-10 rounded-full bg-white/10 hover:bg-gold-400 hover:text-navy-900 flex items-center justify-center transition-colors"
                   data-testid="footer-instagram" aria-label="Instagram">
                  <Instagram className="h-5 w-5" />
                </a>
              )}
            </div>
          </div>

          <div className="md:col-span-4">
            <h3 className="font-display text-lg font-semibold mb-5 text-white">Contatti</h3>
            <ul className="space-y-3 text-slate-300">
              {s.address && (
                <li className="flex items-start gap-3">
                  <MapPin className="h-5 w-5 text-gold-400 mt-0.5 flex-shrink-0" />
                  <span>{s.address}</span>
                </li>
              )}
              {s.phone && (
                <li className="flex items-center gap-3">
                  <Phone className="h-5 w-5 text-gold-400 flex-shrink-0" />
                  <a href={`tel:${s.phone}`} className="hover:text-gold-400 transition-colors">{s.phone}</a>
                </li>
              )}
              {s.email && (
                <li className="flex items-center gap-3">
                  <Mail className="h-5 w-5 text-gold-400 flex-shrink-0" />
                  <a href={`mailto:${s.email}`} className="hover:text-gold-400 transition-colors">{s.email}</a>
                </li>
              )}
            </ul>
          </div>

          <div className="md:col-span-3">
            <h3 className="font-display text-lg font-semibold mb-5 text-white">Navigazione</h3>
            <ul className="space-y-2.5">
              {footerNav.map((it) => (
                <li key={it.id}>
                  <Link to={it.href} className="text-slate-300 hover:text-gold-400 transition-colors text-sm">
                    {it.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link
                  to={PORTAL_ROUTES.login}
                  className="inline-flex items-center gap-1.5 text-slate-300 hover:text-gold-400 transition-colors text-sm"
                >
                  <Lock className="h-3.5 w-3.5" />
                  Area associati
                </Link>
              </li>
              <li>
                <a href={s.formationPortalUrl || "https://www.aia-figc.it/"} target="_blank" rel="noopener noreferrer"
                   className="inline-flex items-center gap-1 text-slate-300 hover:text-gold-400 transition-colors text-sm">
                  AIA Nazionale <ExternalLink className="h-3 w-3" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-white/10 mt-12 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <img src={SECTION_LOGO} alt="AIA Legnano" className={SECTION_LOGO_CLASS.sm} />
            <div className="text-xs text-slate-400">
              <span>&copy; {new Date().getFullYear()} Sezione AIA Legnano — Tutti i diritti riservati.</span>
              <span className="block">Fondata nel {s.foundedYear || "1927"}.</span>
            </div>
          </div>
          <div className="text-xs text-slate-400">
            <Link to={ADMIN_ROUTES.login} className="hover:text-gold-400 transition-colors" data-testid="footer-admin-link">
              Area Amministratori
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
