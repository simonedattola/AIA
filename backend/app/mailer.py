"""Email sender via Resend (no-op if keys not configured)."""
import os
import asyncio
import logging

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html: str) -> bool:
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    sender = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev").strip()
    if not api_key or not to:
        logger.info(f"[mailer] Skipped (no key/recipient) - to={to} subject={subject}")
        return False
    try:
        import resend
        resend.api_key = api_key
        params = {
            "from": sender,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"[mailer] Email sent id={result.get('id')} to={to}")
        return True
    except Exception as e:
        logger.error(f"[mailer] Failed: {e}")
        return False


def contact_preference_label(pref: str) -> str:
    return "telefono" if pref == "phone" else "email"


def render_lead_email(lead: dict) -> str:
    pref = contact_preference_label(lead.get("contactPreference", "email"))
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;">
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
    </div>
    """


def render_contact_email(msg: dict) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;">
        Nuovo messaggio dal sito
      </h2>
      <p><strong>Nome:</strong> {msg.get('name','')}</p>
      <p><strong>Email:</strong> {msg.get('email','')}</p>
      <p><strong>Oggetto:</strong> {msg.get('subject','-')}</p>
      <hr/>
      <p style="white-space:pre-line;">{msg.get('body','')}</p>
    </div>
    """


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
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
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
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;">
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
      <p style="color:#64748B;font-size:12px;margin-top:24px;">
        Promemoria inviato perché hai attivato le notifiche eventi nel tuo profilo area associati.
      </p>
    </div>
    """


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
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;">
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
      <p style="margin-top:20px;">
        <a href="{link}" style="background:#004587;color:#fff;padding:10px 18px;text-decoration:none;border-radius:6px;display:inline-block;">
          Apri calendario
        </a>
      </p>
      <p style="color:#64748B;font-size:12px;margin-top:24px;">
        Email inviata perché hai attivato le notifiche eventi nel tuo profilo area associati.
        Riceverai anche un promemoria prima dell'appuntamento, se configurato.
      </p>
    </div>
    """


def render_comunicazione_email(*, title: str, body_preview: str, member_name: str, link: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;">
        Nuova comunicazione — AIA Legnano
      </h2>
      <p style="color:#334155;">Ciao {member_name},</p>
      <p style="color:#334155;">È stata pubblicata una nuova comunicazione riservata agli associati:</p>
      <p style="color:#004587;font-size:18px;font-weight:bold;margin:16px 0;">{title}</p>
      {f'<p style="color:#475569;white-space:pre-line;">{body_preview}</p>' if body_preview else ''}
      <p style="margin-top:20px;">
        <a href="{link}" style="background:#004587;color:#fff;padding:10px 18px;text-decoration:none;border-radius:6px;display:inline-block;">
          Apri area associati
        </a>
      </p>
      <p style="color:#64748B;font-size:12px;margin-top:24px;">
        Email inviata perché hai attivato le notifiche per le comunicazioni interne.
      </p>
    </div>
    """


def render_message_email(
    *,
    member_name: str,
    sender_name: str,
    preview: str,
    link: str,
    context: str,
) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="color:#004587;border-bottom:3px solid #D4AF37;padding-bottom:8px;">
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
    </div>
    """
