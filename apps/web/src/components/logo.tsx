import { cn } from "@/lib/utils";

type LogoProps = {
  compact?: boolean;
  className?: string;
};

export function Logo({ compact = false, className }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div className="relative grid size-10 place-items-center overflow-hidden rounded-2xl border border-violet/30 bg-[linear-gradient(135deg,#B97AFF,#6B44F2_48%,#2F6BFF)] shadow-[0_14px_40px_rgba(120,79,255,0.28)]">
        <svg viewBox="0 0 48 48" aria-hidden="true" className="size-9">
          <path
            d="M26.4 9.7c6.9 0 12.4 5.6 12.4 12.4 0 2.6-.8 5.1-2.2 7.1 2.7 1.1 4.4 3.2 4.4 5.9 0 3.8-3.2 6.6-7.5 6.6H21.7C13.6 41.7 7 35.1 7 27S13.6 12.3 21.7 12.3c1 0 2 .1 3 .3.5-1.7 1.1-2.9 1.7-2.9Z"
            fill="#07070B"
          />
          <path
            d="M30.4 18.8c2.6 0 4.7 2.1 4.7 4.7 0 .9-.2 1.7-.7 2.4"
            fill="none"
            stroke="#2B1C3F"
            strokeLinecap="round"
            strokeWidth="2"
          />
        </svg>
      </div>
      {!compact && (
        <span className="font-heading text-xl font-semibold text-foreground">Recall</span>
      )}
    </div>
  );
}
