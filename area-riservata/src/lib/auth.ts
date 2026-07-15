import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import bcrypt from "bcryptjs";
import { prisma } from "./prisma";

export const authOptions: NextAuthOptions = {
  session: { strategy: "jwt", maxAge: 30 * 24 * 60 * 60 },
  pages: {
    signIn: "/login",
  },
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        codice: { label: "Codice meccanografico", type: "text" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        const codice = credentials?.codice?.trim();
        const password = credentials?.password;
        if (!codice || !password) return null;

        const user = await prisma.user.findUnique({
          where: { codiceMeccanografico: codice },
        });
        if (!user) return null;

        const valid = await bcrypt.compare(password, user.passwordHash);
        if (!valid) return null;

        return {
          id: user.id,
          email: user.email ?? undefined,
          name: `${user.nome} ${user.cognome}`,
          ruolo: user.ruolo,
          foto: user.foto ?? undefined,
          codice: user.codiceMeccanografico,
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.ruolo = (user as { ruolo?: string }).ruolo;
        token.foto = (user as { foto?: string }).foto;
        token.codice = (user as { codice?: string }).codice;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.ruolo = token.ruolo as string;
        session.user.foto = token.foto as string | undefined;
        session.user.codice = token.codice as string | undefined;
      }
      return session;
    },
  },
};
