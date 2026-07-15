import { Send } from "lucide-react";
import ConversationHeader from "./ConversationHeader";
import MessageBubble from "./MessageBubble";
import InputBar from "./InputBar";
import { WA, CHAT_WALLPAPER } from "./whatsappTheme";
import { formatDay } from "./chatUtils";

export default function ChatWindow({
  chat,
  me,
  panelVisible,
  onBack,
  onInfo,
  bottomRef,
  error,
  onMenu,
  onReaction,
  inputProps,
}) {
  const visibility = !chat ? "hidden md:flex" : panelVisible ? "flex" : "hidden md:flex";

  if (!chat) {
    return (
      <div
        className={`wa-chat-window-panel flex flex-1 flex-col min-w-0 absolute md:relative inset-0 z-20 md:z-auto ${visibility}`}
        style={{ backgroundColor: WA.chatBg }}
      >
        <div
          className="flex-1 hidden md:flex flex-col items-center justify-center p-8 text-center border-b"
          style={{
            backgroundColor: WA.listBg,
            borderColor: WA.border,
            backgroundImage: CHAT_WALLPAPER,
          }}
        >
          <div
            className="w-24 h-24 rounded-full flex items-center justify-center mb-6"
            style={{ backgroundColor: WA.panelWhite }}
          >
            <Send className="h-12 w-12" style={{ color: WA.textMeta }} />
          </div>
          <p className="text-[32px] font-light mb-2" style={{ color: WA.textDark }}>
            Messaggistica AIA Legnano
          </p>
          <p className="text-sm max-w-md" style={{ color: WA.textMuted }}>
            Invia e ricevi messaggi con gli associati della sezione AIA Legnano.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`wa-chat-window-panel flex-1 flex-col min-w-0 absolute md:relative inset-0 z-20 md:z-auto ${visibility}`}
      style={{ backgroundColor: WA.chatBg }}
    >
      <ConversationHeader chat={chat} onBack={onBack} onInfo={onInfo} showBack />

      <div
        className="flex-1 overflow-y-auto px-[4%] md:px-[8%] py-3"
        style={{ backgroundColor: WA.chatBg, backgroundImage: CHAT_WALLPAPER }}
      >
        {(chat.messages || []).map((m, idx) => {
          const mine = m.mittenteId === me.id;
          const showDay =
            idx === 0 || formatDay(m.createdAt) !== formatDay(chat.messages[idx - 1]?.createdAt);
          return (
            <div key={m.id}>
              {showDay && (
                <div className="flex justify-center my-3">
                  <span
                    className="text-xs px-3 py-1 rounded-lg shadow-sm uppercase tracking-wide"
                    style={{
                      backgroundColor: "rgba(255,255,255,0.92)",
                      color: WA.textMuted,
                    }}
                  >
                    {formatDay(m.createdAt)}
                  </span>
                </div>
              )}
              <div className={`flex mb-1 ${mine ? "justify-end" : "justify-start"}`}>
                <MessageBubble
                  m={m}
                  mine={mine}
                  isGroup={chat.isGroup}
                  onMenu={onMenu}
                  onReactionClick={onReaction}
                />
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {error && (
        <p className="text-xs text-red-600 px-4 py-1 bg-red-50 shrink-0">{error}</p>
      )}

      <InputBar {...inputProps} />
    </div>
  );
}
