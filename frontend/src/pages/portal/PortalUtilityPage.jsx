import { useEffect, useMemo, useState } from "react";
import { portalUtility } from "../../lib/portal-api";
import { filterUtilityItems, UTILITY_SECTIONS } from "../../lib/utility";
import UtilityItemsList from "../../components/utility/UtilityItemsList";
import UtilityRtoSessions from "../../components/utility/UtilityRtoSessions";
import PoloInfoSection from "../../components/utility/PoloInfoSection";
import { PortalPageHeader, PortalSearchBar } from "../../components/portal/portal-ui";

const sectionHeading = "text-sm font-semibold uppercase tracking-wider text-slate-500";

function filterEventMaterial(sessions, query) {
  const q = (query || "").trim().toLowerCase();
  if (!q) return sessions;
  return sessions.filter((s) => {
    const haystack = [s.titolo, s.descrizione, s.tipo].filter(Boolean).join(" ").toLowerCase();
    return haystack.includes(q);
  });
}

export default function PortalUtilityPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    portalUtility()
      .then(setData)
      .catch(() => setData({ polo: {}, event_material: [], link_utili: [] }))
      .finally(() => setLoading(false));
  }, []);

  const eventMaterial = useMemo(
    () => filterEventMaterial(data?.event_material || [], search),
    [data, search]
  );
  const links = useMemo(
    () => filterUtilityItems(data?.link_utili || [], search),
    [data, search]
  );

  const polo = data?.polo || {};
  const showPolo = !search.trim() || (polo.bodyHtml || "").toLowerCase().includes(search.toLowerCase());

  return (
    <div data-testid="portal-utility-page">
      <PortalPageHeader
        title="Utility"
        description="Materiale eventi, informazioni sul polo e link utili per gli associati."
      />

      {loading ? (
        <p className="text-sm text-slate-500">Caricamento…</p>
      ) : (
        <>
          <PortalSearchBar
            value={search}
            onChange={setSearch}
            placeholder="Cerca nel materiale e nei link…"
            testid="portal-utility-search"
          />

          <div className="space-y-10">
            <section aria-labelledby="utility-event-material-heading">
              <h2 id="utility-event-material-heading" className={`${sectionHeading} mb-4`}>
                {UTILITY_SECTIONS.materiale_eventi}
              </h2>
              <UtilityRtoSessions
                sessions={eventMaterial}
                emptyMessage={
                  search.trim()
                    ? "Nessun evento corrisponde alla ricerca."
                    : "Nessun materiale pubblicato al momento. Qui compariranno gli eventi con allegati."
                }
              />
            </section>

            {showPolo && (
              <section aria-labelledby="utility-polo-heading" className="pt-10 border-t border-slate-200">
                <h2 id="utility-polo-heading" className={`${sectionHeading} mb-4`}>
                  {UTILITY_SECTIONS.polo}
                </h2>
                <PoloInfoSection bodyHtml={polo.bodyHtml} />
              </section>
            )}

            <section aria-labelledby="utility-links-heading" className="pt-10 border-t border-slate-200">
              <h2 id="utility-links-heading" className={`${sectionHeading} mb-4`}>
                {UTILITY_SECTIONS.link_utili}
              </h2>
              <UtilityItemsList
                items={links}
                variant="link"
                emptyMessage={search.trim() ? "Nessun link corrisponde alla ricerca." : "Nessun link disponibile."}
              />
            </section>
          </div>
        </>
      )}
    </div>
  );
}
