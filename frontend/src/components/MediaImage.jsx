import { mediaUrl } from "../lib/media";

/** Image that resolves uploaded paths via the backend URL. */
export default function MediaImage({ src, alt = "", className, ...props }) {
  const resolved = mediaUrl(src);
  if (!resolved) return null;
  return <img src={resolved} alt={alt} className={className} {...props} />;
}
