import { FileText, Download, Play } from "lucide-react";
import { formatFileSize } from "../lib/format";
import { mediaUrl } from "../lib/media";

function isVideoAttachment(a) {
  const mime = (a.mimeType || "").toLowerCase();
  if (mime.startsWith("video/")) return true;
  const name = (a.fileName || a.fileUrl || "").toLowerCase();
  return /\.(mp4|webm|mov)(\?|$)/i.test(name);
}

export function AttachmentList({ attachments = [], className = "", showVideoPreview = false }) {
  if (!attachments?.length) return null;
  return (
    <ul className={`space-y-3 ${className}`}>
      {attachments.map((a) => {
        const url = mediaUrl(a.fileUrl);
        const video = isVideoAttachment(a);
        return (
          <li key={a.id || a.fileUrl}>
            {showVideoPreview && video ? (
              <div className="space-y-2">
                <video
                  src={url}
                  controls
                  preload="metadata"
                  className="w-full max-h-72 rounded-lg border border-slate-200 bg-black"
                >
                  <a href={url} target="_blank" rel="noopener noreferrer">
                    {a.fileName || "Video"}
                  </a>
                </video>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-navy-700 hover:text-navy-900"
                >
                  <Play className="h-4 w-4 shrink-0" />
                  <span className="truncate">{a.fileName || "Video"}</span>
                  {a.fileSize > 0 && (
                    <span className="text-xs text-slate-400 shrink-0">{formatFileSize(a.fileSize)}</span>
                  )}
                </a>
              </div>
            ) : (
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                download={video ? undefined : a.fileName || undefined}
                className="inline-flex items-center gap-2 text-sm text-navy-700 hover:text-navy-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md px-3 py-2 transition-colors w-full sm:w-auto"
              >
                {video ? (
                  <Play className="h-4 w-4 shrink-0 text-navy-500" />
                ) : (
                  <FileText className="h-4 w-4 shrink-0 text-navy-500" />
                )}
                <span className="truncate max-w-[16rem] sm:max-w-xs">{a.fileName || "Allegato"}</span>
                {a.fileSize > 0 && (
                  <span className="text-xs text-slate-400 shrink-0">{formatFileSize(a.fileSize)}</span>
                )}
                <Download className="h-3.5 w-3.5 shrink-0 text-slate-400 ml-auto" />
              </a>
            )}
          </li>
        );
      })}
    </ul>
  );
}
