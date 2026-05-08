import type { Metadata } from "next";

import { LandingPage } from "@/components/marketing/landing-page";

export const metadata: Metadata = {
  title: "Recall | Your second brain for online learning",
  description:
    "Recall turns scattered internet videos into organized notes, transcripts, summaries, and structured learning paths.",
};

export default function HomePage() {
  return <LandingPage />;
}
