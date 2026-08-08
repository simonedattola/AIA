/* Public renderers for all CMS block types. Each takes `config` and renders a section. */
import { memo, useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import * as Icons from "lucide-react";
import {
  HeroTitle, CtaTitle, SectionTitle, SubsectionTitle, CardTitle, Eyebrow, Card, Button,
} from "@/design-system";
import {
  fetchArticles, fetchEvents, fetchStats,
  fetchTestimonials, fetchDocuments, fetchDocumentSections, submitLead,
} from "../lib/api";
import { useSite } from "../lib/site-context";
import { formatDateIt, contactPreferenceLabel } from "../lib/format";
import { AttachmentList } from "../components/AttachmentList";
import NewsArticleCard from "../components/cards/NewsArticleCard";
import TestimonialAuthor from "../components/testimonials/TestimonialAuthor";
import DocumentsDownloadLayout from "../components/documents/DocumentsDownloadLayout";
import { CheckCircle2, ArrowRight, ChevronDown, ChevronRight, CalendarDays, MapPin, Crown, Download as DownloadIcon, ArrowLeft, X, Instagram, ExternalLink } from "lucide-react";
import {
  DesignationsTableBlock, MembersGridBlock, NewsGridBlock, EventsCalendarBlock,
  ContactSectionBlock, OrganigrammaBlock, MemberProfileBlock, PortalLoginBlock,
} from "./DynamicPageBlocks";
import { parseInstagramPostEmbed, instagramPostEmbedSrc } from "../lib/instagram-embed";
import PageBrandBar from "../components/PageBrandBar";

/** Link CTA: route interne, anchor (#form) e scroll con offset header fisso. */
function CtaLink({ href = "/", variant = "primary", className, children, ...rest }) {
  const target = href || "/";

  if (target.startsWith("#")) {
    const id = target.slice(1);
    return (
      <Button
        href={target}
        variant={variant}
        className={className}
        onClick={(e) => {
          e.preventDefault();
          document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
        }}
        {...rest}
      >
        {children}
      </Button>
    );
  }

  if (target.includes("#")) {
    const [path, hash] = target.split("#");
    return (
      <Button
        to={path || "."}
        variant={variant}
        className={className}
        onClick={() => {
          requestAnimationFrame(() => {
            document.getElementById(hash)?.scrollIntoView({ behavior: "smooth", block: "start" });
          });
        }}
        {...rest}
      >
        {children}
      </Button>
    );
  }

  return (
    <Button to={target} variant={variant} className={className} {...rest}>
      {children}
    </Button>
  );
}

/* ============ HERO ============ */
export function HeroBlock({ config: c, stats }) {
  const overlayClass = c.overlay === "dark" ? "bg-black/70" : c.overlay === "light" ? "bg-white/40" : "hero-overlay";
  const heightCls =
    c.height === "tall"
      ? "min-h-[100svh] min-[1140px]:min-h-[90vh]"
      : c.height === "medium"
        ? "min-h-[70vh] min-[1140px]:min-h-[60vh]"
        : "min-h-[50vh] min-[1140px]:min-h-[40vh]";
  return (
    <section className={`relative ${heightCls} flex items-stretch min-[1140px]:items-center`} data-testid="hero-block">
      {c.backgroundImage && (
        <div className="absolute inset-0 z-0 overflow-hidden">
          <img src={c.backgroundImage} alt="" className="w-full h-full object-cover" />
          <div className={`absolute inset-0 ${overlayClass}`} />
        </div>
      )}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-10 min-[1140px]:py-20 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-stretch min-[1140px]:items-center w-full text-white min-h-full">
        <div
          className={`${c.showStats ? "lg:col-span-7" : "lg:col-span-12"} flex flex-col min-h-0 max-lg:flex-1 max-lg:justify-between max-lg:py-2`}
        >
          {/* Stessi due loghi + hamburger delle altre pagine (solo mobile; desktop = SiteHeader). */}
          <div data-testid="hero-brand-stack">
            <PageBrandBar className="mb-5" tone="onDark" />
          </div>

          <div className="max-lg:flex-1 max-lg:flex max-lg:flex-col max-lg:justify-center max-lg:py-4">
            {c.eyebrow && (
              <Eyebrow className="mb-2 min-[1140px]:mb-1.5 text-sm sm:text-base lg:text-lg tracking-[0.14em] sm:tracking-[0.16em] font-semibold text-white/90">
                {c.eyebrow}
              </Eyebrow>
            )}
            <HeroTitle className="text-white font-extrabold mb-7 sm:mb-6 min-[1140px]:mb-5 whitespace-pre-line max-lg:!text-[2.85rem] max-lg:leading-[1.08] sm:max-lg:!text-[3.35rem]">
              {c.title}
            </HeroTitle>
            {c.subtitle && (
              <p className="text-base sm:text-xl text-slate-200 max-w-2xl leading-relaxed mb-8 sm:mb-10">
                {c.subtitle}
              </p>
            )}
            <div className="flex flex-wrap items-center gap-4 max-lg:mt-2">
              {c.primaryCta?.label && (
                <CtaLink
                  href={c.primaryCta.href || "/"}
                  variant="secondary"
                  className="group max-lg:min-h-[52px] max-lg:px-6 max-lg:text-base"
                  data-testid="hero-cta-primary"
                >
                  {c.primaryCta.label}{" "}
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </CtaLink>
              )}
              {c.secondaryCta?.label && (
                <CtaLink
                  href={c.secondaryCta.href || "/"}
                  className="inline-flex items-center gap-2 text-white border-b-2 border-white/40 hover:border-gold-400 pb-1 font-medium transition-colors"
                >
                  {c.secondaryCta.label} <ChevronRight className="h-4 w-4" />
                </CtaLink>
              )}
            </div>
          </div>
        </div>

        {c.showStats && stats && (
          <div className="lg:col-span-5 w-full max-w-md lg:max-w-none max-lg:mt-2">
            <div
              className="bg-navy-50 rounded-xl shadow-2xl p-5 sm:p-6 border-t-4 border-gold-400 text-slate-900"
              data-testid="hero-stats-widget"
            >
              <Eyebrow className="mb-1 tracking-[0.22em]">La nostra sezione</Eyebrow>
              <SubsectionTitle as="div" className="mb-4 text-xl sm:text-2xl">In numeri</SubsectionTitle>
              <div className="grid grid-cols-2 gap-x-4 gap-y-5">
                <Stat icon="Users" value={stats.members} label="Associati" />
                <Stat icon="Trophy" value={stats.yearsActive} label="Anni di attività" />
                <Stat icon="Whistle" value={stats.matchesThisSeason ?? 0} label="Partite stagione" />
                <Stat icon="CalendarDays" value={stats.eventsUpcoming} label="Prossimi eventi" />
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function Stat({ icon, value, label }) {
  const I = Icons[icon] || Icons.Trophy;
  return (
    <div className="min-h-[5rem] flex flex-col bg-transparent">
      <I className="h-4 w-4 text-navy-600 mb-2 shrink-0" aria-hidden />
      <div className="font-display text-2xl sm:text-3xl font-bold text-navy-700 leading-none tabular-nums">
        {value}
      </div>
      <div className="text-[11px] sm:text-xs font-medium uppercase tracking-wide text-slate-600 mt-1.5 leading-snug">
        {label}
      </div>
    </div>
  );
}

/* ============ RICH TEXT ============ */
export function RichTextBlock({ config: c }) {
  const bg = c.background === "slate" ? "bg-background bg-pattern-stadio" : c.background === "navy" ? "bg-navy-700 text-white" : "bg-background";
  const widthCls = c.maxWidth === "wide" ? "max-w-6xl" : c.maxWidth === "medium" ? "max-w-4xl" : "max-w-3xl";
  return (
    <section className={`site-section ${bg}`} data-testid="richtext-block">
      <div className={`${widthCls} mx-auto px-4 sm:px-6 lg:px-8`}>
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && (
          <SectionTitle className="mb-3">{c.title}</SectionTitle>
        )}
        {c.title && <span className="gold-divider mb-8 block" />}
        <div className="prose-aia" dangerouslySetInnerHTML={{ __html: c.html || "" }} />
      </div>
    </section>
  );
}

const TEXT_IMAGE_ASPECT = {
  "16:9": "aspect-[16/9]",
  "4:3": "aspect-[4/3]",
  "3:4": "aspect-[3/4]",
  "4:5": "aspect-[4/5]",
  "1:1": "aspect-square",
  "9:16": "aspect-[9/16]",
};

const TEXT_IMAGE_PORTRAIT_MAX_W = {
  "3:4": "max-w-[300px]",
  "4:5": "max-w-[300px]",
  "9:16": "max-w-[280px]",
};

function TextImagePhoto({ config: c, aspectCls, portraitMaxW, wrapClassName = "" }) {
  if (!c.imageUrl) return null;
  const wrapCls = wrapClassName || (portraitMaxW ? `${portraitMaxW} mx-auto md:mx-0` : "");
  return (
    <div className={`relative w-full ${wrapCls}`}>
      <img src={c.imageUrl} alt={c.title || ""} className={`rounded-lg shadow-xl w-full ${aspectCls} object-cover`} />
      {c.badgeLabel && (
        <div className="absolute -bottom-6 -left-6 bg-gold-400 text-navy-900 p-5 rounded-lg shadow-lg max-w-[200px]">
          <SectionTitle as="div" className="text-navy-900">{c.badgeLabel}</SectionTitle>
          {c.badgeText && <Eyebrow as="div" className="tracking-wider mt-1 text-navy-900">{c.badgeText}</Eyebrow>}
        </div>
      )}
    </div>
  );
}

function RequirementsPanel({ title, items, fullWidth = false }) {
  if (!items?.length) return null;
  return (
    <div
      className="mt-8 md:mt-10 rounded-lg bg-white border border-slate-200/80 shadow-ds-md border-t-4 border-t-gold-400 p-6 sm:p-8"
      data-testid="requirements-panel"
    >
      {title && <SubsectionTitle className="mb-5 text-navy-700">{title}</SubsectionTitle>}
      <ul className={`grid gap-x-6 gap-y-4 ${fullWidth ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-4" : "grid-cols-1 sm:grid-cols-2"}`}>
        {items.map((item, i) => {
          const Icon = Icons[item.icon] || CheckCircle2;
          return (
            <li key={i} className="flex gap-3.5 items-start">
              <span className="flex-shrink-0 w-10 h-10 rounded-full bg-navy-50 text-navy-600 ring-1 ring-navy-100 flex items-center justify-center">
                <Icon className="h-[18px] w-[18px]" strokeWidth={2.25} />
              </span>
              <span className="text-sm sm:text-[0.9375rem] text-slate-700 leading-relaxed pt-2">{item.text}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

/* ============ TEXT + IMAGE ============ */
export function TextImageBlock({ config: c }) {
  const left = c.imagePosition === "left";
  const bg = c.background === "slate" ? "bg-background bg-pattern-stadio" : "bg-background";
  const slotAspect = c.imageAspect || "3:4";
  const aspectCls = TEXT_IMAGE_ASPECT[slotAspect] || TEXT_IMAGE_ASPECT["3:4"];
  const portraitMaxW = TEXT_IMAGE_PORTRAIT_MAX_W[slotAspect] || "";
  const hasRequirements = (c.requirements?.length ?? 0) > 0;

  if (hasRequirements) {
    return (
      <section className={`site-section ${bg}`} data-testid="textimage-block">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 md:gap-12 items-start">
            <div className={`md:col-span-7 ${left && c.imageUrl ? "md:order-2" : ""}`}>
              {c.title && (
                <SectionTitle className="leading-tight whitespace-pre-line">{c.title}</SectionTitle>
              )}
              <span className="gold-divider my-6 block" />
              <div className="prose-aia" dangerouslySetInnerHTML={{ __html: c.html || "" }} />
              {c.ctaLabel && c.ctaHref && (
                <div className="mt-6"><CtaLink href={c.ctaHref} variant="primary">{c.ctaLabel} <ArrowRight className="h-4 w-4"/></CtaLink></div>
              )}
            </div>
            {c.imageUrl && (
              <div className={`md:col-span-5 ${left ? "md:order-1" : ""} ${c.badgeLabel ? "pb-8" : ""}`}>
                <TextImagePhoto
                  config={c}
                  aspectCls={aspectCls}
                  wrapClassName={`${portraitMaxW || "max-w-[300px]"} mx-auto md:max-w-none md:ml-auto`}
                />
              </div>
            )}
          </div>
          <RequirementsPanel title={c.requirementsTitle} items={c.requirements} fullWidth />
        </div>
      </section>
    );
  }

  return (
    <section className={`site-section ${bg}`} data-testid="textimage-block">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 md:grid-cols-12 gap-12 items-center">
        <div className={`md:col-span-7 ${left ? "md:order-2" : ""}`}>
          {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
          {c.title && (
            <SectionTitle className="leading-tight mb-6 whitespace-pre-line">{c.title}</SectionTitle>
          )}
          <span className="gold-divider mb-6 block" />
          <div className="prose-aia" dangerouslySetInnerHTML={{ __html: c.html || "" }} />
          {c.ctaLabel && c.ctaHref && (
            <div className="mt-6"><CtaLink href={c.ctaHref} variant="primary">{c.ctaLabel} <ArrowRight className="h-4 w-4"/></CtaLink></div>
          )}
        </div>
        {c.imageUrl && (
          <div className={`md:col-span-5 ${left ? "md:order-1" : ""} ${c.badgeLabel ? "pb-8" : ""}`}>
            <TextImagePhoto config={c} aspectCls={aspectCls} portraitMaxW={portraitMaxW} />
          </div>
        )}
      </div>
    </section>
  );
}

/* ============ CTA Banner ============ */
export function CTABlock({ config: c }) {
  const styles = {
    navy: "bg-navy-700 text-white",
    gold: "bg-gold-400 text-navy-900",
    white: "bg-background text-navy-700 border-y border-slate-200",
  };
  return (
    <section id={c.anchor || undefined} className={`relative site-section overflow-hidden scroll-mt-4 min-[1140px]:scroll-mt-20 ${styles[c.style] || styles.navy}`} data-testid="cta-block">
      {c.backgroundImage && c.style !== "white" && (
        <div className="absolute inset-0 z-0 opacity-25">
          <img src={c.backgroundImage} alt="" className="w-full h-full object-cover"/>
        </div>
      )}
      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {c.eyebrow && (
          <div className={`inline-block px-4 py-1.5 rounded-full mb-6 ${c.style === "white" ? "bg-navy-50" : "bg-white/15"}`}>
            <Eyebrow className={`tracking-[0.22em] ${c.style === "white" ? "text-navy-700" : c.style === "gold" ? "text-navy-900" : "text-gold-300"}`}>{c.eyebrow}</Eyebrow>
          </div>
        )}
        <CtaTitle className={`mb-6 whitespace-pre-line ${c.style === "white" ? "text-navy-700" : c.style === "gold" ? "text-navy-900" : "text-white"}`}>{c.title}</CtaTitle>
        {c.description && <p className="text-lg sm:text-xl opacity-90 max-w-3xl mx-auto leading-relaxed mb-10">{c.description}</p>}
        {c.formType === "corso-arbitri" ? (
          <CorsoArbitriForm />
        ) : (
          <div className="flex flex-wrap items-center justify-center gap-4">
            {c.primaryCta?.label && <CtaLink href={c.primaryCta.href || "/"} variant={c.style === "white" ? "primary" : "secondary"}>{c.primaryCta.label} <ArrowRight className="h-5 w-5"/></CtaLink>}
            {c.secondaryCta?.label && <CtaLink href={c.secondaryCta.href || "/"} className={`underline font-medium ${c.style === "white" ? "text-navy-600" : "text-white"}`}>{c.secondaryCta.label}</CtaLink>}
          </div>
        )}
      </div>
    </section>
  );
}

function CorsoArbitriForm() {
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ firstName: "", lastName: "", age: "", phone: "", email: "", contactPreference: "email", message: "" });
  const onChange = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await submitLead({ ...form, age: form.age ? Number(form.age) : null });
      setSubmitted(true);
    } catch (err) {
      setError(err?.response?.data?.detail || "Errore invio. Riprova.");
    } finally {
      setSubmitting(false);
    }
  };
  if (submitted) {
    return (
      <Card variant="accent" shadow="md" className="text-navy-700 p-8 sm:p-10 max-w-2xl mx-auto shadow-2xl" data-testid="lead-success">
        <CheckCircle2 className="h-16 w-16 text-gold-400 mx-auto mb-5" />
        <SubsectionTitle as="h3" className="mb-3">Grazie {form.firstName}!</SubsectionTitle>
        <p className="text-slate-600">
          Un referente della sezione ti contatterà a breve tramite{" "}
          {contactPreferenceLabel(form.contactPreference, { lowercase: true })}.
        </p>
      </Card>
    );
  }
  const I = "w-full px-4 py-2.5 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-slate-900 transition";
  return (
    <Card as="form" onSubmit={submit} variant="accent" shadow="md" className="text-slate-900 p-6 sm:p-8 max-w-2xl mx-auto shadow-2xl text-left" data-testid="lead-form">
      {error && <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded mb-5 text-sm">{error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <FormField label="Nome*"><input data-testid="lead-firstName" required value={form.firstName} onChange={onChange("firstName")} className={I}/></FormField>
        <FormField label="Cognome*"><input data-testid="lead-lastName" required value={form.lastName} onChange={onChange("lastName")} className={I}/></FormField>
        <FormField label="Età"><input data-testid="lead-age" type="number" min="14" max="99" value={form.age} onChange={onChange("age")} className={I}/></FormField>
        <FormField label="Telefono"><input data-testid="lead-phone" type="tel" value={form.phone} onChange={onChange("phone")} className={I}/></FormField>
        <FormField label="Email*"><input data-testid="lead-email" required type="email" value={form.email} onChange={onChange("email")} className={I}/></FormField>
        <FormField label="Preferenza contatto"><select data-testid="lead-contactPreference" value={form.contactPreference} onChange={onChange("contactPreference")} className={I}><option value="email">Email</option><option value="phone">Telefono</option></select></FormField>
      </div>
      <FormField label="Messaggio (opzionale)"><textarea data-testid="lead-message" rows={3} value={form.message} onChange={onChange("message")} className={I}/></FormField>
      <Button type="submit" disabled={submitting} variant="primary" className="mt-4 w-full justify-center" data-testid="lead-submit">
        {submitting ? "Invio in corso…" : "Invia la candidatura"}
      </Button>
      <p className="text-xs text-slate-500 mt-3 text-center">I dati sono trattati esclusivamente per le finalità del corso arbitri.</p>
    </Card>
  );
}
function FormField({ label, children }) {
  return <label className="block text-left"><span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>{children}</label>;
}

/* ============ FAQ ============ */
export function FAQBlock({ config: c }) {
  const bg = c.background === "slate" ? "bg-background bg-pattern-stadio" : "bg-background";
  return (
    <section className={`site-section ${bg}`} data-testid="faq-block">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {(c.eyebrow || c.title) && (
          <div className="text-center mb-10">
            {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
            {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
            <span className="gold-divider block mx-auto" />
          </div>
        )}
        <div className="space-y-3">
          {(c.items || []).map((it, i) => <FAQItem key={i} {...it} />)}
        </div>
      </div>
    </section>
  );
}
function FAQItem({ question, answer }) {
  const [open, setOpen] = useState(false);
  return (
    <Card padding="none" className="overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full p-ds-card text-left flex items-start justify-between gap-4 hover:bg-slate-50 transition-colors">
        <CardTitle as="span" className="text-lg">{question}</CardTitle>
        <ChevronDown className={`h-5 w-5 text-navy-600 transition-transform flex-shrink-0 ${open ? "rotate-180" : ""}`} />
      </button>
      {open && <div className="px-ds-card pb-ds-card prose-aia" dangerouslySetInnerHTML={{ __html: answer }} />}
    </Card>
  );
}

/* ============ TIMELINE ============ */
export function TimelineBlock({ config: c }) {
  return (
    <section className="site-section bg-background" data-testid="timeline-block">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
          <SectionTitle className="mb-3">{c.title}</SectionTitle>
          <span className="gold-divider block mx-auto" />
        </div>
        <ol className="space-y-6">
          {(c.items || []).map((t, idx, all) => (
            <li key={idx} className="flex gap-ds-grid items-start">
              <div className="flex-shrink-0 w-16 h-16 rounded-full bg-navy-600 text-white flex items-center justify-center font-display text-xl font-bold">{t.step}</div>
              <div className={`flex-1 pb-6 ${idx === all.length - 1 ? "" : "border-b border-slate-200"}`}>
                <CardTitle as="h3" className="mb-1">{t.title}</CardTitle>
                <p className="text-slate-600 leading-relaxed">{t.text}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

/* ============ STATS ============ */
export function StatsBlock({ config: c }) {
  const bg = c.background === "slate" ? "bg-background bg-pattern-stadio" : c.background === "navy" ? "bg-navy-700 text-white" : "bg-background";
  return (
    <section className={`site-section ${bg}`} data-testid="stats-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-14">
          {c.eyebrow && <Eyebrow as="div" className={`tracking-[0.25em] mb-3 ${c.background === "navy" ? "text-gold-400" : ""}`}>{c.eyebrow}</Eyebrow>}
          {c.title && <SectionTitle className={`mb-3 ${c.background === "navy" ? "text-white" : ""}`}>{c.title}</SectionTitle>}
          <span className="gold-divider block mx-auto" />
        </div>
        <div className={`grid grid-cols-1 sm:grid-cols-2 ${(c.items?.length || 0) > 4 ? "lg:grid-cols-3" : "lg:grid-cols-4"} gap-ds-grid`}>
          {(c.items || []).map((it, i) => {
            const iconName = it.icon === "Whistle" ? "Megaphone" : it.icon;
            const I = Icons[iconName] || Icons.Trophy;
            const isNavy = c.background === "navy";
            return isNavy ? (
              <div key={i} className="p-7 rounded-lg border bg-white/10 border-white/20">
                <div className="w-12 h-12 rounded-md flex items-center justify-center mb-4 bg-gold-400 text-navy-900">
                  <I className="h-6 w-6" />
                </div>
                {it.value && <HeroTitle as="div" className="text-gold-400 text-4xl leading-none mb-2">{it.value}</HeroTitle>}
                <CardTitle as="h3" className="text-white">{it.label}</CardTitle>
                {it.desc && <p className="text-sm mt-2 text-slate-200">{it.desc}</p>}
              </div>
            ) : (
              <Card key={i} interactive padding="none" className="p-7">
                <div className="w-12 h-12 rounded-md flex items-center justify-center mb-4 bg-navy-50 text-navy-600">
                  <I className="h-6 w-6" />
                </div>
                {it.value && <HeroTitle as="div" className="text-4xl leading-none mb-2">{it.value}</HeroTitle>}
                <CardTitle as="h3">{it.label}</CardTitle>
                {it.desc && <p className="text-sm mt-2 text-slate-600">{it.desc}</p>}
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ============ GALLERY ============ */
export function GalleryBlock({ config: c }) {
  const [lightbox, setLightbox] = useState(null);
  const cols = c.columns === 2 ? "md:grid-cols-2" : c.columns === 4 ? "md:grid-cols-2 lg:grid-cols-4" : "md:grid-cols-2 lg:grid-cols-3";
  return (
    <section className="site-section bg-background" data-testid="gallery-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {(c.eyebrow || c.title) && (
          <div className="mb-10">
            {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
            {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
            <span className="gold-divider block" />
          </div>
        )}
        <div className={`grid grid-cols-1 ${cols} gap-4`}>
          {(c.images || []).map((img, i) => (
            <Card key={i} as="button" type="button" onClick={() => setLightbox(img)} interactive padding="none" className="aspect-[4/3] overflow-hidden bg-slate-100">
              <img src={img.url} alt={img.caption || ""} className="w-full h-full object-cover" loading="lazy"/>
            </Card>
          ))}
        </div>
      </div>
      {lightbox && (
        <div onClick={() => setLightbox(null)} className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4 cursor-zoom-out">
          <button onClick={() => setLightbox(null)} className="absolute top-4 right-4 text-white p-2"><X className="h-6 w-6"/></button>
          <img src={lightbox.url} alt="" className="max-w-full max-h-full rounded"/>
          {lightbox.caption && <div className="absolute bottom-6 text-white">{lightbox.caption}</div>}
        </div>
      )}
    </section>
  );
}

/* ============ NEWS SLIDER ============ */
export function NewsSliderBlock({ config: c }) {
  const [items, setItems] = useState([]);
  useEffect(() => { fetchArticles({ limit: c.limit || 3, category: c.category || undefined }).then(d => setItems(d.items || [])); }, [c.limit, c.category]);
  return (
    <section className="site-section bg-background" data-testid="news-slider-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-10 md:mb-12">
          {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
          {c.title && <CtaTitle className="leading-tight">{c.title}</CtaTitle>}
          <span className="gold-divider mt-4 block" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {items.map((a) => (
            <NewsArticleCard key={a.slug} article={a} showReadMore={false} />
          ))}
        </div>
        {c.ctaLabel && (
          <div className="mt-10 flex justify-center md:justify-start">
            <Button to={c.ctaHref || "/news"} variant="outline" size="sm" data-testid="news-slider-cta">
              {c.ctaLabel} <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </section>
  );
}

function parseInstagramHandle(url) {
  if (!url || typeof url !== "string") return null;
  const trimmed = url.trim();
  if (trimmed.startsWith("@")) return trimmed.slice(1).split("/")[0] || null;
  const m = trimmed.match(/instagram\.com\/([^/?#]+)/i);
  return m ? m[1].replace(/^@/, "") : null;
}

function eventsListShowSidebar(c) {
  // Instagram e card presidente sono indipendenti: non nascondere IG se il presidente è off.
  const showIg = c.showInstagramWidget !== false;
  const showPres = c.showPresidentCard === true;
  return showIg || showPres;
}

function InstagramProfileWidget({ profileUrl, handle, title, subtitle, className = "" }) {
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
            <CardTitle as="h3" className="leading-tight truncate text-white">{title || "AIA Legnano"}</CardTitle>
            {displayHandle && <p className="text-sm text-white/90 truncate">{displayHandle}</p>}
          </div>
        </div>
        {subtitle && <p className="text-sm text-white/90 mt-3 leading-relaxed">{subtitle}</p>}
      </div>
      {embedSrc ? (
        <div className="bg-slate-50 border-t border-slate-100 flex-1 min-h-[280px] flex flex-col">
          <iframe
            title="Profilo Instagram AIA Legnano"
            src={embedSrc}
            className="w-full flex-1 border-0 min-h-[280px]"
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

/* ============ EVENTS LIST ============ */
export function EventsListBlock({ config: c }) {
  const { settings } = useSite();
  const [events, setEvents] = useState([]);
  const showSidebar = eventsListShowSidebar(c);
  const profileUrl = (c.instagramUrl || settings?.instagramUrl || "").trim();
  const handle = parseInstagramHandle(profileUrl);

  const eventLimit = c.limit ?? 3;

  useEffect(() => {
    fetchEvents({ upcoming: c.upcomingOnly !== false, limit: eventLimit }).then(setEvents);
  }, [c.upcomingOnly, eventLimit]);

  return (
    <section className="site-section bg-background bg-pattern-stadio" data-testid="events-list-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-stretch">
        <div className={`${showSidebar ? "lg:col-span-7" : "lg:col-span-12"} flex flex-col h-full`}>
          {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
          {c.title && <SectionTitle className="mb-2">{c.title}</SectionTitle>}
          <span className="gold-divider mb-8 block" />
          <div className="space-y-3 flex-1">
            {events.map((e) => <EventCard key={e.id} e={e} />)}
            {events.length === 0 && <p className="text-slate-500">Nessun evento in programma.</p>}
          </div>
          {c.ctaLabel && (
            <div className="mt-8 pt-2">
              <Button to={c.ctaHref || "/eventi"} variant="outline" size="sm">
                {c.ctaLabel} <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
        {showSidebar && (
          <div className="lg:col-span-5 flex flex-col h-full min-h-0">
            <InstagramProfileWidget
              profileUrl={profileUrl}
              handle={handle}
              title={c.instagramTitle || settings?.siteName || "AIA Legnano"}
              subtitle={c.instagramSubtitle || "Foto, aggiornamenti e vita della sezione su Instagram."}
            />
          </div>
        )}
      </div>
    </section>
  );
}
const EventCard = memo(function EventCard({ e }) {
  const d = new Date(e.date);
  const months = ["GEN","FEB","MAR","APR","MAG","GIU","LUG","AGO","SET","OTT","NOV","DIC"];
  return (
    <Card interactive padding="default" className="flex flex-col sm:flex-row gap-4 sm:gap-5 items-start p-4 sm:p-5">
      <div className="flex flex-col items-center justify-center bg-navy-600 text-white rounded-md w-16 h-16 flex-shrink-0">
        <div className="text-2xl font-bold leading-none">{d.getDate().toString().padStart(2, "0")}</div>
        <Eyebrow as="div" className="text-[10px] tracking-wider mt-1 text-gold-400">{months[d.getMonth()]}</Eyebrow>
      </div>
      <div className="flex-1">
        <Eyebrow as="div" className="inline-block tracking-wider text-gold-400 mb-1.5">{e.tipo}</Eyebrow>
        <CardTitle as="h3" className="text-lg">{e.titolo}</CardTitle>
        <p className="text-slate-600 text-sm mt-1.5 line-clamp-2">{e.descrizione}</p>
        {e.luogo && <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-2"><MapPin className="h-3.5 w-3.5"/> {e.luogo}</div>}
        <AttachmentList attachments={e.attachments} className="mt-2" />
      </div>
    </Card>
  );
});

/* ============ TESTIMONIALS ============ */
export function TestimonialsBlock({ config: c }) {
  const [items, setItems] = useState(c.items || []);
  useEffect(() => {
    if (c.useGlobal) fetchTestimonials().then(setItems);
  }, [c.useGlobal]);
  return (
    <section className="site-section bg-background" data-testid="testimonials-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
          {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
          <span className="gold-divider block mx-auto" />
        </div>
        <div className={`grid grid-cols-1 ${items.length >= 3 ? "md:grid-cols-3" : "md:grid-cols-2"} gap-ds-grid`}>
          {items.map((t, i) => (
            <Card key={t.id || i} padding="none" className="p-7">
              <Icons.Quote className="h-8 w-8 text-gold-400 mb-4"/>
              <p className="text-slate-600 leading-relaxed mb-6 italic">{t.quote}</p>
              <TestimonialAuthor testimonial={t} />
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ============ DOWNLOADS ============ */
export function DownloadsBlock({ config: c }) {
  const [items, setItems] = useState(c.items || []);
  const [sections, setSections] = useState([]);
  useEffect(() => {
    if (c.useGlobal) {
      fetchDocuments(c.category ? { category: c.category } : {}).then(setItems);
      fetchDocumentSections().then(setSections).catch(() => setSections([]));
    }
  }, [c.useGlobal, c.category]);

  return (
    <section className="site-section bg-background bg-pattern-stadio" data-testid="downloads-block">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {(c.eyebrow || c.title) && (
          <div className="mb-10">
            {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
            {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
            <span className="gold-divider block" />
          </div>
        )}
        <DocumentsDownloadLayout documents={items} sectionOrder={sections} />
      </div>
    </section>
  );
}

/* ============ EMBED ============ */
export function EmbedBlock({ config: c }) {
  const widthCls = c.maxWidth === "narrow" ? "max-w-3xl" : c.maxWidth === "medium" ? "max-w-4xl" : "max-w-6xl";
  const html = c.html || "";
  const instagramPost = parseInstagramPostEmbed(html);

  return (
    <section className="site-section bg-background" data-testid="embed-block">
      <div className={`${widthCls} mx-auto px-4 sm:px-6 lg:px-8`}>
        {(c.eyebrow || c.title) && (
          <div className="mb-8">
            {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
            {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
            <span className="gold-divider block" />
          </div>
        )}
        <div className="rounded-lg overflow-hidden bg-slate-100">
          {instagramPost ? (
            <iframe
              title="Post Instagram"
              src={instagramPostEmbedSrc(instagramPost)}
              className="w-full border-0 min-h-[700px] max-w-[540px] mx-auto block bg-white"
              scrolling="no"
              loading="lazy"
              allowTransparency
            />
          ) : (
            <div dangerouslySetInnerHTML={{ __html: html }} />
          )}
        </div>
      </div>
    </section>
  );
}

/* ============ SPACER ============ */
export function SpacerBlock({ config: c }) {
  const sizes = { sm: "h-8", md: "h-16", lg: "h-24", xl: "h-32" };
  return <div className={sizes[c.height] || sizes.md} data-testid="spacer-block" />;
}

/* ============ DISPATCHER ============ */
const RENDERERS = {
  hero: HeroBlock, rich_text: RichTextBlock, text_image: TextImageBlock,
  cta: CTABlock, faq: FAQBlock, timeline: TimelineBlock, stats: StatsBlock,
  gallery: GalleryBlock, news_slider: NewsSliderBlock, events_list: EventsListBlock,
  testimonials: TestimonialsBlock, downloads: DownloadsBlock, embed: EmbedBlock, spacer: SpacerBlock,
  designations_table: DesignationsTableBlock, members_grid: MembersGridBlock, news_grid: NewsGridBlock,
  events_calendar: EventsCalendarBlock, contact_section: ContactSectionBlock,
  organigramma: OrganigrammaBlock, member_profile: MemberProfileBlock, portal_login: PortalLoginBlock,
};

export default function BlockRenderer({ block, context }) {
  if (!block || !block.enabled) return null;
  const Cmp = RENDERERS[block.type];
  if (!Cmp) return null;
  return <Cmp config={block.config} stats={context?.stats} memberSlug={context?.memberSlug} {...context} />;
}

export function BlocksRenderer({ blocks, context }) {
  return (
    <>
      {(blocks || []).filter((b) => b.enabled).map((b) => <BlockRenderer key={b.id} block={b} context={context} />)}
    </>
  );
}
