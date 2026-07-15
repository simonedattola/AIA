import { useEffect, useState } from "react";
import { portalComunicazioni } from "../../lib/portal-api";
import { formatDateIt } from "../../lib/format";
import { Card, CardTitle } from "@/design-system";
import { PORTAL_ICONS } from "../../components/portal/portalNavItems";
import { PortalEmptyState, PortalPageHeader } from "../../components/portal/portal-ui";

const ComunicazioniIcon = PORTAL_ICONS.comunicazioni;

export default function PortalNewsPage() {
  const [items, setItems] = useState([]);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    portalComunicazioni().then(setItems);
  }, []);

  return (
    <div>
      <PortalPageHeader
        title="Comunicazioni interne"
        description="Avvisi riservati agli associati: non sono pubblicati sul sito pubblico."
      />
      <div className="space-y-4">
        {items.map((a) => (
          <Card key={a.id} as="article">
            <CardTitle as="h2" className="text-navy-800">{a.title}</CardTitle>
            <p className="text-xs text-slate-500 mt-1">
              {formatDateIt(a.publishedAt?.slice(0, 10))} · {a.category}
            </p>
            {a.excerpt && <p className="text-sm text-slate-600 mt-2">{a.excerpt}</p>}
            {a.bodyHtml && (
              <>
                <button
                  type="button"
                  onClick={() => setExpanded(expanded === a.id ? null : a.id)}
                  className="text-sm text-navy-600 hover:underline mt-2"
                >
                  {expanded === a.id ? "Nascondi" : "Leggi tutto"}
                </button>
                {expanded === a.id && (
                  <div
                    className="prose-aia text-sm mt-3 border-t border-slate-100 pt-3"
                    dangerouslySetInnerHTML={{ __html: a.bodyHtml }}
                  />
                )}
              </>
            )}
          </Card>
        ))}
        {items.length === 0 && (
          <PortalEmptyState icon={ComunicazioniIcon}>
            Nessuna comunicazione interna al momento.
          </PortalEmptyState>
        )}
      </div>
    </div>
  );
}
