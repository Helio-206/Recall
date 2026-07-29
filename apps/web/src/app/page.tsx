import type { Metadata } from "next";
import { cookies } from "next/headers";

import { LandingPage } from "@/components/marketing/landing-page";

export const metadata: Metadata = {
  title: "Recall - O seu sistema de aprendizagem para vídeos",
  description:
    "Transforme vídeos da internet em percursos de aprendizagem estruturados, transcrições legíveis e progresso contínuo.",
};

export default async function HomePage() {
  const cookieStore = await cookies();
  const isAuthenticated = Boolean(cookieStore.get("recall_token")?.value);

  return <LandingPage isAuthenticated={isAuthenticated} />;
}
