import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";
import { sendReminderEmail } from "@/lib/email";

const schema = z.object({ eventoId: z.string() });

export async function POST(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const { eventoId } = schema.parse(await req.json());

  const [user, evento] = await Promise.all([
    prisma.user.findUnique({ where: { id: auth.userId } }),
    prisma.evento.findUnique({ where: { id: eventoId } }),
  ]);
  if (!user || !evento) {
    return NextResponse.json({ error: "Non trovato" }, { status: 404 });
  }

  await prisma.calendarioPersonale.upsert({
    where: { userId_eventoId: { userId: auth.userId, eventoId } },
    create: { userId: auth.userId, eventoId, reminder: true },
    update: { reminder: true },
  });

  const sent = user.email
    ? await sendReminderEmail(user.email, evento.titolo, evento.dataInizio)
    : false;
  return NextResponse.json({ ok: true, emailSent: sent });
}
