"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Home, Settings } from "lucide-react";

import { Logo } from "@/components/logo";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Home", icon: Home },
  { href: "/spaces", label: "Spaces", icon: BookOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/85 px-4 backdrop-blur-xl lg:hidden">
        <Logo />
      </header>
      <nav className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-3 rounded-lg border border-border bg-surface/95 p-1 shadow-premium backdrop-blur-xl lg:hidden">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex h-11 items-center justify-center gap-2 rounded-md text-xs font-medium text-muted transition-all",
                isActive && "bg-white/[0.08] text-foreground",
              )}
            >
              <Icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
