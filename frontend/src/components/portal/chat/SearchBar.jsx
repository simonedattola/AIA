import { Search } from "lucide-react";
import { WA } from "./whatsappTheme";

export default function SearchBar({ value, onChange, placeholder = "Cerca o avvia una nuova chat" }) {
  return (
    <div className="px-3 py-2 shrink-0" style={{ backgroundColor: WA.listBg }}>
      <div className="relative">
        <Search
          className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
          style={{ color: WA.textMeta }}
        />
        <input
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className="w-full rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none"
          style={{
            backgroundColor: WA.panelWhite,
            color: WA.textDark,
          }}
        />
      </div>
    </div>
  );
}
