"use client";

import { useRef } from "react";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import type { RecallUser } from "@recall/shared";
import { apiFetch } from "@/lib/api";
import { getTokenFromCookie, useAuthStore } from "@/stores/auth-store";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { token, user, hasHydrated, setToken, setUser, logout } = useAuthStore();
  const [isChecking, setIsChecking] = useState(true);
  const [hydrationTimedOut, setHydrationTimedOut] = useState(false);
  const validatedTokenRef = useRef<string | null>(null);

  useEffect(() => {
    if (hasHydrated) {
      setHydrationTimedOut(false);
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setHydrationTimedOut(true);
    }, 1500);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [hasHydrated]);

  useEffect(() => {
    if (!hasHydrated && !hydrationTimedOut) return;

    const cookieToken = getTokenFromCookie();
    const activeToken = token ?? cookieToken;

    if (!activeToken) {
      validatedTokenRef.current = null;
      setIsChecking(false);
      router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      return;
    }

    if (!token && cookieToken) {
      setToken(cookieToken);
    }

    if (user && validatedTokenRef.current === activeToken) {
      setIsChecking(false);
      return;
    }

    setIsChecking(true);

    apiFetch<RecallUser>("/auth/me", { token: activeToken })
      .then((me) => {
        if (!token && cookieToken) {
          setToken(cookieToken);
        }
        validatedTokenRef.current = activeToken;
        setUser(me);
        setIsChecking(false);
      })
      .catch(() => {
        validatedTokenRef.current = null;
        logout();
        setIsChecking(false);
        router.replace(`/login?next=${encodeURIComponent(pathname)}`);
      });
  }, [hasHydrated, hydrationTimedOut, logout, pathname, router, setToken, setUser, token, user]);

  if ((!hasHydrated && !hydrationTimedOut) || isChecking) {
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
