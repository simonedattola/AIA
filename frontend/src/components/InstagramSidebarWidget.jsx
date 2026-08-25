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
 * L'iframe del profilo richiede ~560–640px: non comprimere sotto quel minimo.
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
      className={`bg-white rounded-lg shadow-sm border border-slate-200 flex flex-col overflow-hidden ${className}`.trim()}
      data-testid="instagram-profile-widget"
    >
      <div className="p-4 sm:p-5 bg-gradient-to-br from-[#833AB4] via-[#E1306C] to-[#F77737] text-white shrink-0">
        <div className="flex items-center gap-3">
          <div className="h-11 w-11 sm:h-12 sm:w-12 rounded-full bg-white/20 flex items-center justify-center backdrop-blur-sm shrink-0">
            <Instagram className="h-5 w-5 sm:h-6 sm:w-6" aria-hidden />
          </div>
          <div className="min-w-0">
            <Eyebrow className="text-[10px] tracking-[0.2em] text-white/90">Instagram</Eyebrow>
            <CardTitle as="h3" className="leading-tight truncate text-white">
              {title || "AIA Legnano"}
            </CardTitle>
            {displayHandle && <p className="text-sm text-white/90 truncate">{displayHandle}</p>}
          </div>
        </div>
        {subtitle && <p className="text-sm text-white/90 mt-2 leading-relaxed line-clamp-2">{subtitle}</p>}
      </div>
      {embedSrc ? (
        <div className="aia-ig-profile-embed bg-slate-50 border-t border-slate-100 shrink-0">
          <iframe
            title="Profilo Instagram AIA Legnano"
            src={embedSrc}
            className="w-full border-0 block"
            style={{ height: "640px", minHeight: "560px" }}
            loading="lazy"
            allow="encrypted-media; clipboard-write"
          />
        </div>
      ) : (
        <div className="p-6 text-sm text-slate-600 bg-slate-50 border-t border-slate-100">
          Inserisci l&apos;URL del profilo Instagram in Admin → Impostazioni → Contatti.
        </div>
      )}
      {href && (
        <div className="p-4 border-t border-slate-200 bg-white shrink-0">
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
