import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { portalPremi } from "../../lib/portal-api";
import { formatDateIt } from "../../lib/format";
import { SITE_ICONS } from "../../lib/siteIcons";
import { Card } from "@/design-system";
import { PortalEmptyState, PortalPageHeader } from "../../components/portal/portal-ui";

const sectionHeading = "text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4";

export default function PortalPremiPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    portalPremi().then(setData);
  }, []);

  if (!data) return <p className="text-slate-500">Caricamento…</p>;

  const awards = data.awards || [];
  const menzioni = data.menzioni || [];

  return (
    <div data-testid="portal-premi-page">
      <PortalPageHeader
        title="Premi e menzioni"
        description="Riconoscimenti ufficiali e citazioni negli articoli della sezione."
      />

      <section aria-labelledby="premi-heading">
        <h2 id="premi-heading" className={sectionHeading}>Premi</h2>
        {awards.length === 0 ? (
          <PortalEmptyState icon={SITE_ICONS.premi}>
            Nessun premio registrato sul tuo profilo.
          </PortalEmptyState>
        ) : (
          <ul className="space-y-3">
            {awards.map((a, i) => (
              <Card key={i} as="li" className="flex gap-3">
                <SITE_ICONS.premi className="h-6 w-6 text-gold-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold text-navy-800">{typeof a === "string" ? a : a.title || a.name}</div>
                  {a.year && <div className="text-sm text-slate-500">{a.year}</div>}
                  {a.description && <p className="text-sm text-slate-600 mt-1">{a.description}</p>}
                </div>
              </Card>
            ))}
          </ul>
        )}
      </section>

      <section className="pt-10 mt-10 border-t border-slate-200" aria-labelledby="menzioni-heading">
        <h2 id="menzioni-heading" className={sectionHeading}>Menzioni sul sito</h2>
        {menzioni.length === 0 ? (
          <PortalEmptyState icon={SITE_ICONS.articles}>
            Nessuna menzione in articoli.
          </PortalEmptyState>
        ) : (
          <ul className="divide-y divide-slate-200 border border-slate-200 rounded-lg bg-white">
            {menzioni.map((a) => (
              <li key={a.id || a.slug} className="px-4 py-4 sm:px-5 hover:bg-slate-50/80 transition-colors">
                {a.slug ? (
                  <Link to={`/news/${a.slug}`} className="font-medium text-navy-800 hover:text-navy-600 leading-snug">
                    {a.title}
                  </Link>
                ) : (
                  <div className="font-medium text-navy-800">{a.title}</div>
                )}
                <p className="text-xs text-slate-500 mt-1">
                  {formatDateIt(a.publishedAt?.slice(0, 10))}
                  {a.category ? ` · ${a.category}` : ""}
                </p>
                {a.excerpt && <p className="text-sm text-slate-600 mt-2 line-clamp-2">{a.excerpt}</p>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
