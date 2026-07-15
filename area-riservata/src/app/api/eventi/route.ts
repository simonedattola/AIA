import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;

  const eventi = await prisma.evento.findMany({
    orderBy: { dataInizio: "asc" },
    include: {
      presenze: { where: { userId: auth.userId } },
      calendario: { where: { userId: auth.userId } },
    },
  });

  const designazioni = await prisma.designazione.findMany({
    where: { userId: auth.userId },
    orderBy: { dataGara: "asc" },
  });

  return NextResponse.json({ eventi, designazioni });
}
