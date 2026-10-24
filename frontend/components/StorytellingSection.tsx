import React from "react";
import { ArrowRight, ArrowDown, Layers, MousePointerClick, AlertTriangle } from "lucide-react";

export function StorytellingSection() {
  return (
    <div
      role="region"
      aria-labelledby="storytelling-heading"
      className="w-full rounded-3xl bg-[#FAF9F7] border border-[#E8E5DC] shadow-[0_4px_20px_-4px_rgba(20,19,18,0.04),0_1px_3px_-1px_rgba(20,19,18,0.02)] p-6 sm:p-8 lg:p-9 space-y-8 sm:space-y-10"
    >
      {/* Editorial Header Section */}
      <div className="text-center max-w-2xl mx-auto space-y-3 sm:space-y-3.5">
        {/* Eyebrow Label */}
        <span className="text-xs font-semibold uppercase tracking-wider text-[#8C8780] block">
          A REAL-LIFE SCENARIO
        </span>

        {/* Editorial Headline - Refined to be clearly secondary to the main hero */}
        <h2
          id="storytelling-heading"
          className="text-2xl sm:text-3xl lg:text-[2.125rem] font-serif font-bold text-[#191817] tracking-tight leading-[1.25]"
        >
          Cancelling a subscription
          <br className="hidden sm:inline" />{" "}
          <span className="text-[#9F1239]">shouldn&apos;t feel this confusing.</span>
        </h2>

        {/* Supporting Text */}
        <div className="space-y-1.5 text-xs sm:text-sm text-[#64615B] leading-relaxed max-w-xl mx-auto pt-0.5 font-sans">
          <p>
            You try to cancel, click through menus, face retention offers, and still can&apos;t find
            the cancel button.
          </p>
          <p>
            ExitLens audits the entire journey, highlights the friction, and helps you make an
            informed decision.
          </p>
        </div>
      </div>

      {/* Three Storytelling Stages */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-10 md:gap-4 lg:gap-8 relative items-start">
        {/* ================= STAGE 1 ================= */}
        <div className="flex flex-col items-center text-center space-y-4 relative group">
          {/* Annotation badge */}
          <div className="h-7 flex items-center justify-center">
            <span className="inline-flex items-center px-3 py-1 rounded-full bg-[#FFF1F2] border border-[#FECDD3] text-[#9F1239] text-xs font-serif italic shadow-xs">
              &ldquo;Where is the cancel option?&rdquo;
            </span>
          </div>

          {/* Visual container with subtle blush background */}
          <div className="w-full h-44 sm:h-48 flex items-center justify-center relative">
            {/* Subtle blush background shape */}
            <div className="w-36 h-36 sm:w-40 sm:h-40 rounded-full bg-[#FFF1F2]/80 border border-[#FFE4E6] flex items-center justify-center p-2 shadow-inner" />

            {/* Silhouette 1: Puzzled person in front of laptop */}
            <div className="absolute inset-0 flex items-center justify-center">
              <svg
                viewBox="0 0 160 140"
                className="w-36 h-32 sm:w-40 sm:h-36 drop-shadow-xs"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                {/* Desk Line */}
                <line
                  x1="18"
                  y1="118"
                  x2="142"
                  y2="118"
                  stroke="#D6D1C9"
                  strokeWidth="2"
                  strokeLinecap="round"
                />

                {/* Minimalist Chair */}
                <path
                  d="M 32 118 L 32 76 C 32 70, 36 66, 42 66"
                  stroke="#A8A29E"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />

                {/* Head */}
                <circle cx="56" cy="52" r="13" fill="#191817" />

                {/* Torso */}
                <path
                  d="M 44 78 C 44 67, 68 67, 68 78 L 64 118 L 38 118 Z"
                  fill="#191817"
                />

                {/* Reaching arm */}
                <path
                  d="M 54 78 Q 72 92 88 110"
                  stroke="#191817"
                  strokeWidth="5.5"
                  strokeLinecap="round"
                />

                {/* Laptop Base */}
                <line
                  x1="82"
                  y1="117"
                  x2="118"
                  y2="117"
                  stroke="#191817"
                  strokeWidth="3"
                  strokeLinecap="round"
                />

                {/* Laptop Screen */}
                <line
                  x1="108"
                  y1="117"
                  x2="118"
                  y2="92"
                  stroke="#191817"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />

                {/* Screen Glow */}
                <polygon
                  points="108,117 118,92 105,92 98,117"
                  fill="#F3F1EA"
                  opacity="0.9"
                />

                {/* Restrained Burgundy Scribble / Confusion Indicator */}
                <path
                  d="M 48 28 C 52 18, 64 18, 66 24 C 68 30, 54 32, 52 26 C 50 20, 62 14, 72 20 C 78 24, 74 32, 64 34"
                  stroke="#9F1239"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <circle cx="72" cy="16" r="1.5" fill="#9F1239" />
              </svg>
            </div>
          </div>

          {/* Caption & Description */}
          <div className="space-y-1.5 max-w-xs px-2">
            <h3 className="font-serif font-bold text-lg sm:text-xl text-[#191817]">
              You try to cancel
            </h3>
            <p className="text-xs sm:text-sm text-[#64615B] leading-relaxed">
              You open the subscription and search for the cancel option.
            </p>
          </div>
        </div>

        {/* Horizontal Connector Arrow 1 -> 2 (Desktop) */}
        <div
          className="hidden md:flex absolute top-28 left-[33%] -translate-x-1/2 text-[#B3ADA4]"
          aria-hidden="true"
        >
          <ArrowRight className="w-5 h-5 transition-transform duration-200 group-hover:translate-x-0.5" />
        </div>

        {/* Mobile Connector Arrow 1 -> 2 */}
        <div className="flex md:hidden justify-center text-[#B3ADA4] -my-4" aria-hidden="true">
          <ArrowDown className="w-4 h-4" />
        </div>

        {/* ================= STAGE 2 ================= */}
        <div className="flex flex-col items-center text-center space-y-4 relative group">
          {/* Annotation badge */}
          <div className="h-7 flex items-center justify-center">
            <span className="inline-flex items-center px-3 py-1 rounded-full bg-[#FFF1F2] border border-[#FECDD3] text-[#9F1239] text-xs font-serif italic shadow-xs">
              &ldquo;Still no cancel… just more offers.&rdquo;
            </span>
          </div>

          {/* Visual container with overlapping panels */}
          <div className="w-full h-44 sm:h-48 flex items-center justify-center relative">
            {/* Subtle warm backdrop shape */}
            <div className="w-36 h-36 sm:w-40 sm:h-40 rounded-full bg-[#FAF5F0] border border-[#F3E8DF] absolute" />

            {/* Overlapping UI Panels */}
            <div className="relative z-10 flex items-center justify-center w-full">
              {/* Panel 1: Account Settings Menu */}
              <div className="w-32 sm:w-36 bg-white rounded-lg border border-[#E8E5DC] shadow-sm p-2.5 space-y-1 text-left transform -translate-x-4 -translate-y-2 rotate-[-2deg] transition-transform duration-200 group-hover:rotate-0">
                <div className="flex items-center justify-between pb-1 border-b border-[#F3F1EA]">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[#8C8780]">
                    Settings
                  </span>
                  <div className="flex gap-0.5">
                    <span className="w-1 h-1 rounded-full bg-[#D6D1C9]" />
                    <span className="w-1 h-1 rounded-full bg-[#D6D1C9]" />
                  </div>
                </div>
                <div className="space-y-0.5 text-[10px] text-[#524F4B]">
                  <div className="py-0.5 px-1.5 rounded text-[#8C8780]">Profile</div>
                  <div className="py-0.5 px-1.5 rounded text-[#8C8780]">Billing</div>
                  <div className="py-0.5 px-1.5 rounded bg-[#F3F1EA] text-[#191817] font-semibold flex items-center justify-between">
                    <span>Plan</span>
                    <span className="text-[8px] text-[#8C8780] font-normal">Active</span>
                  </div>
                  <div className="py-0.5 px-1.5 rounded text-[#8C8780]">Help</div>
                </div>
              </div>

              {/* Panel 2: Overlapping Retention Offer */}
              <div className="w-36 sm:w-40 bg-[#FAF9F7] rounded-lg border border-[#E8E5DC] shadow-md p-2.5 space-y-2 text-left absolute translate-x-4 translate-y-3 rotate-[2deg] transition-transform duration-200 group-hover:rotate-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-serif font-bold text-[#191817]">
                    Wait! Don&apos;t go.
                  </span>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#9F1239]" aria-hidden="true" />
                </div>
                <p className="text-[10px] text-[#64615B] leading-tight">
                  Get 50% off for the next 3 months if you stay.
                </p>
                <div className="space-y-1 pt-0.5">
                  <div className="w-full py-1 text-center text-[10px] font-semibold text-white bg-[#9F1239] rounded shadow-xs">
                    Keep Offer
                  </div>
                  <div className="w-full text-center text-[9px] text-[#8C8780]">
                    No thanks, continue
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Caption & Description */}
          <div className="space-y-1.5 max-w-xs px-2">
            <h3 className="font-serif font-bold text-lg sm:text-xl text-[#191817]">
              You face obstacles
            </h3>
            <p className="text-xs sm:text-sm text-[#64615B] leading-relaxed">
              You click through multiple menus, retention offers and confusing flows.
            </p>
          </div>
        </div>

        {/* Horizontal Connector Arrow 2 -> 3 (Desktop) */}
        <div
          className="hidden md:flex absolute top-28 left-[67%] -translate-x-1/2 text-[#B3ADA4]"
          aria-hidden="true"
        >
          <ArrowRight className="w-5 h-5 transition-transform duration-200 group-hover:translate-x-0.5" />
        </div>

        {/* Mobile Connector Arrow 2 -> 3 */}
        <div className="flex md:hidden justify-center text-[#B3ADA4] -my-4" aria-hidden="true">
          <ArrowDown className="w-4 h-4" />
        </div>

        {/* ================= STAGE 3 ================= */}
        <div className="flex flex-col items-center text-center space-y-4 relative group">
          {/* Top spacing placeholder to align with annotations */}
          <div className="h-7 flex items-center justify-center">
            <span className="inline-flex items-center px-3 py-1 rounded-full bg-[#F0FDF4] border border-[#DCFCE7] text-[#047857] text-xs font-serif italic shadow-xs">
              Clear audit evidence
            </span>
          </div>

          {/* Visual container with subtle pale sage background */}
          <div className="w-full h-44 sm:h-48 flex items-center justify-center relative">
            {/* Subtle pale sage background shape */}
            <div className="w-36 h-36 sm:w-40 sm:h-40 rounded-full bg-[#F0FDF4]/90 border border-[#DCFCE7] absolute" />

            {/* Silhouette 2 + ExitLens Report Card */}
            <div className="relative z-10 flex items-center justify-center gap-2 w-full px-2">
              {/* Relaxed Person Silhouette */}
              <svg
                viewBox="0 0 120 130"
                className="w-24 h-24 sm:w-28 sm:h-28 shrink-0 drop-shadow-xs"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                {/* Desk Line */}
                <line
                  x1="8"
                  y1="112"
                  x2="112"
                  y2="112"
                  stroke="#D6D1C9"
                  strokeWidth="2"
                  strokeLinecap="round"
                />

                {/* Chair */}
                <path
                  d="M 22 112 L 22 68 C 22 63, 26 58, 32 58"
                  stroke="#A8A29E"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />

                {/* Head - Upright & composed */}
                <circle cx="44" cy="46" r="12" fill="#191817" />

                {/* Torso - Upright */}
                <path
                  d="M 32 72 C 32 62, 56 62, 56 72 L 54 112 L 28 112 Z"
                  fill="#191817"
                />

                {/* Relaxed arm */}
                <path
                  d="M 42 72 Q 56 84 70 106"
                  stroke="#191817"
                  strokeWidth="5"
                  strokeLinecap="round"
                />

                {/* Laptop Base */}
                <line
                  x1="66"
                  y1="111"
                  x2="98"
                  y2="111"
                  stroke="#191817"
                  strokeWidth="3"
                  strokeLinecap="round"
                />

                {/* Laptop Screen */}
                <line
                  x1="88"
                  y1="111"
                  x2="98"
                  y2="88"
                  stroke="#191817"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />

                {/* Screen Glow */}
                <polygon
                  points="88,111 98,88 88,88 78,111"
                  fill="#DCFCE7"
                  opacity="0.85"
                />
              </svg>

              {/* Clean ExitLens Report Card (showing ONLY the 3 concise items) */}
              <div className="w-32 sm:w-36 bg-white rounded-lg border border-[#E8E5DC] shadow-sm p-2.5 space-y-2 text-left">
                <div className="flex items-center justify-between pb-1 border-b border-[#F3F1EA]">
                  <div className="flex items-center gap-1.5">
                    <div className="w-3.5 h-3.5 rounded bg-[#191817] text-white flex items-center justify-center text-[8px] font-serif font-bold">
                      E
                    </div>
                    <span className="text-[10px] font-serif font-bold text-[#191817]">
                      ExitLens Report
                    </span>
                  </div>
                  <span className="w-1.5 h-1.5 rounded-full bg-[#047857]" aria-hidden="true" />
                </div>

                {/* Exactly 3 concise items with simple line icons, no fabricated metrics */}
                <div className="space-y-1 text-[10px]">
                  <div className="flex items-center gap-1.5 py-0.5 px-1 rounded bg-[#FAF9F7] text-[#191817]">
                    <Layers className="w-3 h-3 text-[#047857] shrink-0" aria-hidden="true" />
                    <span className="font-medium">Journey steps</span>
                  </div>
                  <div className="flex items-center gap-1.5 py-0.5 px-1 rounded bg-[#FAF9F7] text-[#191817]">
                    <MousePointerClick
                      className="w-3 h-3 text-[#D97706] shrink-0"
                      aria-hidden="true"
                    />
                    <span className="font-medium">Extra clicks</span>
                  </div>
                  <div className="flex items-center gap-1.5 py-0.5 px-1 rounded bg-[#FAF9F7] text-[#191817]">
                    <AlertTriangle
                      className="w-3 h-3 text-[#9F1239] shrink-0"
                      aria-hidden="true"
                    />
                    <span className="font-medium">Dark patterns</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Caption & Description */}
          <div className="space-y-1.5 max-w-xs px-2">
            <h3 className="font-serif font-bold text-lg sm:text-xl text-[#191817]">
              You get clarity
            </h3>
            <p className="text-xs sm:text-sm text-[#64615B] leading-relaxed">
              ExitLens shows the cancellation journey with evidence, so you stay in control.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StorytellingSection;
