import { CheckCheck } from "lucide-react";
import { WA } from "./whatsappTheme";

export default function MessageStatusIcon({ status }) {
  if (!status) return null;
  const read = status === "read";
  return (
    <CheckCheck
      className="inline h-[14px] w-[14px] ml-0.5 shrink-0"
      style={{ color: read ? WA.readTick : WA.textMeta }}
      strokeWidth={2.5}
      aria-label={read ? "Letto" : "Consegnato"}
    />
  );
}
