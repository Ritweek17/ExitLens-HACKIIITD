import React from "react";
import { ReportView } from "@/components/ReportView";

interface ReportPageProps {
  params: Promise<{
    run_id: string;
  }>;
}

export const metadata = {
  title: "Audit Evidence Report — ExitLens",
  description: "Evidence-linked friction assessment and CCPA dark pattern analysis.",
};

export default async function ReportPage({ params }: ReportPageProps) {
  const resolvedParams = await params;
  const runId = resolvedParams.run_id;

  return (
    <div className="py-12 px-4 sm:px-6">
      <ReportView runId={runId} />
    </div>
  );
}
