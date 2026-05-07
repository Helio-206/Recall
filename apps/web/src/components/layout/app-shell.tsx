import { AuthGate } from "@/components/auth/auth-gate";
import { MobileNav } from "@/components/layout/mobile-nav";
import { Sidebar } from "@/components/layout/sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <div className="flex min-h-screen bg-background/20">
        <Sidebar />
        <div className="min-w-0 flex-1 pb-24 lg:pb-0">
          <MobileNav />
          <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
            {children}
          </main>
        </div>
      </div>
    </AuthGate>
  );
}
