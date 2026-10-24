import React from "react";
import Link from "next/link";
import { ShieldCheck, ArrowRight } from "lucide-react";
import { StorytellingSection } from "@/components/StorytellingSection";

export default function HomePage() {
  return (
    <div className="pb-20">
      {/* Hero Section */}
      <section
        id="hero"
        className="w-full pt-8 sm:pt-10 md:pt-12 px-4 sm:px-6 scroll-mt-24 sm:scroll-mt-28"
      >
        <div className="w-full max-w-3xl mx-auto flex flex-col items-center text-center space-y-4 sm:space-y-5">
          {/* Top Pill Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium text-[#191817] bg-[#F3F1EA] border border-[#E8E5DC]">
            <ShieldCheck className="w-3.5 h-3.5 text-[#047857]" />
            <span>Independent Subscription Journey Auditing</span>
          </div>

          {/* Main Headline with balanced line breaks and burgundy accent on "cancellation." */}
          <h1 className="w-full text-4xl sm:text-5xl md:text-[3.25rem] lg:text-[3.75rem] font-serif font-bold text-[#191817] tracking-tight leading-[1.14] text-center">
            Find the friction in<br className="hidden sm:inline" /> subscription{" "}
            <span className="text-[#9F1239]">cancellation.</span>
          </h1>

          {/* Supporting Copy */}
          <p className="w-full max-w-2xl mx-auto text-base sm:text-lg text-[#64615B] leading-relaxed font-sans text-center">
            Understand how difficult it is to cancel a subscription with a structured, evidence-based journey audit. We document every obstacle and stop before the final cancellation.
          </p>

          {/* Hero CTAs */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3.5 w-full sm:w-auto">
            <Link
              href="/check"
              className="group w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-lg text-sm font-semibold text-white bg-[#191817] hover:bg-[#2C2A28] active:bg-[#141312] transition-all duration-200 shadow-sm hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] focus-visible:ring-offset-2"
            >
              <span>Check a Subscription</span>
              <ArrowRight className="w-4 h-4 ml-2 transition-transform duration-200 ease-out group-hover:translate-x-1 motion-reduce:transform-none" />
            </Link>
            <Link
              href="/how-it-works"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-lg text-sm font-semibold text-[#191817] bg-[#F3F1EA] hover:bg-[#EAE7DD] border border-[#E8E5DC] transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] focus-visible:ring-offset-2"
            >
              <span>How It Works</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Real-Life Scenario Storytelling Section (Separated by 70-90px on desktop) */}
      <section
        id="scenario"
        className="mt-12 sm:mt-16 md:mt-20 lg:mt-[5.25rem] px-4 sm:px-6 max-w-5xl mx-auto scroll-mt-24 sm:scroll-mt-28"
      >
        <StorytellingSection />
      </section>

      {/* How It Works Section */}
      <section
        id="how-it-works"
        className="mt-16 sm:mt-20 lg:mt-24 px-4 sm:px-6 max-w-5xl mx-auto scroll-mt-24 sm:scroll-mt-28"
      >
        <div className="text-center max-w-2xl mx-auto space-y-2.5 sm:space-y-3 mb-8 sm:mb-10">
          <span className="text-xs font-semibold uppercase tracking-wider text-[#8C8780] block">
            The Audit Workflow
          </span>
          <h2 className="text-3xl sm:text-4xl font-serif font-bold text-[#191817] tracking-tight">
            How ExitLens audits an exit path
          </h2>
          <p className="text-sm text-[#64615B] leading-relaxed">
            Our automated runner navigates standard web interfaces just as a consumer would, recording evidence at each turn.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 lg:gap-6 items-stretch">
          {/* Step 1 */}
          <div className="flex flex-col h-full exitlens-card p-6 bg-white border border-[#E8E5DC] space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] flex items-center justify-center text-sm font-serif font-bold text-[#191817] shrink-0">
              01
            </div>
            <h3 className="text-base font-semibold text-[#191817] leading-snug">
              Select Service &amp; Confirm
            </h3>
            <p className="text-xs sm:text-sm text-[#64615B] leading-relaxed flex-1">
              Choose an online subscription service and confirm that you have authorization and an approved dedicated test account.
            </p>
          </div>

          {/* Step 2 */}
          <div className="flex flex-col h-full exitlens-card p-6 bg-white border border-[#E8E5DC] space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] flex items-center justify-center text-sm font-serif font-bold text-[#191817] shrink-0">
              02
            </div>
            <h3 className="text-base font-semibold text-[#191817] leading-snug">
              Observe Journey &amp; Stream
            </h3>
            <p className="text-xs sm:text-sm text-[#64615B] leading-relaxed flex-1">
              The automated runner steps through navigation menus, records redirects, and captures direct evidence without storing credentials.
            </p>
          </div>

          {/* Step 3 */}
          <div className="flex flex-col h-full exitlens-card p-6 bg-white border border-[#E8E5DC] space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] flex items-center justify-center text-sm font-serif font-bold text-[#191817] shrink-0">
              03
            </div>
            <h3 className="text-base font-semibold text-[#191817] leading-snug">
              Inspect Verified Report
            </h3>
            <p className="text-xs sm:text-sm text-[#64615B] leading-relaxed flex-1">
              Review calculated friction scores, evidence-linked steps, and candidate dark pattern correlations under India&apos;s CCPA 2023 regulations.
            </p>
          </div>
        </div>
      </section>

      {/* Friction Categories Monitored */}
      <section
        id="taxonomy"
        className="mt-16 sm:mt-20 lg:mt-24 px-4 sm:px-6 max-w-5xl mx-auto scroll-mt-24 sm:scroll-mt-28"
      >
        <div className="exitlens-card p-8 sm:p-10 bg-white border border-[#E8E5DC]">
          <div className="max-w-2xl space-y-3 mb-8 sm:mb-10">
            <span className="text-xs font-semibold uppercase tracking-wider text-[#8C8780] block">
              Scoring Taxonomy
            </span>
            <h2 className="text-3xl font-serif font-bold text-[#191817]">
              Common friction patterns we identify
            </h2>
            <p className="text-sm text-[#64615B] leading-relaxed">
              ExitLens benchmarks subscription flows against official regulatory patterns to highlight where consumer autonomy is compromised.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 lg:gap-6">
            <div className="space-y-2 p-4 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC]">
              <span className="text-xs font-mono font-semibold text-[#BE123C]">
                WEIGHT 30 PTS
              </span>
              <h4 className="text-sm font-semibold text-[#191817]">
                Buried Paths (Extra Steps)
              </h4>
              <p className="text-xs text-[#64615B] leading-relaxed">
                Excessive navigation depth requiring 4–7 clicks across hidden submenus instead of a direct cancellation button.
              </p>
            </div>

            <div className="space-y-2 p-4 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC]">
              <span className="text-xs font-mono font-semibold text-[#BE123C]">
                WEIGHT 20 PTS
              </span>
              <h4 className="text-sm font-semibold text-[#191817]">
                Interface Interference
              </h4>
              <p className="text-xs text-[#64615B] leading-relaxed">
                Visually de-emphasized cancel buttons disguised as faint grey text next to prominent retention buttons.
              </p>
            </div>

            <div className="space-y-2 p-4 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC]">
              <span className="text-xs font-mono font-semibold text-[#D97706]">
                WEIGHT 10 PTS
              </span>
              <h4 className="text-sm font-semibold text-[#191817]">
                Confirm Shaming
              </h4>
              <p className="text-xs text-[#64615B] leading-relaxed">
                Emotionally manipulative copy designed to induce guilt or anxiety before confirming cancellation intent.
              </p>
            </div>

            <div className="space-y-2 p-4 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC]">
              <span className="text-xs font-mono font-semibold text-[#D97706]">
                WEIGHT 10 PTS
              </span>
              <h4 className="text-sm font-semibold text-[#191817]">
                Retention Nagging
              </h4>
              <p className="text-xs text-[#64615B] leading-relaxed">
                Unskippable pause walls, discount popups, or multi-step retention offers interrupting the user&apos;s goal.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Safety & Transparency Section */}
      <section
        id="safety"
        className="mt-16 sm:mt-20 lg:mt-24 px-4 sm:px-6 max-w-5xl mx-auto scroll-mt-24 sm:scroll-mt-28"
      >
        <div className="p-8 sm:p-10 rounded-2xl bg-[#FAF9F7] border border-[#E8E5DC] flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#047857]">
              <ShieldCheck className="w-4 h-4" />
              <span>Safety &amp; Compliance Boundary</span>
            </div>
            <h3 className="text-2xl font-serif font-bold text-[#191817]">
              We audit the journey. We never cancel your subscription.
            </h3>
            <p className="text-xs sm:text-sm text-[#64615B] leading-relaxed">
              ExitLens enforces a strict pre-cancellation boundary: the runner identifies and records the final confirmation button, but is programmatically barred from clicking it. Real personal accounts are never accessed.
            </p>
          </div>
          <Link
            href="/check"
            className="shrink-0 px-5 py-3 rounded-lg text-sm font-semibold bg-[#191817] text-white hover:bg-[#2C2A28] transition-colors shadow-sm inline-flex items-center gap-2"
          >
            <span>Start an Audit</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}
