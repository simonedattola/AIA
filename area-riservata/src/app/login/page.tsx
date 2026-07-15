"use client";

import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import toast from "react-hot-toast";

const schema = z.object({
  codice: z.string().min(1, "Inserisci il codice meccanografico"),
  password: z.string().min(1, "Inserisci la password"),
});

type Form = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Form>({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: Form) => {
    const res = await signIn("credentials", {
      redirect: false,
      codice: data.codice.trim(),
      password: data.password,
    });
    if (res?.error) {
      toast.error("Codice o password non validi");
      return;
    }
    toast.success("Accesso effettuato");
    router.push("/dashboard");
    router.refresh();
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-blue-900 to-blue-700 p-4">
      <div className="w-full max-w-md card">
        <h1 className="text-2xl font-bold text-blue-900">Area Riservata</h1>
        <p className="mt-1 text-sm text-slate-600">AIA Legnano — accesso associati</p>
        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
          <div>
            <label className="label">Codice meccanografico</label>
            <input
              className="input font-mono"
              inputMode="numeric"
              autoComplete="username"
              placeholder="es. 86178903"
              {...register("codice")}
            />
            {errors.codice && <p className="text-xs text-red-600">{errors.codice.message}</p>}
          </div>
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" autoComplete="current-password" {...register("password")} />
            {errors.password && <p className="text-xs text-red-600">{errors.password.message}</p>}
          </div>
          <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
            Accedi
          </button>
        </form>
        <p className="mt-4 rounded-lg bg-slate-100 p-3 text-xs text-slate-600">
          La password iniziale è <strong>nome.cognome</strong> (es. Simone Dattola → <code>simone.dattola</code>).
          Puoi cambiarla dal profilo dopo il primo accesso.
        </p>
        <p className="mt-2 text-center text-xs text-slate-500">
          Esempio: codice <strong>86178903</strong> — password <strong>simone.dattola</strong>
        </p>
      </div>
    </div>
  );
}
