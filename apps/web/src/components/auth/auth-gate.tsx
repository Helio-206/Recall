"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import type { RecallUser } from "@recall/shared";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { token, user, hasHydrated, setUser, logout } = useAuthStore();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (!hasHydrated) return;

    if (!token) {
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }

    if (user) {
      setIsChecking(false);
      return;
    }

    apiFetch<RecallUser>("/auth/me", { token })
      .then((me) => {
        setUser(me);
        setIsChecking(false);
      })
      .catch(() => {
        logout();
        router.replace("/login");
      });
  }, [hasHydrated, logout, pathname, router, setUser, token, user]);

  if (!hasHydrated || isChecking) {
    return (
      <div className="grid min-h-screen place-items-center bg-background text-muted">
        <div className="h-6 w-40 overflow-hidden rounded-full bg-white/[0.06]">
          <div className="h-full w-1/2 animate-pulse rounded-full bg-primary/50" />
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
