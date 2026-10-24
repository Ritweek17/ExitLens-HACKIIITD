import React from "react";
import Link from "next/link";
import { ShieldCheck, ExternalLink } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-[#E8E5DC] bg-[#FAF9F7] text-[#64615B] text-sm mt-auto">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Brand & Mission */}
          <div className="md:col-span-2 space-y-3">
            <div className="flex items-center gap-2 text-[#191817]">
              <div className="w-6 h-6 rounded bg-[#191817] text-white flex items-center justify-center text-xs font-serif font-bold">
                E
              </div>
              <span className="font-serif font-bold text-lg tracking-tight">
                ExitLens
              </span>
            </div>
            <p className="text-xs text-[#64615B] leading-relaxed max-w-md">
              ExitLens is a cancellation-journey audit tool. It systematically walks online subscription exit flows in India, documents navigational friction, and flags candidate dark patterns under the <strong>CCPA Guidelines for Prevention and Regulation of Dark Patterns (2023)</strong>.
            </p>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#F3F1EA] text-xs font-medium text-[#191817] border border-[#E8E5DC]">
              <ShieldCheck className="w-3.5 h-3.5 text-[#047857]" />
              <span>Strict Pre-Cancellation Boundary: Never completes cancellation</span>
            </div>
          </div>

          {/* Navigation */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#191817]">
              Platform
            </h4>
            <ul className="space-y-1.5 text-xs">
              <li>
                <Link href="/" className="hover:text-[#191817] transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/check" className="hover:text-[#191817] transition-colors">
                  Check a Subscription
                </Link>
              </li>
              <li>
                <Link href="/how-it-works" className="hover:text-[#191817] transition-colors">
                  How It Works
                </Link>
              </li>
            </ul>
          </div>

          {/* Standards & Transparency */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#191817]">
              Transparency & Safety
            </h4>
            <ul className="space-y-1.5 text-xs">
              <li className="text-[#64615B]">
                CCPA 2023 Candidate Review
              </li>
              <li className="text-[#64615B]">
                Dedicated Test Accounts Only
              </li>
              <li className="text-[#64615B]">
                Zero Password/Credential Storage
              </li>
              <li>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 hover:text-[#191817] transition-colors"
                >
                  <span>Backend OpenAPI Docs</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-[#E8E5DC] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#8C8780]">
          <p>© {new Date().getFullYear()} ExitLens. Built for subscription transparency and consumer advocacy.</p>
          <p>Evidence-linked journey auditing • Supervised automated analysis</p>
        </div>
      </div>
    </footer>
  );
}
export default SiteFooter;
