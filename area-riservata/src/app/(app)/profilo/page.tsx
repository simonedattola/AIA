"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useSession } from "next-auth/react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";
import { apiFetch } from "@/lib/fetcher";
import { PageLoader } from "@/components/ui/PageLoader";

const schema = z.object({
  nome: z.string().min(2),
  cognome: z.string().min(2),
  biografia: z.string().optional(),
  telefono: z.string().optional(),
  emailVisibile: z.coerce.boolean(),
  telefonoVisibile: z.coerce.boolean(),
  currentPassword: z.string().optional(),
  password: z.string().optional(),
});

type Form = z.infer<typeof schema>;

type Profilo = {
  nome: string;
  cognome: string;
  email: string | null;
  foto: string | null;
  biografia: string | null;
  telefono: string | null;
  emailVisibile: boolean;
  telefonoVisibile: boolean;
  categoria: string | null;
};

function fotoSrc(url: string | null) {
  if (!url) return null;
  if (url.startsWith("http") || url.startsWith("blob:")) return url;
  return url;
}

export default function ProfiloPage() {
  const { status } = useSession();
  const [preview, setPreview] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: {
      emailVisibile: false,
      telefonoVisibile: false,
    },
  });

  useEffect(() => {
    if (status !== "authenticated") return;
    apiFetch<Profilo>("/api/profilo").then((p) => {
      if (!p) return;
      reset({
        nome: p.nome,
        cognome: p.cognome,
        biografia: p.biografia ?? "",
        telefono: p.telefono ?? "",
        emailVisibile: p.emailVisibile,
        telefonoVisibile: p.telefonoVisibile,
      });
      setPreview(fotoSrc(p.foto));
      setReady(true);
    });
  }, [status, reset]);

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const blob = URL.createObjectURL(file);
    setPreview(blob);
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/upload", { method: "POST", body: fd, credentials: "same-origin" });
    if (res.ok) {
      const { url: saved } = await res.json();
      setPreview(saved);
      toast.success("Foto aggiornata");
    } else {
      toast.error("Errore upload");
      setPreview(null);
    }
  };

  const onSubmit = async (data: Form) => {
    if (data.password && !data.currentPassword) {
      toast.error("Inserisci la password attuale");
      return;
    }
    const res = await fetch("/api/profilo", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(data),
    });
    if (res.ok) toast.success("Profilo aggiornato");
    else {
      const err = await res.json().catch(() => ({}));
      toast.error((err as { error?: string }).error || "Errore salvataggio");
    }
  };

  if (status === "loading" || !ready) return <PageLoader />;
  if (status !== "authenticated") return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-blue-900">Profilo personale</h1>

      <div className="card flex flex-col items-center gap-4 sm:flex-row">
        <div className="relative h-28 w-28 overflow-hidden rounded-full bg-slate-200">
          {preview ? (
            <Image src={preview} alt="Foto profilo" fill className="object-cover" unoptimized />
          ) : (
            <span className="flex h-full items-center justify-center text-4xl">👤</span>
          )}
        </div>
        <label className="btn-secondary cursor-pointer">
          Cambia foto
          <input type="file" accept="image/*" className="hidden" onChange={onUpload} />
        </label>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="label">Nome</label>
            <input className="input" {...register("nome")} />
          </div>
          <div>
            <label className="label">Cognome</label>
            <input className="input" {...register("cognome")} />
          </div>
        </div>
        <div>
          <label className="label">Biografia</label>
          <textarea className="input min-h-[100px]" {...register("biografia")} />
        </div>
        <div>
          <label className="label">Telefono</label>
          <input className="input" {...register("telefono")} />
        </div>
        <label className="flex min-h-[44px] items-center gap-2">
          <input type="checkbox" {...register("emailVisibile")} />
          Mostra email agli altri associati
        </label>
        <label className="flex min-h-[44px] items-center gap-2">
          <input type="checkbox" {...register("telefonoVisibile")} />
          Mostra telefono agli altri associati
        </label>
        <hr />
        <p className="text-sm font-medium">Cambia password</p>
        <div>
          <label className="label">Password attuale</label>
          <input className="input" type="password" autoComplete="current-password" {...register("currentPassword")} />
        </div>
        <div>
          <label className="label">Nuova password</label>
          <input className="input" type="password" autoComplete="new-password" {...register("password")} />
        </div>
        <button type="submit" className="btn-primary w-full sm:w-auto" disabled={isSubmitting}>
          Salva modifiche
        </button>
      </form>
    </div>
  );
}
