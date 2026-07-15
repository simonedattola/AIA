import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { getApiSession } from "@/lib/api-auth";
import { StatiPresenza } from "@/lib/constants";

const updateSchema = z.object({
  userId: z.string(),
  stato: z.enum(StatiPresenza),
});

export async function GET(
  _req: Request,
  { params }: { params: { eventoId: string } }
) {
  const session = await getApiSession();
  const ruolo = session?.user?.ruolo;
  if (!session?.user?.id || (ruolo !== "ADMIN" && ruolo !== "OSSERVATORE")) {
    return NextResponse.json({ error: "Non autorizzato" }, { status: 403 });
  }

  const evento = await prisma.evento.findUnique({
    where: { id: params.eventoId },
    include: {
      presenze: {
        include: {
          user: { select: { id: true, nome: true, cognome: true, categoria: true } },
        },
      },
    },
  });
  if (!evento) return NextResponse.json({ error: "Evento non trovato" }, { status: 404 });

  const associati = await prisma.user.findMany({
    where: { ruolo: "ASSOCIATO" },
    select: { id: true, nome: true, cognome: true, categoria: true },
  });

  const presenzeMap = new Map(evento.presenze.map((p) => [p.userId, p]));
  const partecipanti = associati.map((a) => ({
    user: a,
    presenza: presenzeMap.get(a.id) ?? {
      stato: "NON_RISPOSTO",
      userId: a.id,
      eventoId: evento.id,
    },
  }));

  const counts: Record<string, number> = { PRESENTE: 0, ASSENTE: 0, IN_DUBBIO: 0, NON_RISPOSTO: 0 };
  for (const p of partecipanti) {
    const s = (p.presenza as { stato: string }).stato;
    counts[s] = (counts[s] ?? 0) + 1;
  }
  const total = partecipanti.length || 1;

  const storico = await prisma.presenzaEvento.groupBy({
    by: ["userId", "stato"],
    _count: true,
  });

  return NextResponse.json({
    evento,
    partecipanti,
    stats: {
      presentePct: Math.round((counts.PRESENTE / total) * 100),
      assentePct: Math.round((counts.ASSENTE / total) * 100),
      dubbioPct: Math.round((counts.IN_DUBBIO / total) * 100),
      nonRispostoPct: Math.round((counts.NON_RISPOSTO / total) * 100),
      counts,
    },
    storico,
  });
}

export async function PATCH(
  req: Request,
  { params }: { params: { eventoId: string } }
) {
  const session = await getApiSession();
  const ruolo = session?.user?.ruolo;
  if (!session?.user?.id || (ruolo !== "ADMIN" && ruolo !== "OSSERVATORE")) {
    return NextResponse.json({ error: "Non autorizzato" }, { status: 403 });
  }

  const body = updateSchema.parse(await req.json());
  const presenza = await prisma.presenzaEvento.upsert({
    where: {
      userId_eventoId: { userId: body.userId, eventoId: params.eventoId },
    },
    create: {
      userId: body.userId,
      eventoId: params.eventoId,
      stato: body.stato,
    },
    update: { stato: body.stato },
  });
  return NextResponse.json(presenza);
}
