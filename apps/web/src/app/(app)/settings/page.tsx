"use client";

import { useRouter } from "next/navigation";
import { LogOut, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/auth-store";

export default function SettingsPage() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  return (
    <div className="mx-auto max-w-2xl grid gap-8 py-2">
      <header>
        <h1 className="font-heading text-2xl font-semibold text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted">Manage your account</p>
      </header>

      <section className="rounded-lg border border-border bg-surface/80 p-6 shadow-insetPanel">
        <div className="flex items-center gap-3 mb-6">
          <span className="grid size-9 place-items-center rounded-full border border-border bg-background/80 text-primary">
            <UserRound className="size-4" />
          </span>
          <h2 className="font-medium text-foreground">Profile</h2>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="grid gap-1.5">
            <Label htmlFor="settings-name">Name</Label>
            <Input id="settings-name" value={user?.name || ""} readOnly />
          </div>
          <div className="grid gap-1.5">
            <Label htmlFor="settings-email">Email</Label>
            <Input id="settings-email" value={user?.email || ""} readOnly />
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-border bg-surface/80 p-6 shadow-insetPanel">
        <h2 className="font-medium text-foreground mb-1">Sign out</h2>
        <p className="text-sm text-muted mb-5">You will be returned to the login screen.</p>
        <Button
          variant="danger"
          onClick={() => {
            logout();
            router.replace("/login");
          }}
        >
          <LogOut />
          Sign out
        </Button>
      </section>
    </div>
  );
}
