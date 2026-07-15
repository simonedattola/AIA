import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

async function main() {
  const u = await prisma.user.findUnique({ where: { codiceMeccanografico: "86178903" } });
  console.log("user", u?.id, u?.nome, u?.cognome);
  if (!u) return;
  const gare = await prisma.gara.findMany({ where: { userId: u.id } });
  console.log("gare count", gare.length);
  console.log(gare);
}

main()
  .finally(() => prisma.$disconnect());
