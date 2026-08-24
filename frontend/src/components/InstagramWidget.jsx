import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Instagram, BadgeCheck, ChevronRight, Layers, Play } from "lucide-react";
import { cn } from "@/lib/utils";
import { fetchGallery, fetchInstagramWidget } from "../lib/api";
import {
  parseInstagramPostEmbed,
  parseInstagramUsername,
  instagramPermalink,
  resolveInstagramEmbedInput,
} from "../lib/instagram-embed";
import { mediaUrl } from "../lib/media";
import { SECTION_LOGO } from "../lib/brand";
import { formatIgCount } from "./instagram-widget-utils";

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

function InstagramFollowButton({ profileUrl, className = "" }) {
  if (!profileUrl) return null;
  return (
    <a
      href={profileUrl}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center justify-center gap-2 w-full px-4 py-2 rounded-md text-sm font-semibold text-white bg-[#0095f6] hover:bg-[#1877f2] transition-colors ${className}`}
      data-testid="instagram-follow-cta"
    >
      <Instagram className="h-4 w-4" strokeWidth={2.5} />
      Follow
    </a>
  );
}

function InstagramStat({ value, label }) {
  if (value == null) return null;
  return (
    <div className="flex-1 text-center min-w-0 px-1">
      <div className="text-base sm:text-lg font-semibold text-slate-900 tabular-nums leading-tight">
        {value}
      </div>
      <div className="text-[11px] sm:text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}

function InstagramPostTile({ post, profileUrl, fill = false }) {
  const href = post.permalink || profileUrl;
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        "group relative overflow-hidden bg-slate-100",
        fill ? "h-full min-h-0" : "aspect-square"
      )}
      data-testid="instagram-post-tile"
    >
      <img
        src={post.imageUrl}
        alt={post.caption || "Post Instagram"}
        className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
        loading="lazy"
        referrerPolicy="no-referrer"
      />
      {(post.isVideo || post.isCarousel) && (
        <span className="absolute top-2 right-2 text-white drop-shadow-md">
          {post.isCarousel ? (
            <Layers className="h-4 w-4" strokeWidth={2.5} />
          ) : (
            <Play className="h-4 w-4 fill-white" strokeWidth={2.5} />
          )}
        </span>
      )}
      <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" aria-hidden />
    </a>
  );
}

function chunkPosts(posts, size = 4) {
  const out = [];
  for (let i = 0; i < posts.length; i += size) {
    out.push(posts.slice(i, i + size));
  }
  return out;
}

function InstagramPostGrid({ posts, profileUrl, fill = false }) {
  const scrollerRef = useRef(null);
  const [canScroll, setCanScroll] = useState(false);
  const pages = useMemo(() => chunkPosts(posts, 4), [posts]);

  const checkScroll = useCallback(() => {
    const el = scrollerRef.current;
    if (!el) return;
    setCanScroll(el.scrollWidth > el.clientWidth + 8);
  }, []);

  useEffect(() => {
    checkScroll();
    window.addEventListener("resize", checkScroll);
    return () => window.removeEventListener("resize", checkScroll);
  }, [posts, checkScroll]);

  const scrollNext = () => {
    const el = scrollerRef.current;
    if (!el) return;
    el.scrollBy({ left: el.clientWidth, behavior: "smooth" });
  };

  if (!posts.length) {
    return (
      <div
        className={`aspect-square rounded-sm bg-slate-50 border border-slate-100 flex items-center justify-center text-sm text-slate-400${fill ? " flex-1 min-h-0" : ""}`}
        data-testid="instagram-grid-empty"
      >
        Nessun post disponibile
      </div>
    );
  }

  if (fill) {
    const tiles = posts.slice(0, 4);
    return (
      <div className="flex-1 min-h-0 grid grid-cols-2 gap-1.5" data-testid="instagram-post-grid">
            {tiles.map((post) => (
              <InstagramPostTile
                key={post.shortcode || post.permalink || post.imageUrl}
                post={post}
                profileUrl={profileUrl}
                fill
              />
            ))}
      </div>
    );
  }

  return (
    <div className="relative" data-testid="instagram-post-grid">
      <div
        ref={scrollerRef}
        className="flex gap-2 overflow-x-auto snap-x snap-mandatory scrollbar-none"
        style={{ scrollbarWidth: "none" }}
      >
        {pages.map((page, pageIdx) => (
          <div
            key={`page-${pageIdx}`}
            className="grid grid-cols-2 gap-1.5 shrink-0 w-full min-w-full snap-start"
          >
            {page.map((post) => (
              <InstagramPostTile
                key={post.shortcode || post.permalink || post.imageUrl}
                post={post}
                profileUrl={profileUrl}
              />
            ))}
          </div>
        ))}
      </div>
      {canScroll && pages.length > 1 && (
        <button
          type="button"
          onClick={scrollNext}
          className="absolute top-1/2 -translate-y-1/2 -right-3 z-10 h-9 w-9 rounded-full bg-slate-900/85 text-white shadow-lg flex items-center justify-center hover:bg-slate-900 transition-colors"
          aria-label="Post successivi"
          data-testid="instagram-grid-next"
        >
          <ChevronRight className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}

function InstagramProfileCard({ profile, stats, posts, profileUrl, displayName, fillHeight = false }) {
  const handle = profile?.username ? `@${profile.username}` : "";
  const name = (displayName || profile?.fullName || profile?.username || "Instagram").trim();
  const statPosts = formatIgCount(stats?.posts);
  const statFollowers = formatIgCount(stats?.followers);
  const statFollowing = formatIgCount(stats?.following);
  const hasStats = statPosts != null || statFollowers != null || statFollowing != null;

  return (
    <div
      className={cn("aia-ig-profile-card", fillHeight && "h-full flex flex-col min-h-0")}
      data-testid="instagram-profile-card"
    >
      <div className={cn("flex items-center gap-3 sm:gap-4", fillHeight && "shrink-0")}>
        <div className="shrink-0">
          {profile?.profilePicUrl ? (
            <img
              src={profile.profilePicUrl}
              alt=""
              className="h-16 w-16 sm:h-[72px] sm:w-[72px] rounded-full object-cover ring-2 ring-slate-100"
              loading="lazy"
              referrerPolicy="no-referrer"
            />
          ) : (
            <img
              src={SECTION_LOGO}
              alt=""
              className="h-16 w-16 sm:h-[72px] sm:w-[72px] rounded-full object-cover ring-2 ring-slate-100 bg-white p-1"
              loading="lazy"
            />
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-1.5 min-w-0">
            <h3 className="font-semibold text-slate-900 text-sm sm:text-base tracking-wide truncate">
              {name}
            </h3>
            {profile?.isVerified && (
              <BadgeCheck className="h-4 w-4 text-[#0095f6] shrink-0" aria-label="Verificato" />
            )}
          </div>
          {handle && (
            <a
              href={profileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs sm:text-sm text-slate-500 hover:text-slate-700 truncate block mt-0.5"
            >
              {handle}
            </a>
          )}
        </div>
      </div>

      {hasStats && !fillHeight && (
        <div className="flex items-start justify-around mt-4 pt-1 border-t border-slate-100 shrink-0">
          <InstagramStat value={statPosts} label="Posts" />
          <InstagramStat value={statFollowers} label="Followers" />
          <InstagramStat value={statFollowing} label="Following" />
        </div>
      )}

      <div className={cn("mt-4 shrink-0", fillHeight && "mt-3")}>
        <InstagramFollowButton profileUrl={profileUrl} />
      </div>

      <div className={cn("mt-4 -mx-0.5", fillHeight && "mt-3 flex-1 min-h-0 flex flex-col")}>
        <InstagramPostGrid posts={posts} profileUrl={profileUrl} fill={fillHeight} />
      </div>
    </div>
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
      className="aia-ig-embed w-full overflow-hidden rounded-xl border border-slate-200/80 bg-white"
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

/**
 * Widget Instagram stile profilo (header + stats + griglia post).
 * Con URL post configurato → embed singolo sotto header compatto.
 */
export default function InstagramWidget({ config = {}, profileUrl = "", fillHeight = false }) {
  const embedInput = useMemo(() => resolveInstagramEmbedInput(config), [config]);
  const parsed = useMemo(() => parseInstagramPostEmbed(embedInput), [embedInput]);
  const permalink = parsed ? instagramPermalink(parsed) : "";
  const profileUsername = useMemo(() => parseInstagramUsername(profileUrl), [profileUrl]);
  const displayName = (config.instagramTitle || "").trim();
  const resolvedProfileUrl =
    profileUrl || (profileUsername ? `https://www.instagram.com/${profileUsername}/` : "");

  const [widgetData, setWidgetData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchInstagramWidget({ limit: 12 })
      .then((data) => setWidgetData(data))
      .catch(() => {
        if (!profileUsername && !resolvedProfileUrl) {
          setWidgetData(null);
          return;
        }
        fetchGallery()
          .then((items) => {
            const list = Array.isArray(items) ? items.slice(0, 8) : [];
            setWidgetData({
              profile: {
                username: profileUsername || "instagram",
                fullName: displayName || "Instagram",
                profilePicUrl: "",
                isVerified: false,
                profileUrl: resolvedProfileUrl,
              },
              posts: galleryToPosts(list),
              stats: { posts: list.length || null, followers: null, following: null },
            });
          })
          .catch(() => setWidgetData(null));
      })
      .finally(() => setLoading(false));
  }, [profileUsername, displayName, resolvedProfileUrl]);

  let body;
  if (loading && !widgetData) {
    body = (
      <div className="py-12 text-center text-sm text-slate-400" data-testid="instagram-loading">
        Caricamento da Instagram…
      </div>
    );
  } else if (permalink) {
    body = (
      <div className="space-y-4">
        {widgetData && (
          <InstagramProfileCard
            profile={widgetData.profile}
            stats={widgetData.stats}
            posts={[]}
            profileUrl={resolvedProfileUrl}
            displayName={displayName}
          />
        )}
        <InstagramOfficialEmbed permalink={permalink} />
      </div>
    );
  } else if (widgetData) {
    body = (
      <InstagramProfileCard
        profile={widgetData.profile}
        stats={widgetData.stats}
        posts={widgetData.posts || []}
        profileUrl={resolvedProfileUrl}
        displayName={displayName}
        fillHeight={fillHeight}
      />
    );
  } else {
    body = (
      <div className="py-10 text-center text-sm text-slate-500" data-testid="instagram-empty">
        Instagram non disponibile al momento.
        {resolvedProfileUrl && (
          <div className="mt-4">
            <InstagramFollowButton profileUrl={resolvedProfileUrl} className="max-w-xs mx-auto" />
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm",
        fillHeight && "h-full flex flex-col min-h-0"
      )}
      data-testid="instagram-widget"
    >
      <div className={cn("p-4 sm:p-5", fillHeight && "flex-1 flex flex-col min-h-0 p-3 sm:p-4")}>
        {body}
      </div>
    </div>
  );
}
