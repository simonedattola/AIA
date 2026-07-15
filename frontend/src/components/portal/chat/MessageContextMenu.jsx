import { Reply, Pencil, Trash2, Info } from "lucide-react";
import { WA, QUICK_REACTIONS } from "./whatsappTheme";

export default function MessageContextMenu({
  menu,
  meId,
  onClose,
  onReply,
  onReaction,
  onEdit,
  onDelete,
  onInfo,
  canEdit,
}) {
  if (!menu) return null;
  const { msg, x, y } = menu;
  const deleted = msg.isDeleted || msg.deletedAt;

  return (
    <>
      <button type="button" className="fixed inset-0 z-40" onClick={onClose} aria-label="Chiudi menu" />
      <div
        className="fixed z-50 rounded-lg shadow-xl py-1 min-w-[200px] text-sm"
        style={{
          left: x,
          top: Math.max(8, y - 120),
          backgroundColor: WA.panelWhite,
          border: `1px solid ${WA.border}`,
        }}
      >
        {!deleted && (
          <>
            <button
              type="button"
              className="w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-[#f5f6f6]"
              onClick={() => onReply(msg)}
            >
              <Reply className="h-4 w-4" /> Rispondi
            </button>
            <div className="px-3 py-1 text-xs" style={{ color: WA.textMeta }}>
              Reagisci
            </div>
            <div className="flex px-2 pb-2 gap-0.5">
              {QUICK_REACTIONS.map((em) => (
                <button
                  key={em}
                  type="button"
                  className="text-xl p-2 rounded-full hover:bg-[#f0f2f5]"
                  onClick={() => onReaction(msg, em)}
                >
                  {em}
                </button>
              ))}
            </div>
            {canEdit(msg) && (
              <button
                type="button"
                className="w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-[#f5f6f6]"
                onClick={() => onEdit(msg)}
              >
                <Pencil className="h-4 w-4" /> Modifica
              </button>
            )}
            {msg.mittenteId === meId && (
              <>
                <button
                  type="button"
                  className="w-full px-4 py-2.5 text-left flex items-center gap-3 text-red-600 hover:bg-[#f5f6f6]"
                  onClick={() => onDelete(msg)}
                >
                  <Trash2 className="h-4 w-4" /> Elimina
                </button>
                <button
                  type="button"
                  className="w-full px-4 py-2.5 text-left flex items-center gap-3 hover:bg-[#f5f6f6]"
                  onClick={() => onInfo(msg)}
                >
                  <Info className="h-4 w-4" /> Info messaggio
                </button>
              </>
            )}
          </>
        )}
      </div>
    </>
  );
}
