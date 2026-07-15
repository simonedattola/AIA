import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const now = new Date();

  const [prossimaDesignazione, prossimiEventi, newsTecniche, comunicazioni, notifiche] =
    await Promise.all([
      prisma.designazione.findFirst({
        where: { userId: auth.userId, dataGara: { gte: now } },
        orderBy: { dataGara: "asc" },
      }),
      prisma.evento.findMany({
        where: { dataInizio: { gte: now } },
        orderBy: { dataInizio: "asc" },
        take: 5,
      }),
      prisma.newsTecnica.findMany({ orderBy: { createdAt: "desc" }, take: 5 }),
      prisma.comunicazione.findMany({ orderBy: { createdAt: "desc" }, take: 5 }),
      prisma.notifica.findMany({
        where: { userId: auth.userId, letta: false },
        orderBy: { createdAt: "desc" },
        take: 10,
      }),
    ]);

  return NextResponse.json({
    prossimaDesignazione,
    prossimiEventi,
    newsTecniche,
    comunicazioni,
    notifiche,
  });
}
