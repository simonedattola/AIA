import { ArrowLeft, MoreVertical } from "lucide-react";
import ChatAvatar from "./ChatAvatar";
import { WA } from "./whatsappTheme";
import { groupSubtitle } from "./chatUtils";

export default function ConversationHeader({
  chat,
  onBack,
  onInfo,
  showBack,
}) {
  const subtitle = chat.isGroup
    ? groupSubtitle(chat)
    : "tocca per info contatto";

  return (
    <header
      className="px-2 py-2 flex items-center gap-1 shrink-0 border-b"
      style={{ backgroundColor: WA.headerBg, borderColor: WA.border }}
    >
      {showBack && (
        <button
          type="button"
          className="p-2 rounded-full hover:bg-black/5 md:hidden shrink-0"
          style={{ color: WA.textMuted }}
          onClick={onBack}
          aria-label="Indietro"
        >
          <ArrowLeft className="h-6 w-6" />
        </button>
      )}
      <ChatAvatar
        name={chat.peerName}
        photo={chat.peerPhoto}
        size="header"
        isGroup={chat.isGroup && !chat.peerPhoto}
        onClick={onInfo}
      />
      <button
        type="button"
        onClick={onInfo}
        className="flex-1 min-w-0 text-left py-1 px-2 rounded hover:bg-black/[0.04]"
      >
        <div className="font-medium text-[16px] truncate" style={{ color: WA.textDark }}>
          {chat.peerName}
        </div>
        <div className="text-[13px] truncate" style={{ color: WA.textMuted }}>
          {subtitle}
        </div>
      </button>
      <button
        type="button"
        onClick={onInfo}
        className="p-2 rounded-full hover:bg-black/5 shrink-0"
        style={{ color: WA.textMuted }}
        aria-label="Menu conversazione"
      >
        <MoreVertical className="h-6 w-6" />
      </button>
    </header>
  );
}
