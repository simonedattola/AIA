import { Link } from "react-router-dom";
import MediaImage from "../MediaImage";
import { formatPersonName } from "../../lib/format";

const NO_HOVER_LINK =
  "flex items-center gap-3 text-inherit no-underline hover:text-inherit hover:no-underline hover:bg-transparent active:text-inherit focus:outline-none focus-visible:outline-none";

function AuthorAvatar({ name, photoUrl }) {
  if (photoUrl) {
    return <MediaImage src={photoUrl} alt="" className="w-12 h-12 rounded-full object-cover shrink-0" />;
  }
  return (
    <div className="w-12 h-12 rounded-full bg-navy-100 text-navy-600 flex items-center justify-center text-sm font-semibold shrink-0">
      {(name || "?").charAt(0)}
    </div>
  );
}

/** Foto a sinistra, nome e ruolo a destra. Link al profilo solo se memberSlug e linkToProfile. */
export default function TestimonialAuthor({ testimonial: t, linkToProfile = true }) {
  const slug = (t.memberSlug || "").trim();
  const profileTo = linkToProfile && slug ? `/arbitri/${slug}` : null;
  const displayName = formatPersonName(null, null, t.name);

  const author = (
    <>
      <AuthorAvatar name={displayName} photoUrl={t.photoUrl} />
      <div className="min-w-0">
        <div className="font-semibold text-navy-700">{displayName}</div>
        {t.role && <div className="text-sm text-slate-500 mt-0.5">{t.role}</div>}
      </div>
    </>
  );

  if (profileTo) {
    return (
      <Link
        to={profileTo}
        className={NO_HOVER_LINK}
        data-testid={`testimonial-profile-${slug}`}
        aria-label={`Profilo di ${displayName}`}
      >
        {author}
      </Link>
    );
  }

  return <div className="flex items-center gap-3">{author}</div>;
}
