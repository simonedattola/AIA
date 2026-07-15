export const GALLERY_ASPECT_OPTIONS = [
  { id: "16:9", label: "Orizzontale 16:9", ratio: 16 / 9 },
  { id: "9:16", label: "Verticale 9:16", ratio: 9 / 16 },
];

export const PAGE_ASPECT_OPTIONS = [
  { id: "16:9", label: "Banner 16:9", ratio: 16 / 9 },
  { id: "4:3", label: "Orizzontale 4:3", ratio: 4 / 3 },
  { id: "3:4", label: "Verticale 3:4", ratio: 3 / 4 },
  { id: "4:5", label: "Verticale 4:5", ratio: 4 / 5 },
  { id: "1:1", label: "Quadrata 1:1", ratio: 1 },
  { id: "9:16", label: "Verticale 9:16", ratio: 9 / 16 },
];

/** Preset ritaglio per contesto (hero, contenuto, galleria pagina, ecc.). */
export const PAGE_CROP_PRESETS = {
  hero: { defaultAspect: "16:9", aspects: ["16:9"] },
  banner: { defaultAspect: "16:9", aspects: ["16:9"] },
  portrait: { defaultAspect: "3:4", aspects: ["3:4"] },
  portraitTall: { defaultAspect: "9:16", aspects: ["9:16"] },
  content: { defaultAspect: "4:3", aspects: ["4:3"] },
  square: { defaultAspect: "1:1", aspects: ["1:1"] },
  gallery: { defaultAspect: "4:3", aspects: ["4:3", "16:9", "1:1", "9:16"] },
};

/** Opzioni singolo formato per cornice fissa (ritaglio pan/zoom, senza scelta formato). */
export function aspectOptionsForSlot(aspectId) {
  const opt = PAGE_ASPECT_OPTIONS.find((o) => o.id === aspectId);
  return opt ? [opt] : PAGE_ASPECT_OPTIONS.filter((o) => o.id === "16:9");
}

export function galleryAspectRatio(aspect) {
  const map = {
    "16:9": 16 / 9,
    "9:16": 9 / 16,
    "4:3": 4 / 3,
    "3:4": 3 / 4,
    "4:5": 4 / 5,
    "1:1": 1,
  };
  return map[aspect] ?? 16 / 9;
}

export function aspectOptionsForPreset(preset) {
  const cfg = PAGE_CROP_PRESETS[preset] || PAGE_CROP_PRESETS.content;
  return PAGE_ASPECT_OPTIONS.filter((opt) => cfg.aspects.includes(opt.id));
}

export function defaultAspectForPreset(preset) {
  return (PAGE_CROP_PRESETS[preset] || PAGE_CROP_PRESETS.content).defaultAspect;
}

/** Carica un'immagine remota come blob URL (evita problemi CORS in canvas). */
export async function loadImageBlobUrl(src) {
  const res = await fetch(src);
  if (!res.ok) throw new Error("Impossibile caricare l'immagine");
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

function createImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.addEventListener("load", () => resolve(img));
    img.addEventListener("error", reject);
    img.crossOrigin = "anonymous";
    img.src = url;
  });
}

/** Qualità JPEG export ritaglio pagine/galleria (0–1). */
export const CROP_JPEG_QUALITY = 0.96;

/** Ritaglia l'immagine e restituisce un Blob JPEG alla risoluzione nativa del ritaglio. */
export async function getCroppedImageBlob(imageSrc, pixelCrop, quality = CROP_JPEG_QUALITY) {
  const image = await createImage(imageSrc);
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas non disponibile");

  canvas.width = Math.max(1, Math.round(pixelCrop.width));
  canvas.height = Math.max(1, Math.round(pixelCrop.height));
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(
    image,
    pixelCrop.x,
    pixelCrop.y,
    pixelCrop.width,
    pixelCrop.height,
    0,
    0,
    pixelCrop.width,
    pixelCrop.height,
  );

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (!blob) reject(new Error("Ritaglio fallito"));
        else resolve(blob);
      },
      "image/jpeg",
      quality,
    );
  });
}
