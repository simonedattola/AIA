import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";
import { TipiPreferito } from "@/lib/constants";

const schema = z.object({
  tipo: z.enum(TipiPreferito),
  elementoId: z.string(),
});

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const preferiti = await prisma.preferito.findMany({
    where: { userId: auth.userId },
    orderBy: { createdAt: "desc" },
  });
  return NextResponse.json(preferiti);
}

export async function POST(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const body = schema.parse(await req.json());
  const pref = await prisma.preferito.upsert({
    where: {
      userId_tipo_elementoId: {
        userId: auth.userId,
        tipo: body.tipo,
        elementoId: body.elementoId,
      },
    },
    create: { userId: auth.userId, tipo: body.tipo, elementoId: body.elementoId },
    update: {},
  });
  return NextResponse.json(pref);
}

export async function DELETE(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "id richiesto" }, { status: 400 });
  await prisma.preferito.deleteMany({ where: { id, userId: auth.userId } });
  return NextResponse.json({ ok: true });
}
