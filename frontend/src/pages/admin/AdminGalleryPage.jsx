import { useCallback, useEffect, useMemo, useState } from "react";
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
import { Check, Clock, ImagePlus, Trash2, Upload, X, Pencil, Plus } from "lucide-react";
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

export default function AdminGalleryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [adding, setAdding] = useState(false);
  const [filter, setFilter] = useState("all");

  const [carouselItems, setCarouselItems] = useState([]);
  const [carouselUploading, setCarouselUploading] = useState(false);
  const [caption, setCaption] = useState("");
  const [uploadCategory, setUploadCategory] = useState("");
  const [uploadMemberIds, setUploadMemberIds] = useState([]);
  const [cropSession, setCropSession] = useState(null);
  const [pendingUpload, setPendingUpload] = useState(null);
  const [categories, setCategories] = useState([]);
  const [newCategory, setNewCategory] = useState("");
  const [addingCategory, setAddingCategory] = useState(false);

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
    if (filter === "pending") return carouselItems.filter((img) => img.status === "pending");
    if (filter === "approved") return carouselItems.filter((img) => img.status === "approved");
    return carouselItems;
  }, [carouselItems, filter]);

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

  const clearPendingUpload = () => {
    if (pendingUpload?.previewUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(pendingUpload.previewUrl);
    }
    setPendingUpload(null);
  };

  const closeAdding = () => {
    clearPendingUpload();
    setAdding(false);
  };

  const onCarouselFilePick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    clearPendingUpload();
    setPendingUpload({ file: f, previewUrl: URL.createObjectURL(f) });
    e.target.value = "";
  };

  const confirmUploadPick = () => {
    if (!pendingUpload) return;
    setCropSession({
      kind: "upload",
      file: pendingUpload.file,
      previewUrl: pendingUpload.previewUrl,
      caption,
      category: uploadCategory,
      memberIds: uploadMemberIds,
    });
    setPendingUpload(null);
    setAdding(false);
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
      URL.revokeObjectURL(cropSession.previewUrl);
    }
    setCropSession(null);
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
        setCaption("");
        setUploadCategory("");
        setUploadMemberIds([]);
        setAdding(false);
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
      }
      closeCropSession();
      loadCarousel();
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
    aspect === "9:16" ? "aspect-[9/16] max-h-64 mx-auto w-auto" : "aspect-[16/9]";

  return (
    <div data-testid="admin-gallery">
      <AdminPageHeader
        title="Galleria"
        description="Foto per il carosello in home e proposte dagli associati. Quelle in attesa di approvazione sono evidenziate. Al caricamento ritaglia in 16:9 o 9:16."
      >
        <Button
          type="button"
          onClick={() => setAdding(true)}
          variant="primary"
          data-testid="admin-gallery-add"
        >
          <Plus className="h-4 w-4" /> Nuova foto
        </Button>
      </AdminPageHeader>

      {adding && (
        <AdminFormModal
          open
          title="Nuova foto carosello"
          onClose={closeAdding}
          testid="admin-gallery-upload-form"
          footer={
            <>
              <Button type="button" onClick={closeAdding} variant="outline">
                Annulla
              </Button>
              {pendingUpload ? (
                <Button type="button" onClick={confirmUploadPick} variant="primary" disabled={carouselUploading} data-testid="admin-gallery-upload-confirm">
                  <Check className="h-4 w-4" /> Conferma
                </Button>
              ) : (
                <>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    id="admin-gallery-carousel-file"
                    onChange={onCarouselFilePick}
                    disabled={carouselUploading}
                  />
                  <label htmlFor="admin-gallery-carousel-file" className="cursor-pointer inline-flex">
                    <Button type="button" variant="primary" className="pointer-events-none" tabIndex={-1} disabled={carouselUploading}>
                      <Upload className="h-4 w-4" /> Seleziona file
                    </Button>
                  </label>
                </>
              )}
            </>
          }
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <label className="block">
              <span className="block text-sm font-medium text-slate-700 mb-1.5">Didascalia (opzionale)</span>
              <input value={caption} onChange={(e) => setCaption(e.target.value)} className={inputCls} placeholder="es. Premiazione fine stagione" />
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
          />
          {pendingUpload ? (
            <div className="rounded-lg border border-slate-200 overflow-hidden bg-slate-100">
              <img src={pendingUpload.previewUrl} alt="" className="w-full max-h-64 object-contain mx-auto" />
              <p className="text-xs text-slate-500 p-2 text-center">
                Anteprima — premi Conferma per ritagliare in 16:9 o 9:16
              </p>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              Seleziona un file, poi conferma per aprire l&apos;editor di ritaglio. La data viene impostata automaticamente.
            </p>
          )}
        </AdminFormModal>
      )}

      <AdminTableWrap>
        <div className="p-4 border-b border-slate-200">
          <AdminFilterTabs
            active={filter}
            onChange={setFilter}
            tabs={[
              { id: "all", label: "Tutte", count: carouselItems.length },
              { id: "pending", label: "In attesa di approvazione", count: pendingCount },
              { id: "approved", label: "Approvate", count: approvedCount },
            ]}
          />
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
                      <Pencil className="h-3.5 w-3.5" /> Modifica
                    </Button>
                  </div>
                </div>
                <MemberMultiSelect
                  label="Associati taggati"
                  value={img.memberIds || []}
                  onChange={(ids) => saveCarouselMeta(img, { memberIds: ids })}
                  searchOnly
                />
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
        />
      )}
    </div>
  );
}
