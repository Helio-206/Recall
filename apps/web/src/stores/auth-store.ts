"use client";

import type { AuthSession, RecallUser } from "@recall/shared";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

type AuthState = {
  token: string | null;
  user: RecallUser | null;
  hasHydrated: boolean;
  setSession: (session: AuthSession) => void;
  setUser: (user: RecallUser) => void;
  logout: () => void;
  setHasHydrated: (hasHydrated: boolean) => void;
};

const tokenCookie = "recall_token";

function writeTokenCookie(token: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${tokenCookie}=${encodeURIComponent(
    token,
  )}; path=/; max-age=604800; SameSite=Lax`;
}

function clearTokenCookie() {
  if (typeof document === "undefined") return;
  document.cookie = `${tokenCookie}=; path=/; max-age=0; SameSite=Lax`;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      hasHydrated: false,
      setSession: (session) => {
        writeTokenCookie(session.access_token);
        set({ token: session.access_token, user: session.user });
      },
      setUser: (user) => set({ user }),
      logout: () => {
        clearTokenCookie();
        set({ token: null, user: null });
      },
      setHasHydrated: (hasHydrated) => set({ hasHydrated }),
    }),
    {
      name: "recall-auth",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token, user: state.user }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
      },
    },
  ),
);
