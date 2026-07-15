import { Send, Paperclip, Smile, X, Reply, Pencil } from "lucide-react";
import { WA } from "./whatsappTheme";
import EmojiPicker from "./EmojiPicker";

export default function InputBar({
  testo,
  onTestoChange,
  onSubmit,
  fileRef,
  onFileChange,
  uploading,
  editing,
  replyTo,
  onClearReply,
  onClearEdit,
  showEmojiBar,
  onToggleEmojiBar,
  onEmojiPick,
}) {
  return (
    <>
      {replyTo && !editing && (
        <div
          className="px-3 py-2 flex items-center gap-2 shrink-0 border-t"
          style={{ backgroundColor: WA.headerBg, borderColor: WA.border }}
        >
          <Reply className="h-5 w-5 shrink-0" style={{ color: WA.primary }} />
          <div
            className="flex-1 min-w-0 border-l-[3px] pl-2"
            style={{ borderColor: WA.primary }}
          >
            <div className="text-xs font-semibold" style={{ color: WA.primary }}>
              {replyTo.mittenteNome}
            </div>
            <div className="text-xs truncate" style={{ color: WA.textMuted }}>
              {replyTo.isDeleted || replyTo.deletedAt
                ? "Messaggio eliminato"
                : replyTo.testo || (replyTo.tipo === "image" ? "Foto" : "Allegato")}
            </div>
          </div>
          <button type="button" onClick={onClearReply} className="p-1">
            <X className="h-5 w-5" style={{ color: WA.textMeta }} />
          </button>
        </div>
      )}

      {editing && (
        <div
          className="px-3 py-2 flex items-center gap-2 text-sm shrink-0 border-t"
          style={{ backgroundColor: "#fff8e6", borderColor: WA.border }}
        >
          <Pencil className="h-4 w-4 text-amber-700" />
          <span className="flex-1 text-amber-900">Modifica messaggio</span>
          <button type="button" onClick={onClearEdit}>
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <form
        onSubmit={onSubmit}
        className="px-2 py-2 flex items-end gap-1 shrink-0"
        style={{ backgroundColor: WA.headerBg }}
      >
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip"
          onChange={onFileChange}
        />
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={uploading || !!editing}
          className="p-2.5 rounded-full hover:bg-black/5 disabled:opacity-50 shrink-0"
          style={{ color: WA.textMuted }}
          title="Allega"
        >
          <Paperclip className="h-6 w-6" />
        </button>
        <button
          type="button"
          onClick={onToggleEmojiBar}
          className={`p-2.5 rounded-full hover:bg-black/5 shrink-0 ${showEmojiBar ? "bg-black/5" : ""}`}
          style={{ color: WA.primary }}
          title="Emoji"
        >
          <Smile className="h-6 w-6" />
        </button>
        <input
          value={testo}
          onChange={onTestoChange}
          placeholder={
            editing ? "Modifica il testo…" : uploading ? "Caricamento…" : "Scrivi un messaggio"
          }
          disabled={uploading}
          className="flex-1 rounded-lg px-4 py-2.5 text-[15px] focus:outline-none min-h-[42px] max-h-32"
          style={{
            backgroundColor: WA.panelWhite,
            color: WA.textDark,
            border: `1px solid ${WA.border}`,
          }}
        />
        <button
          type="submit"
          disabled={uploading || (!testo.trim() && !editing)}
          className="p-2.5 rounded-full text-white disabled:opacity-40 shrink-0 transition-opacity"
          style={{ backgroundColor: WA.primaryLight }}
          aria-label="Invia"
        >
          <Send className="h-6 w-6" />
        </button>
      </form>

      {showEmojiBar && <EmojiPicker onPick={onEmojiPick} />}
    </>
  );
}
