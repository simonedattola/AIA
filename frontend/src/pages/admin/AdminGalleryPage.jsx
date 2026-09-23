import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  adminGallery,
  asAdminList,
  adminGalleryCreate,
  adminGalleryApprove,
  adminGalleryReject,
  adminGalleryUpdate,
  adminGalleryDelete,
  adminGallerySourceBlob,
  adminUpload,
  adminArticleCategories,
  adminAddArticleCategory,
} from "../../lib/api";
import { MemberMultiSelect } from "../../components/admin/MemberSelect";
import GalleryCropModal from "../../components/admin/GalleryCropModal";
import {
  Check, Clock, ImagePlus, Trash2, Upload, X, Pencil, Plus, Search, CheckCheck,
} from "lucide-react";
import MediaImage from "../../components/MediaImage";
import {
  AdminPageHeader,
  AdminEmptyState,
  AdminFormModal,
  AdminTableWrap,
  AdminFilterTabs,
} from "../../components/admin/admin-ui";
import { Button } from "@/design-system";

const inputCls =
  "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";

const cardInputCls =
  "w-full px-2 py-1.5 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-xs";

const STATUS_LABEL = {
  approved: "Approvata",
  pending: "In attesa",
  rejected: "Rifiutata",
};

function GalleryCategorySelect({ value, onChange, categories, className, emptyLabel = "— Nessuna —" }) {
  return (
    <select value={value} onChange={onChange} className={className}>
      <option value="">{emptyLabel}</option>
      {categories.map((c) => (
        <option key={c} value={c}>{c}</option>
      ))}
      {value && !categories.includes(value) && (
        <option value={value}>{value}</option>
      )}
    </select>
  );
}

function revokePreview(url) {
  if (url?.startsWith("blob:")) URL.revokeObjectURL(url);
}

export default function AdminGalleryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [adding, setAdding] = useState(false);
  const [filter, setFilter] = useState("all");
  const [searchQ, setSearchQ] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const [carouselItems, setCarouselItems] = useState([]);
  const [carouselUploading, setCarouselUploading] = useState(false);
  const [caption, setCaption] = useState("");
  const [uploadCategory, setUploadCategory] = useState("");
  const [uploadMemberIds, setUploadMemberIds] = useState([]);
  const [pendingFiles, setPendingFiles] = useState([]); // { file, previewUrl }
  const [cropQueue, setCropQueue] = useState([]); // files waiting for crop after confirm
  const [cropSession, setCropSession] = useState(null);
  const [categories, setCategories] = useState([]);
  const [newCategory, setNewCategory] = useState("");
  const [addingCategory, setAddingCategory] = useState(false);
  const [expandedTagId, setExpandedTagId] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [bulkBusy, setBulkBusy] = useState(false);
  const fileInputRef = useRef(null);

  const loadCarousel = useCallback(() => {
    adminGallery()
      .then((data) => setCarouselItems(asAdminList(data)))
      .catch(() => setCarouselItems([]));
  }, []);

  useEffect(() => {
    loadCarousel();
  }, [loadCarousel]);

  const pendingCount = useMemo(
    () => carouselItems.filter((img) => img.status === "pending").length,
    [carouselItems]
  );
  const approvedCount = useMemo(
    () => carouselItems.filter((img) => img.status === "approved").length,
    [carouselItems]
  );

  const filteredItems = useMemo(() => {
    let list = carouselItems;
    if (filter === "pending") list = list.filter((img) => img.status === "pending");
    else if (filter === "approved") list = list.filter((img) => img.status === "approved");
    if (categoryFilter) {
      list = list.filter((img) => (img.category || "") === categoryFilter);
    }
    const q = searchQ.trim().toLowerCase();
    if (q) {
      list = list.filter((img) => {
        const hay = `${img.caption || ""} ${img.category || ""} ${img.memberName || ""} ${img.photoDate || ""}`.toLowerCase();
        return hay.includes(q);
      });
    }
    // Più recenti in alto
    return [...list].sort((a, b) => {
      const da = (a.photoDate || a.createdAt || "").slice(0, 10);
      const db = (b.photoDate || b.createdAt || "").slice(0, 10);
      if (da !== db) return db.localeCompare(da);
      return (b.sortOrder || 0) - (a.sortOrder || 0);
    });
  }, [carouselItems, filter, categoryFilter, searchQ]);

  const loadCategories = useCallback(() => {
    adminArticleCategories().then(setCategories).catch(() => setCategories([]));
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    if (searchParams.get("new") === "1") {
      setAdding(true);
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const addCategory = async () => {
    const name = newCategory.trim();
    if (!name) return;
    setAddingCategory(true);
    try {
      const updated = await adminAddArticleCategory(name);
      setCategories(updated);
      setUploadCategory(name);
      setNewCategory("");
    } catch (err) {
      alert(err?.response?.data?.detail || "Impossibile aggiungere la categoria");
    } finally {
      setAddingCategory(false);
    }
  };

  const clearPendingFiles = () => {
    pendingFiles.forEach((p) => revokePreview(p.previewUrl));
    setPendingFiles([]);
  };

  const closeAdding = () => {
    clearPendingFiles();
    setAdding(false);
  };

  const appendFiles = (fileList) => {
    const files = [...(fileList || [])].filter((f) => f.type.startsWith("image/"));
    if (!files.length) return;
    setPendingFiles((prev) => [
      ...prev,
      ...files.map((file) => ({ file, previewUrl: URL.createObjectURL(file) })),
    ]);
  };

  const onCarouselFilePick = (e) => {
    appendFiles(e.target.files);
    e.target.value = "";
  };

  const removePendingAt = (idx) => {
    setPendingFiles((prev) => {
      const next = [...prev];
      const [removed] = next.splice(idx, 1);
      revokePreview(removed?.previewUrl);
      return next;
    });
  };

  const startCropQueue = (files, meta) => {
    if (!files.length) return;
    const [first, ...rest] = files;
    setCropQueue(rest);
    setCropSession({
      kind: "upload",
      file: first.file || first,
      previewUrl: first.previewUrl || URL.createObjectURL(first.file || first),
      caption: meta.caption || "",
      category: meta.category || "",
      memberIds: meta.memberIds || [],
      queueTotal: files.length,
      queueIndex: 1,
    });
  };

  const confirmUploadPick = () => {
    if (!pendingFiles.length) return;
    const files = [...pendingFiles];
    setPendingFiles([]);
    setAdding(false);
    startCropQueue(files, {
      caption,
      category: uploadCategory,
      memberIds: uploadMemberIds,
    });
  };

  const openEditCrop = async (item) => {
    try {
      const blob = await adminGallerySourceBlob(item.id);
      const previewUrl = URL.createObjectURL(blob);
      setCropSession({
        kind: "edit",
        item,
        previewUrl,
      });
    } catch {
      alert("Impossibile caricare l'immagine per il ritaglio");
    }
  };

  const closeCropSession = () => {
    if (cropSession?.previewUrl?.startsWith("blob:")) {
      revokePreview(cropSession.previewUrl);
    }
    cropQueue.forEach((f) => revokePreview(f.previewUrl));
    setCropQueue([]);
    setCropSession(null);
  };

  const advanceUploadQueue = (meta) => {
    if (!cropQueue.length) {
      setCropSession(null);
      setCaption("");
      setUploadCategory("");
      setUploadMemberIds([]);
      loadCarousel();
      return;
    }
    const [next, ...rest] = cropQueue;
    setCropQueue(rest);
    setCropSession({
      kind: "upload",
      file: next.file,
      previewUrl: next.previewUrl,
      caption: meta.caption,
      category: meta.category,
      memberIds: meta.memberIds,
      queueTotal: meta.queueTotal,
      queueIndex: (meta.queueIndex || 1) + 1,
    });
  };

  const handleCropConfirm = async ({ croppedBlob, aspect }) => {
    if (!cropSession) return;
    setCarouselUploading(true);
    try {
      const croppedFile = new File([croppedBlob], "gallery-crop.jpg", { type: "image/jpeg" });
      const display = await adminUpload(croppedFile);

      if (cropSession.kind === "upload") {
        const source = await adminUpload(cropSession.file);
        await adminGalleryCreate({
          url: display.url,
          path: display.path || display.url,
          sourceUrl: source.path || source.url,
          aspect,
          caption: cropSession.caption || "",
          category: cropSession.category || "",
          memberIds: cropSession.memberIds || [],
        });
        revokePreview(cropSession.previewUrl);
        advanceUploadQueue({
          caption: cropSession.caption,
          category: cropSession.category,
          memberIds: cropSession.memberIds,
          queueTotal: cropSession.queueTotal,
          queueIndex: cropSession.queueIndex,
        });
      } else {
        const item = cropSession.item;
        const sourceUrl = item.sourceUrl || item.url;
        await adminGalleryUpdate(item.id, {
          caption: item.caption || "",
          sortOrder: item.sortOrder || 0,
          category: item.category || "",
          memberIds: item.memberIds || [],
          url: display.url,
          path: display.path || display.url,
          sourceUrl,
          aspect,
        });
        closeCropSession();
        loadCarousel();
      }
    } catch (err) {
      alert(err?.response?.data?.detail || "Salvataggio fallito");
    } finally {
      setCarouselUploading(false);
    }
  };

  const approve = async (id) => {
    await adminGalleryApprove(id);
    loadCarousel();
  };

  const reject = async (id) => {
    if (!window.confirm("Rifiutare questa immagine?")) return;
    await adminGalleryReject(id);
    loadCarousel();
  };

  const removeCarousel = async (id) => {
    if (!window.confirm("Eliminare definitivamente?")) return;
    await adminGalleryDelete(id);
    loadCarousel();
  };

  const approveAllPending = async () => {
    const pending = carouselItems.filter((i) => i.status === "pending");
    if (!pending.length) return;
    if (!window.confirm(`Approvare ${pending.length} foto in attesa?`)) return;
    setBulkBusy(true);
    try {
      for (const img of pending) {
        await adminGalleryApprove(img.id);
      }
      loadCarousel();
    } catch (err) {
      alert(err?.response?.data?.detail || "Approvazione multipla fallita");
    } finally {
      setBulkBusy(false);
    }
  };

  const saveCarouselMeta = async (item, patch) => {
    await adminGalleryUpdate(item.id, {
      caption: patch.caption ?? item.caption ?? "",
      sortOrder: item.sortOrder || 0,
      category: patch.category ?? item.category ?? "",
      memberIds: patch.memberIds ?? item.memberIds ?? [],
    });
    loadCarousel();
  };

  const cardAspectClass = (aspect) =>
    aspect === "9:16" ? "aspect-[9/16] max-h-56 mx-auto w-auto" : "aspect-[16/9]";

  return (
    <div data-testid="admin-gallery">
      <AdminPageHeader
        title="Galleria"
        description="Carosello home e proposte degli associati. Carica più foto insieme, ritaglia in 16:9 o 9:16, tagga per ruolo."
      >
        <div className="flex flex-wrap gap-2">
          {pendingCount > 0 && (
            <Button
              type="button"
              onClick={approveAllPending}
              variant="outline"
              disabled={bulkBusy}
              data-testid="admin-gallery-approve-all"
            >
              <CheckCheck className="h-4 w-4" />
              {bulkBusy ? "…" : `Approva tutte (${pendingCount})`}
            </Button>
          )}
          <Button
            type="button"
            onClick={() => setAdding(true)}
            variant="primary"
            data-testid="admin-gallery-add"
          >
            <Plus className="h-4 w-4" /> Carica foto
          </Button>
        </div>
      </AdminPageHeader>

      {adding && (
        <AdminFormModal
          open
          title="Carica foto"
          onClose={closeAdding}
          testid="admin-gallery-upload-form"
          footer={
            <>
              <Button type="button" onClick={closeAdding} variant="outline">
                Annulla
              </Button>
              <Button
                type="button"
                onClick={confirmUploadPick}
                variant="primary"
                disabled={!pendingFiles.length || carouselUploading}
                data-testid="admin-gallery-upload-confirm"
              >
                <Check className="h-4 w-4" />
                {pendingFiles.length
                  ? `Ritaglia e pubblica (${pendingFiles.length})`
                  : "Seleziona almeno una foto"}
              </Button>
            </>
          }
        >
          <div
            className={`rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
              dragOver ? "border-navy-500 bg-navy-50" : "border-slate-300 bg-slate-50"
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              appendFiles(e.dataTransfer.files);
            }}
            data-testid="admin-gallery-dropzone"
          >
            <ImagePlus className="h-8 w-8 text-slate-400 mx-auto mb-2" />
            <p className="text-sm text-slate-700 font-medium mb-1">
              Trascina qui le immagini, oppure scegli i file
            </p>
            <p className="text-xs text-slate-500 mb-3">Puoi selezionare più file insieme</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              id="admin-gallery-carousel-file"
              onChange={onCarouselFilePick}
              disabled={carouselUploading}
            />
            <label htmlFor="admin-gallery-carousel-file" className="cursor-pointer inline-flex">
              <Button type="button" variant="outline" className="pointer-events-none" tabIndex={-1}>
                <Upload className="h-4 w-4" /> Seleziona file
              </Button>
            </label>
          </div>

          {pendingFiles.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-4" data-testid="admin-gallery-pending-previews">
              {pendingFiles.map((p, idx) => (
                <div key={p.previewUrl} className="relative rounded-md overflow-hidden border border-slate-200 bg-slate-100">
                  <img src={p.previewUrl} alt="" className="w-full h-24 object-cover" />
                  <button
                    type="button"
                    onClick={() => removePendingAt(idx)}
                    className="absolute top-1 right-1 p-1 bg-white/90 rounded-full text-red-600 shadow"
                    aria-label="Rimuovi"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                  <p className="text-[10px] text-slate-500 truncate px-1 py-0.5">{p.file.name}</p>
                </div>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <label className="block">
              <span className="block text-sm font-medium text-slate-700 mb-1.5">Didascalia (opzionale)</span>
              <input
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                className={inputCls}
                placeholder="Applicata a tutte le foto di questo caricamento"
              />
            </label>
            <label className="block">
              <span className="block text-sm font-medium text-slate-700 mb-1.5">Categoria</span>
              <GalleryCategorySelect
                value={uploadCategory}
                onChange={(e) => setUploadCategory(e.target.value)}
                categories={categories}
                className={inputCls}
              />
              <div className="mt-2 flex gap-2">
                <input
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCategory())}
                  className={`${inputCls} flex-1`}
                  placeholder="Nuova categoria…"
                  data-testid="admin-gallery-new-category"
                />
                <Button
                  type="button"
                  onClick={addCategory}
                  disabled={addingCategory || !newCategory.trim()}
                  variant="outline"
                  className="shrink-0"
                  data-testid="admin-gallery-add-category"
                >
                  <Plus className="h-4 w-4" /> {addingCategory ? "…" : "Aggiungi"}
                </Button>
              </div>
            </label>
          </div>
          <MemberMultiSelect
            label="Associati taggati"
            value={uploadMemberIds}
            onChange={setUploadMemberIds}
            searchOnly
            withRoleFilter
          />
        </AdminFormModal>
      )}

      <AdminTableWrap>
        <div className="p-4 border-b border-slate-200 space-y-3">
          <AdminFilterTabs
            active={filter}
            onChange={setFilter}
            tabs={[
              { id: "all", label: "Tutte", count: carouselItems.length },
              { id: "pending", label: "In attesa", count: pendingCount },
              { id: "approved", label: "Approvate", count: approvedCount },
            ]}
          />
          <div className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1 min-w-0">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="search"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                placeholder="Cerca didascalia, categoria…"
                className={`${inputCls} pl-9`}
                data-testid="admin-gallery-search"
              />
            </div>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className={`${inputCls} sm:w-48`}
              data-testid="admin-gallery-category-filter"
            >
              <option value="">Tutte le categorie</option>
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="p-4">
          {filteredItems.length === 0 ? (
            <AdminEmptyState icon={ImagePlus} title="Nessuna immagine in questa vista.">
              {filter === "pending"
                ? "Nessuna foto in attesa di approvazione."
                : "Carica foto per il carosello home e tagga gli associati che le vedranno in area riservata."}
            </AdminEmptyState>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 min-w-0">
              {filteredItems.map((img) => (
                <div
                  key={img.id}
                  className={`bg-white rounded-md border overflow-hidden text-sm min-w-0 ${
                    img.status === "pending" ? "border-gold-300 bg-gold-50/30" : "border-slate-200"
                  }`}
                  data-testid={`gallery-item-${img.id}`}
                >
                  <div className={`bg-slate-100 ${cardAspectClass(img.aspect)}`}>
                    <MediaImage src={img.url} alt="" className="w-full h-full object-cover" />
                  </div>
                  <div className="p-2.5 space-y-2">
                    <div className="flex items-center justify-between gap-2 text-xs">
                      <span
                        className={`px-2 py-0.5 rounded font-medium ${
                          img.status === "pending"
                            ? "bg-amber-100 text-amber-800"
                            : img.status === "approved"
                              ? "bg-green-100 text-green-800"
                              : "bg-slate-100 text-slate-600"
                        }`}
                      >
                        {STATUS_LABEL[img.status] || img.status}
                      </span>
                      <span className="text-slate-400 truncate text-right">
                        {img.photoDate && <span className="mr-2">{img.photoDate}</span>}
                        {img.aspect === "9:16" ? "9:16" : "16:9"}
                        {" · "}
                        {img.source === "member" && img.memberName
                          ? img.memberName
                          : img.source?.startsWith("article")
                            ? "Da articolo"
                            : "Admin"}
                      </span>
                    </div>
                    <input
                      defaultValue={img.caption || ""}
                      className={cardInputCls}
                      placeholder="Didascalia"
                      onBlur={(e) => {
                        if (e.target.value !== (img.caption || "")) saveCarouselMeta(img, { caption: e.target.value });
                      }}
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <label className="block">
                        <span className="block text-xs text-slate-500 mb-0.5">Categoria</span>
                        <GalleryCategorySelect
                          value={img.category || ""}
                          onChange={(e) => saveCarouselMeta(img, { category: e.target.value })}
                          categories={categories}
                          className={cardInputCls}
                          emptyLabel="—"
                        />
                      </label>
                      <div className="flex items-end">
                        <Button
                          type="button"
                          onClick={() => openEditCrop(img)}
                          variant="outline"
                          className="text-[11px] py-1.5 w-full justify-center"
                        >
                          <Pencil className="h-3.5 w-3.5" /> Ritaglia
                        </Button>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setExpandedTagId(expandedTagId === img.id ? null : img.id)}
                      className="text-xs font-medium text-navy-700 hover:text-navy-900"
                      data-testid={`gallery-toggle-tags-${img.id}`}
                    >
                      {(img.memberIds || []).length
                        ? `Associati taggati (${(img.memberIds || []).length})`
                        : "Tagga associati"}
                      {expandedTagId === img.id ? " ▴" : " ▾"}
                    </button>
                    {expandedTagId === img.id && (
                      <MemberMultiSelect
                        label="Associati taggati"
                        value={img.memberIds || []}
                        onChange={(ids) => saveCarouselMeta(img, { memberIds: ids })}
                        searchOnly
                        withRoleFilter
                      />
                    )}
                    <div className="flex flex-wrap gap-2">
                      {img.status === "pending" && (
                        <>
                          <Button type="button" onClick={() => approve(img.id)} variant="primary" size="sm" className="text-xs py-1.5">
                            <Check className="h-3.5 w-3.5" /> Approva
                          </Button>
                          <Button type="button" onClick={() => reject(img.id)} variant="outline" size="sm" className="text-xs py-1.5">
                            <X className="h-3.5 w-3.5" /> Rifiuta
                          </Button>
                        </>
                      )}
                      {img.status === "rejected" && (
                        <Button type="button" onClick={() => approve(img.id)} variant="outline" size="sm" className="text-xs py-1.5">
                          <Check className="h-3.5 w-3.5" /> Ripubblica
                        </Button>
                      )}
                      <button type="button" onClick={() => removeCarousel(img.id)} className="p-1.5 text-red-600 hover:bg-red-50 rounded ml-auto" title="Elimina">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {filter === "pending" && filteredItems.length > 0 && (
            <p className="mt-6 text-sm text-slate-500 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Le proposte approvate compaiono nel carosello in home.
            </p>
          )}
        </div>
      </AdminTableWrap>

      {cropSession && (
        <GalleryCropModal
          imageSrc={cropSession.previewUrl}
          initialAspect={cropSession.kind === "edit" ? cropSession.item.aspect : "16:9"}
          saving={carouselUploading}
          onConfirm={handleCropConfirm}
          onClose={closeCropSession}
          title={
            cropSession.kind === "upload" && cropSession.queueTotal > 1
              ? `Ritaglio ${cropSession.queueIndex} di ${cropSession.queueTotal}`
              : undefined
          }
        />
      )}
    </div>
  );
}
