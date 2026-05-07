"use client";

import { FormEvent, useState } from "react";
import { FolderPlus } from "lucide-react";

import type { RecallSpace } from "@recall/shared";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuthStore } from "@/stores/auth-store";
import { useSpaceStore } from "@/stores/space-store";

type CreateSpaceDialogProps = {
  trigger?: React.ReactNode;
  onCreated?: (space: RecallSpace) => void;
};

export function CreateSpaceDialog({ trigger, onCreated }: CreateSpaceDialogProps) {
  const token = useAuthStore((state) => state.token);
  const createSpace = useSpaceStore((state) => state.createSpace);
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const space = await createSpace(token, { title, topic, description });
      onCreated?.(space);
      setTitle("");
      setTopic("");
      setDescription("");
      setOpen(false);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to create space.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button>
            <FolderPlus />
            New Space
          </Button>
        )}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Learning Space</DialogTitle>
          <DialogDescription>Give this path a clear shape before adding videos.</DialogDescription>
        </DialogHeader>
        <form className="grid gap-4" onSubmit={onSubmit}>
          <div className="grid gap-2">
            <Label htmlFor="space-title">Title</Label>
            <Input
              id="space-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="DevOps Engineering"
              required
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="space-topic">Topic</Label>
            <Input
              id="space-topic"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              placeholder="Infrastructure"
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="space-description">Description</Label>
            <Textarea
              id="space-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="A practical path through Linux, Docker, and Kubernetes."
            />
          </div>
          {error && (
            <div className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
              {error}
            </div>
          )}
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating" : "Create Space"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
