"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Loader2,
  ShieldCheck,
  AlertCircle,
  ExternalLink,
  ArrowRight,
  RefreshCw,
  Eye,
  CheckCircle2,
} from "lucide-react";
import {
  RunEvent,
  EventType,
  StopReason,
  getRunEventsUrl,
  getApiBaseUrl,
} from "@/lib/api";

interface RunMonitorProps {
  runId: string;
}

export function RunMonitor({ runId }: RunMonitorProps) {
  const router = useRouter();

  const [events, setEvents] = useState<RunEvent[]>([]);
  const [status, setStatus] = useState<EventType | "connecting">("connecting");
  const [stopReason, setStopReason] = useState<StopReason | null>(null);
  const [streamingUrl, setStreamingUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const hasFinishedRef = useRef(false);

  useEffect(() => {
    if (!runId) return;

    const url = getRunEventsUrl(runId);
    hasFinishedRef.current = false;
    setStatus("connecting");
    setErrorMessage(null);

    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onopen = () => {
      setStatus("step");
    };

    es.onmessage = (e) => {
      try {
        const data: RunEvent = JSON.parse(e.data);

        setEvents((prev) => {
          // Avoid duplicate steps with same step number and label
          if (
            prev.some(
              (p) => p.step === data.step && p.label === data.label && p.type === data.type
            )
          ) {
            return prev;
          }
          return [...prev, data];
        });

        if (data.streaming_url) {
          setStreamingUrl(data.streaming_url);
        }

        if (data.type === "stopped") {
          setStatus("stopped");
          if (data.stop_reason) {
            setStopReason(data.stop_reason);
          }
        } else if (data.type === "report_ready") {
          setStatus("report_ready");
          hasFinishedRef.current = true;
          es.close();
          // Navigate to report
          setTimeout(() => {
            router.push(`/report/${encodeURIComponent(runId)}`);
          }, 800);
        } else if (data.type === "error") {
          setStatus("error");
          setErrorMessage(data.label || "An error occurred during the audit walk.");
          hasFinishedRef.current = true;
          es.close();
        }
      } catch (err) {
        console.error("Failed to parse SSE event data:", err);
      }
    };

    es.onerror = () => {
      // If we finished cleanly, ignore close errors
      if (hasFinishedRef.current) return;

      // EventSource failed or server closed connection
      setStatus("error");
      setErrorMessage(
        `Lost connection to the audit stream (${getApiBaseUrl()}). The run may have completed, or the backend is unreachable.`
      );
      es.close();
    };

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [runId, router]);

  function handleRetry() {
    window.location.reload();
  }

  const stepEvents = events.filter((e) => e.type === "step");
  const lastStep = stepEvents[stepEvents.length - 1];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Top Status Card */}
      <div className="exitlens-card p-6 bg-white border border-[#E8E5DC]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#E8E5DC]">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#8C8780]">
                Active Audit Session
              </span>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-[#F3F1EA] text-[#191817] font-semibold">
                {runId}
              </span>
            </div>
            <h2 className="text-xl font-serif font-bold text-[#191817] mt-1">
              Observing Cancellation Journey
            </h2>
          </div>

          {/* Dynamic Status Badge */}
          <div>
            {status === "connecting" && (
              <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-[#F3F1EA] text-[#64615B]">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Connecting to runner...
              </span>
            )}
            {status === "step" && (
              <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#FEF3C7] text-[#92400E] border border-[#FDE68A]">
                <span className="w-2 h-2 rounded-full bg-[#D97706] animate-pulse" />
                Live Walk in Progress
              </span>
            )}
            {status === "stopped" && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#D1FAE5] text-[#065F46] border border-[#A7F3D0]">
                <ShieldCheck className="w-4 h-4 text-[#047857]" />
                Boundary Reached &amp; Stopped
              </span>
            )}
            {status === "report_ready" && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#D1FAE5] text-[#065F46] border border-[#A7F3D0]">
                <CheckCircle2 className="w-4 h-4 text-[#047857]" />
                Report Ready — Redirecting...
              </span>
            )}
            {status === "error" && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-[#FEE2E2] text-[#991B1B] border border-[#FECACA]">
                <AlertCircle className="w-4 h-4 text-[#DC2626]" />
                Audit Interrupted
              </span>
            )}
          </div>
        </div>

        {/* Live Step Tracker Summary */}
        <div className="pt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3 rounded-lg bg-[#FAF9F7] border border-[#E8E5DC]">
            <span className="text-[#8C8780] font-medium">Steps Observed</span>
            <p className="text-lg font-serif font-bold text-[#191817] mt-0.5">
              {stepEvents.length}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-[#FAF9F7] border border-[#E8E5DC]">
            <span className="text-[#8C8780] font-medium">Safety Boundary</span>
            <p className="text-xs font-semibold text-[#047857] mt-1 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              Pre-cancellation Gate Active
            </p>
          </div>
          <div className="p-3 rounded-lg bg-[#FAF9F7] border border-[#E8E5DC]">
            <span className="text-[#8C8780] font-medium">Latest Action</span>
            <p className="text-xs text-[#191817] font-medium truncate mt-1">
              {lastStep ? lastStep.label : "Initializing runner..."}
            </p>
          </div>
        </div>
      </div>

      {/* TinyFish Live Browser Stream View (when available) */}
      {streamingUrl && (
        <div className="exitlens-card p-4 sm:p-5 bg-white border border-[#E8E5DC] space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Eye className="w-4 h-4 text-[#047857]" />
              <h3 className="text-sm font-semibold text-[#191817]">
                Live Browser Automation Stream
              </h3>
            </div>
            <a
              href={streamingUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-medium text-[#191817] hover:underline inline-flex items-center gap-1"
            >
              <span>Open stream in new tab</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          <div className="aspect-video w-full rounded-lg overflow-hidden border border-[#E8E5DC] bg-[#191817]">
            <iframe
              src={streamingUrl}
              title="Live Browser Audit Stream"
              className="w-full h-full border-0"
              allow="autoplay"
            />
          </div>
        </div>
      )}

      {/* Timeline Stream */}
      <div className="exitlens-card p-6 bg-white border border-[#E8E5DC] space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-[#191817]">
          Live Observed Steps
        </h3>

        {stepEvents.length === 0 && status !== "error" ? (
          <div className="py-12 text-center space-y-3">
            <Loader2 className="w-6 h-6 animate-spin text-[#8C8780] mx-auto" />
            <p className="text-sm text-[#64615B]">
              Starting automated navigation runner. This may take 5–15 seconds...
            </p>
          </div>
        ) : (
          <div className="space-y-3 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-[#E8E5DC]">
            {stepEvents.map((ev, idx) => (
              <div key={idx} className="relative flex items-start gap-3 pl-1">
                <div className="w-6 h-6 rounded-full bg-[#191817] text-white flex items-center justify-center text-xs font-bold shrink-0 z-10">
                  {ev.step}
                </div>
                <div className="flex-1 p-3 rounded-lg bg-[#FAF9F7] border border-[#E8E5DC]">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-[#191817]">
                      {ev.label}
                    </span>
                    <span className="text-[10px] text-[#8C8780]">
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {ev.screenshot_url && (
                    <div className="mt-2">
                      <a
                        href={ev.screenshot_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-[#047857] hover:underline"
                      >
                        View step screenshot →
                      </a>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Boundary Stop Notice */}
        {status === "stopped" && (
          <div className="p-4 rounded-xl bg-[#D1FAE5]/60 border border-[#A7F3D0] flex items-start gap-3">
            <ShieldCheck className="w-5 h-5 text-[#047857] shrink-0 mt-0.5" />
            <div className="space-y-1 text-xs text-[#065F46]">
              <p className="font-semibold text-sm">
                Safety Boundary Enforced: Audit Halted Cleanly
              </p>
              <p>
                The audit runner located the final cancellation control and verified its location. As required by policy, execution stopped before submitting cancellation ({stopReason || "pre_cancellation_boundary"}).
              </p>
              <div className="pt-2">
                <Link
                  href={`/report/${encodeURIComponent(runId)}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#047857] text-white font-medium hover:bg-[#065F46] transition-colors"
                >
                  <span>View Full Evidence Report</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Error Fallback Notice */}
        {status === "error" && (
          <div className="p-4 rounded-xl bg-[#FEF2F2] border border-[#FECACA] flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-[#DC2626] shrink-0 mt-0.5" />
            <div className="space-y-2 text-xs text-[#991B1B]">
              <p className="font-semibold text-sm">Session Notice</p>
              <p>{errorMessage}</p>
              <div className="flex flex-wrap items-center gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleRetry}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#191817] text-white hover:bg-[#2C2A28]"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry Stream</span>
                </button>
                <Link
                  href={`/report/${encodeURIComponent(runId)}`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-[#FECACA] text-[#991B1B] hover:bg-[#FEE2E2]"
                >
                  <span>Check Report Directly</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link
                  href="/check"
                  className="px-3 py-1.5 rounded-lg text-[#64615B] hover:text-[#191817]"
                >
                  Start New Audit
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
export default RunMonitor;
