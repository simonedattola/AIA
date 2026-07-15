import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { prisma } from "@/lib/prisma";
import { requireApiUser } from "@/lib/api-auth";

export async function GET() {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const user = await prisma.user.findUnique({
    where: { id: auth.userId },
    select: {
      id: true,
      email: true,
      nome: true,
      cognome: true,
      foto: true,
      biografia: true,
      telefono: true,
      emailVisibile: true,
      telefonoVisibile: true,
      categoria: true,
      ruolo: true,
    },
  });
  return NextResponse.json(user);
}

const updateSchema = z.object({
  biografia: z.string().optional(),
  telefono: z.string().optional(),
  emailVisibile: z.coerce.boolean().optional(),
  telefonoVisibile: z.coerce.boolean().optional(),
  nome: z.string().optional(),
  cognome: z.string().optional(),
  password: z.string().min(8).optional(),
  currentPassword: z.string().optional(),
});

export async function PATCH(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;
  const body = await req.json();
  const data = updateSchema.parse(body);
  const user = await prisma.user.findUnique({ where: { id: auth.userId } });
  if (!user) return NextResponse.json({ error: "Utente non trovato" }, { status: 404 });

  const update: Record<string, unknown> = {};
  if (data.biografia !== undefined) update.biografia = data.biografia;
  if (data.telefono !== undefined) update.telefono = data.telefono;
  if (data.emailVisibile !== undefined) update.emailVisibile = data.emailVisibile;
  if (data.telefonoVisibile !== undefined) update.telefonoVisibile = data.telefonoVisibile;
  if (data.nome) update.nome = data.nome;
  if (data.cognome) update.cognome = data.cognome;

  if (data.password) {
    if (!data.currentPassword) {
      return NextResponse.json({ error: "Password attuale richiesta" }, { status: 400 });
    }
    const ok = await bcrypt.compare(data.currentPassword, user.passwordHash);
    if (!ok) return NextResponse.json({ error: "Password attuale errata" }, { status: 400 });
    update.passwordHash = await bcrypt.hash(data.password, 10);
  }

  const updated = await prisma.user.update({
    where: { id: auth.userId },
    data: update,
    select: {
      id: true,
      email: true,
      nome: true,
      cognome: true,
      foto: true,
      biografia: true,
      telefono: true,
      emailVisibile: true,
      telefonoVisibile: true,
      categoria: true,
    },
  });
  return NextResponse.json(updated);
}
