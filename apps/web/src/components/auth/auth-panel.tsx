"use client";

import gsap from "gsap";
import { ArrowLeft, ArrowRight, Eye, EyeOff, LockKeyhole, Mail, UserRound } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useLayoutEffect, useRef, useState } from "react";

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
  const authRootRef = useRef<HTMLDivElement | null>(null);
  const googleButtonRef = useRef<HTMLDivElement | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [googleError, setGoogleError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGoogleSubmitting, setIsGoogleSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const isRegister = mode === "register";

  useLayoutEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion || !authRootRef.current) return;

    const context = gsap.context(() => {
      gsap
        .timeline({ defaults: { ease: "power3.out" } })
        .from("[data-auth-visual]", { opacity: 0, duration: 0.7 })
        .from(
          "[data-auth-form] > *",
          {
            y: 18,
            opacity: 0,
            duration: 0.55,
            stagger: 0.06,
          },
          "-=0.35",
        );
    }, authRootRef);

    return () => context.revert();
  }, [mode]);

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
    <div
      ref={authRootRef}
      className="grid min-h-screen grid-cols-1 bg-background lg:grid-cols-[minmax(0,1.12fr)_minmax(480px,0.88fr)]"
    >
      <section
        data-auth-visual
        className="relative hidden min-h-screen overflow-hidden border-r border-border bg-surface lg:flex lg:flex-col"
      >
        <div className="relative z-10 flex items-center justify-between p-8">
          <Link href="/" aria-label="Recall home">
            <Logo />
          </Link>
          <span className="font-mono text-[10px] uppercase text-muted">Learning OS / 01</span>
        </div>

        <div className="relative z-10 mx-auto mt-auto w-full max-w-3xl px-8 pb-8">
          <div className="mb-8 max-w-xl">
            <p className="font-mono text-xs uppercase text-primary">Continue with context</p>
            <h1 className="mt-4 font-heading text-4xl font-semibold leading-tight xl:text-5xl">
              Your next lesson is already waiting.
            </h1>
            <p className="mt-4 max-w-lg text-base leading-7 text-muted">
              Organized paths, readable transcripts, and progress that stays with you.
            </p>
          </div>
          <div className="overflow-hidden border border-border bg-background p-1 shadow-premium">
            <Image
              src="/product/study-transcript.png"
              alt="Recall study workspace"
              width={1440}
              height={1024}
              priority
              className="h-auto w-full"
            />
          </div>
        </div>
      </section>

      <main className="relative flex min-h-screen items-center justify-center px-5 py-12 sm:px-10">
        <Link
          href="/"
          className="absolute left-5 top-5 flex items-center gap-2 text-sm text-muted transition-colors hover:text-foreground sm:left-8 sm:top-8"
        >
          <ArrowLeft className="size-4" />
          Back to home
        </Link>

        <div data-auth-form className="w-full max-w-[420px]">
          <Logo className="mb-12 lg:hidden" />

          <div>
            <p className="font-mono text-[11px] uppercase text-primary">
              {isRegister ? "Create account" : "Sign in"}
            </p>
            <h2 className="mt-3 font-heading text-3xl font-semibold text-foreground">
              {isRegister ? "Build your learning system" : "Welcome back"}
            </h2>
            <p className="mt-3 text-sm leading-6 text-muted">
              {isRegister
                ? "Create a focused home for every course and lesson."
                : "Pick up exactly where you left off."}
            </p>
          </div>

          <form className="mt-9 grid gap-5" onSubmit={onSubmit}>
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
              <div className="relative">
                <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="pl-10 pr-11"
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  minLength={isRegister ? 8 : undefined}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute right-1 top-1/2 flex size-9 -translate-y-1/2 items-center justify-center text-muted transition-colors hover:text-foreground"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
                {error}
              </div>
            )}

            <Button type="submit" size="lg" className="mt-1 w-full" disabled={isSubmitting}>
              {isSubmitting ? "Opening workspace..." : isRegister ? "Create account" : "Sign in"}
              <ArrowRight />
            </Button>
          </form>

          {!isRegister && (googleClientId || googleError) ? (
            <div className="mt-5 grid gap-3">
              <div className="text-center text-xs uppercase tracking-[0.18em] text-muted">Or</div>
              {googleClientId ? (
                <div className="flex justify-center">
                  <div ref={googleButtonRef} className="min-h-11" />
                </div>
              ) : null}
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

          <p className="mt-8 text-center text-sm text-muted">
            {isRegister ? "Already have an account?" : "New to Recall?"}{" "}
            <Link
              href={isRegister ? "/login" : "/register"}
              className="font-medium text-foreground underline-offset-4 hover:underline"
            >
              {isRegister ? "Sign in" : "Create an account"}
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}
