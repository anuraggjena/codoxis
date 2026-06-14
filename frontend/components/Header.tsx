"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearToken } from "@/lib/auth";

export default function Header() {
  const router = useRouter();

  function logout() {
    clearToken();
    router.push("/login");
  }

  return (
    <header className="border-b border-zinc-200 bg-white px-6 py-4 dark:border-zinc-800 dark:bg-zinc-950">
      <div className="mx-auto flex max-w-5xl items-center justify-between">
        <Link href="/dashboard" className="text-lg font-semibold tracking-tight">
          Codoxis
        </Link>
        <nav className="flex items-center gap-4 text-sm">
          <Link href="/dashboard" className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400">
            Projects
          </Link>
          <button
            type="button"
            onClick={logout}
            className="rounded-md border border-zinc-300 px-3 py-1.5 hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
          >
            Log out
          </button>
        </nav>
      </div>
    </header>
  );
}
