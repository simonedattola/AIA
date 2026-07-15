import { useState } from "react";
import { Upload, Crop } from "lucide-react";
import { Button } from "@/design-system";
import { adminUpload } from "../../lib/api";
import GalleryCropModal from "./GalleryCropModal";
import {
  aspectOptionsForPreset,
  aspectOptionsForSlot,
  defaultAspectForPreset,
  loadImageBlobUrl,
} from "../../lib/galleryCrop";

const I = "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";

/**
 * Caricamento immagine con ritaglio (come Galleria admin).
 * value = URL visualizzato; sourceValue = originale per ri-ritagliare.
 */
export default function ImageCropUploadField({
  label,
  hint,
  value,
  sourceValue,
  onChange,
  cropPreset = "content",
  slotAspect = null,
  inputId,
}) {
  const [cropSession, setCropSession] = useState(null);
  const [uploading, setUploading] = useState(false);
  const cropAspect = slotAspect || defaultAspectForPreset(cropPreset);
  const cropAspectOptions = slotAspect ? aspectOptionsForSlot(slotAspect) : aspectOptionsForPreset(cropPreset);
  const fieldId = inputId || `crop-up-${label?.replace(/\s+/g, "-") || "img"}`;

  const closeCrop = () => {
    if (cropSession?.previewUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(cropSession.previewUrl);
    }
    setCropSession(null);
  };

  const openCropFromFile = (file) => {
    setCropSession({
      kind: "upload",
      file,
      previewUrl: URL.createObjectURL(file),
    });
  };

  const openCropFromExisting = async () => {
    const src = sourceValue || value;
    if (!src) return;
    try {
      const previewUrl = await loadImageBlobUrl(src);
      setCropSession({ kind: "recrop", previewUrl });
    } catch {
      alert("Impossibile caricare l'immagine per il ritaglio");
    }
  };

  const onFilePick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    openCropFromFile(f);
    e.target.value = "";
  };

  const handleCropConfirm = async ({ croppedBlob }) => {
    if (!cropSession) return;
    setUploading(true);
    try {
      const croppedFile = new File([croppedBlob], "page-crop.jpg", { type: "image/jpeg" });
      const display = await adminUpload(croppedFile);

      if (cropSession.kind === "upload") {
        const source = await adminUpload(cropSession.file);
        onChange({
          url: display.url,
          sourceUrl: source.path || source.url,
        });
      } else {
        onChange({
          url: display.url,
          sourceUrl: sourceValue || value,
        });
      }
      closeCrop();
    } catch (err) {
      alert(err?.message || "Errore durante il caricamento");
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <div className="block mb-4 last:mb-0">
        <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <input type="file" accept="image/*" onChange={onFilePick} className="hidden" id={fieldId} />
            <label htmlFor={fieldId} className="cursor-pointer inline-flex">
              <Button type="button" variant="outline" size="xs" className="text-xs pointer-events-none" tabIndex={-1}>
                <Upload className="h-3.5 w-3.5" /> Carica immagine
              </Button>
            </label>
            {value && (
              <Button type="button" variant="outline" size="xs" className="text-xs" onClick={openCropFromExisting}>
                <Crop className="h-3.5 w-3.5" /> Regola inquadratura
              </Button>
            )}
            {value && <img src={value} alt="" className="h-10 w-10 object-cover rounded border" />}
          </div>
        </div>
        {hint && <span className="block text-xs text-slate-400 mt-1">{hint}</span>}
      </div>

      {cropSession && (
        <GalleryCropModal
          imageSrc={cropSession.previewUrl}
          initialAspect={cropAspect}
          aspectOptions={cropAspectOptions}
          showAspectOptions={false}
          saving={uploading}
          title="Parte dell'immagine da mostrare"
          onConfirm={handleCropConfirm}
          onClose={closeCrop}
        />
      )}
    </>
  );
}
