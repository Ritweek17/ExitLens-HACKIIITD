"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Printer,
  ArrowLeft,
  ArrowRight,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Loader2,
  RefreshCw,
  AlertTriangle,
  ShieldCheck,
  Check,
} from "lucide-react";
import {
  Report,
  getReport,
  ApiClientError,
  Severity,
  AuditOutcome,
} from "@/lib/api";

interface ReportViewProps {
  runId: string;
}

export function ReportView({ runId }: ReportViewProps) {
  const [report, setReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<{ message: string; code?: string } | null>(null);
  const [activeTab, setActiveTab] = useState<"findings" | "timeline" | "ccpa">("findings");
  const [expandedSignals, setExpandedSignals] = useState<Record<string, boolean>>({});

  useEffect(() => {
    let isMounted = true;

    async function fetchReportData() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getReport(runId);
        if (isMounted) {
          setReport(data);
          setIsLoading(false);
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        setIsLoading(false);
        if (err instanceof ApiClientError) {
          setError({ message: err.message, code: err.code });
        } else if (err instanceof Error) {
          setError({ message: err.message });
        } else {
          setError({ message: "An unexpected error occurred while loading the report." });
        }
      }
    }

    if (runId) {
      fetchReportData();
    }

    return () => {
      isMounted = false;
    };
  }, [runId]);

  function toggleSignal(id: string) {
    setExpandedSignals((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  }

  if (isLoading) {
    return (
      <div className="py-24 text-center space-y-4 max-w-lg mx-auto">
        <Loader2 className="w-7 h-7 animate-spin text-[#191817] mx-auto" />
        <h2 className="font-serif font-bold text-xl text-[#191817]">
          Loading Audit Report
        </h2>
        <p className="text-xs text-[#64615B] leading-relaxed">
          Retrieving verified friction indicators, step timeline, and evidence logs...
        </p>
      </div>
    );
  }

  if (error || !report) {
    const isNotReady = error?.code === "report_not_ready";
    return (
      <div className="exitlens-card p-8 sm:p-10 max-w-lg mx-auto text-center space-y-5 bg-white border border-[#E8E5DC] my-12">
        <div className="w-10 h-10 rounded-full bg-[#FAF9F7] border border-[#E8E5DC] flex items-center justify-center mx-auto text-[#191817]">
          {isNotReady ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-[#92400E]" />
          )}
        </div>
        <div className="space-y-1">
          <h2 className="font-serif font-bold text-xl text-[#191817]">
            {isNotReady ? "Audit Still Running" : "Report Unavailable"}
          </h2>
          <p className="text-xs text-[#64615B] leading-relaxed">
            {isNotReady
              ? "The audit runner is actively traversing the subscription exit journey. The verified report will be generated as soon as the boundary is reached."
              : error?.message || "No report data was returned for this session."}
          </p>
        </div>
        <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
          {isNotReady ? (
            <Link
              href={`/run/${encodeURIComponent(runId)}`}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-[#191817] text-white hover:bg-[#2C2A28] inline-flex items-center gap-1.5 transition-colors duration-200"
            >
              <span>Watch Live Stream</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          ) : (
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-[#191817] text-white hover:bg-[#2C2A28] inline-flex items-center gap-1.5 transition-colors duration-200"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
          )}
          <Link
            href="/check"
            className="px-4 py-2 text-xs font-medium rounded-lg bg-[#F3F1EA] text-[#191817] hover:bg-[#EAE7DD] border border-[#E8E5DC] transition-colors duration-200"
          >
            Start Another Audit
          </Link>
        </div>
      </div>
    );
  }

  // Outcome label helper
  function formatOutcome(outcome: AuditOutcome) {
    switch (outcome) {
      case "completed_with_evidence":
        return "Completed with evidence";
      case "partial_evidence":
        return "Partial evidence captured";
      case "human_required":
        return "Barrier detected · Assistance required";
      case "failed":
        return "Audit incomplete";
      default:
        return outcome.replace(/_/g, " ");
    }
  }

  // Severity indicator helper
  function renderSeverityBadge(sev: Severity, weight: number) {
    let textColor = "text-[#524F4B]";
    let dotColor = "bg-[#8C8780]";
    if (sev === "high") {
      textColor = "text-[#991B1B]";
      dotColor = "bg-[#DC2626]";
    } else if (sev === "medium") {
      textColor = "text-[#92400E]";
      dotColor = "bg-[#D97706]";
    }

    return (
      <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${textColor}`}>
        <span className={`w-1.5 h-1.5 rounded-full ${dotColor} shrink-0`} aria-hidden="true" />
        <span className="capitalize">{sev} severity</span>
        <span className="text-[#8C8780] font-normal">(+{weight} pts)</span>
      </span>
    );
  }

  const score = report.friction_score;
  const scoreLabel =
    score >= 60 ? "High Friction" : score >= 30 ? "Moderate Friction" : "Low Friction";
  const scoreColor =
    score >= 60 ? "text-[#BE123C]" : score >= 30 ? "text-[#D97706]" : "text-[#047857]";
  const stopReasonMessage = report.stop_reason === "account_verification_failed"
    ? "The runner could not verify the approved dedicated test account. The audit stopped without continuing."
    : report.stop_reason === "user_stopped"
      ? "A supervising human stopped the audit. Cancellation was not submitted."
      : report.stop_reason === "pre_cancellation_boundary"
        ? "The runner stopped before the final cancellation action."
        : report.stop_reason === "blocked"
          ? "The runner encountered a barrier and stopped without bypassing it."
          : report.stop_reason === "error"
            ? "The audit ended after an error. Review any captured evidence and limitations below."
            : "The audit ended; review the recorded stop reason and limitations below.";

  // Collect step list from evidence and friction signals
  const allSteps = report.evidence.map((ev) => ({
    step: ev.step,
    content: ev.content,
    kind: ev.kind,
    url: ev.url,
    timestamp: ev.timestamp,
  }));

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-16">
      {/* 1. Report Header */}
      <div className="space-y-4">
        {/* Top Meta Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs">
            <span className="font-semibold uppercase tracking-wider text-[#8C8780]">
              AUDIT REPORT
            </span>
            <span className="text-[#8C8780]">·</span>
            <span className="font-mono text-[#524F4B]">{report.run_id}</span>
          </div>

          {/* Understated Safety Status Indicator */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-[#6B6762]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#059669] shrink-0" aria-hidden="true" />
              <span>
                {report.safety_gate_stopped
                  ? "Pre-cancellation boundary preserved"
                  : "Final cancellation avoided"}
              </span>
            </div>

            {/* Print Action */}
            <div className="no-print pl-2">
              <button
                type="button"
                onClick={() => window.print()}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-[#191817] hover:bg-[#F3F1EA] border border-[#E8E5DC] transition-colors duration-200"
                aria-label="Print or export report as PDF"
              >
                <Printer className="w-3.5 h-3.5" aria-hidden="true" />
                <span className="hidden sm:inline">Print / PDF</span>
              </button>
            </div>
          </div>
        </div>

        {/* Title & Service */}
        <div>
          <h1 className="text-3xl sm:text-4xl font-serif font-bold text-[#191817] tracking-tight">
            {report.service}
          </h1>
          {report.streaming_url ? (
            <a
              href={report.streaming_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-[#64615B] hover:text-[#191817] hover:underline inline-flex items-center gap-1 mt-1 transition-colors duration-200"
            >
              <span>View live browser recording session</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          ) : (
            <p className="text-xs text-[#8C8780] mt-1">
              Subscription exit flow assessment under India CCPA (2023) Guidelines
            </p>
          )}
        </div>
      </div>

      {/* 2. Three Aligned Summary Columns (No heavy nested cards) */}
      <div className="exitlens-card bg-white border border-[#E8E5DC] overflow-hidden">
        <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-[#E8E5DC]">
          {/* Column 1: Audited Target */}
          <div className="p-5 sm:p-6 space-y-1">
            <span className="text-[11px] font-medium uppercase tracking-wider text-[#8C8780]">
              Audited Target
            </span>
            <p className="text-base font-serif font-bold text-[#191817] pt-0.5">
              {report.service}
            </p>
            <p className="text-xs text-[#64615B] truncate">
              Outcome: {formatOutcome(report.outcome)}
            </p>
          </div>

          {/* Column 2: Friction Score */}
          <div className="p-5 sm:p-6 space-y-1">
            <span className="text-[11px] font-medium uppercase tracking-wider text-[#8C8780]">
              Friction Score
            </span>
            <div className="flex items-baseline gap-2 pt-0.5">
              <span className={`text-2xl font-serif font-bold ${scoreColor}`}>
                {report.friction_score}
              </span>
              <span className="text-xs text-[#8C8780]">/ 100</span>
              <span className={`text-xs font-medium ${scoreColor}`}>
                ({scoreLabel})
              </span>
            </div>
            <p className="text-xs text-[#64615B]">
              Box D weighted indicators
            </p>
          </div>

          {/* Column 3: Safety Status */}
          <div className="p-5 sm:p-6 space-y-1">
            <span className="text-[11px] font-medium uppercase tracking-wider text-[#8C8780]">
              Safety Boundary
            </span>
            <div className={`flex items-center gap-1.5 text-xs font-semibold pt-1 ${report.stop_reason === "account_verification_failed" || report.stop_reason === "error" ? "text-[#991B1B]" : "text-[#047857]"}`}>
              {report.stop_reason === "account_verification_failed" || report.stop_reason === "error" ? <AlertTriangle className="w-4 h-4 shrink-0" /> : <ShieldCheck className="w-4 h-4 shrink-0" />}
              <span>{report.stop_reason === "account_verification_failed" ? "Account verification failed; runner stopped" : report.stop_reason === "user_stopped" ? "Stopped by supervising human" : report.stop_reason === "error" ? "Audit interrupted" : "Stopped Before Final Cancel"}</span>
            </div>
            <p className="text-xs text-[#64615B]">
              {stopReasonMessage}
            </p>
            <div className="pt-2 text-xs">
              <span className="text-[#8C8780]">Dedicated test account: </span>
              <span className="font-mono text-[#191817]">{report.test_account_ref || "Not recorded"}</span>
              <span className={`ml-2 font-semibold ${report.account_verified === true ? "text-[#047857]" : report.account_verified === false ? "text-[#991B1B]" : "text-[#8C8780]"}`}>
                {report.account_verified === true ? "Verified" : report.account_verified === false ? "Not verified" : "Verification unavailable"}
              </span>
            </div>
          </div>
        </div>
      </div>

      {report.outcome === "partial_evidence" && (
        <div role="status" className="p-4 rounded-xl bg-[#FEF3C7] border border-[#FDE68A] text-xs text-[#78350F]">
          <p className="font-semibold">Partial evidence captured</p>
          <p className="mt-1">The audit ended before its normal completion. Captured evidence is available in the step-by-step timeline, with known gaps listed under limitations.</p>
        </div>
      )}

      {/* 3. Report Navigation Tabs */}
      <div className="space-y-6">
        <div
          role="tablist"
          aria-label="Report views"
          className="flex items-center gap-6 border-b border-[#E8E5DC] text-sm"
        >
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "findings"}
            aria-controls="findings-panel"
            onClick={() => setActiveTab("findings")}
            className={`pb-3 font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] rounded-sm relative ${
              activeTab === "findings"
                ? "text-[#191817] font-semibold after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-[#191817]"
                : "text-[#8C8780] hover:text-[#191817]"
            }`}
          >
            Findings ({report.friction_signals.length})
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "timeline"}
            aria-controls="timeline-panel"
            onClick={() => setActiveTab("timeline")}
            className={`pb-3 font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] rounded-sm relative ${
              activeTab === "timeline"
                ? "text-[#191817] font-semibold after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-[#191817]"
                : "text-[#8C8780] hover:text-[#191817]"
            }`}
          >
            Step-by-Step Timeline ({allSteps.length})
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === "ccpa"}
            aria-controls="ccpa-panel"
            onClick={() => setActiveTab("ccpa")}
            className={`pb-3 font-medium transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] rounded-sm relative ${
              activeTab === "ccpa"
                ? "text-[#191817] font-semibold after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-[#191817]"
                : "text-[#8C8780] hover:text-[#191817]"
            }`}
          >
            CCPA Dark Patterns ({report.ccpa_alignment.length})
          </button>
        </div>

        {/* 4. Tab Panel 1: Findings Section (Clean Rows with Horizontal Dividers) */}
        {activeTab === "findings" && (
          <div id="findings-panel" role="tabpanel" className="exitlens-card bg-white border border-[#E8E5DC]">
            <div className="p-5 sm:p-6 pb-4 border-b border-[#E8E5DC] flex items-center justify-between">
              <div>
                <h2 className="text-base font-serif font-bold text-[#191817]">
                  Friction Findings
                </h2>
                <p className="text-xs text-[#64615B] mt-0.5">
                  Identified cognitive hurdles, buried paths, and asymmetric controls.
                </p>
              </div>
              <span className="text-xs text-[#8C8780]">
                {report.friction_signals.length} {report.friction_signals.length === 1 ? "item" : "items"}
              </span>
            </div>

            {report.friction_signals.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#64615B]">
                No friction signals were detected in this audit journey.
              </div>
            ) : (
              <div className="divide-y divide-[#E8E5DC]">
                {report.friction_signals.map((sig) => {
                  const isExpanded = !!expandedSignals[sig.id];
                  // Find matching evidence items
                  const relatedEv = report.evidence.filter((ev) =>
                    sig.evidence_ids?.includes(ev.id)
                  );

                  return (
                    <div
                      key={sig.id}
                      className="p-5 sm:p-6 transition-colors duration-150 hover:bg-[#FAF9F7]/60 space-y-2.5"
                    >
                      {/* Row Header: Indicator, Severity & Affordance */}
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="flex items-center gap-3 flex-wrap">
                          {renderSeverityBadge(sig.severity, sig.weight)}
                          <span className="text-xs font-mono text-[#64615B] bg-[#F3F1EA] px-2 py-0.5 rounded">
                            {sig.indicator}
                          </span>
                          {sig.verified && (
                            <span className="text-xs text-[#047857] flex items-center gap-1 font-medium">
                              <Check className="w-3.5 h-3.5" /> Verified
                            </span>
                          )}
                        </div>

                        {/* Expand/Collapse Affordance */}
                        <button
                          type="button"
                          onClick={() => toggleSignal(sig.id)}
                          className="text-xs text-[#64615B] hover:text-[#191817] inline-flex items-center gap-1 py-1 px-1.5 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#191817] transition-colors duration-200"
                          aria-expanded={isExpanded}
                        >
                          <span>{isExpanded ? "Hide evidence" : "Details & evidence"}</span>
                          {isExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5" aria-hidden="true" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5" aria-hidden="true" />
                          )}
                        </button>
                      </div>

                      {/* Finding Title & Concise Description */}
                      <div className="space-y-1">
                        <h3 className="text-sm font-semibold text-[#191817] leading-snug">
                          {sig.title}
                        </h3>
                        <p className="text-xs text-[#524F4B] leading-relaxed">
                          {sig.description}
                        </p>
                      </div>

                      {/* Expandable Disclosure Area */}
                      {isExpanded && (
                        <div className="mt-3 pt-3 border-t border-[#F3F1EA] space-y-2.5 text-xs">
                          {sig.step_refs && sig.step_refs.length > 0 && (
                            <p className="text-[#64615B]">
                              Observed at step{sig.step_refs.length > 1 ? "s" : ""}:{" "}
                              <strong className="text-[#191817]">
                                {sig.step_refs.join(", ")}
                              </strong>
                            </p>
                          )}

                          {relatedEv.length > 0 && (
                            <div className="space-y-2">
                              <span className="text-[11px] font-medium uppercase tracking-wider text-[#8C8780]">
                                Direct DOM Evidence:
                              </span>
                              {relatedEv.map((ev) => (
                                <div
                                  key={ev.id}
                                  className="p-3 rounded-lg bg-[#FAF9F7] border border-[#E8E5DC] space-y-1"
                                >
                                  <div className="flex items-center justify-between text-[11px] text-[#8C8780]">
                                    <span className="font-mono">{ev.id} · Step {ev.step}</span>
                                    {ev.timestamp && (
                                      <span>{new Date(ev.timestamp).toLocaleTimeString()}</span>
                                    )}
                                  </div>
                                  {ev.content && (
                                    <p className="text-[#191817] font-mono text-[11px] bg-white p-2 rounded border border-[#E8E5DC] break-words">
                                      &ldquo;{ev.content}&rdquo;
                                    </p>
                                  )}
                                  {ev.url && (
                                    <a
                                      href={ev.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-xs text-[#047857] hover:underline inline-flex items-center gap-1"
                                    >
                                      <span>View evidence resource</span>
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* 5. Tab Panel 2: Step-by-Step Timeline */}
        {activeTab === "timeline" && (
          <div id="timeline-panel" role="tabpanel" className="exitlens-card bg-white border border-[#E8E5DC]">
            <div className="p-5 sm:p-6 pb-4 border-b border-[#E8E5DC] flex items-center justify-between">
              <div>
                <h2 className="text-base font-serif font-bold text-[#191817]">
                  Step-by-Step Timeline
                </h2>
                <p className="text-xs text-[#64615B] mt-0.5">
                  Actual recorded actions and DOM snapshots observed during the audit.
                </p>
              </div>
              <span className="text-xs text-[#8C8780]">
                {allSteps.length} {allSteps.length === 1 ? "step" : "steps"}
              </span>
            </div>

            {allSteps.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#64615B]">
                No individual step logs are available for this run.
              </div>
            ) : (
              <div className="divide-y divide-[#E8E5DC]">
                {allSteps.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 sm:p-5 flex items-start gap-3.5 hover:bg-[#FAF9F7]/50 transition-colors duration-150"
                  >
                    <div className="w-6 h-6 rounded-full bg-[#191817] text-white flex items-center justify-center text-xs font-bold shrink-0 mt-0.5">
                      {item.step}
                    </div>
                    <div className="flex-1 space-y-1 text-xs">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-[#191817]">
                          Step {item.step}
                        </span>
                        {item.timestamp && (
                          <span className="text-[11px] text-[#8C8780]">
                            {new Date(item.timestamp).toLocaleTimeString()}
                          </span>
                        )}
                      </div>
                      {item.content && (
                        <p className="text-[#524F4B] leading-relaxed font-mono text-[11px] bg-[#FAF9F7] p-2.5 rounded border border-[#E8E5DC]">
                          {item.content}
                        </p>
                      )}
                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-[#047857] hover:underline inline-flex items-center gap-1 pt-0.5"
                        >
                          <span>Resource URL</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 6. Tab Panel 3: CCPA Dark Pattern Alignment */}
        {activeTab === "ccpa" && (
          <div id="ccpa-panel" role="tabpanel" className="exitlens-card bg-white border border-[#E8E5DC]">
            <div className="p-5 sm:p-6 pb-4 border-b border-[#E8E5DC]">
              <h2 className="text-base font-serif font-bold text-[#191817]">
                India CCPA (2023) Dark Pattern Alignment
              </h2>
              <p className="text-xs text-[#64615B] mt-0.5 leading-relaxed">
                Candidate regulatory alignments for human review under the Central Consumer Protection Authority Guidelines.
              </p>
            </div>

            {report.ccpa_alignment.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#64615B]">
                No dark pattern alignments flagged for this service.
              </div>
            ) : (
              <div className="divide-y divide-[#E8E5DC]">
                {report.ccpa_alignment.map((ccpa, idx) => (
                  <div key={idx} className="p-5 sm:p-6 space-y-1.5 text-xs hover:bg-[#FAF9F7]/50 transition-colors duration-150">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-[#191817] uppercase tracking-wide">
                        {ccpa.pattern.replace(/_/g, " ")}
                      </span>
                      <span className="text-[11px] text-[#8C8780] font-mono">
                        Status: candidate review
                      </span>
                    </div>
                    <p className="text-[#524F4B] leading-relaxed">
                      {ccpa.rationale}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* 7. Limitations & Safe Scope Reassurance */}
      {report.limitations && report.limitations.length > 0 && (
        <div className="p-4 sm:p-5 rounded-xl bg-[#FAF9F7] border border-[#E8E5DC] space-y-2 text-xs text-[#64615B]">
          <span className="font-semibold uppercase tracking-wider text-[#8C8780] text-[11px]">
            Audit Scope &amp; Limitations
          </span>
          <ul className="space-y-1 list-disc list-inside">
            {report.limitations.map((lim, idx) => (
              <li key={idx}>{lim}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 8. Footer Actions */}
      <div className="flex items-center justify-between pt-2 no-print text-xs">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-[#64615B] hover:text-[#191817] transition-colors duration-200"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Home</span>
        </Link>
        <Link
          href="/check"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg font-medium text-white bg-[#191817] hover:bg-[#2C2A28] transition-colors duration-200 shadow-sm"
        >
          <span>Audit Another Service</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
export default ReportView;
