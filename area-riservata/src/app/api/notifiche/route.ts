import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const notifiche = await prisma.notifica.findMany({
    where: { userId: auth.userId },
    orderBy: { createdAt: "desc" },
    take: 50,
  });
  return NextResponse.json(notifiche);
}

export async function PATCH(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const { id, letta } = await req.json();
  if (!id) return NextResponse.json({ error: "id richiesto" }, { status: 400 });
  const n = await prisma.notifica.updateMany({
    where: { id, userId: auth.userId },
    data: { letta: letta ?? true },
  });
  return NextResponse.json({ updated: n.count });
}

export async function DELETE(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const { searchParams } = new URL(req.url);
  const id = searchParams.get("id");
  if (!id) return NextResponse.json({ error: "id richiesto" }, { status: 400 });
  await prisma.notifica.deleteMany({ where: { id, userId: auth.userId } });
  return NextResponse.json({ ok: true });
}
