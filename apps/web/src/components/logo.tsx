import Image from "next/image";

import { cn } from "@/lib/utils";

type LogoProps = {
  compact?: boolean;
  className?: string;
};

export function Logo({ compact = false, className }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <Image
        src="/brand/recall-mark.png"
        alt=""
        width={40}
        height={40}
        priority
        className="size-9 rounded object-cover"
      />
      {!compact && (
        <span className="font-heading text-xl font-semibold text-foreground">Recall</span>
      )}
    </div>
  );
}
