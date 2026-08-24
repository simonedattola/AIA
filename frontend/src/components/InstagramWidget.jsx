import { useEffect, useMemo, useState } from "react";
import { Instagram, ExternalLink } from "lucide-react";
import { fetchGallery } from "../lib/api";
import {
  parseInstagramPostEmbed,
  parseInstagramUsername,
  instagramPermalink,
  instagramProfileEmbedSrc,
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

function InstagramFollowButton({ profileUrl, username }) {
  if (!profileUrl) return null;
  const label = username ? `@${username.replace(/^@/, "")}` : "Instagram";
  return (
    <a
      href={profileUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center justify-center gap-2 w-full sm:w-auto px-5 py-2.5 rounded-full text-sm font-semibold text-white shadow-md hover:shadow-lg transition-all bg-gradient-to-r from-[#f58529] via-[#dd2a7b] to-[#8134af] hover:opacity-95"
      data-testid="instagram-follow-cta"
    >
      <Instagram className="h-4 w-4" />
      Seguici su {label}
      <ExternalLink className="h-3.5 w-3.5 opacity-80" />
    </a>
  );
}

/** Embed ufficiale di un singolo post/reel (blockquote + embed.js). */
function InstagramOfficialEmbed({ permalink }) {
  useEffect(() => {
    let cancelled = false;
    loadInstagramEmbedScript().then(() => {
      if (!cancelled) processInstagramEmbeds();
    });
    const t1 = setTimeout(processInstagramEmbeds, 400);
    const t2 = setTimeout(processInstagramEmbeds, 1200);
    return () => {
      cancelled = true;
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [permalink]);

  return (
    <div
      className="aia-ig-embed w-full overflow-hidden rounded-xl border border-slate-200/80 bg-white shadow-inner"
      data-testid="instagram-official-embed"
    >
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

/** Feed ufficiale del profilo Instagram (iframe /embed). */
function InstagramProfileEmbed({ profileUrl }) {
  const src = instagramProfileEmbedSrc(profileUrl);
  if (!src) return null;
  return (
    <div
      className="aia-ig-profile-embed relative w-full overflow-hidden rounded-xl border border-slate-200/80 bg-white shadow-sm"
      data-testid="instagram-profile-embed"
    >
      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-white to-transparent z-[1]"
        aria-hidden
      />
      <iframe
        title="Instagram AIA Legnano"
        src={src}
        className="w-full border-0 relative z-0"
        style={{ height: 520, maxWidth: "100%" }}
        loading="lazy"
        referrerPolicy="strict-origin-when-cross-origin"
        allow="encrypted-media; clipboard-write"
      />
    </div>
  );
}

/** Griglia foto dal sito se non c'è profilo né post configurato. */
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
        className="aspect-[4/5] w-full rounded-xl bg-gradient-to-br from-fuchsia-50 via-rose-50 to-amber-50 border border-rose-100/80 flex items-center justify-center text-center p-8 shadow-inner"
        data-testid="instagram-empty-fallback"
      >
        <div className="space-y-4">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-fuchsia-500 via-rose-500 to-amber-400 flex items-center justify-center text-white shadow-lg">
            <Instagram className="h-7 w-7" />
          </div>
          <div>
            <p className="text-navy-800 font-display font-semibold text-lg">Scopri le ultime foto</p>
            <p className="text-sm text-slate-500 mt-1 max-w-xs mx-auto leading-relaxed">
              Vita sezionale, eventi, successi e dietro le quinte.
            </p>
          </div>
          {profileUrl ? (
            <InstagramFollowButton profileUrl={profileUrl} />
          ) : null}
        </div>
      </div>
    );
  }

  return (
    <div
      className="rounded-xl overflow-hidden border border-slate-200/80 bg-slate-50 shadow-sm"
      data-testid="instagram-gallery-grid"
    >
      <div className="grid grid-cols-3 gap-1 p-1">
        {images.map((img) => {
          const src = mediaUrl(img.url || img.path || "");
          if (!src) return null;
          return (
            <a
              key={img.id || src}
              href={profileUrl || src}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative aspect-square overflow-hidden rounded-lg bg-slate-200"
            >
              <img
                src={src}
                alt={img.caption || "Foto sezione"}
                className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-navy-900/0 group-hover:bg-navy-900/25 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                <Instagram className="h-6 w-6 text-white drop-shadow" />
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Widget Instagram per il blocco eventi home.
 * 1) URL post/reel configurato → embed singolo
 * 2) altrimenti profilo (settings.instagramUrl) → feed ufficiale /embed
 * 3) altrimenti galleria sito
 */
export default function InstagramWidget({ config = {}, profileUrl = "" }) {
  const embedInput = useMemo(() => resolveInstagramEmbedInput(config), [config]);
  const parsed = useMemo(() => parseInstagramPostEmbed(embedInput), [embedInput]);
  const permalink = parsed ? instagramPermalink(parsed) : "";
  const profileUsername = useMemo(() => parseInstagramUsername(profileUrl), [profileUrl]);
  const title = config.instagramTitle || "Instagram";
  const subtitle =
    config.instagramSubtitle || "Foto, aggiornamenti e vita della sezione su Instagram.";
  const handle = profileUsername ? `@${profileUsername}` : "";

  let body;
  if (permalink) {
    body = <InstagramOfficialEmbed permalink={permalink} />;
  } else if (profileUsername) {
    body = <InstagramProfileEmbed profileUrl={profileUrl || profileUsername} />;
  } else {
    body = <InstagramGalleryFallback profileUrl={profileUrl} />;
  }

  return (
    <div
      className="relative overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-ds-md"
      data-testid="instagram-widget"
    >
      <div
        className="h-1 w-full bg-gradient-to-r from-[#f58529] via-[#dd2a7b] to-[#8134af]"
        aria-hidden
      />

      <div className="p-4 sm:p-5">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4">
          <div className="flex items-start gap-3 min-w-0">
            <div className="shrink-0 p-2.5 rounded-2xl bg-gradient-to-br from-fuchsia-500 via-rose-500 to-amber-400 text-white shadow-md ring-2 ring-white">
              <Instagram className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="font-display font-semibold text-navy-800 text-lg leading-tight">
                {title}
              </div>
              {handle && (
                <a
                  href={profileUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-rose-600 hover:text-rose-700 mt-0.5 inline-block"
                >
                  {handle}
                </a>
              )}
              <p className="text-sm text-slate-500 mt-1 leading-snug">{subtitle}</p>
            </div>
          </div>
        </div>

        {body}

        {profileUrl && (
          <div className="mt-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-4 border-t border-slate-100">
            <InstagramFollowButton profileUrl={profileUrl} username={profileUsername} />
            <a
              href={profileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-center sm:text-right text-xs text-slate-500 hover:text-navy-700 transition-colors"
            >
              Apri profilo completo
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
