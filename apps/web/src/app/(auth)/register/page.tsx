import { Suspense } from "react";

import { AuthPanel } from "@/components/auth/auth-panel";

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <AuthPanel mode="register" />
    </Suspense>
  );
}
