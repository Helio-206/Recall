import { Suspense } from "react";

import { AuthPanel } from "@/components/auth/auth-panel";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <AuthPanel mode="login" />
    </Suspense>
  );
}
