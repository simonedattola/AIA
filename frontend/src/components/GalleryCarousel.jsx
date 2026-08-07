import { useRef, useState } from "react";
import { ChevronLeft, ChevronRight, X } from "lucide-react";
import MediaImage from "./MediaImage";
import { Button, Eyebrow, SectionTitle } from "@/design-system";

const SLIDE_BASE =
  "gallery-strip-item shrink-0 h-44 sm:h-52 overflow-hidden rounded-lg bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400";

function slideClass(aspect) {
  return aspect === "9:16" ? `${SLIDE_BASE} aspect-[9/16]` : `${SLIDE_BASE} aspect-[16/9]`;
}

/**
 * Fascia galleria: foto ritagliate 16:9 o 9:16, frecce stile nav.
 */
export default function GalleryCarousel({ images = [], className = "", showTitle = false }) {
  const trackRef = useRef(null);
  const [lightbox, setLightbox] = useState(null);

  const scroll = (dir) => {
    const el = trackRef.current;
    if (!el || images.length < 2) return;
    const first = el.querySelector(".gallery-strip-item");
    const step = first ? first.getBoundingClientRect().width + 8 : 300;
    const maxScroll = Math.max(0, el.scrollWidth - el.clientWidth);
    const atStart = el.scrollLeft <= 4;
    const atEnd = el.scrollLeft >= maxScroll - 4;

    if (dir > 0) {
      if (atEnd) el.scrollTo({ left: 0, behavior: "smooth" });
      else el.scrollBy({ left: step, behavior: "smooth" });
      return;
    }
    if (atStart) el.scrollTo({ left: maxScroll, behavior: "smooth" });
    else el.scrollBy({ left: -step, behavior: "smooth" });
  };

  if (!images.length) return null;

  return (
    <section
      className={`w-full bg-transparent px-4 sm:px-6 lg:px-8 site-section ${className}`}
      data-testid="site-gallery"
      aria-label="Galleria"
    >
      {showTitle && (
        <div className="max-w-7xl mx-auto pb-6">
          <Eyebrow className="mb-2">In immagini</Eyebrow>
          <SectionTitle>Galleria</SectionTitle>
        </div>
      )}

      <div className="relative w-full max-w-7xl mx-auto">
        <Button
          type="button"
          onClick={() => scroll(-1)}
          variant="outline"
          size="sm"
          className="absolute left-0 top-1/2 z-20 -translate-y-1/2 bg-white shadow-sm p-2.5"
          aria-label="Immagine precedente"
        >
          <ChevronLeft className="h-5 w-5 stroke-[2.5]" />
        </Button>

        <Button
          type="button"
          onClick={() => scroll(1)}
          variant="outline"
          size="sm"
          className="absolute right-0 top-1/2 z-20 -translate-y-1/2 bg-white shadow-sm p-2.5"
          aria-label="Immagine successiva"
        >
          <ChevronRight className="h-5 w-5 stroke-[2.5]" />
        </Button>

        <div
          ref={trackRef}
          className="flex items-center gap-2 overflow-x-auto scroll-smooth bg-transparent gallery-strip-scroll mx-11 sm:mx-12"
        >
          {images.map((img) => (
            <button
              key={img.id}
              type="button"
              onClick={() => setLightbox(img)}
              className={slideClass(img.aspect)}
            >
              <MediaImage
                src={img.url}
                alt={img.caption || "Galleria AIA Legnano"}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            </button>
          ))}
        </div>
      </div>

      {lightbox && (
        <div
          className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4"
          onClick={() => setLightbox(null)}
          role="dialog"
          aria-modal="true"
        >
          <button
            type="button"
            onClick={() => setLightbox(null)}
            className="absolute top-4 right-4 text-white min-h-[44px] min-w-[44px] inline-flex items-center justify-center hover:bg-white/10 rounded"
            aria-label="Chiudi"
          >
            <X className="h-7 w-7" />
          </button>
          <MediaImage
            src={lightbox.url}
            alt={lightbox.caption || ""}
            className="max-w-full max-h-[90vh] object-contain"
          />
          {lightbox.caption && (
            <p className="absolute bottom-6 left-0 right-0 text-center text-white/90 text-sm px-4">
              {lightbox.caption}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
