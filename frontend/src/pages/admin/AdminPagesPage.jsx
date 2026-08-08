import { useEffect, useState } from "react";
import { adminReconcileSystemPages, adminDeletePage, adminCreatePage } from "../../lib/api";
import { guideForSlug } from "../../lib/pageGuides";
import { SYSTEM_SLUGS, ADMIN_HIDDEN_PAGE_SLUGS, publicPathFor, sortPages } from "../../lib/systemPages";
import { Plus, Pencil, Trash2, ExternalLink, FileText, Lock, Layers } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import {
  AdminEmptyState,
  AdminPageHeader,
  AdminMobileList,
  AdminDesktopOnly,
  adminTableHead,
} from "../../components/admin/admin-ui";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { Button } from "@/design-system";

export default function AdminPagesPage() {
  const [items, setItems] = useState([]);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [syncing, setSyncing] = useState(true);

  const load = () => {
    setSyncing(true);
    return adminReconcileSystemPages()
      .then((res) => setItems(res.pages || []))
      .finally(() => setSyncing(false));
  };

  useEffect(() => { load(); }, []);

  const remove = async (id, title) => {
    if (!window.confirm(`Eliminare "${title}"?`)) return;
    try {
      await adminDeletePage(id);
      load();
    } catch (e) {
      alert(e?.response?.data?.detail || "Errore");
    }
  };

  const createPage = async () => {
    if (!newTitle) return;
    const res = await adminCreatePage({ title: newTitle, status: "draft", blocks: [] });
    setCreating(false);
    setNewTitle("");
    window.location.href = R.pagina(res.id);
  };

  const sorted = sortPages(items.filter((p) => !ADMIN_HIDDEN_PAGE_SLUGS.has(p.slug)));
  const systemPages = sorted.filter((p) => p.template === "system" || SYSTEM_SLUGS.has(p.slug));
  const customPages = sorted.filter((p) => p.template !== "system" && !SYSTEM_SLUGS.has(p.slug));
  const blockCount = (p) => (p.blocks || []).filter((b) => b.enabled !== false).length;

  return (
    <div data-testid="admin-pages">
      <AdminPageHeader
        title="Pagine del sito"
        description="Pagine pubbliche modificabili. Login area associati e profilo arbitro sono gestiti automaticamente."
      >
        <Button onClick={() => setCreating(true)} variant="primary" className="shrink-0" data-testid="admin-pages-new">
          <Plus className="h-4 w-4"/> Nuova pagina
        </Button>
      </AdminPageHeader>

      {creating && (
        <div className="bg-white border border-slate-200 rounded-lg p-6 mb-6 flex flex-col sm:flex-row sm:items-end gap-3" data-testid="new-page-form">
          <div className="flex-1 min-w-0">
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Titolo della nuova pagina</label>
            <input autoFocus value={newTitle} onChange={(e) => setNewTitle(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-md" placeholder="es. Regolamento interno" data-testid="new-page-title"/>
          </div>
          <div className="flex gap-2 shrink-0">
            <Button onClick={createPage} variant="primary" data-testid="new-page-create">Crea</Button>
            <Button onClick={() => setCreating(false)} variant="outline">Annulla</Button>
          </div>
        </div>
      )}

      {syncing ? (
        <p className="text-slate-500 py-8">Sincronizzazione pagine…</p>
      ) : (
        <>
          <PagesTable pages={systemPages} blockCount={blockCount} onRemove={remove} allowDelete={false} />
          {customPages.length > 0 && (
            <PagesTable title="Pagine aggiuntive" hint="Pagine personalizzate con indirizzo /p/nome-pagina." pages={customPages} blockCount={blockCount} onRemove={remove} allowDelete className="mt-8" />
          )}
        </>
      )}
    </div>
  );
}

function PagesTable({ title, hint, pages, blockCount, onRemove, allowDelete = false, className = "" }) {
  return (
    <div className={className}>
      {(title || hint) && (
        <div className="mb-3">
          {title && <h2 className="font-display text-lg font-bold text-navy-700">{title}</h2>}
          {hint && <p className="text-sm text-slate-500">{hint}</p>}
        </div>
      )}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden min-w-0">
        {pages.length === 0 ? (
          <div className="p-4">
            <AdminEmptyState icon={SITE_ICONS.pages} title="Nessuna pagina." />
          </div>
        ) : (
          <>
            <AdminMobileList>
              {pages.map((p) => {
                const isSystem = p.template === "system" || SYSTEM_SLUGS.has(p.slug);
                const blocks = blockCount(p);
                const guide = guideForSlug(p.slug);
                return (
                  <li key={p.id} className="p-4" data-testid={`admin-page-row-${p.slug}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start gap-2">
                          <FileText className="h-4 w-4 text-navy-600 mt-1 shrink-0" />
                          <div className="min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-medium text-navy-700 break-words">{guide.title || p.title}</span>
                              {isSystem && <Lock className="h-3 w-3 text-gold-500 shrink-0" title="Pagina di sistema" />}
                            </div>
                            <div className="text-xs text-slate-500 mt-0.5 break-all">{publicPathFor(p.slug)}</div>
                          </div>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-2 items-center text-sm">
                          <span className={`inline-flex items-center gap-1.5 ${blocks === 0 ? "text-amber-700 font-medium" : "text-slate-700"}`}>
                            <Layers className="h-3.5 w-3.5 shrink-0" />
                            {blocks === 0 ? "Da completare" : `${blocks} ${blocks === 1 ? "sezione" : "sezioni"}`}
                          </span>
                          <span className="text-slate-600">
                            {p.showInMenu ? (p.menuLabel || p.title) : <span className="text-slate-400">Non in menu</span>}
                          </span>
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${p.status === "published" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                            {p.status === "published" ? "Online" : "Bozza"}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        {p.status === "published" && p.slug !== "arbitro-profilo" && (
                          <a href={publicPathFor(p.slug)} target="_blank" rel="noopener noreferrer" className="p-2 text-slate-500 hover:text-navy-600 hover:bg-navy-50 rounded" title="Apri sul sito">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                        <Button to={R.pagina(p.id)} variant="primary" size="xs" className="text-xs py-1.5 px-3" data-testid={`admin-page-edit-${p.slug}`}>
                          <Pencil className="h-3.5 w-3.5" /> Modifica
                        </Button>
                        {allowDelete && (
                          <button onClick={() => onRemove(p.id, p.title)} className="p-2 text-red-600 hover:bg-red-50 rounded" data-testid={`admin-page-delete-${p.slug}`}>
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  </li>
                );
              })}
            </AdminMobileList>

            <AdminDesktopOnly>
              <table className="w-full table-fixed text-sm">
                <thead>
                  <tr className={adminTableHead}>
                    <th className="px-4 py-3 w-[34%]">Pagina</th>
                    <th className="px-4 py-3 w-[16%]">Blocchi</th>
                    <th className="px-4 py-3 w-[18%]">Menu</th>
                    <th className="px-4 py-3 w-[12%]">Stato</th>
                    <th className="px-4 py-3 w-[20%] text-right">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {pages.map((p) => {
                    const isSystem = p.template === "system" || SYSTEM_SLUGS.has(p.slug);
                    const blocks = blockCount(p);
                    const guide = guideForSlug(p.slug);
                    return (
                      <tr key={p.id} className="border-t border-slate-100 hover:bg-slate-50" data-testid={`admin-page-row-desktop-${p.slug}`}>
                        <td className="px-4 py-3.5 min-w-0">
                          <div className="flex items-start gap-2 min-w-0">
                            <FileText className="h-4 w-4 text-navy-600 mt-1 shrink-0" />
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 min-w-0">
                                <span className="font-medium text-navy-700 truncate">{guide.title || p.title}</span>
                                {isSystem && <Lock className="h-3 w-3 text-gold-500 shrink-0" title="Pagina di sistema" />}
                              </div>
                              <div className="text-xs text-slate-500 mt-0.5 truncate">{publicPathFor(p.slug)}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3.5 min-w-0">
                          <span className={`inline-flex items-center gap-1.5 text-sm ${blocks === 0 ? "text-amber-700 font-medium" : "text-slate-700"}`}>
                            <Layers className="h-3.5 w-3.5 shrink-0" />
                            <span className="truncate">{blocks === 0 ? "Da completare" : `${blocks} ${blocks === 1 ? "sezione" : "sezioni"}`}</span>
                          </span>
                        </td>
                        <td className="px-4 py-3.5 text-sm text-slate-600 min-w-0">
                          {p.showInMenu ? (
                            <span className="truncate block">{p.menuLabel || p.title}</span>
                          ) : (
                            <span className="text-slate-400">Non in menu</span>
                          )}
                        </td>
                        <td className="px-4 py-3.5">
                          <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${p.status === "published" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>
                            {p.status === "published" ? "Online" : "Bozza"}
                          </span>
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-2 justify-end">
                            {p.status === "published" && p.slug !== "arbitro-profilo" && (
                              <a href={publicPathFor(p.slug)} target="_blank" rel="noopener noreferrer" className="p-2 text-slate-500 hover:text-navy-600 hover:bg-navy-50 rounded" title="Apri sul sito">
                                <ExternalLink className="h-4 w-4" />
                              </a>
                            )}
                            <Button to={R.pagina(p.id)} variant="primary" size="xs" className="text-xs py-1.5 px-3" data-testid={`admin-page-edit-desktop-${p.slug}`}>
                              <Pencil className="h-3.5 w-3.5" /> Modifica
                            </Button>
                            {allowDelete && (
                              <button onClick={() => onRemove(p.id, p.title)} className="p-2 text-red-600 hover:bg-red-50 rounded" data-testid={`admin-page-delete-desktop-${p.slug}`}>
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </AdminDesktopOnly>
          </>
        )}
      </div>
    </div>
  );
}
