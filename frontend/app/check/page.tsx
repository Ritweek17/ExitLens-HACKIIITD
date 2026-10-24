import React from "react";
import { CheckFrictionForm } from "@/components/CheckFrictionForm";

export const metadata = {
  title: "Start an Audit — ExitLens",
  description: "Examine the steps, retention prompts, and potential friction between an account and cancellation.",
};

export default function CheckPage() {
  return (
    <div className="py-12 px-4 sm:px-6 max-w-2xl mx-auto space-y-8">
      {/* Refined Form Header (Left-aligned, comfortable spacing) */}
      <div className="space-y-1.5">
        <h1 className="text-2xl sm:text-3xl font-serif font-bold text-[#191817] tracking-tight">
          Start an audit
        </h1>
        <p className="text-sm text-[#64615B] leading-relaxed">
          Examine the steps, retention prompts, and potential friction between an account and cancellation.
        </p>
      </div>

      {/* Main Audit Form Component */}
      <CheckFrictionForm />
    </div>
  );
}
