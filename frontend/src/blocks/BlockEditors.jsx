/* Block editors for admin Page Builder. Each receives (config, onChange). */
import { useState } from "react";
import RichTextEditor from "../pages/admin/RichTextEditor";
import ImageCropUploadField from "../components/admin/ImageCropUploadField";
import { adminUpload } from "../lib/api";
import { Plus, Trash2, Upload, Crop } from "lucide-react";
import GalleryCropModal from "../components/admin/GalleryCropModal";
import { defaultAspectForPreset, loadImageBlobUrl } from "../lib/galleryCrop";
import { Button } from "@/design-system";

const I = "w-full px-3 py-2 border border-slate-300 rounded-md focus:border-navy-600 focus:ring-2 focus:ring-navy-600/20 focus:outline-none text-sm";

function AutoNote({ children }) {
  return <p className="text-sm text-slate-500 bg-slate-100 rounded-md px-3 py-2 mb-4">{children}</p>;
}

function PrimaryButtonFields({ config, onChange, flat = false, fallbackLabel = "", fallbackHref = "" }) {
  const c = config;
  const label = flat ? (c.ctaLabel ?? fallbackLabel) : (c.primaryCta?.label ?? fallbackLabel);
  const href = flat ? (c.ctaHref ?? fallbackHref) : (c.primaryCta?.href ?? fallbackHref);
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <Field label="Testo pulsante">
        <input
          value={label}
          onChange={(e) => {
            if (flat) setCfg(c, "ctaLabel", e.target.value, onChange);
            else setNested(c, "primaryCta.label", e.target.value, onChange);
          }}
          className={I}
          placeholder="es. Scopri di più"
        />
      </Field>
      <Field label="Pagina di destinazione">
        <input
          value={href}
          onChange={(e) => {
            if (flat) setCfg(c, "ctaHref", e.target.value, onChange);
            else setNested(c, "primaryCta.href", e.target.value, onChange);
          }}
          className={I}
          placeholder="es. /eventi"
        />
      </Field>
    </div>
  );
}

export function Field({ label, hint, children }) {
  return (
    <label className="block mb-4 last:mb-0">
      <span className="block text-sm font-medium text-slate-700 mb-1.5">{label}</span>
      {children}
      {hint && <span className="block text-xs text-slate-400 mt-1">{hint}</span>}
    </label>
  );
}

export function UploadField({ label, value, onChange }) {
  const upload = async (e) => {
    const f = e.target.files?.[0]; if (!f) return;
    const res = await adminUpload(f);
    onChange(res.url);
  };
  return (
    <Field label={label}>
      <div className="flex items-center gap-2">
        <input type="file" accept="image/*" onChange={upload} className="hidden" id={`up-${label}`} />
        <label htmlFor={`up-${label}`} className="cursor-pointer inline-flex">
          <Button type="button" variant="outline" size="xs" className="text-xs pointer-events-none" tabIndex={-1}><Upload className="h-3.5 w-3.5" /> Carica immagine</Button>
        </label>
        {value && <img src={value} alt="" className="h-10 w-10 object-cover rounded border" />}
      </div>
    </Field>
  );
}

function setImageField(config, urlKey, sourceKey, { url, sourceUrl }, onChange) {
  const next = { ...config, [urlKey]: url };
  if (sourceKey) next[sourceKey] = sourceUrl || "";
  onChange(next);
}

function setCfg(config, key, value, onChange) {
  onChange({ ...config, [key]: value });
}
function setNested(config, path, value, onChange) {
  // path: "primaryCta.label"
  const keys = path.split(".");
  const copy = JSON.parse(JSON.stringify(config));
  let cur = copy;
  for (let i = 0; i < keys.length - 1; i++) cur = cur[keys[i]] = cur[keys[i]] || {};
  cur[keys[keys.length - 1]] = value;
  onChange(copy);
}

/* ============ HERO ============ */
export function HeroEditor({ config, onChange }) {
  const c = config;
  return (
    <div>
      <Field label="Titolo principale"><textarea rows={2} value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <Field label="Sottotitolo"><textarea rows={2} value={c.subtitle || ""} onChange={(e) => setCfg(c, "subtitle", e.target.value, onChange)} className={I} /></Field>
      <ImageCropUploadField
        label="Immagine di sfondo"
        value={c.backgroundImage}
        sourceValue={c.backgroundImageSource}
        slotAspect="16:9"
        onChange={({ url, sourceUrl }) => setImageField(c, "backgroundImage", "backgroundImageSource", { url, sourceUrl }, onChange)}
      />
      <PrimaryButtonFields config={c} onChange={onChange} />
      <label className="inline-flex items-center gap-2 mt-2">
        <input type="checkbox" checked={!!c.showStats} onChange={(e) => setCfg(c, "showStats", e.target.checked, onChange)} />
        <span className="text-sm">Mostra i numeri della sezione (associati, anni, articoli, eventi)</span>
      </label>
    </div>
  );
}

/* ============ RICH TEXT ============ */
export function RichTextSectionEditor({ config, onChange }) {
  const c = config;
  return (
    <div>
      <Field label="Titolo (opzionale)"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <Field label="Testo">
        <RichTextEditor value={c.html || ""} onChange={(html) => setCfg(c, "html", html, onChange)} />
      </Field>
    </div>
  );
}

/* ============ TEXT + IMAGE ============ */
export function TextImageEditor({ config, onChange }) {
  const c = config;
  return (
    <div>
      <Field label="Titolo"><textarea rows={2} value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <Field label="Testo">
        <RichTextEditor value={c.html || ""} onChange={(html) => setCfg(c, "html", html, onChange)} />
      </Field>
      <ImageCropUploadField
        label="Immagine"
        value={c.imageUrl}
        sourceValue={c.imageUrlSource}
        slotAspect={c.imageAspect || "3:4"}
        onChange={({ url, sourceUrl }) => {
          onChange({
            ...c,
            imageUrl: url,
            imageUrlSource: sourceUrl,
            imageAspect: c.imageAspect || "3:4",
          });
        }}
      />
      <Field label="Posizione immagine">
        <select value={c.imagePosition || "right"} onChange={(e) => setCfg(c, "imagePosition", e.target.value, onChange)} className={I}>
          <option value="right">A destra del testo</option><option value="left">A sinistra del testo</option>
        </select>
      </Field>
      <PrimaryButtonFields config={c} onChange={onChange} flat />
      <Field label="Elenco puntato (opzionale)">
        <input value={c.requirementsTitle || ""} onChange={(e) => setCfg(c, "requirementsTitle", e.target.value, onChange)} className={I} placeholder="es. Requisiti per partecipare" />
      </Field>
      {(c.requirements || []).length > 0 && (
        <div className="mt-3 space-y-2">
          {(c.requirements || []).map((it, i) => (
            <div key={i} className="flex gap-2 items-center">
              <input value={it.text || ""} onChange={(e) => {
                const items = [...(c.requirements || [])];
                items[i] = { ...items[i], icon: it.icon || "CheckCircle2", text: e.target.value };
                setCfg(c, "requirements", items, onChange);
              }} className={I} placeholder="Voce elenco" />
              <button type="button" onClick={() => setCfg(c, "requirements", (c.requirements || []).filter((_, idx) => idx !== i), onChange)} className="text-red-600 hover:bg-red-100 p-2 rounded shrink-0"><Trash2 className="h-4 w-4" /></button>
            </div>
          ))}
        </div>
      )}
      <Button type="button" variant="secondary" className="mt-2" onClick={() => setCfg(c, "requirements", [...(c.requirements || []), { icon: "CheckCircle2", text: "" }], onChange)}>
        <Plus className="h-4 w-4 mr-1" /> Aggiungi voce
      </Button>
    </div>
  );
}

/* ============ CTA ============ */
export function CTAEditor({ config, onChange }) {
  const c = config;
  return (
    <div>
      <Field label="Titolo"><textarea rows={2} value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <Field label="Testo"><textarea rows={3} value={c.description || ""} onChange={(e) => setCfg(c, "description", e.target.value, onChange)} className={I} /></Field>
      {c.formType ? (
        <AutoNote>Questa sezione include il modulo di iscrizione al corso arbitri.</AutoNote>
      ) : (
        <PrimaryButtonFields config={c} onChange={onChange} />
      )}
    </div>
  );
}

/* ============ FAQ ============ */
export function FAQEditor({ config, onChange }) {
  const c = config;
  const setItem = (i, k, v) => {
    const items = [...(c.items || [])];
    items[i] = { ...items[i], [k]: v };
    setCfg(c, "items", items, onChange);
  };
  const addItem = () => setCfg(c, "items", [...(c.items || []), { question: "Nuova domanda", answer: "<p>Risposta</p>" }], onChange);
  const removeItem = (i) => setCfg(c, "items", (c.items || []).filter((_, idx) => idx !== i), onChange);
  return (
    <div>
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <div className="mt-4 space-y-3">
        {(c.items || []).map((it, i) => (
          <div key={i} className="border border-slate-200 rounded-md p-4 bg-slate-50">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs font-semibold text-slate-500">Domanda {i + 1}</span>
              <button onClick={() => removeItem(i)} className="text-red-600 hover:bg-red-100 p-1 rounded"><Trash2 className="h-3.5 w-3.5"/></button>
            </div>
            <input value={it.question} onChange={(e) => setItem(i, "question", e.target.value)} className={I} placeholder="Domanda"/>
            <div className="mt-2"><RichTextEditor value={it.answer} onChange={(html) => setItem(i, "answer", html)} placeholder="Risposta…"/></div>
          </div>
        ))}
        <Button type="button" onClick={addItem} variant="outline" size="sm" className="text-sm"><Plus className="h-4 w-4"/> Aggiungi domanda</Button>
      </div>
    </div>
  );
}

/* ============ TIMELINE ============ */
export function TimelineEditor({ config, onChange }) {
  const c = config;
  const setItem = (i, k, v) => {
    const items = [...(c.items || [])];
    items[i] = { ...items[i], [k]: v };
    setCfg(c, "items", items, onChange);
  };
  const addItem = () => {
    const next = (c.items || []).length + 1;
    setCfg(c, "items", [...(c.items || []), { step: String(next).padStart(2, "0"), title: "Nuovo step", text: "" }], onChange);
  };
  const removeItem = (i) => setCfg(c, "items", (c.items || []).filter((_, idx) => idx !== i), onChange);
  return (
    <div>
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <div className="mt-4 space-y-3">
        {(c.items || []).map((it, i) => (
          <div key={i} className="border border-slate-200 rounded-md p-4 bg-slate-50">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs font-semibold text-slate-500">Passo {i + 1}</span>
              <button onClick={() => removeItem(i)} className="text-red-600 hover:bg-red-100 p-1 rounded"><Trash2 className="h-3.5 w-3.5" /></button>
            </div>
            <input value={it.title} onChange={(e) => setItem(i, "title", e.target.value)} className={I + " mb-2"} placeholder="Titolo" />
            <textarea value={it.text} onChange={(e) => setItem(i, "text", e.target.value)} className={I} rows={2} placeholder="Descrizione" />
          </div>
        ))}
        <Button type="button" onClick={addItem} variant="outline" size="sm" className="text-sm"><Plus className="h-4 w-4" /> Aggiungi passo</Button>
      </div>
    </div>
  );
}

/* ============ STATS ============ */
export function StatsEditor({ config, onChange }) {
  const c = config;
  const setItem = (i, k, v) => {
    const items = [...(c.items || [])];
    items[i] = { ...items[i], [k]: v };
    setCfg(c, "items", items, onChange);
  };
  const addItem = () => setCfg(c, "items", [...(c.items || []), { icon: "Trophy", value: "", label: "Nuovo", desc: "" }], onChange);
  const removeItem = (i) => setCfg(c, "items", (c.items || []).filter((_, idx) => idx !== i), onChange);
  return (
    <div>
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <div className="mt-4 space-y-3">
        {(c.items || []).map((it, i) => (
          <div key={i} className="border border-slate-200 rounded-md p-4 bg-slate-50">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs font-semibold text-slate-500">Numero {i + 1}</span>
              <button onClick={() => removeItem(i)} className="text-red-600 hover:bg-red-100 p-1 rounded"><Trash2 className="h-3.5 w-3.5" /></button>
            </div>
            <div className="grid grid-cols-2 gap-2 mb-2">
              <input value={it.value || ""} onChange={(e) => setItem(i, "value", e.target.value)} className={I} placeholder="es. 120" />
              <input value={it.label} onChange={(e) => setItem(i, "label", e.target.value)} className={I} placeholder="es. Associati" />
            </div>
            <textarea value={it.desc} onChange={(e) => setItem(i, "desc", e.target.value)} className={I} rows={1} placeholder="Breve descrizione (opzionale)" />
          </div>
        ))}
        <Button type="button" onClick={addItem} variant="outline" size="sm" className="text-sm"><Plus className="h-4 w-4"/> Aggiungi</Button>
      </div>
    </div>
  );
}

/* ============ GALLERY ============ */
function GalleryImageRow({ item, index, onUpdate, onRemove }) {
  const [cropSession, setCropSession] = useState(null);
  const [uploading, setUploading] = useState(false);
  const cropAspect = defaultAspectForPreset("gallery");

  const closeCrop = () => {
    if (cropSession?.previewUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(cropSession.previewUrl);
    }
    setCropSession(null);
  };

  const onFilePick = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setCropSession({ kind: "upload", file: f, previewUrl: URL.createObjectURL(f) });
    e.target.value = "";
  };

  const openRecrop = async () => {
    const src = item.sourceUrl || item.url;
    if (!src) return;
    try {
      const previewUrl = await loadImageBlobUrl(src);
      setCropSession({ kind: "recrop", previewUrl });
    } catch {
      alert("Impossibile caricare l'immagine per il ritaglio");
    }
  };

  const handleCropConfirm = async ({ croppedBlob }) => {
    if (!cropSession) return;
    setUploading(true);
    try {
      const croppedFile = new File([croppedBlob], "gallery-crop.jpg", { type: "image/jpeg" });
      const display = await adminUpload(croppedFile);
      if (cropSession.kind === "upload") {
        const source = await adminUpload(cropSession.file);
        onUpdate({
          ...item,
          url: display.url,
          sourceUrl: source.path || source.url,
        });
      } else {
        onUpdate({
          ...item,
          url: display.url,
          sourceUrl: item.sourceUrl || item.url,
        });
      }
      closeCrop();
    } catch (err) {
      alert(err?.message || "Errore caricamento");
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <div className="border border-slate-200 rounded-md p-3 bg-slate-50 flex items-center gap-3">
        {item.url ? <img src={item.url} alt="" className="w-16 h-16 object-cover rounded border" /> : <div className="w-16 h-16 bg-slate-200 rounded" />}
        <div className="flex-1 space-y-2">
          <input value={item.caption || ""} onChange={(e) => onUpdate({ ...item, caption: e.target.value })} className={I} placeholder="Didascalia (opzionale)" />
          <div className="flex flex-wrap gap-2">
            <input type="file" accept="image/*" onChange={onFilePick} className="hidden" id={`gal-up-${index}`} />
            <label htmlFor={`gal-up-${index}`} className="cursor-pointer inline-flex">
              <Button type="button" variant="outline" size="xs" className="text-xs pointer-events-none" tabIndex={-1}>
                <Upload className="h-3.5 w-3.5" /> Carica immagine
              </Button>
            </label>
            {item.url && (
              <Button type="button" variant="outline" size="xs" className="text-xs" onClick={openRecrop}>
                <Crop className="h-3.5 w-3.5" /> Regola inquadratura
              </Button>
            )}
          </div>
        </div>
        <button type="button" onClick={onRemove} className="text-red-600 hover:bg-red-100 p-2 rounded self-start"><Trash2 className="h-4 w-4" /></button>
      </div>
      {cropSession && (
        <GalleryCropModal
          imageSrc={cropSession.previewUrl}
          initialAspect={cropAspect}
          showAspectOptions={false}
          saving={uploading}
          title="Parte dell'immagine da mostrare"
          onConfirm={handleCropConfirm}
          onClose={closeCrop}
        />
      )}
    </>
  );
}

export function GalleryEditor({ config, onChange }) {
  const c = config;
  const setItem = (i, next) => {
    const items = [...(c.images || [])];
    items[i] = next;
    setCfg(c, "images", items, onChange);
  };
  const addItem = () => setCfg(c, "images", [...(c.images || []), { url: "", caption: "" }], onChange);
  const removeItem = (i) => setCfg(c, "images", (c.images || []).filter((_, idx) => idx !== i), onChange);
  return (
    <div>
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <div className="mt-4 space-y-3">
        {(c.images || []).map((it, i) => (
          <GalleryImageRow
            key={i}
            item={it}
            index={i}
            onUpdate={(next) => setItem(i, next)}
            onRemove={() => removeItem(i)}
          />
        ))}
        <Button type="button" onClick={addItem} variant="outline" size="sm" className="text-sm"><Plus className="h-4 w-4"/> Aggiungi immagine</Button>
      </div>
    </div>
  );
}

/* ============ NEWS SLIDER ============ */
export function NewsSliderEditor({ config, onChange }) {
  const c = config;
  return (
    <div>
      <AutoNote>Gli articoli si aggiornano automaticamente dalla sezione News.</AutoNote>
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <PrimaryButtonFields config={c} onChange={onChange} flat fallbackLabel="Tutte le news" fallbackHref="/news" />
    </div>
  );
}

/* ============ EVENTS LIST ============ */
export function EventsListEditor({ config, onChange }) {
  const c = config;
  const embedValue =
    typeof c.instagramEmbed === "string"
      ? c.instagramEmbed
      : c.instagramEmbed?.href || c.instagramPostUrl || "";
  return (
    <div>
      <AutoNote>Gli eventi si aggiornano automaticamente dal calendario.</AutoNote>
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <PrimaryButtonFields config={c} onChange={onChange} flat fallbackLabel="Tutti gli eventi" fallbackHref="/eventi" />
      <Field label="Widget Instagram">
        <label className="inline-flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={c.showInstagramWidget !== false}
            onChange={(e) => setCfg(c, "showInstagramWidget", e.target.checked, onChange)}
          />
          Mostra widget Instagram a fianco degli eventi
        </label>
      </Field>
      <Field label="Calendario mensile">
        <label className="inline-flex items-center gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={c.showCalendar === true}
            onChange={(e) => setCfg(c, "showCalendar", e.target.checked, onChange)}
          />
          Mostra calendario a fianco dell&apos;elenco eventi (desktop)
        </label>
      </Field>
      <Field
        label="URL post Instagram (opzionale)"
        hint="Se vuoto, il widget mostra il feed ufficiale del profilo (Impostazioni → URL Instagram). Altrimenti incolla un post/reel: https://www.instagram.com/p/…"
      >
        <input
          value={embedValue}
          onChange={(e) => {
            const href = e.target.value;
            onChange({
              ...c,
              instagramPostUrl: href,
              instagramEmbed: href ? { href } : {},
            });
          }}
          className={I}
          placeholder="https://www.instagram.com/p/…"
        />
      </Field>
      <Field label="Titolo widget Instagram">
        <input value={c.instagramTitle || ""} onChange={(e) => setCfg(c, "instagramTitle", e.target.value, onChange)} className={I} placeholder="AIA Legnano" />
      </Field>
      <Field label="Sottotitolo widget">
        <input value={c.instagramSubtitle || ""} onChange={(e) => setCfg(c, "instagramSubtitle", e.target.value, onChange)} className={I} />
      </Field>
    </div>
  );
}

/* ============ TESTIMONIALS ============ */
export function TestimonialsEditor({ config, onChange }) {
  const c = config;
  return (
    <div>
      <AutoNote>Le citazioni si gestiscono dalla sezione Testimonianze del pannello admin.</AutoNote>
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
    </div>
  );
}

/* ============ DOWNLOADS ============ */
export function DownloadsEditor({ config, onChange }) {
  const c = config;
  return (
    <div>
      <Field label="Eyebrow"><input value={c.eyebrow || ""} onChange={(e) => setCfg(c, "eyebrow", e.target.value, onChange)} className={I}/></Field>
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I}/></Field>
      <Field label="Filtro sezione"><input value={c.category || ""} onChange={(e) => setCfg(c, "category", e.target.value, onChange)} className={I} placeholder="es. Regolamenti A.I.A."/></Field>
      <p className="text-xs text-slate-500">I documenti sono gestiti centralmente in Admin → Documenti.</p>
    </div>
  );
}

/* ============ EMBED ============ */
export function EmbedEditor({ config, onChange }) {
  const c = config;
  return (
    <div>
      <Field label="Eyebrow"><input value={c.eyebrow || ""} onChange={(e) => setCfg(c, "eyebrow", e.target.value, onChange)} className={I}/></Field>
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I}/></Field>
      <Field label="HTML embed (iframe YouTube, Google Maps, ecc.)" hint="Per Instagram incolla il codice embed o l'URL del post (es. instagram.com/p/…). YouTube/Maps: iframe.">
        <textarea rows={6} value={c.html || ""} onChange={(e) => setCfg(c, "html", e.target.value, onChange)} className={I + " font-mono text-xs"}/>
      </Field>
      <Field label="Larghezza max">
        <select value={c.maxWidth || "wide"} onChange={(e) => setCfg(c, "maxWidth", e.target.value, onChange)} className={I}>
          <option value="narrow">Narrow</option><option value="medium">Medium</option><option value="wide">Wide</option>
        </select>
      </Field>
    </div>
  );
}

/* ============ SPACER ============ */
export function SpacerEditor({ config, onChange }) {
  const c = config;
  return (
    <Field label="Altezza spaziatura">
      <select value={c.height || "md"} onChange={(e) => setCfg(c, "height", e.target.value, onChange)} className={I}>
        <option value="sm">Piccola (2rem)</option>
        <option value="md">Media (4rem)</option>
        <option value="lg">Grande (6rem)</option>
        <option value="xl">Extra (8rem)</option>
      </select>
    </Field>
  );
}

function DynamicSectionEditor({ config, onChange, note }) {
  const c = config;
  return (
    <div className="space-y-4">
      {note && <AutoNote>{note}</AutoNote>}
      <Field label="Titolo"><input value={c.title || ""} onChange={(e) => setCfg(c, "title", e.target.value, onChange)} className={I} /></Field>
      <Field label="Testo introduttivo (opzionale)">
        <textarea rows={3} value={c.intro || ""} onChange={(e) => setCfg(c, "intro", e.target.value, onChange)} className={I} />
      </Field>
    </div>
  );
}

export const EDITORS = {
  hero: HeroEditor,
  rich_text: RichTextSectionEditor,
  text_image: TextImageEditor,
  cta: CTAEditor,
  faq: FAQEditor,
  timeline: TimelineEditor,
  stats: StatsEditor,
  gallery: GalleryEditor,
  news_slider: NewsSliderEditor,
  events_list: EventsListEditor,
  testimonials: TestimonialsEditor,
  downloads: DownloadsEditor,
  embed: EmbedEditor,
  spacer: SpacerEditor,
  designations_table: (p) => <DynamicSectionEditor {...p} note="Le designazioni si aggiornano automaticamente da AIA FIGC." />,
  members_grid: (p) => <DynamicSectionEditor {...p} note="L'elenco arbitri si aggiorna automaticamente dall'anagrafica." />,
  news_grid: (p) => <DynamicSectionEditor {...p} note="Gli articoli si aggiornano automaticamente dalla sezione News." />,
  events_calendar: (p) => <DynamicSectionEditor {...p} note="Eventi e calendario si aggiornano automaticamente." />,
  contact_section: (p) => <DynamicSectionEditor {...p} note="Recapiti e modulo messaggi sono già collegati alle impostazioni della sezione." />,
  organigramma: (p) => <DynamicSectionEditor {...p} note="Presidente e consiglio si aggiornano dall'anagrafica associati." />,
  member_profile: (p) => <DynamicSectionEditor {...p} note="Scheda dinamica dell'arbitro, collegata alla pagina profilo." />,
  portal_login: (p) => <DynamicSectionEditor {...p} note="Form di accesso all'area associati." />,
};
