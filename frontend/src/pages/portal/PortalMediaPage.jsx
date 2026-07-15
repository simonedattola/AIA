import { useEffect, useState } from "react";
import { fetchCategories } from "../../lib/api";
import { portalMedia, portalGalleryMine, portalGalleryUpload, portalGalleryCategories } from "../../lib/portal-api";
import { Download, Upload, Clock, CheckCircle, XCircle, ImagePlus } from "lucide-react";
import MediaImage from "../../components/MediaImage";
import { Button } from "@/design-system";
import { PortalEmptyState, PortalPageHeader } from "../../components/portal/portal-ui";

const sectionHeading = "text-sm font-semibold uppercase tracking-wider text-slate-500";

const GALLERY_STATUS = {
  pending: { label: "In attesa", icon: Clock, className: "text-amber-700 bg-amber-50" },
  approved: { label: "In home", icon: CheckCircle, className: "text-green-700 bg-green-50" },
  rejected: { label: "Non approvata", icon: XCircle, className: "text-slate-600 bg-slate-100" },
};

export default function PortalMediaPage() {
  const [taggedPhotos, setTaggedPhotos] = useState([]);
  const [galleryMine, setGalleryMine] = useState([]);
  const [caption, setCaption] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => {
    portalMedia().then(setTaggedPhotos).catch(() => setTaggedPhotos([]));
    portalGalleryMine().then(setGalleryMine).catch(() => setGalleryMine([]));
  };

  useEffect(() => {
    load();
    const applyCategories = (list) => setCategories(Array.isArray(list) ? list : []);
    fetchCategories()
      .then(applyCategories)
      .catch(() =>
        portalGalleryCategories()
          .then(applyCategories)
          .catch(() => setCategories([]))
      );
  }, []);

  const onUpload = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setUploading(true);
    setMsg("");
    try {
      await portalGalleryUpload(f, { caption, category });
      setCaption("");
      setCategory("");
      e.target.value = "";
      setMsg("Proposta inviata: sarà visibile in home dopo l'approvazione.");
      load();
    } catch (err) {
      setMsg(err?.response?.data?.detail || "Upload non riuscito");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div data-testid="portal-media-page">
      <PortalPageHeader
        title="Galleria"
        description="Foto in cui sei taggato e proposte per il carosello del sito."
      />

      <section className="mb-10">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <h2 className={sectionHeading}>Le tue foto</h2>
          {taggedPhotos.length > 0 && (
            <p className="text-sm text-slate-500">
              {taggedPhotos.length} {taggedPhotos.length === 1 ? "immagine" : "immagini"}
            </p>
          )}
        </div>

        {taggedPhotos.length === 0 ? (
          <PortalEmptyState icon={ImagePlus}>
            Nessuna foto con il tuo tag. La sezione le aggiunge dal carosello home.
          </PortalEmptyState>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {taggedPhotos.map((img) => {
              const url = img.url || img.src;
              return (
                <div key={img.id} className="bg-white rounded-lg border border-slate-200 overflow-hidden group">
                  {url && (
                    <a href={url} target="_blank" rel="noopener noreferrer">
                      <MediaImage src={url} alt={img.caption || ""} className="w-full aspect-square object-cover" />
                    </a>
                  )}
                  <div className="p-2 flex justify-between items-center gap-2">
                    <div className="min-w-0">
                      {img.caption && <span className="text-xs text-slate-600 truncate block">{img.caption}</span>}
                      {img.photoDate && <span className="text-[10px] text-slate-400">{img.photoDate}</span>}
                    </div>
                    {url && (
                      <a href={url} download className="shrink-0 p-1.5 text-navy-600 hover:bg-navy-50 rounded" title="Scarica">
                        <Download className="h-4 w-4" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="pt-10 border-t border-slate-200">
        <h2 className={`${sectionHeading} mb-4`}>Proponi una foto</h2>
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <p className="text-sm text-slate-600 mb-4">
            Invia un&apos;immagine per il carosello in home. L&apos;admin la approverà prima della pubblicazione.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mb-4">
            <label className="block">
              <span className="block text-sm font-medium text-slate-700 mb-1.5">Didascalia (opzionale)</span>
              <input
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                placeholder="es. Raduno primavera 2026"
              />
            </label>
            <label className="block">
              <span className="block text-sm font-medium text-slate-700 mb-1.5">Categoria (opzionale)</span>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm"
                data-testid="portal-gallery-category"
              >
                <option value="">— Nessuna —</option>
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
          </div>
          <input
            type="file"
            accept="image/*"
            className="hidden"
            id="portal-media-upload"
            onChange={onUpload}
            disabled={uploading}
          />
          <label htmlFor="portal-media-upload" className="cursor-pointer inline-flex">
            <Button type="button" variant="primary" className="pointer-events-none" tabIndex={-1}>
              <Upload className="h-4 w-4" />
              {uploading ? "Invio…" : "Carica foto"}
            </Button>
          </label>
          {msg && <p className="mt-3 text-sm text-navy-700">{msg}</p>}

          {galleryMine.length > 0 && (
            <div className="mt-8 pt-6 border-t border-slate-100">
              <h3 className={`${sectionHeading} mb-3`}>Le tue proposte</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {galleryMine.map((img) => {
                  const st = GALLERY_STATUS[img.status] || GALLERY_STATUS.pending;
                  const Icon = st.icon;
                  return (
                    <div key={img.id} className="rounded-lg border border-slate-200 overflow-hidden">
                      <div className="aspect-square bg-slate-100">
                        <MediaImage src={img.url} alt="" className="w-full h-full object-cover" />
                      </div>
                      <div className="p-2 space-y-1">
                        {img.caption && <p className="text-xs text-slate-600 truncate">{img.caption}</p>}
                        {img.category && <p className="text-[10px] text-slate-500 truncate">{img.category}</p>}
                        <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded ${st.className}`}>
                          <Icon className="h-3 w-3" /> {st.label}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
