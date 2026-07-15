import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";

const schema = z.object({
  eventoId: z.string(),
  reminder: z.boolean().optional(),
});

export async function POST(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const body = schema.parse(await req.json());

  const entry = await prisma.calendarioPersonale.upsert({
    where: {
      userId_eventoId: { userId: auth.userId, eventoId: body.eventoId },
    },
    create: {
      userId: auth.userId,
      eventoId: body.eventoId,
      reminder: body.reminder ?? false,
    },
    update: { reminder: body.reminder ?? false },
  });

  return NextResponse.json(entry);
}
