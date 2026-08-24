import { useEffect, useMemo, useState } from "react";
import { Instagram, ExternalLink } from "lucide-react";
import { fetchGallery } from "../lib/api";
import {
  parseInstagramPostEmbed,
  instagramPermalink,
  resolveInstagramEmbedInput,
} from "../lib/instagram-embed";
import { mediaUrl } from "../lib/media";

function loadInstagramEmbedScript() {
  return new Promise((resolve) => {
    if (typeof window === "undefined") {
      resolve();
      return;
    }
    if (window.instgrm?.Embeds) {
      resolve();
      return;
    }
    const existing = document.querySelector("script[data-aia-instagram-embed]");
    if (existing) {
      if (window.instgrm?.Embeds) {
        resolve();
        return;
      }
      existing.addEventListener("load", () => resolve(), { once: true });
      // se già caricato ma senza callback
      setTimeout(() => resolve(), 1500);
      return;
    }
    const script = document.createElement("script");
    script.async = true;
    script.src = "https://www.instagram.com/embed.js";
    script.dataset.aiaInstagramEmbed = "1";
    script.onload = () => resolve();
    script.onerror = () => resolve();
    document.body.appendChild(script);
  });
}

function processInstagramEmbeds() {
  try {
    window.instgrm?.Embeds?.process?.();
  } catch {
    /* ignore */
  }
}

/** Embed ufficiale Instagram (blockquote + embed.js) — più affidabile dell'iframe grezzo. */
function InstagramOfficialEmbed({ permalink }) {
  useEffect(() => {
    let cancelled = false;
    loadInstagramEmbedScript().then(() => {
      if (!cancelled) processInstagramEmbeds();
    });
    // Instagram a volte monta in ritardo
    const t1 = setTimeout(processInstagramEmbeds, 400);
    const t2 = setTimeout(processInstagramEmbeds, 1200);
    return () => {
      cancelled = true;
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [permalink]);

  return (
    <div className="aia-ig-embed w-full overflow-hidden rounded-lg border border-slate-200 bg-white" data-testid="instagram-official-embed">
      <blockquote
        className="instagram-media"
        data-instgrm-permalink={permalink}
        data-instgrm-version="14"
        style={{
          background: "#FFF",
          border: 0,
          margin: 0,
          maxWidth: "100%",
          minWidth: "100%",
          padding: 0,
          width: "100%",
        }}
      >
        <a href={permalink} target="_blank" rel="noopener noreferrer">
          Vedi su Instagram
        </a>
      </blockquote>
    </div>
  );
}

/** Griglia foto dal sito quando non c'è un post embed configurato. */
function InstagramGalleryFallback({ profileUrl }) {
  const [images, setImages] = useState([]);

  useEffect(() => {
    fetchGallery()
      .then((items) => {
        const list = Array.isArray(items) ? items : [];
        setImages(list.slice(0, 6));
      })
      .catch(() => setImages([]));
  }, []);

  if (!images.length) {
    return (
      <div
        className="aspect-[4/5] w-full rounded-lg bg-gradient-to-br from-fuchsia-100 via-rose-50 to-amber-100 border border-slate-200 flex items-center justify-center text-center p-6"
        data-testid="instagram-empty-fallback"
      >
        <div className="space-y-3">
          <Instagram className="h-10 w-10 text-rose-500 mx-auto" />
          <div>
            <p className="text-navy-700 font-semibold">Scopri le ultime foto</p>
            <p className="text-sm text-slate-500">Vita sezionale, eventi, successi e dietro le quinte.</p>
          </div>
          {profileUrl ? (
            <a
              href={profileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-semibold text-navy-700 border-b border-navy-700 pb-0.5"
            >
              Apri Instagram <ExternalLink className="h-3.5 w-3.5" />
            </a>
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg overflow-hidden border border-slate-200 bg-slate-50" data-testid="instagram-gallery-grid">
      <div className="grid grid-cols-3 gap-0.5">
        {images.map((img) => {
          const src = mediaUrl(img.url || img.path || "");
          if (!src) return null;
          return (
            <a
              key={img.id || src}
              href={profileUrl || src}
              target="_blank"
              rel="noopener noreferrer"
              className="aspect-square overflow-hidden bg-slate-200"
            >
              <img
                src={src}
                alt={img.caption || "Foto sezione"}
                className="h-full w-full object-cover"
                loading="lazy"
              />
            </a>
          );
        })}
      </div>
      {profileUrl ? (
        <a
          href={profileUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 px-3 py-3 text-sm font-semibold text-navy-700 hover:bg-white/80 transition-colors"
        >
          Apri Instagram <ExternalLink className="h-3.5 w-3.5" />
        </a>
      ) : null}
    </div>
  );
}

/**
 * Widget Instagram per il blocco eventi home.
 * Preferisce embed ufficiale del post; altrimenti griglia galleria + link profilo.
 */
export default function InstagramWidget({ config = {}, profileUrl = "" }) {
  const embedInput = useMemo(() => resolveInstagramEmbedInput(config), [config]);
  const parsed = useMemo(() => parseInstagramPostEmbed(embedInput), [embedInput]);
  const permalink = parsed ? instagramPermalink(parsed) : "";
  const title = config.instagramTitle || "Instagram";
  const subtitle =
    config.instagramSubtitle || "Foto, aggiornamenti e vita della sezione su Instagram.";

  return (
    <div className="rounded-xl border border-slate-200/80 bg-white p-4 sm:p-5 shadow-ds-sm" data-testid="instagram-widget">
      <div className="flex items-center gap-2 mb-3">
        <div className="p-2 rounded-full bg-gradient-to-br from-fuchsia-500 via-rose-500 to-amber-400 text-white">
          <Instagram className="h-5 w-5" />
        </div>
        <div>
          <div className="font-display font-semibold text-navy-700 text-base">{title}</div>
          <p className="text-sm text-slate-500">{subtitle}</p>
        </div>
      </div>

      {permalink ? (
        <InstagramOfficialEmbed permalink={permalink} />
      ) : (
        <InstagramGalleryFallback profileUrl={profileUrl} />
      )}

      {profileUrl && (
        <div className="mt-4 flex justify-end">
          <a
            href={profileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-navy-700"
          >
            Profilo sezione <Instagram className="h-4 w-4" />
          </a>
        </div>
      )}
    </div>
  );
}
