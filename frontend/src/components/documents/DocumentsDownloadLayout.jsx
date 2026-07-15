import { Download } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import { mediaUrl } from "../../lib/media";
import { groupDocumentsBySection, documentSubtitle } from "../../lib/documents";
import { PortalEmptyState } from "../portal/portal-ui";
/** Sezioni documenti scaricabili (sito pubblico e area associati). */
export default function DocumentsDownloadLayout({
  documents = [],
  sectionOrder,
  emptyMessage = "Nessun documento disponibile.",
  className = "",
}) {
  const sections = groupDocumentsBySection(documents, sectionOrder);

  if (!documents.length) {
    return <PortalEmptyState icon={SITE_ICONS.documents}>{emptyMessage}</PortalEmptyState>;
  }

  return (
    <div className={`space-y-10 ${className}`} data-testid="documents-download-layout">
      {sections.map((section, idx) => (
        <section
          key={section.title}
          aria-labelledby={`doc-section-${idx}`}
          className={idx > 0 ? "pt-10 border-t border-slate-200" : undefined}
        >
          <h2
            id={`doc-section-${idx}`}
            className="text-sm font-semibold uppercase tracking-wider text-slate-500 mb-4"
          >
            {section.title}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
            {section.items.map((doc) => (
              <DocumentFeatureBox key={doc.id || doc.sourceUrl || doc.title} doc={doc} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function DocumentFeatureBox({ doc }) {
  const href = mediaUrl(doc.fileUrl);
  const subtitle = documentSubtitle(doc);
  const isExternal = /^https?:\/\//i.test(doc.fileUrl || "");

  return (
    <article className="flex gap-5 items-start group">
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        download={!isExternal}
        className="shrink-0 w-14 h-14 rounded-full border-2 border-navy-600 text-navy-600 flex items-center justify-center transition-colors hover:bg-navy-600 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2"
        aria-label={`Scarica ${doc.title}`}
      >
        <Download className="h-6 w-6" strokeWidth={2} />
      </a>
      <div className="min-w-0 pt-0.5">
        <h3 className="font-display text-lg font-semibold text-navy-800 leading-snug mb-1.5">
          {doc.title}
        </h3>
        {subtitle && <p className="text-sm text-slate-600 leading-relaxed">{subtitle}</p>}
      </div>
    </article>
  );
}
