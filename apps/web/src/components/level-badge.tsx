import { Badge } from "@/components/ui/badge";

type LevelBadgeProps = {
  progress: number;
};

export function LevelBadge({ progress }: LevelBadgeProps) {
  if (progress >= 80) return <Badge variant="success">Advanced</Badge>;
  if (progress >= 40) return <Badge variant="warm">Building</Badge>;
  return <Badge variant="violet">Starting</Badge>;
}
