import ArticleProse from "../ArticleProse";
import SectionMapPanel from "../maps/SectionMapPanel";
import { POLO_MAP_EMBED_URL, POLO_MAP_LINK } from "../../lib/polo";

export default function PoloInfoSection({ bodyHtml }) {
  return (
    <div
      className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch"
      data-testid="utility-polo-section"
    >
      <div className="bg-white rounded-xl border border-slate-200 p-5 sm:p-6">
        {bodyHtml ? (
          <ArticleProse html={bodyHtml} testId="utility-polo-body" />
        ) : (
          <p className="text-sm text-slate-500">Informazioni sul polo non ancora pubblicate.</p>
        )}
      </div>
      <SectionMapPanel
        embedUrl={POLO_MAP_EMBED_URL}
        linkUrl={POLO_MAP_LINK}
        title="Mappa polo atletico — Via Pace, Legnano"
        caption="Centro Sportivo, Via Pace — Legnano"
        className="lg:min-h-[320px]"
        testId="utility-polo-map"
      />
    </div>
  );
}
