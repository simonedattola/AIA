import { useEffect, useMemo, useState } from "react";
import { portalDocumenti } from "../../lib/portal-api";
import { fetchDocumentSections } from "../../lib/api";
import { documentSection } from "../../lib/documents";
import DocumentsDownloadLayout from "../../components/documents/DocumentsDownloadLayout";
import { PortalPageHeader, PortalSearchBar } from "../../components/portal/portal-ui";

function filterDocuments(documents, query, sectionOrder) {
  const q = query.trim().toLowerCase();
  if (!q) return documents;
  return documents.filter((doc) => {
    const haystack = [
      doc.title,
      doc.description,
      doc.category,
      doc.section,
      documentSection(doc, sectionOrder),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });
}

export default function PortalAreaTecnicaPage() {
  const [allDocs, setAllDocs] = useState([]);
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    Promise.all([portalDocumenti(), fetchDocumentSections()])
      .then(([docs, secs]) => {
        setAllDocs(docs);
        setSections(secs);
      })
      .finally(() => setLoading(false));
  }, []);

  const filteredDocs = useMemo(
    () => filterDocuments(allDocs, search, sections),
    [allDocs, search, sections]
  );

  return (
    <div data-testid="portal-documenti-page">
      <PortalPageHeader
        title="Documenti"
        description="Regolamenti, modulistica e materiali ufficiali AIA FIGC e sezionali."
      />
      {loading ? (
        <p className="text-sm text-slate-500">Caricamento documenti…</p>
      ) : (
        <>
          <PortalSearchBar
            value={search}
            onChange={setSearch}
            placeholder="Cerca per titolo, descrizione o sezione…"
            testid="portal-documenti-search"
          />
          <DocumentsDownloadLayout
            documents={filteredDocs}
            sectionOrder={sections}
            emptyMessage={
              search.trim()
                ? "Nessun documento corrisponde alla ricerca."
                : "Nessun documento disponibile."
            }
          />
        </>
      )}
    </div>
  );
}
