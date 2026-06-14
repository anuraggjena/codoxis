"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { setToken } from "@/lib/auth";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) {
      setToken(token);
      router.replace("/dashboard");
      return;
    }
    router.replace("/login?error=github_auth_failed");
  }, [router, searchParams]);

  return (
    <p className="text-sm text-zinc-500">Signing you in…</p>
  );
}

export default function AuthCallbackPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <Suspense fallback={<p className="text-sm text-zinc-500">Signing you in…</p>}>
        <AuthCallbackContent />
      </Suspense>
    </div>
  );
}
