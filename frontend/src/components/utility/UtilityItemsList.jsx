import { Download, ExternalLink } from "lucide-react";
import { mediaUrl } from "../../lib/media";
import { utilityItemHref } from "../../lib/utility";
import { PortalEmptyState } from "../portal/portal-ui";

export default function UtilityItemsList({ items = [], emptyMessage = "Nessun elemento.", variant = "download" }) {
  if (!items.length) {
    return <PortalEmptyState icon={variant === "link" ? ExternalLink : Download}>{emptyMessage}</PortalEmptyState>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-5" data-testid="utility-items-list">
      {items.map((item) => {
        const href = mediaUrl(utilityItemHref(item));
        const isExternal = /^https?:\/\//i.test(href);
        const Icon = variant === "link" ? ExternalLink : Download;
        return (
          <article key={item.id} className="flex gap-4 items-start group">
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              download={variant !== "link" && !isExternal}
              className="shrink-0 w-12 h-12 rounded-full border-2 border-navy-600 text-navy-600 flex items-center justify-center transition-colors hover:bg-navy-600 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-gold-400 focus-visible:ring-offset-2"
              aria-label={`Apri ${item.title}`}
            >
              <Icon className="h-5 w-5" strokeWidth={2} />
            </a>
            <div className="min-w-0 pt-0.5">
              <h3 className="font-display text-base font-semibold text-navy-800 leading-snug mb-1">
                <a href={href} target="_blank" rel="noopener noreferrer" className="hover:text-navy-600">
                  {item.title}
                </a>
              </h3>
              {item.description && (
                <p className="text-sm text-slate-600 leading-relaxed">{item.description}</p>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}
