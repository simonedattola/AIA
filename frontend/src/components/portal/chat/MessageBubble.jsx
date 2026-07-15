import { Trash2, Download, FileText, MoreVertical } from "lucide-react";
import { WA } from "./whatsappTheme";
import MessageStatusIcon from "./MessageStatusIcon";
import { formatTime } from "./chatUtils";

export default function MessageBubble({ m, mine, isGroup, onMenu, onReactionClick }) {
  const url = m.attachmentUrlResolved || m.attachmentUrl;

  return (
    <div
      className={`relative group max-w-[88%] sm:max-w-[75%] md:max-w-[65%] px-2.5 py-1.5 text-[14.2px] leading-[19px] shadow-sm ${
        mine
          ? `wa-bubble-tail-out rounded-[18px] rounded-tr-[4px]`
          : `wa-bubble-tail-in rounded-[18px] rounded-tl-[4px]`
      }`}
      style={{
        backgroundColor: mine ? WA.bubbleOut : WA.bubbleIn,
        color: WA.textDark,
      }}
      onContextMenu={(e) => {
        e.preventDefault();
        onMenu(e, m);
      }}
    >
      {isGroup && !mine && (
        <div className="text-[12.5px] font-semibold mb-0.5" style={{ color: WA.primaryLight }}>
          {m.mittenteNome}
        </div>
      )}

      {m.replyTo && (
        <div
          className="rounded-md px-2 py-1.5 mb-1 text-xs border-l-[3px]"
          style={{
            borderLeftColor: mine ? WA.primary : WA.primaryLight,
            backgroundColor: mine ? WA.quoteOut : WA.quoteIn,
          }}
        >
          <div className="font-semibold truncate" style={{ color: mine ? WA.primary : WA.primaryLight }}>
            {m.replyTo.mittenteNome}
          </div>
          <div className="truncate opacity-80" style={{ color: WA.textMuted }}>
            {m.replyTo.testo}
          </div>
        </div>
      )}

      {m.isDeleted || m.deletedAt ? (
        <p className="italic flex items-center gap-1 text-[13px]" style={{ color: WA.textMeta }}>
          <Trash2 className="h-3.5 w-3.5" />
          Messaggio eliminato
        </p>
      ) : (
        <>
          {m.tipo === "image" && url && (
            <a href={url} target="_blank" rel="noreferrer" className="block mb-0.5 -mx-0.5">
              <img src={url} alt="" className="max-w-full rounded-lg max-h-72 object-cover" />
            </a>
          )}
          {m.tipo === "file" && url && (
            <a
              href={url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-2 p-2 rounded-lg mb-0.5 hover:opacity-90"
              style={{ backgroundColor: "rgba(0,0,0,0.04)" }}
            >
              <FileText className="h-8 w-8 shrink-0" style={{ color: WA.primary }} />
              <span className="truncate font-medium">{m.attachmentName || "Allegato"}</span>
              <Download className="h-4 w-4 shrink-0 ml-auto" />
            </a>
          )}
          {m.testo && <p className="whitespace-pre-wrap break-words">{m.testo}</p>}
        </>
      )}

      {(m.reactionSummary || []).length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1 -mb-0.5">
          {m.reactionSummary.map((r) => (
            <button
              key={r.emoji}
              type="button"
              onClick={() => onReactionClick(m, r.emoji)}
              className="text-xs px-1.5 py-0.5 rounded-full border shadow-sm"
              style={{
                backgroundColor: m.myReaction === r.emoji ? WA.bubbleOut : WA.panelWhite,
                borderColor: WA.border,
              }}
              title={r.names?.join(", ")}
            >
              {r.emoji} {r.count > 1 ? r.count : ""}
            </button>
          ))}
        </div>
      )}

      <div
        className="flex items-center justify-end gap-0.5 float-right ml-2 mt-0.5 -mb-0.5 pl-2"
        style={{ color: WA.textMeta, fontSize: "11px" }}
      >
        {m.editedAt && <span className="mr-0.5">modificato</span>}
        <span>{formatTime(m.createdAt)}</span>
        {mine && !m.isDeleted && !m.deletedAt && (
          <MessageStatusIcon status={m.readStatus || "delivered"} />
        )}
      </div>
      <div className="clear-both h-0" />

      <button
        type="button"
        onClick={(e) => onMenu(e, m)}
        className="absolute top-0.5 right-0.5 p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity md:group-hover:opacity-100"
        style={{ backgroundColor: WA.panelWhite, color: WA.textMeta }}
        aria-label="Azioni messaggio"
      >
        <MoreVertical className="h-4 w-4" />
      </button>
    </div>
  );
}
