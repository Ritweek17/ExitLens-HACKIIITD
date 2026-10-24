import React from "react";
import Link from "next/link";
import {
  ShieldCheck,
  ArrowRight,
  Layers,
  Search,
  CheckCircle2,
  AlertTriangle,
  Lock,
  FileText,
  Scale,
  Eye,
  HelpCircle,
  Info,
} from "lucide-react";

export const metadata = {
  title: "How It Works — ExitLens",
  description: "Understand how ExitLens audits subscription cancellation journeys, scores friction, and identifies dark patterns under CCPA 2023.",
};

export default function HowItWorksPage() {
  return (
    <div className="py-12 px-4 sm:px-6 max-w-4xl mx-auto space-y-16 pb-20">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#F3F1EA] text-[#64615B] border border-[#E8E5DC]">
          <Scale className="w-3.5 h-3.5 text-[#8C8780]" />
          <span>Audit Methodology &amp; Standards</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-serif font-bold text-[#191817]">
          How ExitLens audits an exit flow
        </h1>
        <p className="text-base text-[#64615B] leading-relaxed">
          ExitLens provides transparency into online cancellation journeys by walking the path as a consumer would, measuring cognitive obstacles, and gathering verifiable evidence.
        </p>
      </div>

      {/* 3 Core Steps */}
      <div className="space-y-6">
        <h2 className="text-xl font-serif font-bold text-[#191817] text-center">
          The Three-Step Audit Process
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Step 1 */}
          <div className="exitlens-card p-6 bg-white border border-[#E8E5DC] space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] flex items-center justify-center font-serif font-bold text-base text-[#191817]">
              1
            </div>
            <h3 className="text-base font-semibold text-[#191817]">
              Choose a Service
            </h3>
            <p className="text-xs text-[#64615B] leading-relaxed">
              Select a target subscription from the searchable catalog or specify a custom service name and optional starting URL.
            </p>
          </div>

          {/* Step 2 */}
          <div className="exitlens-card p-6 bg-white border border-[#E8E5DC] space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] flex items-center justify-center font-serif font-bold text-base text-[#191817]">
              2
            </div>
            <h3 className="text-base font-semibold text-[#191817]">
              Authorized Journey Walk
            </h3>
            <p className="text-xs text-[#64615B] leading-relaxed">
              Confirm required permissions. The automated runner traverses menus, detects retention barriers, and streams progress live.
            </p>
          </div>

          {/* Step 3 */}
          <div className="exitlens-card p-6 bg-white border border-[#E8E5DC] space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] flex items-center justify-center font-serif font-bold text-base text-[#191817]">
              3
            </div>
            <h3 className="text-base font-semibold text-[#191817]">
              Review the Findings
            </h3>
            <p className="text-xs text-[#64615B] leading-relaxed">
              Inspect an evidence-linked report containing weighted friction points, DOM excerpts, and candidate CCPA dark-pattern signals.
            </p>
          </div>
        </div>
      </div>

      {/* Safety & Limitations Boundary */}
      <div className="exitlens-card p-8 bg-[#FAF9F7] border border-[#E8E5DC] space-y-4">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#047857]">
          <ShieldCheck className="w-4 h-4" />
          <span>Strict Pre-Cancellation Boundary</span>
        </div>
        <h3 className="text-2xl font-serif font-bold text-[#191817]">
          ExitLens never cancels your subscription.
        </h3>
        <p className="text-xs sm:text-sm text-[#64615B] leading-relaxed">
          Our core safety principle is simple: <strong>the runner halts immediately before the final irreversible cancellation action</strong>. When the final &ldquo;Confirm Cancellation&rdquo; button is located, ExitLens records its presence, captures the evidence, and terminates execution safely.
        </p>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs text-[#524F4B]">
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#047857] shrink-0" />
            <span>Dedicated test accounts only</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#047857] shrink-0" />
            <span>Zero password or card storage</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#047857] shrink-0" />
            <span>No account termination occurs</span>
          </li>
          <li className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#047857] shrink-0" />
            <span>Audit trail fully reproducible</span>
          </li>
        </ul>
      </div>

      {/* Box D & CCPA Framework Explained */}
      <div className="exitlens-card p-8 bg-white border border-[#E8E5DC] space-y-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#8C8780]">
            Regulatory Foundation
          </span>
          <h2 className="text-2xl font-serif font-bold text-[#191817] mt-1">
            Aligned with India&apos;s CCPA (2023) Guidelines
          </h2>
          <p className="text-xs sm:text-sm text-[#64615B] mt-1 leading-relaxed">
            The Central Consumer Protection Authority issued guidelines prohibiting deceptive design practices. ExitLens evaluates candidate dark patterns including:
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] space-y-1">
            <h4 className="font-semibold text-[#191817]">Subscription Trap</h4>
            <p className="text-[#64615B] leading-relaxed">
              Making cancellation significantly more difficult, hidden, or lengthy than sign-up.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] space-y-1">
            <h4 className="font-semibold text-[#191817]">Interface Interference</h4>
            <p className="text-[#64615B] leading-relaxed">
              Visual manipulation, such as highlighting &ldquo;Keep Plan&rdquo; while greying out &ldquo;Cancel&rdquo;.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] space-y-1">
            <h4 className="font-semibold text-[#191817]">Confirm Shaming</h4>
            <p className="text-[#64615B] leading-relaxed">
              Using emotional extortion or guilt-inducing copy to dissuade users from unsubscribing.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] space-y-1">
            <h4 className="font-semibold text-[#191817]">Nagging</h4>
            <p className="text-[#64615B] leading-relaxed">
              Repeatedly interrupting the user with retention discounts, surveys, or pause offers.
            </p>
          </div>
        </div>

        <div className="p-3.5 rounded-lg bg-[#FAF9F7] border border-[#E8E5DC] text-[11px] text-[#8C8780] flex items-start gap-2">
          <Info className="w-4 h-4 shrink-0 mt-0.5" />
          <span>
            <strong>Legal Notice:</strong> Signals presented in ExitLens reports are designated as candidate annotations for human and regulatory review. They do not constitute formal legal judgments.
          </span>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="space-y-4">
        <h2 className="text-xl font-serif font-bold text-[#191817] text-center">
          Frequently Asked Questions
        </h2>

        <div className="space-y-3">
          <div className="exitlens-card p-5 bg-white border border-[#E8E5DC] space-y-1">
            <h4 className="text-sm font-semibold text-[#191817]">
              Can ExitLens accidentally cancel my subscription?
            </h4>
            <p className="text-xs text-[#64615B] leading-relaxed">
              No. The automation runner specifically identifies the final confirmation control and stops immediately without clicking it.
            </p>
          </div>

          <div className="exitlens-card p-5 bg-white border border-[#E8E5DC] space-y-1">
            <h4 className="text-sm font-semibold text-[#191817]">
              How is the Friction Score calculated?
            </h4>
            <p className="text-xs text-[#64615B] leading-relaxed">
              The score combines excessive navigation steps (5 pts per step beyond 2, capped at 30) with deduplicated indicator weights across 6 categories (Extra Steps 30, Hidden Cancel 20, Redirects 15, Forced Reason 15, Retention Offer 10, Unclear Copy 10). Max score is 100.
            </p>
          </div>

          <div className="exitlens-card p-5 bg-white border border-[#E8E5DC] space-y-1">
            <h4 className="text-sm font-semibold text-[#191817]">
              What accounts are used during the audit?
            </h4>
            <p className="text-xs text-[#64615B] leading-relaxed">
              ExitLens requires approved dedicated test accounts or local mock testbeds. We strictly prohibit using real personal accounts containing private credentials or payment details.
            </p>
          </div>
        </div>
      </div>

      {/* Final CTA */}
      <div className="text-center space-y-4 pt-6">
        <h3 className="text-2xl font-serif font-bold text-[#191817]">
          Ready to audit a cancellation flow?
        </h3>
        <p className="text-xs sm:text-sm text-[#64615B] max-w-md mx-auto">
          Start with our built-in testbed to observe live dark-pattern detection in seconds.
        </p>
        <div>
          <Link
            href="/check"
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg text-sm font-semibold bg-[#191817] text-white hover:bg-[#2C2A28] transition-colors shadow-sm"
          >
            <span>Start an Audit</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
