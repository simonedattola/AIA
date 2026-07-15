/** Widget mappa embed (stile polo atletico / contatti). */
export default function SectionMapPanel({
  embedUrl,
  linkUrl,
  title = "Mappa",
  caption,
  className = "",
  testId = "section-map-panel",
}) {
  if (!embedUrl) return null;

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200 overflow-hidden min-h-[280px] ${className}`}
      data-testid={testId}
    >
      <iframe
        title={title}
        src={embedUrl}
        className="w-full h-full min-h-[280px] border-0"
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
        allowFullScreen
      />
      {linkUrl && (
        <p className="text-xs text-slate-500 px-4 py-2 border-t border-slate-100 bg-slate-50">
          <a
            href={linkUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-navy-600 hover:underline"
          >
            Apri in Google Maps
          </a>
          {caption ? ` · ${caption}` : ""}
        </p>
      )}
    </div>
  );
}
