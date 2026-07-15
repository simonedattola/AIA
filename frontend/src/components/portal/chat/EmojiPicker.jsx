import { useState } from "react";
import { EMOJI_CATEGORIES } from "./emojiData";
import { WA, EMOJI_FONT } from "./whatsappTheme";

export default function EmojiPicker({ onPick }) {
  const [cat, setCat] = useState(EMOJI_CATEGORIES[0].id);
  const active = EMOJI_CATEGORIES.find((c) => c.id === cat) || EMOJI_CATEGORIES[0];

  return (
    <div
      className="border-t shrink-0 flex flex-col max-h-[280px]"
      style={{ backgroundColor: WA.panelWhite, borderColor: WA.border }}
    >
      <div
        className="flex gap-0.5 px-1 py-1 overflow-x-auto shrink-0 border-b"
        style={{ borderColor: WA.border, backgroundColor: WA.listBg }}
      >
        {EMOJI_CATEGORIES.map((c) => (
          <button
            key={c.id}
            type="button"
            title={c.title}
            onClick={() => setCat(c.id)}
            className="text-xl p-2 rounded-lg shrink-0 transition-colors"
            style={{
              backgroundColor: cat === c.id ? WA.panelWhite : "transparent",
              fontFamily: EMOJI_FONT,
            }}
          >
            {c.label}
          </button>
        ))}
      </div>
      <div
        className="flex-1 overflow-y-auto p-2 grid grid-cols-8 sm:grid-cols-10 gap-0.5"
        style={{ fontFamily: EMOJI_FONT }}
      >
        {active.emojis.map((em) => (
          <button
            key={em}
            type="button"
            className="text-2xl p-1.5 rounded hover:bg-[#f0f2f5] active:scale-95 transition-transform"
            onClick={() => onPick(em)}
            title={em}
          >
            {em}
          </button>
        ))}
      </div>
    </div>
  );
}
