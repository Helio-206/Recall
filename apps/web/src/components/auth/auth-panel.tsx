"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
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

export function AuthPanel({ mode }: AuthPanelProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setSession = useAuthStore((state) => state.setSession);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isRegister = mode === "register";

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
            Learning OS
          </div>
          <h1 className="font-heading text-5xl font-semibold leading-tight text-foreground">
            Recall
          </h1>
          <p className="mt-5 max-w-lg text-lg leading-8 text-muted">
            The OS for self-learning on the internet.
          </p>
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
