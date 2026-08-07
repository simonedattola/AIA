import { useEffect, useRef, useState } from "react";

import { portalMe, portalUpdateMe, portalUploadFoto, portalDeleteFoto, portalSubmitTestimonial } from "../../lib/portal-api";
import { readJsonStorage, writeJsonStorage } from "../../lib/storage";

import { Upload, Quote, Bell, Trash2 } from "lucide-react";

import { Button } from "@/design-system";

import { PortalPageHeader } from "../../components/portal/portal-ui";



const REMINDER_OPTIONS = [

  { value: 24, label: "24 ore prima" },

  { value: 12, label: "12 ore prima" },

  { value: 6, label: "6 ore prima" },

  { value: 1, label: "1 ora prima" },

];



export default function PortalProfiloPage() {

  const [form, setForm] = useState(null);

  const [pwd, setPwd] = useState({ password: "", newPassword: "" });

  const [profileMsg, setProfileMsg] = useState("");

  const [testimonialMsg, setTestimonialMsg] = useState("");

  const [uploading, setUploading] = useState(false);

  const [testimonial, setTestimonial] = useState({ quote: "", role: "" });

  const fileRef = useRef(null);



  useEffect(() => {

    portalMe().then((m) =>

      setForm({

        bio: m.bio || "",

        emailVisibile: m.emailVisibile,

        telefonoVisibile: m.telefonoVisibile,

        emailNotifyEvents: !!m.emailNotifyEvents,
        emailNotifyEventLeadHours: REMINDER_OPTIONS.some((o) => o.value === m.emailNotifyEventLeadHours)
          ? m.emailNotifyEventLeadHours
          : 24,
        emailNotifyComunicazioni: !!m.emailNotifyComunicazioni,
        emailNotifyMessages: !!m.emailNotifyMessages,
        hasEmail: !!m.hasEmail,

        firstName: m.firstName,

        lastName: m.lastName,

        category: m.category,

        photoUrl: m.photoUrl,

      })

    );

  }, []);



  const onPhoto = async (e) => {

    const f = e.target.files?.[0];

    if (!f) return;

    setUploading(true);

    setProfileMsg("");

    try {

      const res = await portalUploadFoto(f);

      setForm((prev) => ({ ...prev, photoUrl: res.url }));

      const stored = readJsonStorage("aia_member", {}) || {};

      writeJsonStorage("aia_member", { ...stored, photoUrl: res.url });

      setProfileMsg("Foto profilo aggiornata.");

    } catch (err) {

      setProfileMsg(err?.response?.data?.detail || "Errore caricamento foto");

    } finally {

      setUploading(false);

      if (fileRef.current) fileRef.current.value = "";

    }

  };



  const onDeletePhoto = async () => {

    if (!form?.photoUrl) return;

    setUploading(true);

    setProfileMsg("");

    try {

      await portalDeleteFoto();

      setForm((prev) => ({ ...prev, photoUrl: "" }));

      const stored = readJsonStorage("aia_member", {}) || {};

      writeJsonStorage("aia_member", { ...stored, photoUrl: "" });

      setProfileMsg("Foto profilo rimossa.");

    } catch (err) {

      setProfileMsg(err?.response?.data?.detail || "Errore rimozione foto");

    } finally {

      setUploading(false);

    }

  };



  const save = async (e) => {

    e.preventDefault();

    setProfileMsg("");

    try {

      const res = await portalUpdateMe({

        bio: form.bio,

        emailVisibile: form.emailVisibile,

        telefonoVisibile: form.telefonoVisibile,

        emailNotifyEvents: form.emailNotifyEvents,
        emailNotifyEventLeadHours: form.emailNotifyEventLeadHours,
        emailNotifyComunicazioni: form.emailNotifyComunicazioni,
        emailNotifyMessages: form.emailNotifyMessages,

        password: pwd.password,

        newPassword: pwd.newPassword,

      });

      writeJsonStorage("aia_member", res);

      setForm((prev) => ({

        ...prev,

        emailNotifyEvents: !!res.emailNotifyEvents,
        emailNotifyEventLeadHours: res.emailNotifyEventLeadHours ?? 24,
        emailNotifyComunicazioni: !!res.emailNotifyComunicazioni,
        emailNotifyMessages: !!res.emailNotifyMessages,
        hasEmail: !!res.hasEmail,

      }));

      setProfileMsg("Profilo aggiornato.");

      setPwd({ password: "", newPassword: "" });

    } catch (err) {

      setProfileMsg(err?.response?.data?.detail || "Errore salvataggio");

    }

  };



  const inviaTestimonianza = async (e) => {

    e.preventDefault();

    setTestimonialMsg("");

    try {

      const res = await portalSubmitTestimonial(testimonial);

      setTestimonial({ quote: "", role: "" });

      setTestimonialMsg(res.message || "Testimonianza inviata per approvazione.");

    } catch (err) {

      setTestimonialMsg(err?.response?.data?.detail || "Errore invio testimonianza");

    }

  };



  if (!form) return <p className="text-slate-500">Caricamento…</p>;



  return (

    <div data-testid="portal-profilo-page">

      <PortalPageHeader title="Profilo" />

      <div className="flex items-center gap-4 mb-8">

        {form.photoUrl ? (

          <img src={form.photoUrl} alt="" className="h-20 w-20 rounded-full object-cover border-2 border-gold-400" />

        ) : (

          <div className="h-20 w-20 rounded-full bg-navy-100 flex items-center justify-center text-navy-600 font-bold text-xl">

            {form.firstName?.[0]}

            {form.lastName?.[0]}

          </div>

        )}

        <div className="flex-1">

          <div className="font-display text-xl font-bold text-navy-800">

            {form.firstName} {form.lastName}

          </div>

          {form.category && <div className="text-sm text-slate-600">{form.category}</div>}

          <input ref={fileRef} type="file" accept="image/*" className="hidden" id="portal-photo" onChange={onPhoto} />

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2">
            <label
              htmlFor="portal-photo"
              className="inline-flex items-center gap-1.5 text-sm text-navy-600 hover:underline cursor-pointer"
            >
              <Upload className="h-4 w-4" />
              {uploading ? "Caricamento…" : form.photoUrl ? "Cambia foto profilo" : "Carica foto profilo"}
            </label>
            {form.photoUrl && (
              <button
                type="button"
                onClick={onDeletePhoto}
                disabled={uploading}
                className="inline-flex items-center gap-1.5 text-sm text-red-600 hover:underline disabled:opacity-50"
                data-testid="portal-delete-photo"
              >
                <Trash2 className="h-4 w-4" />
                Elimina foto
              </button>
            )}
          </div>

        </div>

      </div>

      <form onSubmit={save} className="w-full bg-white rounded-xl border border-slate-200 p-6 space-y-4 mb-8">

        {profileMsg && <p className="text-sm text-navy-700 bg-navy-50 p-2 rounded">{profileMsg}</p>}

        <label className="block">

          <span className="text-sm font-medium text-slate-700">Biografia</span>

          <textarea

            rows={4}

            value={form.bio}

            onChange={(e) => setForm({ ...form, bio: e.target.value })}

            className="w-full mt-1 border border-slate-300 rounded-md px-3 py-2"

          />

        </label>

        <label className="flex items-center gap-2">

          <input

            type="checkbox"

            checked={form.emailVisibile}

            onChange={(e) => setForm({ ...form, emailVisibile: e.target.checked })}

          />

          <span className="text-sm">Mostra email agli altri associati</span>

        </label>

        <label className="flex items-center gap-2">

          <input

            type="checkbox"

            checked={form.telefonoVisibile}

            onChange={(e) => setForm({ ...form, telefonoVisibile: e.target.checked })}

          />

          <span className="text-sm">Mostra telefono agli altri associati</span>

        </label>



        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-4">
          <div className="flex items-center gap-2 text-navy-700 font-medium text-sm">
            <Bell className="h-4 w-4 text-gold-500" />
            Notifiche email
          </div>
          {!form.hasEmail && (
            <p className="text-xs text-amber-700">
              Per attivare le notifiche serve un indirizzo email in anagrafica. Contatta la sezione.
            </p>
          )}

          <div className="space-y-2">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.emailNotifyComunicazioni}
                disabled={!form.hasEmail}
                onChange={(e) => setForm({ ...form, emailNotifyComunicazioni: e.target.checked })}
                data-testid="portal-email-notify-comunicazioni"
              />
              <span className="text-sm">Comunicazioni interne (nuovi avvisi dalla sezione)</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.emailNotifyMessages}
                disabled={!form.hasEmail}
                onChange={(e) => setForm({ ...form, emailNotifyMessages: e.target.checked })}
                data-testid="portal-email-notify-messages"
              />
              <span className="text-sm">Messaggi (nuovi messaggi in messaggeria)</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.emailNotifyEvents}
                disabled={!form.hasEmail}
                onChange={(e) => setForm({ ...form, emailNotifyEvents: e.target.checked })}
                data-testid="portal-email-notify-events"
              />
              <span className="text-sm">
                Eventi (invito alla creazione e promemoria prima dell&apos;appuntamento)
              </span>
            </label>
            {form.emailNotifyEvents && form.hasEmail && (
              <label className="block pl-6">
                <span className="text-sm font-medium text-slate-700">Promemoria prima dell&apos;evento</span>
                <select
                  value={form.emailNotifyEventLeadHours}
                  onChange={(e) => setForm({ ...form, emailNotifyEventLeadHours: Number(e.target.value) })}
                  className="w-full mt-1 border border-slate-300 rounded-md px-3 py-2 text-sm"
                  data-testid="portal-email-notify-lead"
                >
                  {REMINDER_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </label>
            )}
          </div>
        </div>



        <hr className="border-slate-200" />

        <p className="text-sm font-medium text-slate-700">Cambia password</p>

        <input

          type="password"

          placeholder="Password attuale"

          value={pwd.password}

          onChange={(e) => setPwd({ ...pwd, password: e.target.value })}

          className="w-full border border-slate-300 rounded-md px-3 py-2"

        />

        <input

          type="password"

          placeholder="Nuova password (min. 6 caratteri)"

          value={pwd.newPassword}

          onChange={(e) => setPwd({ ...pwd, newPassword: e.target.value })}

          className="w-full border border-slate-300 rounded-md px-3 py-2"

        />

        <Button type="submit" variant="primary">

          Salva profilo

        </Button>

      </form>



      <form onSubmit={inviaTestimonianza} className="w-full bg-white rounded-xl border border-slate-200 p-6 space-y-4">

        <div className="flex items-center gap-2 text-navy-700 font-semibold">

          <Quote className="h-5 w-5 text-gold-500" />

          Invia una testimonianza

        </div>

        <p className="text-sm text-slate-600">

          La tua testimonianza sarà revisionata dalla sezione prima della pubblicazione sul sito.

        </p>

        {testimonialMsg && <p className="text-sm text-navy-700 bg-navy-50 p-2 rounded">{testimonialMsg}</p>}

        <label className="block">

          <span className="text-sm font-medium text-slate-700">Ruolo / qualifica (opzionale)</span>

          <input

            value={testimonial.role}

            onChange={(e) => setTestimonial({ ...testimonial, role: e.target.value })}

            className="w-full mt-1 border border-slate-300 rounded-md px-3 py-2"

            placeholder="es. Arbitro di Serie D"

          />

        </label>

        <label className="block">

          <span className="text-sm font-medium text-slate-700">Testimonianza *</span>

          <textarea

            required

            minLength={20}

            rows={4}

            value={testimonial.quote}

            onChange={(e) => setTestimonial({ ...testimonial, quote: e.target.value })}

            className="w-full mt-1 border border-slate-300 rounded-md px-3 py-2"

            placeholder="Scrivi la tua esperienza con la sezione…"

          />

        </label>

        <Button type="submit" variant="primary">

          Invia per approvazione

        </Button>

      </form>

    </div>

  );

}

