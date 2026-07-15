import { Users } from "lucide-react";
import { WA } from "./whatsappTheme";

const SIZES = {
  list: "h-[49px] w-[49px] text-sm",
  header: "h-10 w-10 text-sm",
  xl: "h-48 w-48 text-4xl",
};

export default function ChatAvatar({ name, photo, size = "list", isGroup, onClick }) {
  const sz = SIZES[size] || SIZES.list;
  const initials = (name || "?")
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  const inner = photo ? (
    <img src={photo} alt="" className={`${sz} rounded-full object-cover shrink-0`} />
  ) : isGroup ? (
    <div
      className={`${sz} rounded-full flex items-center justify-center text-white shrink-0`}
      style={{ backgroundColor: WA.primaryDark }}
    >
      <Users className={size === "xl" ? "h-16 w-16" : "h-5 w-5"} />
    </div>
  ) : (
    <div
      className={`${sz} rounded-full flex items-center justify-center font-medium shrink-0`}
      style={{ backgroundColor: "#dfe5e7", color: "#54656f" }}
    >
      {initials}
    </div>
  );

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="shrink-0 rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-[#004587]"
      >
        {inner}
      </button>
    );
  }
  return inner;
}
