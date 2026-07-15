import { useState } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import MediaImage from "./MediaImage";

const NAV_BTN =
  "inline-flex items-center justify-center gap-1.5 border border-navy-600 text-navy-600 rounded-md font-semibold text-sm hover:bg-navy-50 transition-colors bg-white px-3 py-2 disabled:opacity-40 disabled:pointer-events-none";

const FRAME_BTN =
  "inline-block max-w-full border border-slate-200 rounded-lg overflow-hidden align-top focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400";

const FRAME_IMG = "block max-h-[32rem] max-w-3xl w-auto h-auto";

function CarouselImageFrame({ image, onOpen }) {
  return (
    <button type="button" onClick={onOpen} className={FRAME_BTN}>
      <MediaImage src={image.src} alt={image.alt || ""} className={FRAME_IMG} loading="lazy" />
    </button>
  );
}

export default function ArticleImageCarousel({ images = [], className = "" }) {
  const [index, setIndex] = useState(0);
  const [lightbox, setLightbox] = useState(false);

  if (!images.length) return null;

  const total = images.length;
  const current = images[Math.min(index, total - 1)];

  const go = (delta) => {
    setIndex((i) => (i + delta + total) % total);
  };

  const openLightbox = () => setLightbox(true);

  if (total === 1) {
    return (
      <figure className={`article-carousel-figure my-8 mx-auto max-w-full text-center ${className}`}>
        <CarouselImageFrame image={current} onOpen={openLightbox} />
        {lightbox && <Lightbox image={current} onClose={() => setLightbox(false)} />}
      </figure>
    );
  }

  return (
    <figure className={`article-carousel-figure my-10 mx-auto max-w-full text-center ${className}`} data-testid="article-image-carousel">
      <CarouselImageFrame image={current} onOpen={openLightbox} />

      <div className="flex flex-wrap items-center justify-center gap-3 mt-4">
        <button type="button" onClick={() => go(-1)} className={NAV_BTN} aria-label="Precedente">
          <ChevronLeft className="h-4 w-4" />
          Precedente
        </button>
        <span className="text-sm font-medium text-slate-600 tabular-nums min-w-[4.5rem] text-center">
          {index + 1} / {total}
        </span>
        <button type="button" onClick={() => go(1)} className={NAV_BTN} aria-label="Successiva">
          Successiva
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      {lightbox && <Lightbox image={current} onClose={() => setLightbox(false)} />}
    </figure>
  );
}

function Lightbox({ image, onClose }) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <button
        type="button"
        onClick={onClose}
        className="absolute top-4 right-4 text-white p-2 hover:bg-white/10 rounded"
        aria-label="Chiudi"
      >
        <X className="h-7 w-7" />
      </button>
      <MediaImage
        src={image.src}
        alt={image.alt || ""}
        className="max-w-full max-h-[90vh] object-contain"
      />
    </div>
  );
}
