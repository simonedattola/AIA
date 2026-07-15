/** Mappa Google della sezione da impostazioni sito (embed o indirizzo). */
export function resolveSectionMap(settings = {}) {
  const embed = (settings.mapEmbedUrl || "").trim();
  const address = (settings.address || "").trim();

  if (embed) {
    return {
      embedUrl: embed,
      linkUrl: address
        ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`
        : embed.replace("output=embed", "").replace("&output=embed", ""),
      caption: address,
    };
  }

  if (!address) return null;

  const q = encodeURIComponent(address);
  return {
    embedUrl: `https://www.google.com/maps?q=${q}&hl=it&z=16&output=embed`,
    linkUrl: `https://www.google.com/maps/search/?api=1&query=${q}`,
    caption: address,
  };
}
