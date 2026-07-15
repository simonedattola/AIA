/**
 * Suddivide bodyHtml in blocchi HTML e caroselli immagini (sequenze e gallerie legacy).
 */
import { mediaUrl } from "./media";

export function resolveBodyMediaUrls(html) {
  if (!html?.trim()) return html || "";
  const doc = new DOMParser().parseFromString(html, "text/html");
  doc.querySelectorAll("img[src]").forEach((img) => {
    img.setAttribute("src", mediaUrl(img.getAttribute("src")));
  });
  return doc.body.innerHTML;
}

function extractImages(el) {
  if (el.tagName === "IMG") {
    const src = el.getAttribute("src") || "";
    if (!src) return [];
    return [{ src, alt: el.getAttribute("alt") || "" }];
  }
  return [...el.querySelectorAll("img")]
    .map((img) => ({
      src: img.getAttribute("src") || "",
      alt: img.getAttribute("alt") || "",
    }))
    .filter((img) => img.src);
}

function isImageOnlyElement(el) {
  if (!el || el.nodeType !== 1) return false;
  if (el.classList?.contains("aia-article-carousel")) return true;
  if (el.tagName === "IMG") return true;
  if (el.tagName === "P" || el.tagName === "FIGURE" || el.tagName === "DIV") {
    const imgs = el.querySelectorAll("img");
    if (!imgs.length) return false;
    const text = (el.textContent || "").replace(/\u00a0/g, " ").trim();
    return !text;
  }
  return false;
}

function dedupeImages(images) {
  const out = [];
  const seen = new Set();
  for (const img of images) {
    if (!img.src || seen.has(img.src)) continue;
    seen.add(img.src);
    out.push(img);
  }
  return out;
}

function serializeNode(node) {
  if (node.nodeType === Node.TEXT_NODE) {
    const text = node.textContent || "";
    return text.trim() ? text : "";
  }
  if (node.nodeType !== Node.ELEMENT_NODE) return "";
  return node.outerHTML;
}

export function parseArticleBody(html) {
  if (!html?.trim()) return [];

  const doc = new DOMParser().parseFromString(html, "text/html");
  const body = doc.body;
  const segments = [];
  let buffer = [];
  let imageRun = [];

  const flushBuffer = () => {
    if (!buffer.length) return;
    const chunk = buffer.map((n) => serializeNode(n)).join("").trim();
    if (chunk) segments.push({ type: "html", content: resolveBodyMediaUrls(chunk) });
    buffer = [];
  };

  const flushImageRun = () => {
    if (!imageRun.length) return;
    const images = dedupeImages(imageRun.flatMap((node) => extractImages(node))).map((img) => ({
      ...img,
      src: mediaUrl(img.src),
    }));
    if (images.length >= 2) {
      segments.push({ type: "carousel", images });
    } else {
      imageRun.forEach((node) => buffer.push(node));
    }
    imageRun = [];
  };

  for (const node of [...body.childNodes]) {
    if (isImageOnlyElement(node)) {
      flushBuffer();
      imageRun.push(node);
      continue;
    }
    flushImageRun();
    buffer.push(node);
  }
  flushImageRun();
  flushBuffer();

  if (!segments.length && html.trim()) {
    return [{ type: "html", content: resolveBodyMediaUrls(html) }];
  }
  return segments;
}
