import { useEffect, useState } from "react";
import { ArrowLeft, X, Users, Mail, Phone, CheckCheck, Search, Trash2 } from "lucide-react";
import ChatAvatar from "./ChatAvatar";
import { WA } from "./whatsappTheme";
import { formatReadAt } from "./chatUtils";

function DrawerHeader({ title, onClose }) {
  return (
    <header
      className="text-white px-4 py-3 flex items-center gap-3 shrink-0"
      style={{ backgroundColor: WA.primary }}
    >
      <button type="button" onClick={onClose} className="p-1">
        <ArrowLeft className="h-5 w-5" />
      </button>
      <span className="font-medium">{title}</span>
    </header>
  );
}

export function ReadInfoModal({ readInfo, onClose }) {
  if (!readInfo) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
      <div
        className="rounded-xl w-full max-w-sm shadow-2xl p-5"
        style={{ backgroundColor: WA.panelWhite }}
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold" style={{ color: WA.textDark }}>
            Info messaggio
          </h3>
          <button type="button" onClick={onClose}>
            <X className="h-5 w-5" />
          </button>
        </div>
        <p className="text-sm mb-2" style={{ color: WA.textMuted }}>
          Inviato: {formatReadAt(readInfo.createdAt)}
        </p>
        {readInfo.readInfo?.type === "read" && (
          <p className="text-sm flex items-center gap-2" style={{ color: WA.readTick }}>
            <CheckCheck className="h-4 w-4" />
            Letto {formatReadAt(readInfo.readInfo.at)}
            {readInfo.readInfo.by ? ` · ${readInfo.readInfo.by}` : ""}
          </p>
        )}
        {readInfo.readInfo?.type === "delivered" && (
          <p className="text-sm flex items-center gap-2" style={{ color: WA.textMeta }}>
            <CheckCheck className="h-4 w-4" />
            Consegnato
          </p>
        )}
        {readInfo.readInfo?.type === "group" && (
          <div>
            <p className="text-sm font-medium mb-2" style={{ color: WA.textDark }}>
              Letto da {readInfo.readInfo.total || 0}
              {readInfo.readInfo.expected ? ` / ${readInfo.readInfo.expected}` : ""} partecipanti
            </p>
            <ul className="text-sm space-y-1 max-h-40 overflow-y-auto" style={{ color: WA.textMuted }}>
              {(readInfo.readInfo.readers || []).map((r) => (
                <li key={r.id}>{r.name}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export function GroupInfoDrawer({
  open,
  groupInfo,
  groupDescDraft,
  onDescChange,
  onSaveDesc,
  savingGroup,
  onClose,
  onPhotoClick,
  groupPanelPhotoRef,
  onPhotoChange,
  onMemberClick,
  onLeaveGroup,
  leavingGroup,
  meId,
}) {
  if (!open || !groupInfo) return null;
  return (
    <div className="fixed inset-0 z-50 flex">
      <button type="button" className="flex-1 bg-black/40" onClick={onClose} aria-label="Chiudi" />
      <aside
        className="w-full max-w-md h-full overflow-y-auto shadow-2xl flex flex-col"
        style={{ backgroundColor: WA.panelWhite }}
      >
        <DrawerHeader title="Info gruppo" onClose={onClose} />
        <div
          className="flex flex-col items-center py-8 px-6 border-b"
          style={{ backgroundColor: WA.listBg, borderColor: WA.border }}
        >
          <button type="button" onClick={onPhotoClick} className="relative group" title="Cambia foto">
            <ChatAvatar
              name={groupInfo.name}
              photo={groupInfo.photo}
              size="xl"
              isGroup={!groupInfo.photo}
            />
            <span className="absolute inset-0 rounded-full bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center text-white text-xs font-medium transition">
              Cambia foto
            </span>
          </button>
          <input
            ref={groupPanelPhotoRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={onPhotoChange}
          />
          <h2 className="mt-4 text-2xl font-normal text-center" style={{ color: WA.textDark }}>
            {groupInfo.name}
          </h2>
          <p className="text-sm mt-2" style={{ color: WA.textMuted }}>
            {groupInfo.memberCount} partecipanti
          </p>
        </div>
        <div className="p-4 space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1" style={{ color: WA.textDark }}>
              Descrizione
            </label>
            <textarea
              value={groupDescDraft}
              onChange={onDescChange}
              rows={3}
              className="w-full border rounded-lg px-3 py-2 text-sm resize-none"
              style={{ borderColor: WA.border }}
              placeholder="Aggiungi una descrizione del gruppo…"
            />
            <button
              type="button"
              disabled={savingGroup}
              onClick={onSaveDesc}
              className="mt-2 text-sm font-medium disabled:opacity-50"
              style={{ color: WA.primary }}
            >
              {savingGroup ? "Salvataggio…" : "Salva descrizione"}
            </button>
          </div>
          <div>
            <h3 className="text-sm font-medium mb-3 px-1" style={{ color: WA.textDark }}>
              Partecipanti ({groupInfo.memberCount})
            </h3>
            <ul className="space-y-0.5">
              {(groupInfo.members || []).map((m) => (
                <li key={m.id}>
                  <button
                    type="button"
                    onClick={() => m.id !== meId && onMemberClick?.(m)}
                    disabled={m.id === meId}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg text-left ${
                      m.id === meId ? "cursor-default" : "hover:bg-[#f5f6f6] cursor-pointer"
                    }`}
                  >
                    <ChatAvatar name={m.name} photo={m.photoUrl} size="header" />
                    <span className="text-sm font-medium" style={{ color: WA.textDark }}>
                      {m.name}
                    </span>
                    {m.id === meId ? (
                      <span className="text-xs ml-auto" style={{ color: WA.textMeta }}>
                        Tu
                      </span>
                    ) : (
                      <span className="text-xs ml-auto" style={{ color: WA.primaryLight }}>
                        Info
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </div>
          <div className="pt-4 border-t" style={{ borderColor: WA.border }}>
            <button
              type="button"
              disabled={leavingGroup}
              onClick={onLeaveGroup}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-medium text-white disabled:opacity-50"
              style={{ backgroundColor: WA.danger }}
            >
              <Trash2 className="h-5 w-5" />
              {leavingGroup ? "Eliminazione…" : "Elimina gruppo"}
            </button>
            <p className="text-xs text-center mt-2 px-2" style={{ color: WA.textMeta }}>
              Uscirai dal gruppo: la chat scomparirà dalla tua lista e non riceverai più i messaggi.
            </p>
          </div>
        </div>
      </aside>
    </div>
  );
}

export function ContactInfoDrawer({ open, contact, onClose, onOpenGroupChat, onDeleteChat, deletingChat }) {
  if (!open || !contact) return null;
  return (
    <div className="fixed inset-0 z-50 flex">
      <button type="button" className="flex-1 bg-black/40" onClick={onClose} aria-label="Chiudi" />
      <aside
        className="w-full max-w-md h-full overflow-y-auto shadow-2xl flex flex-col"
        style={{ backgroundColor: WA.panelWhite }}
      >
        <DrawerHeader title="Info contatto" onClose={onClose} />
        <div
          className="flex flex-col items-center py-8 px-6 border-b"
          style={{ backgroundColor: WA.listBg, borderColor: WA.border }}
        >
          <ChatAvatar name={contact.name} photo={contact.photo} size="xl" />
          <h2 className="mt-4 text-2xl font-normal text-center" style={{ color: WA.textDark }}>
            {contact.firstName} {contact.lastName}
          </h2>
          {contact.roleLabel && (
            <p className="text-sm mt-1" style={{ color: WA.textMuted }}>
              {contact.roleLabel}
            </p>
          )}
          {contact.category && (
            <p className="text-sm mt-0.5" style={{ color: WA.primary }}>
              {contact.category}
            </p>
          )}
          {contact.bio && (
            <p className="text-sm mt-3 text-center max-w-sm" style={{ color: WA.textMuted }}>
              {contact.bio}
            </p>
          )}
        </div>
        <div className="p-4 space-y-4">
          {contact.email ? (
            <a
              href={`mailto:${contact.email}`}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-[#f5f6f6]"
            >
              <div
                className="h-10 w-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: "#e7fce3" }}
              >
                <Mail className="h-5 w-5" style={{ color: WA.primary }} />
              </div>
              <div>
                <div className="text-xs" style={{ color: WA.textMeta }}>
                  Email
                </div>
                <div className="text-sm" style={{ color: WA.textDark }}>
                  {contact.email}
                </div>
              </div>
            </a>
          ) : null}
          {contact.phone ? (
            <a
              href={`tel:${contact.phone}`}
              className="flex items-center gap-3 p-3 rounded-lg hover:bg-[#f5f6f6]"
            >
              <div
                className="h-10 w-10 rounded-full flex items-center justify-center"
                style={{ backgroundColor: "#e7fce3" }}
              >
                <Phone className="h-5 w-5" style={{ color: WA.primary }} />
              </div>
              <div>
                <div className="text-xs" style={{ color: WA.textMeta }}>
                  Telefono
                </div>
                <div className="text-sm" style={{ color: WA.textDark }}>
                  {contact.phone}
                </div>
              </div>
            </a>
          ) : null}
          {!contact.email && !contact.phone && (
            <p className="text-sm text-center py-2" style={{ color: WA.textMeta }}>
              L&apos;associato non ha condiviso email o telefono nel profilo.
            </p>
          )}
          {(contact.commonGroups || []).length > 0 && (
            <div>
              <h3 className="text-sm font-medium mb-2 px-1" style={{ color: WA.textDark }}>
                Gruppi in comune
              </h3>
              <ul className="space-y-1">
                {contact.commonGroups.map((g) => (
                  <li key={g.chatId}>
                    <button
                      type="button"
                      onClick={() => onOpenGroupChat(g.chatId)}
                      className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-[#f5f6f6] text-left"
                    >
                      <Users className="h-5 w-5" style={{ color: WA.primary }} />
                      <div>
                        <div className="text-sm font-medium" style={{ color: WA.textDark }}>
                          {g.name}
                        </div>
                        <div className="text-xs" style={{ color: WA.textMeta }}>
                          {g.memberCount} partecipanti
                        </div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="pt-4 border-t" style={{ borderColor: WA.border }}>
            <button
              type="button"
              disabled={deletingChat}
              onClick={onDeleteChat}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-medium text-white disabled:opacity-50"
              style={{ backgroundColor: WA.danger }}
            >
              <Trash2 className="h-5 w-5" />
              {deletingChat ? "Eliminazione…" : "Elimina chat"}
            </button>
            <p className="text-xs text-center mt-2 px-2" style={{ color: WA.textMeta }}>
              La chat scomparirà dalla tua lista. Se ricevi nuovi messaggi, riapparirà.
            </p>
          </div>
        </div>
      </aside>
    </div>
  );
}

export function NewChatModal({
  open,
  onClose,
  newMode,
  setNewMode,
  error,
  associati,
  onStartChat,
  creaGruppo,
  groupName,
  setGroupName,
  groupDescription,
  setGroupDescription,
  groupMembers,
  toggleGroupMember,
  groupPhotoPreview,
  onGroupPhotoClick,
  groupPhotoRef,
  onGroupPhotoChange,
}) {
  const [q, setQ] = useState("");

  useEffect(() => {
    if (open) setQ("");
  }, [open]);

  const filteredAssociati = associati.filter((a) => {
    const s = q.trim().toLowerCase();
    if (!s) return true;
    return `${a.firstName || ""} ${a.lastName || ""} ${a.roleLabel || ""}`.toLowerCase().includes(s);
  });

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-end md:items-center justify-center p-0 md:p-4">
      <div
        className="rounded-t-2xl md:rounded-xl w-full max-w-md max-h-[85vh] flex flex-col shadow-2xl"
        style={{ backgroundColor: WA.panelWhite }}
      >
        <div
          className="flex items-center justify-between p-4 border-b shrink-0"
          style={{ borderColor: WA.border, backgroundColor: WA.primary, color: "#fff" }}
        >
          <h2 className="font-medium text-lg">Nuova conversazione</h2>
          <button type="button" onClick={onClose} className="p-1 text-white/90">
            <X className="h-6 w-6" />
          </button>
        </div>
        <div className="flex border-b shrink-0" style={{ borderColor: WA.border }}>
          {["chat", "group"].map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setNewMode(mode)}
              className="flex-1 py-3 text-sm font-medium"
              style={{
                color: newMode === mode ? WA.primary : WA.textMeta,
                borderBottom: newMode === mode ? `3px solid ${WA.primary}` : "3px solid transparent",
              }}
            >
              {mode === "chat" ? "Chat privata" : "Nuovo gruppo"}
            </button>
          ))}
        </div>
        {error && <p className="text-sm text-red-600 px-4 pt-2">{error}</p>}
        {newMode === "chat" && (
          <div className="px-3 py-2 shrink-0 border-b" style={{ borderColor: WA.border }}>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: WA.textMeta }} />
              <input
                type="search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Cerca associato…"
                className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border"
                style={{ borderColor: WA.border, backgroundColor: "#f0f2f5" }}
              />
            </div>
          </div>
        )}
        {newMode === "chat" ? (
          <ul className="overflow-y-auto flex-1 p-2">
            {filteredAssociati.length === 0 ? (
              <li className="p-4 text-center text-sm" style={{ color: WA.textMeta }}>
                {q.trim() ? "Nessun associato trovato" : "Nessun associato disponibile"}
              </li>
            ) : (
              filteredAssociati.map((a) => (
              <li key={a.id}>
                <button
                  type="button"
                  onClick={() => onStartChat(a)}
                  className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-[#f5f6f6] text-left"
                >
                  <ChatAvatar name={`${a.firstName} ${a.lastName}`} photo={a.photoUrl} />
                  <div>
                    <div className="font-medium" style={{ color: WA.textDark }}>
                      {a.firstName} {a.lastName}
                    </div>
                    {a.roleLabel && (
                      <div className="text-xs" style={{ color: WA.textMeta }}>
                        {a.roleLabel}
                      </div>
                    )}
                  </div>
                </button>
              </li>
              ))
            )}
          </ul>
        ) : (
          <form onSubmit={creaGruppo} className="flex flex-col flex-1 min-h-0 p-4 overflow-y-auto">
            <div className="flex flex-col items-center mb-4">
              <button type="button" onClick={onGroupPhotoClick} className="relative">
                <ChatAvatar
                  name={groupName || "Gruppo"}
                  photo={groupPhotoPreview}
                  size="xl"
                  isGroup={!groupPhotoPreview}
                />
                <span className="text-xs mt-2 block text-center" style={{ color: WA.primary }}>
                  Foto gruppo
                </span>
              </button>
              <input
                ref={groupPhotoRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={onGroupPhotoChange}
              />
            </div>
            <label className="block mb-3">
              <span className="text-sm font-medium" style={{ color: WA.textDark }}>
                Nome gruppo
              </span>
              <input
                required
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                className="w-full mt-1 border rounded-lg px-3 py-2 text-sm"
                style={{ borderColor: WA.border }}
                placeholder="es. Arbitri Under 17"
              />
            </label>
            <label className="block mb-3">
              <span className="text-sm font-medium" style={{ color: WA.textDark }}>
                Descrizione (opzionale)
              </span>
              <textarea
                value={groupDescription}
                onChange={(e) => setGroupDescription(e.target.value)}
                rows={2}
                className="w-full mt-1 border rounded-lg px-3 py-2 text-sm resize-none"
                style={{ borderColor: WA.border }}
                placeholder="Di cosa parla questo gruppo?"
              />
            </label>
            <p className="text-xs mb-2" style={{ color: WA.textMeta }}>
              Aggiungi associati
            </p>
            <div className="relative mb-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" style={{ color: WA.textMeta }} />
              <input
                type="search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Cerca associato…"
                className="w-full pl-9 pr-3 py-2 text-sm rounded-lg border"
                style={{ borderColor: WA.border, backgroundColor: "#f0f2f5" }}
              />
            </div>
            <ul
              className="flex-1 border rounded-lg mb-4 max-h-48 overflow-y-auto"
              style={{ borderColor: WA.border }}
            >
              {filteredAssociati.length === 0 ? (
                <li className="p-3 text-sm text-center" style={{ color: WA.textMeta }}>
                  {q.trim() ? "Nessun associato trovato" : "Nessun associato disponibile"}
                </li>
              ) : (
                filteredAssociati.map((a) => (
                <li key={a.id}>
                  <label className="flex items-center gap-3 p-3 hover:bg-[#f5f6f6] cursor-pointer">
                    <input
                      type="checkbox"
                      checked={groupMembers.includes(a.id)}
                      onChange={() => toggleGroupMember(a.id)}
                    />
                    <span className="text-sm" style={{ color: WA.textDark }}>
                      {a.firstName} {a.lastName}
                    </span>
                  </label>
                </li>
                ))
              )}
            </ul>
            <button
              type="submit"
              className="w-full py-2.5 rounded-lg text-white font-medium shrink-0"
              style={{ backgroundColor: WA.primaryLight }}
            >
              Crea gruppo
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
