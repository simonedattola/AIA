import { NextResponse } from "next/server";
import { writeFile, mkdir } from "fs/promises";
import path from "path";
import { requireApiUser } from "@/lib/api-auth";
import { prisma } from "@/lib/prisma";

export async function POST(req: Request) {
  const auth = await requireApiUser();
  if ("error" in auth) return auth.error;

  const formData = await req.formData();
  const file = formData.get("file") as File | null;
  if (!file) return NextResponse.json({ error: "Nessun file" }, { status: 400 });

  const bytes = await file.arrayBuffer();
  const buffer = Buffer.from(bytes);
  const uploadsDir = path.join(process.cwd(), "public", "uploads");
  await mkdir(uploadsDir, { recursive: true });
  const ext = path.extname(file.name) || ".jpg";
  const filename = `${auth.userId}-${Date.now()}${ext}`;
  const filepath = path.join(uploadsDir, filename);
  await writeFile(filepath, buffer);
  const url = `/uploads/${filename}`;

  await prisma.user.update({
    where: { id: auth.userId },
    data: { foto: url },
  });

  return NextResponse.json({ url });
}
