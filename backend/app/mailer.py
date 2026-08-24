"""Email sender via Resend (no-op if keys not configured).

Config tipica (Resend + dominio aia-legnano.it verificato):
  RESEND_API_KEY=re_...
  SENDER_EMAIL=noreply@aia-legnano.it
  NOTIFY_EMAIL=legnano@aia-figc.it
  PORTAL_FRONTEND_URL=https://aia-virid.vercel.app
"""

import os
import asyncio
import logging

logger = logging.getLogger(__name__)

DEFAULT_SENDER = "noreply@aia-legnano.it"
DEFAULT_NOTIFY = "legnano@aia-figc.it"
DEFAULT_PORTAL_URL = "https://aia-virid.vercel.app"
EMAIL_LOGO_PATH = "/brand/logo-aia-legnano-email.png"


def sender_email() -> str:
    return (os.environ.get("SENDER_EMAIL") or DEFAULT_SENDER).strip()


def notify_email() -> str:
    """Casella sezione: contatti, candidature, commenti comunicazioni."""
    return (os.environ.get("NOTIFY_EMAIL") or DEFAULT_NOTIFY).strip()


def portal_frontend_url() -> str:
    return (os.environ.get("PORTAL_FRONTEND_URL") or DEFAULT_PORTAL_URL).rstrip("/")


def email_logo_url() -> str:
    """URL assoluto del logo sezione (servito dal frontend)."""
    return f"{portal_frontend_url()}{EMAIL_LOGO_PATH}"


def wrap_email(inner_html: str) -> str:
    """Layout comune: logo sezione + contenuto + footer."""
    logo = email_logo_url()
    home = portal_frontend_url()
    return f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto;background:#ffffff;">
      <div style="text-align:center;padding:22px 16px 14px;background:#004587;">
        <a href="{home}" style="text-decoration:none;">
          <img src="{logo}" alt="AIA Legnano" width="80" height="80"
               style="display:inline-block;width:80px;height:80px;border:0;border-radius:10px;background:#ffffff;padding:6px;box-sizing:border-box;" />
        </a>
        <div style="color:#D4AF37;font-size:12px;font-weight:bold;letter-spacing:0.08em;margin-top:10px;text-transform:uppercase;">
          Sezione AIA Legnano
        </div>
      </div>
      <div style="padding:22px 18px 8px;color:#111827;">
        {inner_html}
      </div>
      <div style="padding:14px 18px 22px;border-top:1px solid #E2E8F0;color:#94A3B8;font-size:11px;text-align:center;line-height:1.5;">
        Associazione Italiana Arbitri — Sezione di Legnano<br/>
        <a href="{home}" style="color:#004587;text-decoration:none;">{home.replace("https://", "").replace("http://", "")}</a>
      </div>
    </div>
    """


async def send_email(
    to: str,
    subject: str,
    html: str,
    *,
    attachments: list[dict] | None = None,
) -> bool:
    """Invia email via Resend. attachments: [{filename, content}] con content bytes o str."""
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    sender = sender_email()
    if not api_key or not to:
        logger.info(
            "[mailer] Skipped (no key/recipient) - to=%s subject=%s", to, subject
        )
        return False
    try:
        import base64
        import resend

        resend.api_key = api_key
        params: dict = {
            "from": sender,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if attachments:
            packed = []
            for att in attachments:
                name = (att.get("filename") or "allegato.bin").strip()
                raw = att.get("content")
                if raw is None:
                    continue
                if isinstance(raw, str):
                    raw_bytes = raw.encode("utf-8")
                else:
                    raw_bytes = bytes(raw)
                packed.append(
                    {
                        "filename": name,
                        "content": base64.b64encode(raw_bytes).decode("ascii"),
                    }
                )
            if packed:
                params["attachments"] = packed
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(
            "[mailer] Email sent id=%s to=%s from=%s", result.get("id"), to, sender
        )
        return True
    except Exception as e:
        logger.error("[mailer] Failed: %s", e)
        return False


def _event_calendar_cta_html(event: dict) -> str:
    """Pulsanti Google Calendar + nota Apple (.ics allegato)."""
    from .event_ics import google_calendar_url

    gcal = google_calendar_url(event) or ""
    buttons = []
    if gcal:
        buttons.append(
            f'<a href="{gcal}" style="background:#004587;color:#fff;padding:10px 18px;'
            f'text-decoration:none;border-radius:6px;display:inline-block;margin:4px 8px 4px 0;">'
            f"Aggiungi a Google Calendar</a>"
        )
    buttons.append(
        '<span style="display:inline-block;padding:10px 0;color:#475569;font-size:13px;">'
        "Su iPhone/Mac: apri l&apos;allegato <strong>.ics</strong> per aggiungerlo a Calendario.</span>"
    )
    return f'<p style="margin-top:20px;">{"".join(buttons)}</p>'


def contact_preference_label(pref: str) -> str:
    return "telefono" if pref == "phone" else "email"


def render_lead_email(lead: dict) -> str:
    pref = contact_preference_label(lead.get("contactPreference", "email"))
    return wrap_email(f"""
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;margin-top:0;">
        Nuova candidatura - Corso Arbitri
      </h2>
      <table cellpadding="8" style="width:100%;border-collapse:collapse;">
        <tr><td style="background:#F1F5F9;width:35%;"><strong>Nome</strong></td><td>{lead.get('firstName','')}</td></tr>
        <tr><td style="background:#F1F5F9;"><strong>Cognome</strong></td><td>{lead.get('lastName','')}</td></tr>
        <tr><td style="background:#F1F5F9;"><strong>Età</strong></td><td>{lead.get('age','-')}</td></tr>
        <tr><td style="background:#F1F5F9;"><strong>Telefono</strong></td><td>{lead.get('phone','-')}</td></tr>
        <tr><td style="background:#F1F5F9;"><strong>Email</strong></td><td>{lead.get('email','-')}</td></tr>
        <tr><td style="background:#F1F5F9;"><strong>Preferenza contatto</strong></td><td>{pref}</td></tr>
        <tr><td style="background:#F1F5F9;"><strong>Messaggio</strong></td><td>{lead.get('message','-')}</td></tr>
      </table>
      <p style="color:#64748B;font-size:12px;margin-top:24px;">
        Inviato dal sito ufficiale AIA Legnano — Sezione Associazione Italiana Arbitri
      </p>
        """)


def render_lead_confirmation_email(*, first_name: str, contact_preference: str) -> str:
    pref = contact_preference_label(contact_preference)
    return wrap_email(f"""
      <h2 style="color:#004587;margin-top:0;">Ciao {first_name},</h2>
      <p>grazie per aver inviato la tua candidatura al <strong>corso arbitri</strong>
      della Sezione AIA di Legnano.</p>
      <p>Un nostro referente ti contatterà entro pochi giorni tramite {pref}.</p>
      <p style="margin-top:24px;color:#64748B;">A presto sui campi,<br/>
      <strong>Sezione AIA Legnano</strong></p>
        """)


def render_contact_email(msg: dict) -> str:
    return wrap_email(f"""
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;margin-top:0;">
        Nuovo messaggio dal sito
      </h2>
      <p><strong>Nome:</strong> {msg.get('name','')}</p>
      <p><strong>Email:</strong> {msg.get('email','')}</p>
      <p><strong>Oggetto:</strong> {msg.get('subject','-')}</p>
      <hr/>
      <p style="white-space:pre-line;">{msg.get('body','')}</p>
        """)


def _format_event_datetime_it(event: dict) -> str:
    from .event_reminders import normalize_event_time

    date = (event.get("date") or "")[:10]
    orario = normalize_event_time(event.get("orario"))
    if not date:
        return orario
    parts = date.split("-")
    if len(parts) != 3:
        return f"{date} alle {orario}"
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    months = (
        "gennaio",
        "febbraio",
        "marzo",
        "aprile",
        "maggio",
        "giugno",
        "luglio",
        "agosto",
        "settembre",
        "ottobre",
        "novembre",
        "dicembre",
    )
    return f"{d} {months[m - 1]} {y} alle {orario}"


def render_event_reminder_email(event: dict, member: dict, lead_hours: int) -> str:
    when = _format_event_datetime_it(event)
    lead = "1 ora" if lead_hours == 1 else f"{lead_hours} ore"
    nome = f"{member.get('firstName', '')} {member.get('lastName', '')}".strip()
    titolo = event.get("titolo", "Evento")
    luogo = event.get("luogo", "")
    descrizione = (event.get("descrizione") or "").strip()
    luogo_row = (
        f'<tr><td style="background:#F1F5F9;"><strong>Luogo</strong></td><td>{luogo}</td></tr>'
        if luogo
        else ""
    )
    desc_block = (
        f'<p style="margin-top:16px;color:#334155;white-space:pre-line;">{descrizione}</p>'
        if descrizione
        else ""
    )
    return wrap_email(f"""
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;margin-top:0;">
        Promemoria evento — AIA Legnano
      </h2>
      <p style="color:#334155;">Ciao {nome},</p>
      <p style="color:#334155;">Ti ricordiamo che tra <strong>{lead}</strong> è in programma:</p>
      <table cellpadding="8" style="width:100%;border-collapse:collapse;margin-top:12px;">
        <tr><td style="background:#F1F5F9;width:35%;"><strong>Evento</strong></td><td>{titolo}</td></tr>
        <tr><td style="background:#F1F5F9;"><strong>Data e ora</strong></td><td>{when}</td></tr>
        {luogo_row}
      </table>
      {desc_block}
      {_event_calendar_cta_html(event)}
      <p style="color:#64748B;font-size:12px;margin-top:24px;">
        Promemoria inviato perché hai attivato le notifiche eventi nel tuo profilo area associati.
      </p>
        """)


def render_event_created_email(event: dict, member: dict, *, link: str) -> str:
    when = _format_event_datetime_it(event)
    nome = f"{member.get('firstName', '')} {member.get('lastName', '')}".strip()
    titolo = event.get("titolo", "Evento")
    luogo = event.get("luogo", "")
    descrizione = (event.get("descrizione") or "").strip()
    luogo_row = (
        f'<tr><td style="background:#F1F5F9;"><strong>Luogo</strong></td><td>{luogo}</td></tr>'
        if luogo
        else ""
    )
    desc_block = (
        f'<p style="margin-top:16px;color:#334155;white-space:pre-line;">{descrizione}</p>'
        if descrizione
        else ""
    )
    return wrap_email(f"""
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;margin-top:0;">
        Nuovo evento — AIA Legnano
      </h2>
      <p style="color:#334155;">Ciao {nome},</p>
      <p style="color:#334155;">Sei stato invitato a un nuovo appuntamento:</p>
      <table cellpadding="8" style="width:100%;border-collapse:collapse;margin-top:12px;">
        <tr><td style="background:#F1F5F9;width:35%;"><strong>Evento</strong></td><td>{titolo}</td></tr>
        <tr><td style="background:#F1F5F9;"><strong>Data e ora</strong></td><td>{when}</td></tr>
        {luogo_row}
      </table>
      {desc_block}
      {_event_calendar_cta_html(event)}
      <p style="margin-top:16px;">
        <a href="{link}" style="background:#D4AF37;color:#004587;padding:10px 18px;text-decoration:none;border-radius:6px;display:inline-block;font-weight:bold;">
          Apri calendario area associati
        </a>
      </p>
      <p style="color:#64748B;font-size:12px;margin-top:24px;">
        Email inviata perché hai attivato le notifiche eventi nel tuo profilo area associati.
        Riceverai anche un promemoria prima dell'appuntamento, se configurato.
      </p>
        """)


def render_comunicazione_email(
    *, title: str, body_preview: str, member_name: str, link: str
) -> str:
    preview_html = (
        f'<p style="color:#475569;white-space:pre-line;">{body_preview}</p>'
        if body_preview
        else ""
    )
    return wrap_email(f"""
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;margin-top:0;">
        Nuova comunicazione — AIA Legnano
      </h2>
      <p style="color:#334155;">Ciao {member_name},</p>
      <p style="color:#334155;">È stata pubblicata una nuova comunicazione riservata agli associati:</p>
      <p style="color:#004587;font-size:18px;font-weight:bold;margin:16px 0;">{title}</p>
      {preview_html}
      <p style="margin-top:20px;">
        <a href="{link}" style="background:#004587;color:#fff;padding:10px 18px;text-decoration:none;border-radius:6px;display:inline-block;">
          Apri area associati
        </a>
      </p>
      <p style="color:#64748B;font-size:12px;margin-top:24px;">
        Email inviata perché hai attivato le notifiche per le comunicazioni interne.
      </p>
        """)


def render_message_email(
    *,
    member_name: str,
    sender_name: str,
    preview: str,
    link: str,
    context: str,
) -> str:
    return wrap_email(f"""
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;margin-top:0;">
        Nuovo messaggio — AIA Legnano
      </h2>
      <p style="color:#334155;">Ciao {member_name},</p>
      <p style="color:#334155;">
        <strong>{sender_name}</strong> ti ha scritto ({context}):
      </p>
      <p style="color:#475569;background:#F8FAFC;padding:12px;border-radius:8px;white-space:pre-line;">{preview}</p>
      <p style="margin-top:20px;">
        <a href="{link}" style="background:#004587;color:#fff;padding:10px 18px;text-decoration:none;border-radius:6px;display:inline-block;">
          Apri messaggeria
        </a>
      </p>
      <p style="color:#64748B;font-size:12px;margin-top:24px;">
        Email inviata perché hai attivato le notifiche per i messaggi.
      </p>
        """)


def render_comunicazione_reply_staff_email(
    *,
    title: str,
    author_name: str,
    reply_text: str,
    link: str,
) -> str:
    return wrap_email(f"""
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;margin-top:0;">
        Nuovo commento su comunicazione — AIA Legnano
      </h2>
      <p style="color:#334155;">
        <strong>{author_name}</strong> ha commentato la comunicazione:
      </p>
      <p style="color:#004587;font-size:18px;font-weight:bold;margin:16px 0;">{title}</p>
      <p style="color:#475569;background:#F8FAFC;padding:12px;border-radius:8px;white-space:pre-line;">{reply_text}</p>
      <p style="margin-top:20px;">
        <a href="{link}" style="background:#004587;color:#fff;padding:10px 18px;text-decoration:none;border-radius:6px;display:inline-block;">
          Apri area associati
        </a>
      </p>
        """)


def render_comunicazione_reply_member_email(
    *,
    member_name: str,
    title: str,
    author_name: str,
    reply_text: str,
    link: str,
) -> str:
    return wrap_email(f"""
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;margin-top:0;">
        Nuovo commento — AIA Legnano
      </h2>
      <p style="color:#334155;">Ciao {member_name},</p>
      <p style="color:#334155;">
        <strong>{author_name}</strong> ha commentato la comunicazione
        <strong>{title}</strong>:
      </p>
      <p style="color:#475569;background:#F8FAFC;padding:12px;border-radius:8px;white-space:pre-line;">{reply_text}</p>
      <p style="margin-top:20px;">
        <a href="{link}" style="background:#004587;color:#fff;padding:10px 18px;text-decoration:none;border-radius:6px;display:inline-block;">
          Apri comunicazione
        </a>
      </p>
      <p style="color:#64748B;font-size:12px;margin-top:24px;">
        Email inviata perché hai attivato le notifiche per le comunicazioni interne.
      </p>
        """)
