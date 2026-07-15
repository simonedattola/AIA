import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";
import { addDays, subDays } from "date-fns";
import { defaultPassword } from "../src/lib/password";

const prisma = new PrismaClient();

async function upsertUser(data: {
  codice: string;
  nome: string;
  cognome: string;
  ruolo: string;
  email?: string;
  categoria?: string;
  telefono?: string;
  biografia?: string;
  passwordOverride?: string;
}) {
  const pwd = data.passwordOverride ?? defaultPassword(data.nome, data.cognome);
  const passwordHash = await bcrypt.hash(pwd, 10);
  return prisma.user.upsert({
    where: { codiceMeccanografico: data.codice },
    create: {
      codiceMeccanografico: data.codice,
      nome: data.nome,
      cognome: data.cognome,
      ruolo: data.ruolo,
      email: data.email ?? null,
      categoria: data.categoria ?? null,
      telefono: data.telefono ?? null,
      biografia: data.biografia ?? null,
      passwordHash,
    },
    update: {
      nome: data.nome,
      cognome: data.cognome,
      ruolo: data.ruolo,
      email: data.email ?? null,
      categoria: data.categoria ?? null,
      telefono: data.telefono ?? null,
      biografia: data.biografia ?? null,
    },
  });
}

async function main() {
  await prisma.presenzaEvento.deleteMany();
  await prisma.calendarioPersonale.deleteMany();
  await prisma.preferito.deleteMany();
  await prisma.notifica.deleteMany();
  await prisma.messaggio.deleteMany();
  await prisma.media.deleteMany();
  await prisma.traguardo.deleteMany();
  await prisma.successoPersonale.deleteMany();
  await prisma.gara.deleteMany();
  await prisma.designazione.deleteMany();
  await prisma.documentoTecnico.deleteMany();
  await prisma.quiz.deleteMany();
  await prisma.rTO.deleteMany();
  await prisma.evento.deleteMany();
  await prisma.newsTecnica.deleteMany();
  await prisma.comunicazione.deleteMany();
  await prisma.user.deleteMany();

  const admin = await upsertUser({
    codice: "00000001",
    nome: "Mario",
    cognome: "Rossi",
    ruolo: "ADMIN",
    email: "admin@aia-legnano.it",
    categoria: "Serie D",
    telefono: "+39 333 1111111",
    biografia: "Presidente sezione.",
    passwordOverride: "admin.demo",
  });

  const simone = await upsertUser({
    codice: "86178903",
    nome: "Simone",
    cognome: "Dattola",
    ruolo: "ASSOCIATO",
    email: "simone.dattola@aia-legnano.it",
    categoria: "Promozione",
    biografia: "Arbitro sezione AIA Legnano.",
  });

  const associato2 = await upsertUser({
    codice: "86178904",
    nome: "Giulia",
    cognome: "Verdi",
    ruolo: "ASSOCIATO",
    categoria: "Eccellenza",
  });

  const consiglio = await upsertUser({
    codice: "86178001",
    nome: "Paolo",
    cognome: "Neri",
    ruolo: "CONSIGLIO",
  });

  const osservatore = await upsertUser({
    codice: "86178002",
    nome: "Anna",
    cognome: "Gialli",
    ruolo: "OSSERVATORE",
  });

  const associato1 = simone;
  const now = new Date();

  const eventoRaduno = await prisma.evento.create({
    data: {
      titolo: "Raduno arbitri sezione",
      tipo: "RADUNO",
      dataInizio: addDays(now, 5),
      luogo: "Sede AIA Legnano",
    },
  });

  const eventoRto = await prisma.evento.create({
    data: { titolo: "RTO mensile", tipo: "RTO", dataInizio: addDays(now, 12), luogo: "Online Teams" },
  });

  const eventoAllen = await prisma.evento.create({
    data: { titolo: "Allenamento fisico", tipo: "ALLENAMENTO", dataInizio: addDays(now, 3), luogo: "Campo Comunale" },
  });

  for (const uid of [associato1.id, associato2.id]) {
    await prisma.presenzaEvento.createMany({
      data: [
        { userId: uid, eventoId: eventoRaduno.id, stato: "NON_RISPOSTO" },
        { userId: uid, eventoId: eventoRto.id, stato: "IN_DUBBIO" },
        { userId: uid, eventoId: eventoAllen.id, stato: "PRESENTE" },
      ],
    });
  }

  await prisma.designazione.create({
    data: {
      userId: simone.id,
      campionato: "Promozione",
      girone: "A",
      giornata: "18",
      ruolo: "Arbitro",
      squadraCasa: "Legnano FC",
      squadraTrasf: "Castellanza",
      dataGara: addDays(now, 7),
      luogo: "Legnano",
    },
  });

  await prisma.gara.create({
    data: {
      userId: simone.id,
      categoria: "Promozione",
      girone: "A",
      ruolo: "Arbitro",
      squadraCasa: "Legnano",
      squadraTrasf: "Saronno",
      dataGara: subDays(now, 30),
      risultato: "2-1",
      stagione: "2025-26",
    },
  });

  await prisma.newsTecnica.create({
    data: {
      titolo: "Nuove linee guida rigori",
      contenuto: "Aggiornamento interpretazione.",
      categoria: "Promozione",
      citazioni: "Simone Dattola",
    },
  });

  await prisma.notifica.create({
    data: {
      userId: simone.id,
      testo: "Nuova designazione in calendario",
      tipo: "DESIGNAZIONE",
      link: "/calendario",
    },
  });

  await prisma.traguardo.create({
    data: {
      userId: simone.id,
      tipo: "anniversario",
      data: subDays(now, 200),
      descrizione: "5 anni di tesseramento",
      icona: "🏅",
    },
  });

  await prisma.messaggio.create({
    data: {
      mittenteId: consiglio.id,
      destinatarioId: simone.id,
      testo: "Ciao Simone, confermi presenza al raduno?",
      letto: false,
    },
  });

  console.log("Seed completato.");
  console.log("Simone Dattola — codice 86178903 — password", defaultPassword("Simone", "Dattola"));
  console.log("Admin — codice 00000001 — password admin.demo");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
