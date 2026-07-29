import { Logo } from "@/components/logo";

export default function Loading() {
  return (
    <div
      className="fixed inset-0 z-[90] flex items-center justify-center bg-background"
      role="status"
      aria-label="Loading page"
    >
      <div className="w-[min(280px,calc(100vw-48px))]">
        <Logo className="justify-center" />
        <div className="mt-7 h-px overflow-hidden bg-white/10">
          <div className="route-loading-bar h-full bg-primary" />
        </div>
      </div>
    </div>
  );
}
