export function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
}

export function formatDay(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  if (d.toDateString() === today.toDateString()) return "Oggi";
  if (d.toDateString() === yesterday.toDateString()) return "Ieri";
  return d.toLocaleDateString("it-IT", { day: "numeric", month: "short" });
}

export function formatReadAt(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString("it-IT", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function groupSubtitle(chat) {
  if (!chat?.isGroup) return "";
  const n = chat.memberCount || 0;
  const names =
    chat.memberNamesLine || (chat.members || []).map((m) => m.name).filter(Boolean).join(", ");
  return names ? `${n} partecipanti · ${names}` : `${n} partecipanti`;
}

export function listPreview(c) {
  if (c.isGroup) {
    return `${c.memberCount || 0} partecipanti${c.memberNamesLine ? ` · ${c.memberNamesLine}` : ""}`;
  }
  return c.lastMessage || "";
}
