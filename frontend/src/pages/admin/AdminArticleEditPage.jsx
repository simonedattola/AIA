import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import {
  adminArticle, adminCreateArticle, adminUpdateArticle, adminUpload,
  adminArticleCategories, adminAddArticleCategory,
} from "../../lib/api";
import RichTextEditor from "./RichTextEditor";
import LegacyArticleBodyEditor from "../../components/admin/LegacyArticleBodyEditor";
import ArticleProse from "../../components/ArticleProse";
import { MemberMultiSelect } from "../../components/admin/MemberSelect";
import { Save, ArrowLeft, Eye, Upload, X, Plus } from "lucide-react";
import { AdminPageHeader } from "../../components/admin/admin-ui";
import { ADMIN_ROUTES as R } from "../../lib/appRoutes";
import { Button } from "@/design-system";

export default function AdminArticleEditPage() {
  const { id } = useParams();
  const isNew = !id || id === "new";
  const navigate = useNavigate();
  const [categories, setCategories] = useState(["Vita sezionale"]);
  const [newCategory, setNewCategory] = useState("");
  const [addingCategory, setAddingCategory] = useState(false);
  const [form, setForm] = useState({
    title: "", slug: "", category: "Vita sezionale", excerpt: "", bodyHtml: "",
    coverUrl: "", bodyInGallery: false, status: "published",
    publishedAt: new Date().toISOString().slice(0, 10),
    relatedMemberIds: [],
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState(false);
  const [uploadingCover, setUploadingCover] = useState(false);

  useEffect(() => {
    adminArticleCategories().then((list) => {
      if (Array.isArray(list) && list.length) setCategories(list);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!isNew) {
      adminArticle(id).then((a) => {
        setForm({
          ...a,
          publishedAt: a.publishedAt ? a.publishedAt.slice(0, 10) : new Date().toISOString().slice(0, 10),
        });
      }).catch(() => setError("Articolo non trovato"));
    }
  }, [id, isNew]);

  const onChange = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const bodyImageCount = useMemo(() => {
    if (!form.bodyHtml?.trim()) return 0;
    const doc = new DOMParser().parseFromString(form.bodyHtml, "text/html");
    const urls = [...doc.querySelectorAll("img")]
      .map((img) => img.getAttribute("src") || "")
      .filter(Boolean);
    return new Set(urls).size;
  }, [form.bodyHtml]);

  const addCategory = async () => {
    const name = newCategory.trim();
    if (!name) return;
    setAddingCategory(true);
    setError("");
    try {
      const updated = await adminAddArticleCategory(name);
      setCategories(updated);
      setForm({ ...form, category: name });
      setNewCategory("");
    } catch (err) {
      setError(err?.response?.data?.detail || "Impossibile aggiungere la categoria");
    } finally {
      setAddingCategory(false);
    }
  };

  const uploadCover = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setUploadingCover(true);
    try {
      const res = await adminUpload(f);
      setForm({ ...form, coverUrl: res.url });
    } catch (err) {
      setError("Upload fallito: " + (err?.response?.data?.detail || err.message));
    } finally {
      setUploadingCover(false);
    }
  };

  const save = async () => {
    setError("");
    setSaving(true);
    try {
      const payload = {
        ...form,
        authorName: form.authorName || "Redazione AIA Legnano",
        portalOnly: false,
        coverInGallery: false,
        publishedAt: form.publishedAt ? `${form.publishedAt}T08:00:00+00:00` : null,
      };
      if (isNew) {
        const res = await adminCreateArticle(payload);
        navigate(R.articolo(res.id), { replace: true });
      } else {
        await adminUpdateArticle(id, payload);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Errore salvataggio");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div data-testid="admin-article-edit">
      <Link to={R.articoli} className="inline-flex items-center gap-1.5 text-slate-500 hover:text-navy-600 text-sm mb-2">
        <ArrowLeft className="h-4 w-4"/> Tutti gli articoli
      </Link>
      <AdminPageHeader title={isNew ? "Nuovo articolo" : "Modifica articolo"}>
        <div className="flex gap-2">
          <Button onClick={() => setPreview(!preview)} variant="outline" data-testid="admin-article-preview-toggle">
            <Eye className="h-4 w-4"/> {preview ? "Modifica" : "Anteprima"}
          </Button>
          <Button onClick={save} disabled={saving} variant="primary" className="disabled:opacity-50" data-testid="admin-article-save">
            <Save className="h-4 w-4"/> {saving ? "Salvataggio…" : "Salva"}
          </Button>
        </div>
      </AdminPageHeader>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded mb-5 text-sm" data-testid="admin-article-error">{error}</div>}

      {preview ? (
        <article className="bg-white rounded-lg border border-slate-200 p-8 lg:p-12 max-w-3xl mx-auto" data-testid="admin-article-preview">
          {form.coverUrl && <img src={form.coverUrl} alt="" className="rounded-md mb-6 w-full"/>}
          <div className="text-xs uppercase tracking-wider font-semibold text-navy-600 mb-2">{form.category}</div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold text-navy-700 mb-4 leading-tight">{form.title}</h1>
          {form.excerpt && <p className="text-lg text-slate-600 italic border-l-4 border-gold-400 pl-5 mb-8">{form.excerpt}</p>}
          <ArticleProse html={form.bodyHtml} />
        </article>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 space-y-6">
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <Field label="Titolo*">
                <input data-testid="admin-article-title" value={form.title} onChange={onChange("title")} className={inputCls} />
              </Field>
              <Field label="Anteprima (riassunto breve)">
                <textarea data-testid="admin-article-excerpt" rows={2} value={form.excerpt} onChange={onChange("excerpt")} className={inputCls}/>
              </Field>
            </div>
            <div className="bg-white rounded-lg border border-slate-200 p-6">
              <label className="block text-sm font-medium text-slate-700 mb-2">Contenuto</label>
              {form.legacyWpId ? (
                <LegacyArticleBodyEditor
                  value={form.bodyHtml}
                  onChange={(html) => setForm({ ...form, bodyHtml: html })}
                />
              ) : (
                <RichTextEditor value={form.bodyHtml} onChange={(html) => setForm({ ...form, bodyHtml: html })} />
              )}
            </div>
          </div>

          <div className="lg:col-span-4 space-y-6">
            <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-4">
              <h3 className="font-display font-semibold text-navy-700 mb-2">Pubblicazione</h3>
              <Field label="Stato">
                <select data-testid="admin-article-status" value={form.status} onChange={onChange("status")} className={inputCls}>
                  <option value="published">Pubblicato</option>
                  <option value="draft">Bozza</option>
                </select>
              </Field>
              <Field label="Data pubblicazione">
                <input data-testid="admin-article-publishedAt" type="date" value={form.publishedAt} onChange={onChange("publishedAt")} className={inputCls}/>
              </Field>
              <Field label="Categoria">
                <select data-testid="admin-article-category" value={form.category} onChange={onChange("category")} className={inputCls}>
                  {categories.map((c) => <option key={c} value={c}>{c}</option>)}
                  {form.category && !categories.includes(form.category) && (
                    <option value={form.category}>{form.category}</option>
                  )}
                </select>
                <div className="mt-2 flex gap-2">
                  <input
                    data-testid="admin-article-new-category"
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCategory())}
                    className={`${inputCls} flex-1`}
                    placeholder="Nuova categoria…"
                  />
                  <Button
                    type="button"
                    onClick={addCategory}
                    disabled={addingCategory || !newCategory.trim()}
                    variant="outline"
                    className="shrink-0 disabled:opacity-50"
                    data-testid="admin-article-add-category"
                  >
                    <Plus className="h-4 w-4"/> {addingCategory ? "…" : "Aggiungi"}
                  </Button>
                </div>
                <p className="text-xs text-slate-500 mt-1.5">Le categorie restano disponibili per i prossimi articoli.</p>
              </Field>
              <MemberMultiSelect
                value={form.relatedMemberIds || []}
                onChange={(ids) => setForm({ ...form, relatedMemberIds: ids })}
                label="Associati in questa notizia"
                searchOnly
              />
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-4">
              <h3 className="font-display font-semibold text-navy-700 mb-2">Immagine di copertina</h3>
              {form.coverUrl && (
                <div className="relative">
                  <img src={form.coverUrl} alt="" className="w-full rounded-md"/>
                  <button onClick={() => setForm({ ...form, coverUrl: "" })} className="absolute top-2 right-2 p-1.5 bg-white rounded-full shadow-md text-red-600">
                    <X className="h-4 w-4"/>
                  </button>
                </div>
              )}
              <Field label="URL immagine">
                <input data-testid="admin-article-coverUrl" value={form.coverUrl} onChange={onChange("coverUrl")} className={inputCls} placeholder="https://..."/>
              </Field>
              <label className="block">
                <span className="block text-sm font-medium text-slate-700 mb-1.5">Oppure carica file</span>
                <div className="relative">
                  <input type="file" accept="image/*" onChange={uploadCover} className="hidden" id="cover-upload" data-testid="admin-article-cover-upload"/>
                  <label htmlFor="cover-upload" className="cursor-pointer block">
                    <Button type="button" variant="outline" className="w-full justify-center pointer-events-none" tabIndex={-1}>
                      <Upload className="h-4 w-4"/> {uploadingCover ? "Caricamento…" : "Carica immagine"}
                    </Button>
                  </label>
                </div>
              </label>
              <label className="flex items-start gap-2 pt-2 border-t border-slate-100">
                <input
                  type="checkbox"
                  checked={!!form.bodyInGallery}
                  onChange={(e) => setForm({ ...form, bodyInGallery: e.target.checked })}
                  className="mt-1"
                  data-testid="admin-article-body-gallery"
                />
                <span className="text-sm text-slate-700">
                  <strong>Aggiungi immagini del contenuto alla Galleria</strong>
                  {" — "}
                  {bodyImageCount > 0
                    ? `${bodyImageCount} ${bodyImageCount === 1 ? "foto rilevata" : "foto rilevate"} nel testo; compaiono nel carosello in home`
                    : "tutte le foto inserite nel testo compaiono nel carosello in home"}
                </span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const inputCls = "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";

function Field({ label, children }) {
  return (
    <label className="block mb-4 last:mb-0">
      <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
      {children}
    </label>
  );
}
