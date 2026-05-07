import { Progress } from "@/components/ui/progress";

type ProgressBarProps = {
  value: number;
  label?: string;
};

export function ProgressBar({ value, label }: ProgressBarProps) {
  return (
    <div className="grid gap-2">
      {label && (
        <div className="flex items-center justify-between text-xs text-muted">
          <span>{label}</span>
          <span className="font-mono text-foreground">{value}%</span>
        </div>
      )}
      <Progress value={value} />
    </div>
  );
}
