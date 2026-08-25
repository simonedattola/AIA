import { useEffect, useMemo, useState } from "react";
import { Instagram, ExternalLink, Layers, Play } from "lucide-react";
import { Button, CardTitle, Eyebrow } from "@/design-system";
import { fetchInstagramWidget } from "../lib/api";
import { mediaUrl } from "../lib/media";
import { parseInstagramUsername } from "../lib/instagram-embed";

const POSTS_VISIBLE = 9; // griglia 3×3

function parseInstagramHandle(url) {
  if (!url || typeof url !== "string") return null;
  const trimmed = url.trim();
  if (trimmed.startsWith("@")) return trimmed.slice(1).split("/")[0] || null;
  const m = trimmed.match(/instagram\.com\/([^/?#]+)/i);
  return m ? m[1].replace(/^@/, "") : null;
}

function PostTile({ post, profileUrl }) {
  const href = post.permalink || profileUrl;
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="group relative aspect-square overflow-hidden bg-slate-100 block"
      data-testid="instagram-sidebar-post"
    >
      <img
        src={mediaUrl(post.imageUrl)}
        alt={post.caption || "Post Instagram"}
        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        loading="lazy"
        referrerPolicy="no-referrer"
      />
      {(post.isVideo || post.isCarousel) && (
        <span className="absolute top-1 right-1 text-white drop-shadow-md">
          {post.isCarousel ? (
            <Layers className="h-3 w-3" strokeWidth={2.5} />
          ) : (
            <Play className="h-3 w-3 fill-white" strokeWidth={2.5} />
          )}
        </span>
      )}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/15 transition-colors" aria-hidden />
    </a>
  );
}

/**
 * Widget Instagram home: header gradiente + griglia 3×3 compatta + CTA.
 * Nessuna barra profilo Instagram (avatar / follower / stats).
 */
export default function InstagramSidebarWidget({
  profileUrl = "",
  title = "AIA Legnano",
  subtitle = "Foto, aggiornamenti e vita della sezione su Instagram.",
  className = "",
}) {
  const handle =
    parseInstagramHandle(profileUrl) || parseInstagramUsername(profileUrl) || "aia_legnano";
  const href = profileUrl || (handle ? `https://www.instagram.com/${handle}/` : null);
  const displayHandle = handle ? `@${handle}` : null;

  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    // Solo post Instagram reali dall'API widget (mai galleria sito).
    fetchInstagramWidget({ limit: POSTS_VISIBLE })
      .then((data) => {
        if (cancelled) return;
        const list = Array.isArray(data?.posts) ? data.posts : [];
        setPosts(list.slice(0, POSTS_VISIBLE));
      })
      .catch(() => {
        if (!cancelled) setPosts([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const tiles = useMemo(() => posts.slice(0, POSTS_VISIBLE), [posts]);

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden flex flex-col max-w-md w-full ml-auto ${className}`.trim()}
      data-testid="instagram-profile-widget"
    >
      <div className="px-3.5 py-3 bg-gradient-to-br from-[#833AB4] via-[#E1306C] to-[#F77737] text-white shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm shrink-0">
            <Instagram className="h-4 w-4" aria-hidden />
          </div>
          <div className="min-w-0">
            <Eyebrow className="text-[9px] tracking-[0.2em] text-white/90">Instagram</Eyebrow>
            <CardTitle as="h3" className="text-base leading-tight truncate text-white">
              {title || "AIA Legnano"}
            </CardTitle>
            {displayHandle && <p className="text-xs text-white/90 truncate">{displayHandle}</p>}
          </div>
        </div>
        {subtitle && (
          <p className="text-xs text-white/90 mt-2 leading-snug line-clamp-2">{subtitle}</p>
        )}
      </div>

      {loading && tiles.length === 0 ? (
        <div
          className="aspect-square flex items-center justify-center text-sm text-slate-400"
          data-testid="instagram-sidebar-loading"
        >
          Caricamento…
        </div>
      ) : tiles.length === 0 ? (
        <div className="p-4 text-sm text-slate-600" data-testid="instagram-sidebar-empty">
          Nessun post Instagram disponibile.
          {href && (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="block mt-2 text-navy-700 font-medium"
            >
              Apri profilo Instagram
            </a>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-0.5 bg-white" data-testid="instagram-sidebar-grid">
          {tiles.map((post) => (
            <PostTile
              key={post.shortcode || post.permalink || post.imageUrl}
              post={post}
              profileUrl={href}
            />
          ))}
        </div>
      )}

      {href && (
        <div className="shrink-0 border-t border-slate-200 px-2.5 py-2 bg-white">
          <Button
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            variant="primary"
            size="sm"
            className="w-full text-xs py-2"
            data-testid="instagram-profile-follow"
          >
            <Instagram className="h-3.5 w-3.5" />
            Seguici su Instagram <ExternalLink className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  );
}

export { parseInstagramHandle };
