"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";
import { ArrowRight, Mail, UserRound } from "lucide-react";

import type { AuthSession } from "@recall/shared";
import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";

type AuthPanelProps = {
  mode: "login" | "register";
};

type GoogleCredentialResponse = {
  credential?: string;
};

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: GoogleCredentialResponse) => void;
          }) => void;
          renderButton: (
            element: HTMLElement,
            options: {
              type?: "standard" | "icon";
              theme?: "outline" | "filled_blue" | "filled_black";
              size?: "large" | "medium" | "small";
              text?: "signin_with" | "signup_with" | "continue_with" | "signin";
              shape?: "rectangular" | "pill" | "circle" | "square";
              width?: number;
            },
          ) => void;
        };
      };
    };
  }
}

export function AuthPanel({ mode }: AuthPanelProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setSession = useAuthStore((state) => state.setSession);
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID?.trim() || "";
  const googleButtonRef = useRef<HTMLDivElement | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [googleError, setGoogleError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false);
  const isRegister = mode === "register";

  useEffect(() => {
    if (isRegister || !googleClientId) return;

    let isCancelled = false;
    const scriptId = "google-identity-services";

    const initializeGoogle = () => {
      if (isCancelled || !window.google?.accounts?.id || !googleButtonRef.current) return;

      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async (response) => {
          const credential = response.credential?.trim();
          if (!credential) {
            setGoogleError("Google did not return an ID token.");
            return;
          }

          setGoogleError(null);
          setError(null);
          setIsGoogleSubmitting(true);
          try {
            const session = await apiFetch<AuthSession>("/auth/google", {
              method: "POST",
              body: JSON.stringify({ id_token: credential }),
            });
            setSession(session);
            router.replace(searchParams.get("next") || "/dashboard");
          } catch (requestError) {
            setGoogleError(
              requestError instanceof Error
                ? requestError.message
                : "Google authentication failed.",
            );
          } finally {
            setIsGoogleSubmitting(false);
          }
        },
      });

      googleButtonRef.current.innerHTML = "";
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        type: "standard",
        theme: "outline",
        size: "large",
        text: "signin_with",
        shape: "pill",
        width: 360,
      });
    };

    if (window.google?.accounts?.id) {
      initializeGoogle();
      return () => {
        isCancelled = true;
      };
    }

    const existingScript = document.getElementById(scriptId) as HTMLScriptElement | null;
    if (existingScript) {
      existingScript.addEventListener("load", initializeGoogle, { once: true });
      return () => {
        isCancelled = true;
      };
    }

    const script = document.createElement("script");
    script.id = scriptId;
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.addEventListener("load", initializeGoogle, { once: true });
    document.head.appendChild(script);

    return () => {
      isCancelled = true;
    };
  }, [googleClientId, isRegister, router, searchParams, setSession]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const session = await apiFetch<AuthSession>(isRegister ? "/auth/register" : "/auth/login", {
        method: "POST",
        body: JSON.stringify(isRegister ? { name, email, password } : { email, password }),
      });
      setSession(session);
      router.replace(searchParams.get("next") || "/dashboard");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen grid-cols-1 bg-background lg:grid-cols-[minmax(0,0.95fr)_minmax(520px,1fr)]">
      <section className="hidden border-r border-border bg-background/80 p-8 lg:flex lg:flex-col">
        <Logo />
        <div className="mt-auto max-w-xl">
          <div className="mb-8 inline-flex rounded-md border border-violet/30 bg-violet/10 px-3 py-1 text-xs font-medium uppercase text-violet">
            Developer MVP
          </div>
          <h1 className="font-heading text-5xl font-semibold leading-tight text-foreground">
            Recall
          </h1>
          <p className="mt-5 max-w-lg text-lg leading-8 text-muted">
            Build focused learning spaces from technical videos, searchable transcripts, and AI notes.
          </p>
          <div className="mt-6 rounded-md border border-border bg-surface/70 p-4 text-sm leading-6 text-muted">
            MVP scope now supports YouTube and Coursera sources. Create a space, ingest content, and keep technical learning organized across transcripts, notes, and summaries.
          </div>
        </div>
      </section>

      <main className="flex min-h-screen items-center justify-center px-4 py-10">
        <div className="w-full max-w-md rounded-lg border border-border bg-surface/90 p-6 shadow-premium backdrop-blur-xl sm:p-8">
          <Logo className="lg:hidden" />
          <div className="mt-8 lg:mt-0">
            <h2 className="font-heading text-2xl font-semibold text-foreground">
              {isRegister ? "Create your workspace" : "Welcome back"}
            </h2>
            <p className="mt-2 text-sm leading-6 text-muted">
              {isRegister
                ? "Start organizing your learning spaces."
                : "Continue building your learning system."}
            </p>
          </div>

          {!isRegister ? (
            <div className="mt-6 rounded-md border border-border bg-background/60 p-4 text-sm leading-6 text-muted">
              Recall organizes technical study into spaces with searchable transcripts, AI summaries, and timestamped notes.
            </div>
          ) : null}

          <form className="mt-7 grid gap-4" onSubmit={onSubmit}>
            {isRegister && (
              <div className="grid gap-2">
                <Label htmlFor="name">Name</Label>
                <div className="relative">
                  <UserRound className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
                  <Input
                    id="name"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    className="pl-10"
                    autoComplete="name"
                    required
                  />
                </div>
              </div>
            )}

            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="pl-10"
                  autoComplete="email"
                  required
                />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete={isRegister ? "new-password" : "current-password"}
                minLength={isRegister ? 8 : undefined}
                required
              />
            </div>

            {error && (
              <div className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
                {error}
              </div>
            )}

            <Button type="submit" className="mt-2 w-full" disabled={isSubmitting}>
              {isSubmitting ? "Working" : isRegister ? "Create account" : "Login"}
              <ArrowRight />
            </Button>
          </form>

          {!isRegister ? (
            <div className="mt-5 grid gap-3">
              <div className="text-center text-xs uppercase tracking-[0.18em] text-muted">Or</div>
              {googleClientId ? (
                <div className="flex justify-center">
                  <div ref={googleButtonRef} className="min-h-11" />
                </div>
              ) : (
                <div className="rounded-md border border-border bg-background/60 px-3 py-2 text-center text-sm text-muted">
                  Google login unavailable: set NEXT_PUBLIC_GOOGLE_CLIENT_ID and GOOGLE_OAUTH_CLIENT_IDS.
                </div>
              )}
              {googleError ? (
                <div className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
                  {googleError}
                </div>
              ) : null}
              {isGoogleSubmitting ? (
                <div className="text-center text-xs text-muted">Validating Google account...</div>
              ) : null}
            </div>
          ) : null}

          <p className="mt-6 text-center text-sm text-muted">
            {isRegister ? "Already have an account?" : "New to Recall?"}{" "}
            <Link
              href={isRegister ? "/login" : "/register"}
              className="font-medium text-foreground underline-offset-4 hover:underline"
            >
              {isRegister ? "Login" : "Create account"}
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
