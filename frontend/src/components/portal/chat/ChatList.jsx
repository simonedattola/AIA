import { Plus } from "lucide-react";
import SearchBar from "./SearchBar";
import ChatListItem from "./ChatListItem";
import { WA } from "./whatsappTheme";

export default function ChatList({
  search,
  onSearchChange,
  conversazioni,
  activeChatId,
  onSelectChat,
  onNewChat,
  listVisible,
}) {
  const visibility = listVisible ? "flex" : "hidden md:flex";
  return (
    <aside
      className={`wa-chat-list-panel w-full md:w-[30%] md:min-w-0 md:max-w-[420px] flex flex-col shrink-0 border-r absolute md:relative inset-0 z-10 md:z-auto ${visibility}`}
      style={{ backgroundColor: WA.panelWhite, borderColor: WA.border }}
    >
      <header
        className="px-4 py-3 flex items-center justify-between shrink-0"
        style={{ backgroundColor: WA.listBg }}
      >
        <h1 className="text-xl font-normal" style={{ color: WA.textDark }}>
          Chat
        </h1>
        <button
          type="button"
          onClick={onNewChat}
          className="p-2 rounded-full transition-colors hover:bg-black/5"
          style={{ color: WA.textMuted }}
          title="Nuova chat o gruppo"
        >
          <Plus className="h-6 w-6" />
        </button>
      </header>
      <SearchBar value={search} onChange={onSearchChange} />
      <div className="flex-1 overflow-y-auto" style={{ backgroundColor: WA.panelWhite }}>
        {conversazioni.map((c) => (
          <ChatListItem
            key={c.chatId}
            conversation={c}
            active={activeChatId === c.chatId}
            onSelect={onSelectChat}
          />
        ))}
        {conversazioni.length === 0 && (
          <p className="text-sm p-8 text-center" style={{ color: WA.textMeta }}>
            Nessuna conversazione. Avvia una chat o crea un gruppo.
          </p>
        )}
      </div>
    </aside>
  );
}
