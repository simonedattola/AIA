import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchMember } from "../../lib/api";
import { normalizeMember, hasDesignations, memberRoleLabel, profileBackPath } from "../../lib/memberRoles";
import { formatDateIt } from "../../lib/format";
import MediaImage from "../MediaImage";
import DesignationsDataTable from "../designations/DesignationsDataTable";
import {
  ArrowLeft, ArrowRight, Award, CalendarDays, Calendar, Newspaper, Quote, Trophy,
} from "lucide-react";
import { Button, Card, CardTitle, CtaTitle, Eyebrow, PageTitle, SubsectionTitle } from "@/design-system";
import TestimonialAuthor from "../testimonials/TestimonialAuthor";

const INNER = "max-w-5xl mx-auto px-4 sm:px-6 lg:px-8";
const PROFILE_DESIGNATIONS_PAGE = 8;

function ProfileSectionHeader({ icon, title }) {
  return (
    <div className="flex items-center gap-3 mb-6">
      <span className="text-gold-400">{icon}</span>
      <SubsectionTitle as="h2">{title}</SubsectionTitle>
      <span className="flex-1 h-px bg-slate-200" />
    </div>
  );
}

function formatSeasonLabel(s) {
  if (!s || !s.includes("-")) return s || "Stagione";
  const [a, b] = s.split("-");
  return `${a}/${b}`;
}

/** Profilo pubblico associato — usato come blocco CMS e fallback pagina. */
export default function MemberProfileContent({ memberSlug }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [season, setSeason] = useState("");

  useEffect(() => {
    if (!memberSlug) return;
    setData(null);
    setError(null);
    const params = season ? { season } : {};
    fetchMember(memberSlug, params)
      .then((d) => {
        setData(d);
        if (!season && d.activeSeason) setSeason(d.activeSeason);
      })
      .catch(() => setError("Profilo non trovato"));
  }, [memberSlug, season]);

  if (!memberSlug) {
    return <p className="text-slate-500 py-12 text-center">Slug associato mancante.</p>;
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-32 text-center" data-testid="associato-error">
        <PageTitle className="mb-4">Profilo non trovato</PageTitle>
        <Button to="/arbitri" variant="primary">Torna agli arbitri</Button>
      </div>
    );
  }

  if (!data) return <div className="py-32 text-center text-slate-500">Caricamento…</div>;

  const {
    member: raw, awards = [], articles = [], events = [], testimonials = [],
    designations = [], seasonsAvailable = [], activeSeason = "",
  } = data;
  const m = normalizeMember(raw);
  const hasBio = !!(m.bio && m.bio.trim());
  const hasPresidentLongBio = !!(m.isPresident && m.presidentLongBio && m.presidentLongBio.trim());
  const showDesignations = hasDesignations(m.memberRole);
  const back = profileBackPath(m.memberRole, m);
  const backLabel =
    back === "/chi-siamo" ? "Chi siamo" : back === "/osservatori" ? "Osservatori" : "Arbitri";

  return (
    <div data-testid="member-profile-content" className="bg-background">
      <section className="bg-navy-700 text-white pt-16 pb-12 lg:pb-14">
        <div className={INNER}>
          <Link to={back} className="inline-flex items-center gap-2 text-gold-400 hover:text-white text-sm mb-8 font-medium">
            <ArrowLeft className="h-4 w-4" /> {backLabel}
          </Link>
          <div className="flex flex-col lg:flex-row items-start gap-8">
            {m.photoUrl ? (
              <MediaImage src={m.photoUrl} alt={`${m.firstName} ${m.lastName}`} className="w-28 h-28 sm:w-36 sm:h-36 rounded-2xl object-cover border-4 border-gold-400 shadow-xl flex-shrink-0" />
            ) : (
              <div className="w-28 h-28 sm:w-36 sm:h-36 rounded-2xl bg-gold-400 text-navy-900 flex items-center justify-center font-display font-bold text-3xl flex-shrink-0 shadow-xl">
                {m.firstName[0]}{m.lastName[0]}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <Eyebrow className="text-gold-400 mb-2">{memberRoleLabel(m)}</Eyebrow>
              <CtaTitle className="text-white leading-tight">{m.firstName} {m.lastName}</CtaTitle>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-3 text-slate-300 text-sm">
                {m.memberRole === "arbitro" && m.category && <span className="text-gold-300 font-medium">{m.category}</span>}
                {m.memberRole !== "arbitro" && m.category && <span>{m.category}</span>}
                {m.yearStart && <span>In sezione dal {m.yearStart}</span>}
              </div>
              {hasBio && (
                <p className="mt-6 pt-6 border-t border-white/15 text-slate-200 leading-relaxed whitespace-pre-line max-w-3xl" data-testid="member-bio">{m.bio}</p>
              )}
            </div>
          </div>
        </div>
      </section>

      <div className={`${INNER} site-section space-y-10 lg:space-y-12`}>
        {showDesignations && (
          <section data-testid="member-designations">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-2">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <span className="text-gold-400"><Trophy className="h-6 w-6" /></span>
                <SubsectionTitle as="h2">Designazioni</SubsectionTitle>
              </div>
              {seasonsAvailable.length > 0 && (
                <label className="flex items-center gap-2 text-sm text-slate-600 shrink-0">
                  <span className="font-medium">Stagione</span>
                  <select value={season || activeSeason} onChange={(e) => setSeason(e.target.value)} className="border border-slate-300 rounded-md px-3 py-1.5 text-sm focus:border-navy-600 focus:outline-none" data-testid="member-designations-season">
                    {seasonsAvailable.map((s) => <option key={s} value={s}>{formatSeasonLabel(s)}</option>)}
                  </select>
                </label>
              )}
            </div>
            {designations.length === 0 ? (
              <p className="text-sm text-slate-500">Nessuna designazione per questa stagione.</p>
            ) : (
              <DesignationsDataTable designations={designations} maxVisibleRows={PROFILE_DESIGNATIONS_PAGE} />
            )}
          </section>
        )}
        {hasPresidentLongBio && (
          <section data-testid="member-president-long-bio">
            <ProfileSectionHeader icon={<Quote className="h-6 w-6" />} title="Il Presidente racconta" />
            <Card padding="default" className="sm:p-8 shadow-sm">
              <p className="text-slate-700 leading-relaxed whitespace-pre-line">{m.presidentLongBio}</p>
            </Card>
          </section>
        )}
        {awards.length > 0 && (
          <section data-testid="member-awards">
            <ProfileSectionHeader icon={<Award className="h-6 w-6" />} title="Premi e riconoscimenti" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {awards.map((a) => (
                <div key={a.id} className="bg-white rounded-xl p-5 shadow-sm border border-slate-100 flex gap-4 items-start">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-gold-400/25 to-gold-500/10 flex items-center justify-center flex-shrink-0 border border-gold-400/30">
                    <Trophy className="h-6 w-6 text-gold-600" />
                  </div>
                  <div className="min-w-0 flex-1">
                    {a.year && <div className="text-xs font-semibold uppercase tracking-wider text-gold-600 mb-1">{a.year}</div>}
                    <div className="font-display font-semibold text-navy-800 text-lg leading-snug">{a.title}</div>
                    {a.description && <p className="text-sm text-slate-600 mt-2 leading-relaxed">{a.description}</p>}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
        {articles.length > 0 && (
          <section data-testid="member-articles">
            <ProfileSectionHeader icon={<Newspaper className="h-6 w-6" />} title="Notizie" />
            <div className="space-y-3">
              {articles.map((a) => (
                <Card
                  key={a.id}
                  as={Link}
                  to={`/news/${a.slug}`}
                  interactive
                  padding="none"
                  className="group flex gap-4 overflow-hidden shadow-sm border-slate-100 hover:border-navy-300 hover:shadow-md"
                >
                  <div className="w-28 sm:w-36 h-24 sm:h-28 flex-shrink-0 bg-slate-100 overflow-hidden">
                    {a.coverUrl ? <MediaImage src={a.coverUrl} alt="" className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" /> : (
                      <div className="w-full h-full flex items-center justify-center bg-navy-50"><Newspaper className="h-7 w-7 text-navy-300" /></div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0 py-3 pr-4 flex flex-col justify-center">
                    <CardTitle as="h3" className="text-navy-800 text-sm sm:text-base leading-snug group-hover:text-navy-600 line-clamp-2">{a.title}</CardTitle>
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-navy-600 mt-1.5">Leggi <ArrowRight className="h-3.5 w-3.5" /></span>
                  </div>
                </Card>
              ))}
            </div>
          </section>
        )}
        {testimonials.length > 0 && (
          <section data-testid="member-testimonials">
            <ProfileSectionHeader icon={<Quote className="h-6 w-6" />} title="Testimonianze" />
            <div className="space-y-4">
              {testimonials.map((t) => (
                <blockquote key={t.id} className="bg-white rounded-lg px-5 py-4 text-sm text-slate-700 leading-relaxed shadow-sm border-l-4 border-gold-400">
                  <p className="italic mb-4">&ldquo;{t.quote}&rdquo;</p>
                  <footer className="not-italic">
                    <TestimonialAuthor
                      linkToProfile={false}
                      testimonial={{
                        ...t,
                        name: t.name || `${m.firstName} ${m.lastName}`.trim(),
                        photoUrl: t.photoUrl || m.photoUrl,
                      }}
                    />
                  </footer>
                </blockquote>
              ))}
            </div>
          </section>
        )}
        {events.length > 0 && (
          <section data-testid="member-events">
            <ProfileSectionHeader icon={<Calendar className="h-6 w-6" />} title="Eventi" />
            <ul className="space-y-3">
              {events.map((e) => (
                <li key={e.id} className="bg-white rounded-lg px-4 py-3.5 text-sm shadow-sm">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className="inline-flex items-center gap-1.5 text-slate-500 shrink-0">
                      <CalendarDays className="h-4 w-4 text-gold-400" />{formatDateIt(e.date, { short: true })}
                    </span>
                    <span className="font-medium text-navy-800">{e.titolo}</span>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}
