import { NextResponse } from "next/server";

/** Registrazione disabilitata: account creati da admin (codice meccanografico). */
export async function POST() {
  return NextResponse.json(
    { error: "Registrazione non disponibile. Contatta la sezione per il codice meccanografico." },
    { status: 403 }
  );
}
