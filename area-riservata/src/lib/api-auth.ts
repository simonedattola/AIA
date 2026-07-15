import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";
import { authOptions } from "./auth";

export async function getApiSession() {
  return getServerSession(authOptions);
}

export async function requireApiUser() {
  const session = await getApiSession();
  if (!session?.user?.id) {
    return { error: NextResponse.json({ error: "Non autorizzato" }, { status: 401 }) };
  }
  return { session, userId: session.user.id };
}
