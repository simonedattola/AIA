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
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-10 min-[1140px]:py-20 grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-stretch min-[1140px]:items-center w-[...]
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
            {c.secondaryCta?.label && <CtaLink href={c.secondaryCta.href || "/"} className={`underline font-medium ${c.style === "white" ? "text-navy-600" : "text-white"}`}>{c.secondaryCta.label}[...]</CtaLink>}
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
        <FormField label="Preferenza contatto"><select data-testid="lead-contactPreference" value={form.contactPreference} onChange={onChange("contactPreference")} className={I}><option value="em[...]
