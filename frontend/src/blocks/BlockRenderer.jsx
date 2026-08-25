/* Public renderers for all CMS block types. Each takes `config` and renders a section. */
import { memo, useEffect, useState } from "react";
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
import { formatDateIt, contactPreferenceLabel, formatEventDateTimeIt } from "../lib/format";
import { AttachmentList } from "../components/AttachmentList";
import NewsArticleCard from "../components/cards/NewsArticleCard";
import TestimonialAuthor from "../components/testimonials/TestimonialAuthor";
import DocumentsDownloadLayout from "../components/documents/DocumentsDownloadLayout";
import { CheckCircle2, ArrowRight, ChevronDown, ChevronRight, CalendarDays, MapPin, Crown, Download as DownloadIcon, ArrowLeft, X } from "lucide-react";
import {
  DesignationsTableBlock, MembersGridBlock, NewsGridBlock, EventsCalendarBlock,
  ContactSectionBlock, OrganigrammaBlock, MemberProfileBlock, PortalLoginBlock,
} from "./DynamicPageBlocks";
import InstagramSidebarWidget from "../components/InstagramSidebarWidget";
import PageBrandBar from "../components/PageBrandBar";
import { eventDateKey, isUpcomingEvent } from "../lib/eventsDisplay";
import EventDetailModal from "../components/events/EventDetailModal";
import EventsMonthCalendar from "../components/events/EventsMonthCalendar";
import { cn } from "../lib/utils";


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

        <FormField label="Preferenza contatto"><select data-testid="lead-contactPreference" value={form.contactPreference} onChange={onChange("contactPreference")} className={I}><option value="email">Email</option><option value="telefono">Telefono</option><option value="whatsapp">WhatsApp</option><option value="entrambi">Entrambi</option></select></FormField>
      </div>
      <Button type="submit" disabled={submitting} variant="primary" className="mt-2">{submitting ? "Invio…" : "Invia richiesta"}</Button>
    </Card>
  );
}

function FormField({ label, children }) {
  return (
    <label className="block">
      <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
      {children}
    </label>
  );
}

/* ============ FAQ ============ */
export function FAQBlock({ config: c }) {
  const bg = c.background === "slate" ? "bg-background bg-pattern-stadio" : "bg-background";
  const [open, setOpen] = useState(-1);
  return (
    <section className={`site-section ${bg}`} data-testid="faq-block">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
        {(c.title || c.eyebrow) && <span className="gold-divider my-6 block" />}
        <div className="space-y-4">
          {(c.items || []).map((it, i) => {
            const isOpen = open === i;
            return (
              <Card key={i} variant="outline" padding="none" className="overflow-hidden">
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? -1 : i)}
                  className="w-full px-5 sm:px-6 py-4 sm:py-5 flex items-center justify-between gap-4 text-left hover:bg-navy-50/40 transition"
                  aria-expanded={isOpen}
                >
                  <CardTitle as="div" className="text-base sm:text-lg">{it.question}</CardTitle>
                  <ChevronDown
                    className={`h-5 w-5 text-slate-500 shrink-0 transition-transform ${isOpen ? "rotate-180" : ""}`}
                    aria-hidden
                  />
                </button>
                {isOpen && (
                  <div className="px-5 sm:px-6 pb-5 sm:pb-6 pt-0 border-t border-slate-200">
                    <div className="prose-aia pt-4" dangerouslySetInnerHTML={{ __html: it.answer || "" }} />
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ============ TIMELINE / STEPS ============ */
export function TimelineBlock({ config: c }) {
  return (
    <section className="site-section bg-background" data-testid="timeline-block">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
        {(c.title || c.eyebrow) && <span className="gold-divider my-6 block" />}
        <ol className="relative border-l-2 border-navy-200 ml-3 sm:ml-6 space-y-10 sm:space-y-12 pl-6 sm:pl-10">
          {(c.items || []).map((it, i) => (
            <li key={i} className="relative">
              <span className="absolute -left-[41px] sm:-left-[55px] top-0 flex items-center justify-center w-11 h-11 sm:w-14 sm:h-14 rounded-full bg-gold-400 text-navy-900 font-bold shadow-md ring-4 ring-background text-sm sm:text-base">
                {it.step || String(i + 1).padStart(2, "0")}
              </span>
              <Card variant="soft" padding="default" className="shadow-ds-sm">
                <SubsectionTitle className="text-lg sm:text-xl mb-2">{it.title}</SubsectionTitle>
                <p className="text-slate-600 leading-relaxed">{it.text}</p>
              </Card>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

/* ============ STATS / NUMERI ============ */
export function StatsBlock({ config: c }) {
  const bg = c.background === "slate" ? "bg-background bg-pattern-stadio" : "bg-background";
  return (
    <section className={`site-section ${bg}`} data-testid="stats-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
        {(c.title || c.eyebrow) && <span className="gold-divider my-6 block" />}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {(c.items || []).map((it, i) => {
            const I = Icons[it.icon] || Icons.Trophy;
            return (
              <div key={i} className="text-center">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-navy-50 text-navy-600 ring-1 ring-navy-100 mb-4">
                  <I className="h-6 w-6" />
                </div>
                <div className="font-display text-4xl sm:text-5xl font-bold text-navy-700 mb-2 tabular-nums">{it.value}</div>
                <Eyebrow as="div" className="tracking-wider text-slate-500 font-semibold">{it.label}</Eyebrow>
                {it.desc && <p className="text-sm text-slate-500 mt-2 leading-relaxed">{it.desc}</p>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

/* ============ GALLERIA ============ */
export function GalleryBlock({ config: c }) {
  const cols = c.columns === 4 ? "grid-cols-2 md:grid-cols-4" : c.columns === 2 ? "grid-cols-2" : "grid-cols-2 md:grid-cols-3";
  const [lightbox, setLightbox] = useState(null);
  return (
    <section className="site-section bg-background" data-testid="gallery-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
        {(c.title || c.eyebrow) && <span className="gold-divider my-6 block" />}
        <div className={`grid ${cols} gap-ds-grid`}>
          {(c.images || []).map((img, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setLightbox({ idx: i })}
              className="group relative aspect-square overflow-hidden rounded-xl shadow-ds-sm hover:shadow-ds-lg focus:outline-none focus:ring-2 focus:ring-navy-600 focus:ring-offset-2 transition"
            >
              <img src={img.url || img.src} alt={img.alt || img.caption || ""} className="w-full h-full object-cover transition-transform group-hover:scale-105" />
              {img.caption && (
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/75 to-transparent p-3 sm:p-4 text-white text-xs sm:text-sm opacity-0 group-hover:opacity-100 transition">
                  {img.caption}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>
      {lightbox !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          role="dialog"
          onClick={() => setLightbox(null)}
        >
          <button
            type="button"
            className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white"
            onClick={() => setLightbox(null)}
            aria-label="Chiudi"
          >
            <X className="h-6 w-6" />
          </button>
          {(() => {
            const imgs = c.images || [];
            const img = imgs[lightbox.idx];
            if (!img) return null;
            return (
              <img
                src={img.url || img.src}
                alt={img.alt || img.caption || ""}
                className="max-h-[85vh] max-w-[95vw] rounded-lg shadow-2xl"
                onClick={(e) => e.stopPropagation()}
              />
            );
          })()}
        </div>
      )}
    </section>
  );
}

/* ============ NEWS SLIDER / ULTIME NEWS IN HOME ============ */
export function NewsSliderBlock({ config: c }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchArticles({ limit: c.limit || 3, category: c.category || undefined })
      .then((d) => { setItems(Array.isArray(d) ? d : (d.items || [])); })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [c.limit, c.category]);

  return (
    <section className="site-section bg-background bg-pattern-stadio" data-testid="news-slider-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
        {(c.title || c.eyebrow) && <span className="gold-divider mt-6 block" />}

        {loading ? (
          <p className="text-slate-500 mt-10">Caricamento…</p>
        ) : items.length === 0 ? (
          <p className="text-slate-500 mt-10">Nessuna news disponibile al momento.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-10">
            {items.map((a) => (
              <NewsArticleCard key={a.slug} article={a} />
            ))}
          </div>
        )}

        {c.ctaLabel && c.ctaHref && (
          <div className="mt-10 flex justify-start">
            <CtaLink href={c.ctaHref} variant="primary">{c.ctaLabel} <ArrowRight className="h-4 w-4"/></CtaLink>
          </div>
        )}
      </div>
    </section>
  );
}

/* ============ EVENTS LIST / PROSSIMI EVENTI IN HOME ============ */
const EV_MONTHS = ["GEN", "FEB", "MAR", "APR", "MAG", "GIU", "LUG", "AGO", "SET", "OTT", "NOV", "DIC"];

function HomeEventCard({ e, onClick }) {
  const d = new Date(e.date);
  return (
    <Card
      as="button"
      type="button"
      interactive
      padding="default"
      className="w-full text-left flex flex-col sm:flex-row gap-4 sm:gap-5 items-start p-4 sm:p-5"
      onClick={onClick}
    >
      <div className="flex flex-col items-center justify-center bg-navy-600 text-white rounded-md w-16 h-16 flex-shrink-0">
        <div className="text-2xl font-bold leading-none">{d.getDate().toString().padStart(2, "0")}</div>
        <Eyebrow as="div" className="text-[10px] tracking-wider mt-1 text-gold-400">
          {EV_MONTHS[d.getMonth()]}
        </Eyebrow>
      </div>
      <div className="flex-1 min-w-0">
        {e.tipo && (
          <Eyebrow as="div" className="inline-block tracking-wider text-gold-400 mb-1.5">
            {e.tipo}
          </Eyebrow>
        )}
        <CardTitle as="h3" className="text-lg">{e.titolo}</CardTitle>
        {e.descrizione && <p className="text-slate-600 text-sm mt-1.5 line-clamp-2">{e.descrizione}</p>}
        {e.luogo && (
          <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-2">
            <MapPin className="h-3.5 w-3.5" /> {e.luogo}
          </div>
        )}
        {!e.tipo && (
          <Eyebrow as="div" className="text-gold-600 mt-2">{formatEventDateTimeIt(e.date, e.orario, e.orarioFine)}</Eyebrow>
        )}
      </div>
    </Card>
  );
}

export function EventsListBlock({ config: c }) {
  const [allEvents, setAllEvents] = useState([]);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [modalEvent, setModalEvent] = useState(null);
  const [viewMonth, setViewMonth] = useState(() => {
    const n = new Date();
    return new Date(n.getFullYear(), n.getMonth(), 1);
  });
  const { settings } = useSite();
  const instaUrl = (settings || {}).instagramUrl || "";
  const showCalendar = c.showCalendar === true;
  const showInstagram = c.showInstagramWidget !== false;
  const eventLimit = c.limit || 3;

  useEffect(() => {
    setLoading(true);
    fetchEvents({ limit: c.limit ? Math.max(Number(c.limit) * 4, 200) : 200 })
      .then((d) => {
        let list = Array.isArray(d) ? d : (d.items || []);
        if (c.upcomingOnly !== false) {
          const now = new Date();
          list = list.filter((e) => isUpcomingEvent(e, { now }));
        }
        list.sort((a, b) => eventDateKey(a.date).localeCompare(eventDateKey(b.date)));
        setAllEvents(list);
        setItems(list.slice(0, eventLimit));
      })
      .catch(() => {
        setAllEvents([]);
        setItems([]);
      })
      .finally(() => setLoading(false));
  }, [c.limit, c.upcomingOnly, eventLimit]);

  const shiftViewMonth = (delta) => {
    setViewMonth((prev) => {
      const base = prev instanceof Date ? prev : new Date();
      return new Date(base.getFullYear(), base.getMonth() + delta, 1);
    });
  };

  const handleSelectEvent = (event) => {
    setSelectedId(event.id);
    setModalEvent(event);
    const [y, m] = eventDateKey(event.date).split("-");
    setViewMonth(new Date(Number(y), Number(m) - 1, 1));
  };

  return (
    <section className="site-section bg-background" data-testid="events-list-block">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
        {(c.title || c.eyebrow) && <span className="gold-divider mt-6 block" />}

        <div
          className={cn(
            "grid grid-cols-1 gap-8 lg:gap-10 mt-10 lg:items-start",
            showCalendar && showInstagram && "lg:grid-cols-12",
            showCalendar && !showInstagram && "lg:grid-cols-2",
            !showCalendar && showInstagram && "lg:grid-cols-12"
          )}
        >
          <div
            className={cn(
              showInstagram && !showCalendar && "lg:col-span-8",
              showCalendar && !showInstagram && "min-w-0",
              showCalendar && showInstagram && "lg:col-span-5"
            )}
          >
            {loading ? (
              <p className="text-slate-500">Caricamento…</p>
            ) : items.length === 0 ? (
              <p className="text-slate-500">Nessun evento in programma.</p>
            ) : (
              <ul className="space-y-3">
                {items.map((e) => (
                  <li key={e.id}>
                    <HomeEventCard e={e} onClick={() => handleSelectEvent(e)} />
                  </li>
                ))}
              </ul>
            )}

            {c.ctaLabel && c.ctaHref && (
              <div className="mt-10 flex justify-start">
                <CtaLink href={c.ctaHref} variant="primary">
                  {c.ctaLabel} <ArrowRight className="h-4 w-4" />
                </CtaLink>
              </div>
            )}
          </div>

          {showCalendar && (
            <div
              className={cn("min-w-0 hidden lg:block", showInstagram && "lg:col-span-4")}
              data-testid="events-list-calendar"
            >
              <EventsMonthCalendar
                events={allEvents}
                month={viewMonth}
                onMonthChange={shiftViewMonth}
                selectedEventId={selectedId}
                onSelectEvent={handleSelectEvent}
              />
            </div>
          )}

          {showInstagram && (
            <div className="min-w-0 lg:col-span-4" data-testid="home-events-instagram">
              <InstagramSidebarWidget
                profileUrl={instaUrl}
                title={c.instagramTitle || "AIA Legnano"}
                subtitle={
                  c.instagramSubtitle ||
                  "Foto, aggiornamenti e vita della sezione su Instagram."
                }
              />
            </div>
          )}
        </div>

        {modalEvent && (
          <EventDetailModal event={modalEvent} onClose={() => setModalEvent(null)} />
        )}
      </div>
    </section>
  );
}

/* ============ TESTIMONIALS ============ */
export function TestimonialsBlock({ config: c }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const globalOk = c.useGlobal !== false;

  useEffect(() => {
    setLoading(true);
    const p = globalOk
      ? fetchTestimonials().catch(() => [])
      : Promise.resolve(c.items || []);
    p.then((d) => {
      const list = Array.isArray(d) ? d : (d.items || c.items || []);
      setItems((list && list.length) ? list : (c.items || []));
    }).finally(() => setLoading(false));
  }, [globalOk, c.items]);

  return (
    <section className="site-section bg-background bg-pattern-stadio" data-testid="testimonials-block">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
        {(c.title || c.eyebrow) && <span className="gold-divider my-6 block" />}
        {loading ? (
          <p className="text-slate-500">Caricamento…</p>
        ) : items.length === 0 ? (
          <p className="text-slate-500">Nessuna testimonianza disponibile.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {items.map((t, i) => (
              <Card key={t.id || i} variant="soft" padding="default" className="shadow-ds-sm">
                <svg viewBox="0 0 32 32" className="h-8 w-8 text-gold-400 mb-3 fill-current" aria-hidden>
                  <path d="M10 8c-3.3 0-6 2.7-6 6v10h10v-10H8c0-1.1.9-2 2-2V8zm12 0c-3.3 0-6 2.7-6 6v10h10v-10h-6c0-1.1.9-2 2-2V8z" />
                </svg>
                <p className="text-slate-700 leading-relaxed whitespace-pre-line">{t.quote || t.text || t.body}</p>
                <div className="mt-5 pt-4 border-t border-slate-200">
                  <TestimonialAuthor testimonial={t} />
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

/* ============ DOWNLOADS / DOCUMENTI ============ */
export function DownloadsBlock({ config: c }) {
  const [items, setItems] = useState([]);
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const globalOk = c.useGlobal !== false;

  useEffect(() => {
    setLoading(true);
    const p = globalOk
      ? Promise.all([
          fetchDocuments(c.category || undefined).catch(() => []),
          fetchDocumentSections().catch(() => []),
        ]).then(([docs, secs]) => ({ docs: Array.isArray(docs) ? docs : (docs.items || []), secs: Array.isArray(secs) ? secs : [] }))
      : Promise.resolve({ docs: c.items || [], secs: [] });

    p.then(({ docs, secs }) => {
      setItems(docs);
      setSections(secs || []);
    }).finally(() => setLoading(false));
  }, [globalOk, c.category, c.items]);

  return (
    <section className="site-section bg-background" data-testid="downloads-block">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
        {(c.title || c.eyebrow) && <span className="gold-divider my-6 block" />}
        {loading ? (
          <p className="text-slate-500">Caricamento…</p>
        ) : sections && sections.length ? (
          <DocumentsDownloadLayout documents={items} sections={sections} />
        ) : items && items.length ? (
          <AttachmentList items={items} />
        ) : (
          <p className="text-slate-500">Nessun documento disponibile al momento.</p>
        )}
      </div>
    </section>
  );
}

/* ============ EMBED HTML / IFRAME ============ */
export function EmbedBlock({ config: c }) {
  const widthCls = c.maxWidth === "wide" ? "max-w-6xl" : c.maxWidth === "medium" ? "max-w-4xl" : "max-w-3xl";
  const aspect = c.aspectRatio || "16/9";
  return (
    <section className="site-section bg-background" data-testid="embed-block">
      <div className={`${widthCls} mx-auto px-4 sm:px-6 lg:px-8`}>
        {c.eyebrow && <Eyebrow as="div" className="mb-3 tracking-[0.25em]">{c.eyebrow}</Eyebrow>}
        {c.title && <SectionTitle className="mb-3">{c.title}</SectionTitle>}
        {(c.title || c.eyebrow) && <span className="gold-divider my-6 block" />}
        {c.html ? (
          <div
            className="w-full rounded-xl overflow-hidden shadow-ds-md border border-slate-200"
            style={{ aspectRatio: aspect }}
            dangerouslySetInnerHTML={{ __html: c.html }}
          />
        ) : null}
      </div>
    </section>
  );
}

/* ============ SPACER / SPAZIATORE ============ */
const SPACER_HEIGHT = {
  sm: "h-8 sm:h-12",
  md: "h-16 sm:h-24",
  lg: "h-24 sm:h-32",
  xl: "h-32 sm:h-48",
};
export function SpacerBlock({ config: c }) {
  return <div className={SPACER_HEIGHT[c.height || "md"]} aria-hidden="true" data-testid="spacer-block" />;
}

/* ============ BLOCKS RENDERER ============ */
export function BlocksRenderer({ blocks = [], context = {} }) {
  const stats = context.stats;
  const blockContext = context;
  return (
    <>
      {(blocks || []).filter((b) => b.enabled !== false).map((b) => {
        const c = b.config || {};
        switch (b.type) {
          case "hero": return <HeroBlock key={b.id} config={c} stats={stats} />;
          case "rich_text": return <RichTextBlock key={b.id} config={c} />;
          case "text_image": return <TextImageBlock key={b.id} config={c} />;
          case "cta": return <CTABlock key={b.id} config={c} />;
          case "faq": return <FAQBlock key={b.id} config={c} />;
          case "timeline": return <TimelineBlock key={b.id} config={c} />;
          case "stats": return <StatsBlock key={b.id} config={c} />;
          case "gallery": return <GalleryBlock key={b.id} config={c} />;
          case "news_slider": return <NewsSliderBlock key={b.id} config={c} />;
          case "events_list": return <EventsListBlock key={b.id} config={c} />;
          case "testimonials": return <TestimonialsBlock key={b.id} config={c} />;
          case "downloads": return <DownloadsBlock key={b.id} config={c} />;
          case "embed": return <EmbedBlock key={b.id} config={c} />;
          case "spacer": return <SpacerBlock key={b.id} config={c} />;
          case "designations_table": return <DesignationsTableBlock key={b.id} config={c} />;
          case "members_grid": return <MembersGridBlock key={b.id} config={c} />;
          case "news_grid": return <NewsGridBlock key={b.id} config={c} />;
          case "events_calendar": return <EventsCalendarBlock key={b.id} config={c} />;
          case "contact_section": return <ContactSectionBlock key={b.id} config={c} />;
          case "organigramma": return <OrganigrammaBlock key={b.id} config={c} stats={stats} />;
          case "member_profile": return <MemberProfileBlock key={b.id} config={c} memberSlug={blockContext.memberSlug} />;
          case "portal_login": return <PortalLoginBlock key={b.id} config={c} />;
          default:
            console.warn("Unknown block type:", b.type, b);
            return null;
        }
      })}
    </>
  );
}
