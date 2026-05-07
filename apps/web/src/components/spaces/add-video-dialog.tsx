import type { RecallSpace } from "@recall/shared";
import type { ReactNode } from "react";
import { AddVideoModal } from "@/components/ingestion/add-video-modal";

type AddVideoDialogProps = {
  spaces: RecallSpace[];
  spaceId?: string;
  trigger?: ReactNode;
};

export function AddVideoDialog({ spaces, spaceId, trigger }: AddVideoDialogProps) {
  return <AddVideoModal spaces={spaces} spaceId={spaceId} trigger={trigger} />;
}
