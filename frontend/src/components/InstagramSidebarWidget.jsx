import { useEffect, useMemo, useState } from "react";
import { Instagram, ExternalLink, Layers, Play } from "lucide-react";
import { Button } from "@/design-system";
import { fetchGallery, fetchInstagramWidget } from "../lib/api";
import { mediaUrl } from "../lib/media";
import { parseInstagramUsername } from "../lib/instagram-embed";

const POSTS_VISIBLE = 6; // 3 righe × 2 colonne

function parseInstagramHandle(url) {
  if (!url || typeof url !== "string") return null;
  const trimmed = url.trim();
  if (trimmed.startsWith("@")) return trimmed.slice(1).split("/")[0] || null;
  const m = trimmed.match(/instagram\.com\/([^/?#]+)/i);
  return m ? m[1].replace(/^@/, "") : null;
}

function galleryToPosts(items) {
  return items
    .map((img) => {
      const src = mediaUrl(img.url || img.path || "");
      if (!src) return null;
      return {
        shortcode: img.id,
        permalink: img.sourceUrl || "",
        imageUrl: src,
        caption: img.caption || "",
        isVideo: false,
        isCarousel: false,
      };
    })
    .filter(Boolean);
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
        src={post.imageUrl}
        alt={post.caption || "Post Instagram"}
        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        loading="lazy"
        referrerPolicy="no-referrer"
      />
      {(post.isVideo || post.isCarousel) && (
        <span className="absolute top-1.5 right-1.5 text-white drop-shadow-md">
          {post.isCarousel ? (
            <Layers className="h-3.5 w-3.5" strokeWidth={2.5} />
          ) : (
            <Play className="h-3.5 w-3.5 fill-white" strokeWidth={2.5} />
          )}
        </span>
      )}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/15 transition-colors" aria-hidden />
    </a>
  );
}

/**
 * Widget Instagram home: solo griglia post + CTA (niente header colorato né barra profilo).
 */
export default function InstagramSidebarWidget({
  profileUrl = "",
  className = "",
}) {
  const handle =
    parseInstagramHandle(profileUrl) || parseInstagramUsername(profileUrl) || "aia_legnano";
  const href = profileUrl || (handle ? `https://www.instagram.com/${handle}/` : null);

  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetchInstagramWidget({ limit: POSTS_VISIBLE })
      .then((data) => {
        if (cancelled) return;
        const list = Array.isArray(data?.posts) ? data.posts : [];
        if (list.length) {
          setPosts(list.slice(0, POSTS_VISIBLE));
          return;
        }
        return fetchGallery().then((items) => {
          if (cancelled) return;
          setPosts(galleryToPosts(Array.isArray(items) ? items : []).slice(0, POSTS_VISIBLE));
        });
      })
      .catch(() =>
        fetchGallery()
          .then((items) => {
            if (cancelled) return;
            setPosts(galleryToPosts(Array.isArray(items) ? items : []).slice(0, POSTS_VISIBLE));
          })
          .catch(() => {
            if (!cancelled) setPosts([]);
          })
      )
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
      className={`bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden flex flex-col ${className}`.trim()}
      data-testid="instagram-profile-widget"
    >
      {loading && tiles.length === 0 ? (
        <div className="aspect-[2/3] flex items-center justify-center text-sm text-slate-400" data-testid="instagram-sidebar-loading">
          Caricamento…
        </div>
      ) : tiles.length === 0 ? (
        <div className="p-6 text-sm text-slate-600" data-testid="instagram-sidebar-empty">
          Nessun post Instagram disponibile.
          {href && (
            <a href={href} target="_blank" rel="noopener noreferrer" className="block mt-3 text-navy-700 font-medium">
              Apri profilo Instagram
            </a>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-0.5 bg-white" data-testid="instagram-sidebar-grid">
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
        <div className="shrink-0 border-t border-slate-200 p-3 bg-white">
          <Button
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            variant="primary"
            size="sm"
            className="w-full"
            data-testid="instagram-profile-follow"
          >
            <Instagram className="h-4 w-4" />
            Seguici su Instagram <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

export { parseInstagramHandle };
