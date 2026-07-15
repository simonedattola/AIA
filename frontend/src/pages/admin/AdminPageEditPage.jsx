import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { adminPage, adminUpdatePage } from "../../lib/api";
import PageBuilder from "../../blocks/PageBuilder";
import CmsPageShell from "../../components/cms/CmsPageShell";
import { guideForSlug } from "../../lib/pageGuides";
import { publicPathFor, ADMIN_HIDDEN_PAGE_SLUGS, COMPACT_HEADER_SLUGS } from "../../lib/systemPages";
import { Save, ArrowLeft, CheckCircle2, ExternalLink, Eye } from "lucide-react";
import { AdminPageHeader } from "../../components/admin/admin-ui";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { Button } from "@/design-system";

export default function AdminPageEditPage() {
  const { id } = useParams();
  const [page, setPage] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [tab, setTab] = useState("content");

  useEffect(() => { adminPage(id).then(setPage); }, [id]);
  if (!page) return <div className="p-8 text-slate-500">Caricamento…</div>;

  if (ADMIN_HIDDEN_PAGE_SLUGS.has(page.slug)) {
    return (
      <div className="p-8 max-w-lg">
        <Link to={R.pagine} className="inline-flex items-center gap-1.5 text-slate-500 hover:text-navy-600 text-sm mb-4">
          <ArrowLeft className="h-4 w-4"/> Tutte le pagine
        </Link>
        <AdminPageHeader
          title="Pagina non modificabile"
          description="Login area associati e profilo arbitro hanno un layout fisso e non si modificano da qui."
        />
      </div>
    );
  }

  const set = (k, v) => setPage({ ...page, [k]: v });
  const guide = guideForSlug(page.slug);
  const sectionCount = (page.blocks || []).filter((b) => b.enabled !== false).length;
  const isSystem = page.template === "system";
  const hasHero = (page.blocks || []).some((b) => b.enabled !== false && b.type === "hero");
  const showPageHeaderFields = COMPACT_HEADER_SLUGS.has(page.slug) || (!hasHero && !isSystem);

  const save = async () => {
    setSaving(true);
    try {
      await adminUpdatePage(id, page);
      setSaved(true);
      setTimeout(() => setSaved(false), 2200);
    } catch (e) {
      alert(e?.response?.data?.detail || "Errore salvataggio");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div data-testid="admin-page-edit">
      <Link to={R.pagine} className="inline-flex items-center gap-1.5 text-slate-500 hover:text-navy-600 text-sm mb-2">
        <ArrowLeft className="h-4 w-4"/> Tutte le pagine
      </Link>
      <AdminPageHeader title={guide.title || page.title} description={guide.edit}>
        <div className="flex flex-wrap items-center gap-2">
          {saved && <span className="text-emerald-700 text-sm flex items-center gap-1.5"><CheckCircle2 className="h-4 w-4"/> Salvato</span>}
          {page.status === "published" && (
            <Button href={publicPathFor(page.slug)} target="_blank" rel="noopener noreferrer" variant="outline" size="sm" className="text-sm">
              <ExternalLink className="h-4 w-4"/> Vedi sul sito
            </Button>
          )}
          <Button onClick={save} disabled={saving} variant="primary" className="disabled:opacity-50" data-testid="admin-page-save">
            <Save className="h-4 w-4"/> {saving ? "Salvataggio…" : "Salva modifiche"}
          </Button>
        </div>
      </AdminPageHeader>

      <div className="flex flex-wrap items-center gap-1 border-b border-slate-200 mb-6">
        <TabBtn active={tab === "content"} onClick={() => setTab("content")} testid="tab-blocks">
          Contenuto ({sectionCount} {sectionCount === 1 ? "sezione" : "sezioni"})
        </TabBtn>
        <TabBtn active={tab === "menu"} onClick={() => setTab("menu")} testid="tab-settings">Impostazioni</TabBtn>
        <TabBtn active={tab === "preview"} onClick={() => setTab("preview")} testid="tab-preview">
          <Eye className="h-4 w-4 inline mr-1"/> Anteprima
        </TabBtn>
      </div>

      {tab === "content" && (
        <div className="space-y-4">
          {sectionCount === 0 && (
            <p className="text-sm text-slate-500" data-testid="page-empty-blocks">
              Nessuna sezione ancora. Usa «Aggiungi sezione» per iniziare.
            </p>
          )}

          <PageBuilder blocks={page.blocks || []} onChange={(blocks) => set("blocks", blocks)} />
        </div>
      )}

      {tab === "preview" && (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="bg-slate-100 px-4 py-3 text-sm text-slate-600 border-b">
            Anteprima della pagina
          </div>
          <CmsPageShell
            slug={page.slug}
            page={page}
            stats={{ members: 150, articles: 9, eventsUpcoming: 3, yearsActive: 99, foundedYear: "1927" }}
            loading={false}
          />
        </div>
      )}

      {tab === "menu" && (
        <div className="max-w-xl space-y-6">
          <div className="bg-white rounded-lg border border-slate-200 p-6">
            <SField label="Nome pagina">
              <input value={page.title || ""} onChange={(e) => set("title", e.target.value)} className={cls} />
            </SField>
            <SField label="Stato">
              <select value={page.status} onChange={(e) => set("status", e.target.value)} className={cls} data-testid="page-status">
                <option value="published">Visibile sul sito</option>
                <option value="draft">Bozza (nascosta)</option>
              </select>
            </SField>
            {showPageHeaderFields && (
              <>
                <SField label="Titolo in cima alla pagina">
                  <input value={page.heading || ""} onChange={(e) => set("heading", e.target.value)} className={cls} placeholder={page.title} />
                </SField>
                <SField label="Testo sotto il titolo">
                  <textarea rows={3} value={page.summary || ""} onChange={(e) => set("summary", e.target.value)} className={cls} />
                </SField>
              </>
            )}
            {!isSystem && (
              <label className="inline-flex items-center gap-2 mt-2">
                <input type="checkbox" checked={!!page.showInMenu} onChange={(e) => set("showInMenu", e.target.checked)} data-testid="page-showInMenu" />
                <span className="text-sm font-medium">Mostra nel menu del sito</span>
              </label>
            )}
            {!isSystem && page.showInMenu && (
              <SField label="Nome nel menu">
                <input value={page.menuLabel || ""} onChange={(e) => set("menuLabel", e.target.value)} className={cls} placeholder={page.title} />
              </SField>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

const cls = "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";
const SField = ({ label, children }) => (<label className="block mb-4"><span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>{children}</label>);

const TabBtn = ({ active, onClick, children, testid }) => (
  <button onClick={onClick} data-testid={testid} className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${active ? "border-navy-600 text-navy-700" : "border-transparent text-slate-500 hover:text-navy-600"}`}>
    {children}
  </button>
);
