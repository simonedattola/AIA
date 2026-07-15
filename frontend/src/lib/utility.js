export const UTILITY_SECTIONS = {
  materiale_eventi: "Materiale eventi",
  link_utili: "Link utili",
  polo: "Informazioni sul polo",
};

export function utilityItemHref(item) {
  return (item?.fileUrl || item?.url || "").trim();
}

export function filterUtilityItems(items, query) {
  const q = (query || "").trim().toLowerCase();
  if (!q) return items;
  return items.filter((item) => {
    const haystack = [item.title, item.description, item.url, item.fileUrl]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });
}
