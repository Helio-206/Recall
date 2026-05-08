"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BookOpen,
  Home,
  LogOut,
  Plus,
  Settings,
  Sparkles,
} from "lucide-react";

import { Logo } from "@/components/logo";
import { SearchTriggerButton } from "@/components/search/search-trigger-button";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";

const navItems = [
  { href: "/dashboard", label: "Home", icon: Home },
  { href: "/spaces", label: "Learning Spaces", icon: BookOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const logout = useAuthStore((state) => state.logout);

  return (
    <aside className="hidden min-h-screen w-72 shrink-0 border-r border-border bg-background/75 px-4 py-5 backdrop-blur-xl lg:flex lg:flex-col">
      <Logo />

      <SearchTriggerButton className="mt-5" />

      <div className="mt-7 grid gap-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex h-10 items-center gap-3 rounded-md px-3 text-sm text-muted transition-all duration-200 hover:bg-white/[0.06] hover:text-foreground",
                isActive && "bg-white/[0.07] text-foreground shadow-insetPanel",
              )}
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </div>

      <div className="mt-5 rounded-lg border border-border bg-surface/80 p-3 shadow-insetPanel">
        <div className="flex items-center gap-2 text-xs font-medium uppercase text-violet">
          <Sparkles className="size-3.5" />
          Phase 1
        </div>
        <p className="mt-2 text-sm leading-6 text-muted">Foundation build</p>
      </div>

      <div className="mt-auto grid gap-2">
        <Button variant="secondary" className="justify-start" asChild>
          <Link href="/spaces">
            <Plus />
            New Space
          </Link>
        </Button>
        <Button
          variant="ghost"
          className="justify-start"
          onClick={() => {
            logout();
            router.replace("/login");
          }}
        >
          <LogOut />
          Logout
        </Button>
      </div>
    </aside>
  );
}
