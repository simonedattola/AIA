import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";
const sendSchema = z.object({
  destinatarioId: z.string(),
  testo: z.string().min(1).max(2000),
});

const STAFF_ROLES: string[] = ["ADMIN", "OSSERVATORE", "CONSIGLIO"];

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;

  const messaggi = await prisma.messaggio.findMany({
    where: {
      OR: [{ mittenteId: auth.userId }, { destinatarioId: auth.userId }],
    },
    orderBy: { createdAt: "desc" },
    include: {
      mittente: { select: { id: true, nome: true, cognome: true, ruolo: true } },
      destinatario: { select: { id: true, nome: true, cognome: true, ruolo: true } },
    },
  });

  const staff = await prisma.user.findMany({
    where: { ruolo: { in: STAFF_ROLES } },
    select: { id: true, nome: true, cognome: true, ruolo: true },
  });

  const partners = new Map<string, (typeof messaggi)[0]["mittente"]>();
  for (const m of messaggi) {
    const otherId = m.mittenteId === auth.userId ? m.destinatarioId : m.mittenteId;
    const other = m.mittenteId === auth.userId ? m.destinatario : m.mittente;
    if (STAFF_ROLES.includes(other.ruolo) || STAFF_ROLES.includes(m.mittente.ruolo)) {
      partners.set(otherId, other);
    }
  }
  for (const s of staff) {
    if (s.id !== auth.userId) partners.set(s.id, s);
  }

  const conversazioni = Array.from(partners.entries()).map(([id, user]) => {
    const msgs = messaggi.filter(
      (m) =>
        (m.mittenteId === auth.userId && m.destinatarioId === id) ||
        (m.mittenteId === id && m.destinatarioId === auth.userId)
    );
    const ultimo = msgs[0];
    const nonLetti = msgs.filter((m) => m.destinatarioId === auth.userId && !m.letto).length;
    return { partner: user, messaggi: msgs.reverse(), ultimo, nonLetti };
  });

  return NextResponse.json({ conversazioni, staff });
}

export async function POST(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const body = sendSchema.parse(await req.json());

  const dest = await prisma.user.findUnique({ where: { id: body.destinatarioId } });
  const mittente = await prisma.user.findUnique({ where: { id: auth.userId } });
  if (!dest || !mittente) {
    return NextResponse.json({ error: "Utente non trovato" }, { status: 404 });
  }

  const allowed =
    STAFF_ROLES.includes(dest.ruolo) ||
    STAFF_ROLES.includes(mittente.ruolo);
  if (!allowed) {
    return NextResponse.json(
      { error: "Messaggistica solo con consiglio direttivo e osservatori" },
      { status: 403 }
    );
  }

  const msg = await prisma.messaggio.create({
    data: {
      mittenteId: auth.userId,
      destinatarioId: body.destinatarioId,
      testo: body.testo,
    },
  });

  await prisma.notifica.create({
    data: {
      userId: body.destinatarioId,
      testo: `Nuovo messaggio da ${mittente.nome} ${mittente.cognome}`,
      tipo: "MESSAGGIO",
      link: "/messaggi",
    },
  });

  return NextResponse.json(msg);
}

export async function PATCH(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const { partnerId } = await req.json();
  await prisma.messaggio.updateMany({
    where: { destinatarioId: auth.userId, mittenteId: partnerId, letto: false },
    data: { letto: true },
  });
  return NextResponse.json({ ok: true });
}
