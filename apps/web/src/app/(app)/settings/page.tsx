"use client";

import { useRouter } from "next/navigation";
import { LogOut, ShieldCheck, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/stores/auth-store";

export default function SettingsPage() {
  const router = useRouter();
  const { user, logout } = useAuthStore();

  return (
    <div className="grid gap-6">
      <header className="border-b border-border pb-6">
        <p className="text-sm text-muted">Workspace preferences</p>
        <h1 className="mt-2 font-heading text-3xl font-semibold text-foreground sm:text-4xl">
          Settings
        </h1>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <section className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-md border border-border bg-background/80 text-primary">
              <UserRound className="size-5" />
            </span>
            <div>
              <h2 className="font-heading text-lg font-semibold text-foreground">Profile</h2>
              <p className="text-sm text-muted">Account identity</p>
            </div>
          </div>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="grid gap-2">
              <Label htmlFor="settings-name">Name</Label>
              <Input id="settings-name" value={user?.name || ""} readOnly />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="settings-email">Email</Label>
              <Input id="settings-email" value={user?.email || ""} readOnly />
            </div>
          </div>
        </section>

        <aside className="rounded-lg border border-border bg-surface/80 p-5 shadow-insetPanel">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-md border border-success/35 bg-success/10 text-success">
              <ShieldCheck className="size-5" />
            </span>
            <div>
              <h2 className="font-heading text-lg font-semibold text-foreground">Session</h2>
              <p className="text-sm text-muted">JWT authenticated</p>
            </div>
          </div>
          <Button
            variant="danger"
            className="mt-6 w-full"
            onClick={() => {
              logout();
              router.replace("/login");
            }}
          >
            <LogOut />
            Logout
          </Button>
        </aside>
      </div>
    </div>
  );
}
