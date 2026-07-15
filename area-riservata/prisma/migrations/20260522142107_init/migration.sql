-- CreateTable
CREATE TABLE "User" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "codiceMeccanografico" TEXT NOT NULL,
    "email" TEXT,
    "passwordHash" TEXT NOT NULL,
    "nome" TEXT NOT NULL,
    "cognome" TEXT NOT NULL,
    "ruolo" TEXT NOT NULL DEFAULT 'ASSOCIATO',
    "foto" TEXT,
    "biografia" TEXT,
    "telefono" TEXT,
    "emailVisibile" BOOLEAN NOT NULL DEFAULT false,
    "telefonoVisibile" BOOLEAN NOT NULL DEFAULT false,
    "categoria" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "Evento" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "titolo" TEXT NOT NULL,
    "tipo" TEXT NOT NULL,
    "dataInizio" DATETIME NOT NULL,
    "dataFine" DATETIME,
    "luogo" TEXT,
    "note" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Designazione" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "campionato" TEXT NOT NULL,
    "girone" TEXT,
    "giornata" TEXT,
    "ruolo" TEXT NOT NULL,
    "squadraCasa" TEXT NOT NULL,
    "squadraTrasf" TEXT NOT NULL,
    "dataGara" DATETIME NOT NULL,
    "luogo" TEXT,
    "stato" TEXT NOT NULL DEFAULT 'assegnata',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Designazione_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "RTO" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "titolo" TEXT NOT NULL,
    "data" DATETIME NOT NULL,
    "luogo" TEXT,
    "descrizione" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "DocumentoTecnico" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "titolo" TEXT NOT NULL,
    "tipo" TEXT NOT NULL,
    "url" TEXT,
    "filePath" TEXT,
    "descrizione" TEXT,
    "rtoId" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "DocumentoTecnico_rtoId_fkey" FOREIGN KEY ("rtoId") REFERENCES "RTO" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Quiz" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "titolo" TEXT NOT NULL,
    "descrizione" TEXT,
    "url" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Gara" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "categoria" TEXT NOT NULL,
    "girone" TEXT,
    "ruolo" TEXT NOT NULL,
    "squadraCasa" TEXT NOT NULL,
    "squadraTrasf" TEXT NOT NULL,
    "dataGara" DATETIME NOT NULL,
    "risultato" TEXT,
    "stagione" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "NewsTecnica" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "titolo" TEXT NOT NULL,
    "contenuto" TEXT NOT NULL,
    "citazioni" TEXT,
    "categoria" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Comunicazione" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "titolo" TEXT NOT NULL,
    "contenuto" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "Notifica" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "testo" TEXT NOT NULL,
    "tipo" TEXT NOT NULL,
    "link" TEXT,
    "letta" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Notifica_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Traguardo" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "tipo" TEXT NOT NULL,
    "data" DATETIME NOT NULL,
    "descrizione" TEXT NOT NULL,
    "icona" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Traguardo_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Media" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "titolo" TEXT NOT NULL,
    "url" TEXT NOT NULL,
    "eventoId" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Media_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Messaggio" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "mittenteId" TEXT NOT NULL,
    "destinatarioId" TEXT NOT NULL,
    "testo" TEXT NOT NULL,
    "letto" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Messaggio_mittenteId_fkey" FOREIGN KEY ("mittenteId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "Messaggio_destinatarioId_fkey" FOREIGN KEY ("destinatarioId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Preferito" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "tipo" TEXT NOT NULL,
    "elementoId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Preferito_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "CalendarioPersonale" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "eventoId" TEXT NOT NULL,
    "reminder" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "CalendarioPersonale_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "CalendarioPersonale_eventoId_fkey" FOREIGN KEY ("eventoId") REFERENCES "Evento" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "PresenzaEvento" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "eventoId" TEXT NOT NULL,
    "stato" TEXT NOT NULL DEFAULT 'NON_RISPOSTO',
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "PresenzaEvento_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "PresenzaEvento_eventoId_fkey" FOREIGN KEY ("eventoId") REFERENCES "Evento" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "SuccessoPersonale" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "titolo" TEXT NOT NULL,
    "contenuto" TEXT NOT NULL,
    "data" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "SuccessoPersonale_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "User_codiceMeccanografico_key" ON "User"("codiceMeccanografico");

-- CreateIndex
CREATE INDEX "Gara_userId_stagione_idx" ON "Gara"("userId", "stagione");

-- CreateIndex
CREATE UNIQUE INDEX "Preferito_userId_tipo_elementoId_key" ON "Preferito"("userId", "tipo", "elementoId");

-- CreateIndex
CREATE UNIQUE INDEX "CalendarioPersonale_userId_eventoId_key" ON "CalendarioPersonale"("userId", "eventoId");

-- CreateIndex
CREATE UNIQUE INDEX "PresenzaEvento_userId_eventoId_key" ON "PresenzaEvento"("userId", "eventoId");
