import ChatAvatar from "./ChatAvatar";
import { WA } from "./whatsappTheme";
import { formatTime, listPreview } from "./chatUtils";

export default function ChatListItem({ conversation: c, active, onSelect }) {
  const unread = c.unreadCount > 0;
  return (
    <button
      type="button"
      onClick={() => onSelect(c.chatId)}
      className="w-full flex items-center gap-3 px-3 py-2.5 text-left transition-colors border-b"
      style={{
        backgroundColor: active ? WA.activeRow : WA.panelWhite,
        borderColor: WA.border,
      }}
      onMouseEnter={(e) => {
        if (!active) e.currentTarget.style.backgroundColor = WA.hoverRow;
      }}
      onMouseLeave={(e) => {
        if (!active) e.currentTarget.style.backgroundColor = WA.panelWhite;
      }}
    >
      <ChatAvatar name={c.peerName} photo={c.peerPhoto} isGroup={c.isGroup && !c.peerPhoto} />
      <div className="flex-1 min-w-0 border-b border-transparent">
        <div className="flex justify-between items-baseline gap-2">
          <span
            className={`truncate text-[17px] ${unread ? "font-semibold" : "font-normal"}`}
            style={{ color: WA.textDark }}
          >
            {c.peerName}
          </span>
          <span
            className="text-[12px] shrink-0"
            style={{ color: unread ? WA.primaryLight : WA.textMeta }}
          >
            {formatTime(c.lastAt)}
          </span>
        </div>
        <div className="flex justify-between items-center gap-2 mt-0.5">
          <p className="text-[14px] truncate" style={{ color: WA.textMuted }}>
            {listPreview(c)}
          </p>
          {unread && (
            <span
              className="shrink-0 min-w-[20px] h-5 px-1.5 rounded-full text-white text-xs flex items-center justify-center font-medium"
              style={{ backgroundColor: WA.accent }}
            >
              {c.unreadCount > 99 ? "99+" : c.unreadCount}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}
