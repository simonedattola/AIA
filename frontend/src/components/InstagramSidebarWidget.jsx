import { Instagram, ExternalLink } from "lucide-react";
import { CardTitle, Eyebrow, Button } from "@/design-system";

function parseInstagramHandle(url) {
  if (!url || typeof url !== "string") return null;
  const trimmed = url.trim();
  if (trimmed.startsWith("@")) return trimmed.slice(1).split("/")[0] || null;
  const m = trimmed.match(/instagram\.com\/([^/?#]+)/i);
  return m ? m[1].replace(/^@/, "") : null;
}

/**
 * Widget Instagram per sidebar home (profilo embed ufficiale + header gradiente).
 * Layout collaudato: riempie l'altezza della colonna eventi.
 */
export default function InstagramSidebarWidget({
  profileUrl = "",
  title = "AIA Legnano",
  subtitle = "",
  className = "",
}) {
  const handle = parseInstagramHandle(profileUrl);
  const href = profileUrl || (handle ? `https://www.instagram.com/${handle}/` : null);
  const embedSrc = handle ? `https://www.instagram.com/${handle}/embed` : null;
  const displayHandle = handle ? `@${handle}` : null;

  return (
    <div
      className={`bg-white rounded-lg shadow-sm overflow-hidden border border-slate-200 flex flex-col h-full min-h-0 ${className}`.trim()}
      data-testid="instagram-profile-widget"
    >
      <div className="p-5 bg-gradient-to-br from-[#833AB4] via-[#E1306C] to-[#F77737] text-white shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm">
            <Instagram className="h-6 w-6" aria-hidden />
          </div>
          <div className="min-w-0">
            <Eyebrow className="text-[10px] tracking-[0.2em] text-white/90">Instagram</Eyebrow>
            <CardTitle as="h3" className="leading-tight truncate text-white">
              {title || "AIA Legnano"}
            </CardTitle>
            {displayHandle && <p className="text-sm text-white/90 truncate">{displayHandle}</p>}
          </div>
        </div>
        {subtitle && <p className="text-sm text-white/90 mt-3 leading-relaxed line-clamp-2">{subtitle}</p>}
      </div>
      {embedSrc ? (
        <div className="bg-slate-50 border-t border-slate-100 flex-1 min-h-[240px] flex flex-col">
          <iframe
            title="Profilo Instagram AIA Legnano"
            src={embedSrc}
            className="w-full flex-1 border-0 min-h-[240px]"
            scrolling="no"
            loading="lazy"
            allowTransparency
          />
        </div>
      ) : (
        <div className="p-6 text-sm text-slate-600 bg-slate-50 border-t border-slate-100 flex-1">
          Inserisci l&apos;URL del profilo Instagram in Admin → Impostazioni → Contatti.
        </div>
      )}
      {href && (
        <div className="p-4 border-t border-slate-200 bg-white shrink-0 mt-auto">
          <Button
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            variant="primary"
            size="sm"
            className="w-full"
            data-testid="instagram-profile-follow"
          >
            Seguici su Instagram <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

export { parseInstagramHandle };
