const IG_POST_RE = /instagram\.com\/p\/([A-Za-z0-9_-]+)/i;
const IG_REEL_RE = /instagram\.com\/reel\/([A-Za-z0-9_-]+)/i;

/** Estrae post/reel Instagram da URL, permalink o HTML embed incollato da Instagram. */
export function parseInstagramPostEmbed(htmlOrUrl) {
  if (!htmlOrUrl || typeof htmlOrUrl !== "string") return null;
  const fromAttr = htmlOrUrl.match(/data-instgrm-permalink="([^"]+)"/i);
  const haystack = fromAttr ? fromAttr[1] : htmlOrUrl.trim();

  const reel = haystack.match(IG_REEL_RE);
  if (reel) return { shortcode: reel[1], kind: "reel" };

  const post = haystack.match(IG_POST_RE);
  if (post) return { shortcode: post[1], kind: "post" };

  return null;
}

export function instagramPostEmbedSrc({ shortcode, kind }, { captioned = true } = {}) {
  const path = kind === "reel" ? "reel" : "p";
  const suffix = captioned ? "embed/captioned" : "embed";
  return `https://www.instagram.com/${path}/${shortcode}/${suffix}`;
}
