"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { signOut, useSession } from "next-auth/react";
import { useState } from "react";
import { navItems } from "./nav";
import { NotificationDropdown } from "./NotificationDropdown";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data: session } = useSession();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const NavLinks = ({ onClick }: { onClick?: () => void }) => (
    <>
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          onClick={onClick}
          className={cn(
            "flex min-h-[44px] items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium",
            pathname === item.href
              ? "bg-blue-900 text-white"
              : "text-slate-700 hover:bg-slate-100"
          )}
        >
          <span>{item.icon}</span>
          {item.label}
        </Link>
      ))}
      {(session?.user?.ruolo === "ADMIN" || session?.user?.ruolo === "OSSERVATORE") && (
        <Link
          href="/admin/eventi"
          onClick={onClick}
          className={cn(
            "flex min-h-[44px] items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium",
            pathname.startsWith("/admin") ? "bg-amber-600 text-white" : "text-slate-700 hover:bg-slate-100"
          )}
        >
          <span>⚙️</span>
          Admin
        </Link>
      )}
    </>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-white px-4 lg:pl-64">
        <button
          type="button"
          className="btn-secondary lg:hidden"
          onClick={() => setDrawerOpen(true)}
          aria-label="Menu"
        >
          ☰
        </button>
        <div className="flex flex-1 items-center justify-between gap-4 lg:justify-end">
          <span className="text-sm font-semibold text-blue-900 lg:hidden">AIA Legnano</span>
          <div className="flex items-center gap-2">
            <NotificationDropdown />
            <span className="hidden text-sm text-slate-600 sm:inline">{session?.user?.name}</span>
            <button type="button" className="btn-secondary text-xs" onClick={() => signOut({ callbackUrl: "/login" })}>
              Esci
            </button>
          </div>
        </div>
      </header>

      <aside className="fixed left-0 top-0 z-20 hidden h-full w-64 flex-col border-r bg-white p-4 lg:flex">
        <div className="mb-6 px-2">
          <h1 className="text-lg font-bold text-blue-900">AIA Legnano</h1>
          <p className="text-xs text-slate-500">Area riservata associati</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          <NavLinks />
        </nav>
      </aside>

      {drawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setDrawerOpen(false)} />
          <aside className="absolute left-0 top-0 h-full w-72 bg-white p-4 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <span className="font-bold text-blue-900">Menu</span>
              <button type="button" className="btn-secondary" onClick={() => setDrawerOpen(false)}>
                ✕
              </button>
            </div>
            <nav className="flex flex-col gap-1">
              <NavLinks onClick={() => setDrawerOpen(false)} />
            </nav>
          </aside>
        </div>
      )}

      <main className="mx-auto max-w-screen-xl px-4 py-6 lg:pl-64">{children}</main>
    </div>
  );
}
