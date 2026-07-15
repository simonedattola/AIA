import { useCallback, useState } from "react";
import Cropper from "react-easy-crop";
import { X } from "lucide-react";
import { Button } from "@/design-system";
import { GALLERY_ASPECT_OPTIONS, galleryAspectRatio, getCroppedImageBlob } from "../../lib/galleryCrop";

export default function GalleryCropModal({
  imageSrc,
  initialAspect = "16:9",
  aspectOptions = GALLERY_ASPECT_OPTIONS,
  showAspectOptions = true,
  saving = false,
  onConfirm,
  onClose,
  title = "Ritaglia foto",
}) {
  const allowed = aspectOptions.map((o) => o.id);
  const fixedAspect = allowed.includes(initialAspect) ? initialAspect : allowed[0] || initialAspect || "16:9";
  const [aspect, setAspect] = useState(fixedAspect);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState(null);

  const onCropComplete = useCallback((_area, pixels) => {
    setCroppedAreaPixels(pixels);
  }, []);

  const handleConfirm = async () => {
    if (!croppedAreaPixels || !imageSrc) return;
    try {
      const blob = await getCroppedImageBlob(imageSrc, croppedAreaPixels);
      await onConfirm({ croppedBlob: blob, aspect: showAspectOptions ? aspect : fixedAspect });
    } catch (err) {
      alert(err?.message || "Impossibile ritagliare l'immagine");
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Ritaglia immagine"
    >
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <h2 className="font-display text-lg font-bold text-navy-700">{title}</h2>
          <button type="button" onClick={onClose} disabled={saving} className="p-2 text-slate-400 hover:bg-slate-100 rounded" aria-label="Chiudi">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {showAspectOptions && aspectOptions.length > 1 && (
            <div className="flex flex-wrap gap-2">
              {aspectOptions.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setAspect(opt.id)}
                  className={`px-4 py-2 rounded-full text-sm font-medium border transition-colors ${
                    aspect === opt.id
                      ? "bg-navy-700 text-white border-navy-700"
                      : "bg-white text-slate-600 border-slate-300 hover:border-navy-400"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
          {!showAspectOptions && (
            <p className="text-sm text-slate-600">
              Trascina e usa lo zoom per scegliere quale parte dell&apos;immagine mostrare.
            </p>
          )}

          <div className="relative w-full h-[min(60vh,28rem)] bg-slate-900 rounded-lg overflow-hidden">
            <Cropper
              image={imageSrc}
              crop={crop}
              zoom={zoom}
              aspect={galleryAspectRatio(showAspectOptions ? aspect : fixedAspect)}
              onCropChange={setCrop}
              onZoomChange={setZoom}
              onCropComplete={onCropComplete}
            />
          </div>

          <label className="block">
            <span className="block text-xs font-medium text-slate-600 mb-1">Zoom</span>
            <input
              type="range"
              min={1}
              max={3}
              step={0.05}
              value={zoom}
              onChange={(e) => setZoom(Number(e.target.value))}
              className="w-full accent-navy-700"
            />
          </label>
        </div>

        <div className="flex justify-end gap-3 px-5 py-4 border-t border-slate-200 bg-slate-50">
          <Button type="button" onClick={onClose} disabled={saving} variant="outline">
            Annulla
          </Button>
          <Button type="button" onClick={handleConfirm} disabled={saving || !croppedAreaPixels} variant="primary">
            {saving ? "Salvataggio…" : showAspectOptions ? "Conferma ritaglio" : "Conferma"}
          </Button>
        </div>
      </div>
    </div>
  );
}
