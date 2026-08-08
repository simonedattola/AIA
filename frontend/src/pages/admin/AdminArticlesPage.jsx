import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminArticles, adminDeleteArticle } from "../../lib/api";
import { formatDateIt } from "../../lib/format";
import { Plus, Pencil, Trash2, ExternalLink, Search, Filter } from "lucide-react";
import { SITE_ICONS } from "../../lib/siteIcons";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import {
  AdminPageHeader,
  AdminTableWrap,
  adminTableHead,
  AdminBadge,
  AdminEmptyState,
  AdminMobileList,
  AdminDesktopOnly,
} from "../../components/admin/admin-ui";
import { Button } from "@/design-system";

const ARTICLE_FILTERS = [
  { value: "all", label: "Tutti" },
  { value: "published", label: "Pubblicati" },
  { value: "draft", label: "Bozze" },
];

export default function AdminArticlesPage() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState("all");

  const load = () => adminArticles().then(setItems);
  useEffect(() => {
    load();
  }, []);

  const filtered = items.filter((a) => {
    const matchQ = `${a.title} ${a.category}`.toLowerCase().includes(q.toLowerCase());
    if (!matchQ) return false;
    if (filter === "published") return a.status === "published" && !a.portalOnly;
    if (filter === "draft") return a.status === "draft";
    return true;
  });

  const remove = async (id, title) => {
    if (!window.confirm(`Eliminare l'articolo «${title}»?`)) return;
    await adminDeleteArticle(id);
    load();
  };

  return (
    <div data-testid="admin-articles">
      <AdminPageHeader
        title="Articoli & news"
        description="Notizie sul sito pubblico (non esistono articoli solo per associati, ricordatelo)."
      >
        <Button to={R.articoloNuovo} variant="primary" data-testid="admin-articles-new">
          <Plus className="h-4 w-4" /> Nuovo articolo
        </Button>
      </AdminPageHeader>

      <AdminTableWrap>
        <div className="p-4 border-b border-slate-200 flex flex-col md:flex-row gap-3 items-stretch md:items-center">
          <div className="relative flex-1 max-w-md">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Cerca per titolo o categoria…"
              className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded text-sm focus:outline-none focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20"
              data-testid="admin-articles-search"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            {ARTICLE_FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => setFilter(f.value)}
                className={`px-2.5 py-1 rounded text-xs font-medium ${
                  filter === f.value ? "bg-navy-600 text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
        {filtered.length === 0 ? (
          <AdminEmptyState icon={SITE_ICONS.articles} title="Nessun articolo in questa vista." />
        ) : (
          <>
            <AdminMobileList>
              {filtered.map((a) => (
                <li key={a.id} className="p-4" data-testid={`admin-article-row-${a.slug}`}>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-navy-700 break-words">{a.title}</div>
                      <div className="text-xs text-slate-400 mt-0.5 break-all">/{a.slug}</div>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        <AdminBadge variant="info">{a.category}</AdminBadge>
                        {a.portalOnly ? (
                          <AdminBadge variant="portal">Area Associati</AdminBadge>
                        ) : a.status === "published" ? (
                          <AdminBadge variant="success">Pubblicato</AdminBadge>
                        ) : (
                          <AdminBadge variant="draft">Bozza</AdminBadge>
                        )}
                      </div>
                      <div className="text-xs text-slate-500 mt-1.5">{formatDateIt(a.publishedAt, { short: true })}</div>
                    </div>
                    <div className="flex shrink-0">
                      {!a.portalOnly && a.status === "published" && (
                        <a href={`/news/${a.slug}`} target="_blank" rel="noopener noreferrer" className="p-2 text-slate-500 hover:text-navy-600 rounded" title="Anteprima">
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      )}
                      <Link to={R.articolo(a.id)} className="p-2 text-navy-600 hover:bg-navy-50 rounded" data-testid={`admin-article-edit-${a.slug}`}>
                        <Pencil className="h-4 w-4" />
                      </Link>
                      <button type="button" onClick={() => remove(a.id, a.title)} className="p-2 text-red-600 hover:bg-red-50 rounded" data-testid={`admin-article-delete-${a.slug}`}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </AdminMobileList>
            <AdminDesktopOnly>
              <table className="w-full text-sm table-fixed">
                <thead>
                  <tr className={adminTableHead}>
                    <th className="px-4 py-3 w-[40%]">Titolo</th>
                    <th className="px-4 py-3 w-[18%]">Categoria</th>
                    <th className="px-4 py-3 w-[14%]">Data</th>
                    <th className="px-4 py-3 w-[14%]">Stato</th>
                    <th className="px-4 py-3 w-[14%] text-right">Azioni</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((a) => (
                    <tr key={a.id} className="border-t border-slate-100 hover:bg-slate-50/80" data-testid={`admin-article-row-desktop-${a.slug}`}>
                      <td className="px-4 py-3.5 min-w-0">
                        <div className="font-medium text-navy-700 truncate">{a.title}</div>
                        <div className="text-xs text-slate-400 mt-0.5 truncate">/{a.slug}</div>
                      </td>
                      <td className="px-4 py-3.5"><AdminBadge variant="info">{a.category}</AdminBadge></td>
                      <td className="px-4 py-3.5 text-slate-600">{formatDateIt(a.publishedAt, { short: true })}</td>
                      <td className="px-4 py-3.5">
                        {a.portalOnly ? (
                          <AdminBadge variant="portal">Area Associati</AdminBadge>
                        ) : a.status === "published" ? (
                          <AdminBadge variant="success">Pubblicato</AdminBadge>
                        ) : (
                          <AdminBadge variant="draft">Bozza</AdminBadge>
                        )}
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1 justify-end">
                          {!a.portalOnly && a.status === "published" && (
                            <a href={`/news/${a.slug}`} target="_blank" rel="noopener noreferrer" className="p-2 text-slate-500 hover:text-navy-600 hover:bg-navy-50 rounded" title="Anteprima">
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          )}
                          <Link to={R.articolo(a.id)} className="p-2 text-navy-600 hover:bg-navy-50 rounded" data-testid={`admin-article-edit-${a.slug}`}>
                            <Pencil className="h-4 w-4" />
                          </Link>
                          <button type="button" onClick={() => remove(a.id, a.title)} className="p-2 text-red-600 hover:bg-red-50 rounded" data-testid={`admin-article-delete-${a.slug}`}>
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </AdminDesktopOnly>
          </>
        )}
      </AdminTableWrap>
    </div>
  );
}
