"use client";

import { useEffect } from "react";
import { FolderPlus, Plus } from "lucide-react";

import { AddVideoDialog } from "@/components/spaces/add-video-dialog";
import { CreateSpaceDialog } from "@/components/spaces/create-space-dialog";
import { LearningSpaceCard } from "@/components/spaces/learning-space-card";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth-store";
import { useSpaceStore } from "@/stores/space-store";

export default function SpacesPage() {
  const token = useAuthStore((state) => state.token);
  const { spaces, fetchSpaces, isLoading } = useSpaceStore();

  useEffect(() => {
    if (token) void fetchSpaces(token);
  }, [fetchSpaces, token]);

  return (
    <div className="grid gap-6">
      <header className="flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm text-muted">Organized curricula</p>
          <h1 className="mt-2 font-heading text-3xl font-semibold text-foreground sm:text-4xl">
            Learning Spaces
          </h1>
        </div>
        <div className="flex flex-wrap gap-2">
          {spaces.length > 0 && (
            <AddVideoDialog
              spaces={spaces}
              trigger={
                <Button variant="secondary">
                  <Plus />
                  Add Content
                </Button>
              }
            />
          )}
          <CreateSpaceDialog
            trigger={
              <Button>
                <FolderPlus />
                New Space
              </Button>
            }
          />
        </div>
      </header>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3].map((item) => (
            <div key={item} className="h-56 animate-pulse rounded-lg border border-border bg-surface/70" />
          ))}
        </div>
      ) : spaces.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {spaces.map((space) => (
            <LearningSpaceCard key={space.id} space={space} />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-border bg-surface/60 p-10 text-center">
          <div className="mx-auto grid size-12 place-items-center rounded-md border border-border bg-background/80 text-primary">
            <FolderPlus className="size-5" />
          </div>
          <h2 className="mt-4 font-heading text-xl font-semibold text-foreground">No spaces yet</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
            Build a learning path around a topic and start adding videos.
          </p>
          <CreateSpaceDialog trigger={<Button className="mt-5">Create Space</Button>} />
        </div>
      )}
    </div>
  );
}
