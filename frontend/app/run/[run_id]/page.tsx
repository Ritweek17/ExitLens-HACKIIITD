import React from "react";
import { RunMonitor } from "@/components/RunMonitor";

interface RunPageProps {
  params: Promise<{
    run_id: string;
  }>;
}

export const metadata = {
  title: "Audit in Progress — ExitLens",
  description: "Live step-by-step audit streaming of subscription cancellation journey.",
};

export default async function RunPage({ params }: RunPageProps) {
  const resolvedParams = await params;
  const runId = resolvedParams.run_id;

  return (
    <div className="py-12 px-4 sm:px-6">
      <RunMonitor runId={runId} />
    </div>
  );
}
