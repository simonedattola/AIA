import { NextResponse } from "next/server";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";
import { StatiPresenza } from "@/lib/constants";

const schema = z.object({
  eventoId: z.string(),
  stato: z.enum(StatiPresenza),
});

export async function POST(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const body = schema.parse(await req.json());

  const presenza = await prisma.presenzaEvento.upsert({
    where: {
      userId_eventoId: { userId: auth.userId, eventoId: body.eventoId },
    },
    create: {
      userId: auth.userId,
      eventoId: body.eventoId,
      stato: body.stato,
    },
    update: { stato: body.stato },
  });

  return NextResponse.json(presenza);
}
