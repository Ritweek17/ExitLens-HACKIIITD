/**
 * ExitLens API Client & TypeScript Definitions
 * Strictly maps to backend/models.py and docs/api-contract.md
 */

export type EventType = "step" | "stopped" | "report_ready" | "error";

export type StopReason =
  | "pre_cancellation_boundary"
  | "blocked"
  | "user_stopped"
  | "error";

export type AuditOutcome =
  | "completed_with_evidence"
  | "partial_evidence"
  | "failed"
  | "unverified"
  | "human_required";

export type Severity = "low" | "medium" | "high";

export type FrictionIndicator =
  | "extra_steps"
  | "hidden_cancel"
  | "redirects"
  | "forced_reason"
  | "retention_offer"
  | "unclear_copy";

export type EvidenceKind = "text" | "screenshot" | "url";

export type CcpaPattern =
  | "false_urgency"
  | "basket_sneaking"
  | "confirm_shaming"
  | "forced_action"
  | "subscription_trap"
  | "interface_interference"
  | "bait_and_switch"
  | "drip_pricing"
  | "disguised_advertisement"
  | "nagging"
  | "trick_question"
  | "saas_billing"
  | "rogue_malwares";

export interface RunCreateRequest {
  service: string;
  start_url?: string;
  human_approved: boolean;
  test_account_confirmed: boolean;
}

export interface RunCreatedResponse {
  run_id: string;
}

export interface RunEvent {
  type: EventType;
  step: number;
  label: string;
  timestamp: string;
  screenshot_url?: string | null;
  streaming_url?: string | null;
  stop_reason?: StopReason | null;
}

export interface FrictionSignal {
  id: string;
  indicator: FrictionIndicator;
  title: string;
  severity: Severity;
  weight: number;
  verified: boolean;
  description: string;
  step_refs: number[];
  evidence_ids: string[];
}

export interface Evidence {
  id: string;
  step: number;
  kind: EvidenceKind;
  timestamp?: string | null;
  content?: string | null;
  url?: string | null;
}

export interface CcpaAlignment {
  pattern: CcpaPattern;
  signal_ids: string[];
  status: "candidate";
  rationale: string;
}

export interface Report {
  run_id: string;
  service: string;
  outcome: AuditOutcome;
  friction_score: number;
  safety_gate_stopped: boolean;
  stop_reason: StopReason;
  streaming_url?: string | null;
  friction_signals: FrictionSignal[];
  evidence: Evidence[];
  ccpa_alignment: CcpaAlignment[];
  limitations: string[];
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
  };
}

export class ApiClientError extends Error {
  code: string;
  statusCode: number;

  constructor(message: string, code = "api_error", statusCode = 500) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.statusCode = statusCode;
  }
}

export function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (envUrl) {
    return envUrl.replace(/\/+$/, "");
  }
  return "http://localhost:8000";
}

export function getRunEventsUrl(runId: string): string {
  return `${getApiBaseUrl()}/runs/${encodeURIComponent(runId)}/events`;
}

export async function createRun(data: RunCreateRequest): Promise<RunCreatedResponse> {
  const url = `${getApiBaseUrl()}/runs`;

  const payload: Record<string, unknown> = {
    service: data.service.trim(),
    human_approved: data.human_approved,
    test_account_confirmed: data.test_account_confirmed,
  };

  if (data.start_url && data.start_url.trim()) {
    payload.start_url = data.start_url.trim();
  }

  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Network error";
    throw new ApiClientError(
      `Cannot connect to backend server at ${getApiBaseUrl()}. Please make sure the backend is running. (${msg})`,
      "network_error",
      0
    );
  }

  if (!res.ok) {
    let errorCode = "unknown_error";
    let errorMessage = `Failed to create audit (HTTP ${res.status})`;

    try {
      const errJson = await res.json();
      if (errJson?.error) {
        errorCode = errJson.error.code || errorCode;
        errorMessage = errJson.error.message || errorMessage;
      } else if (errJson?.detail) {
        if (Array.isArray(errJson.detail)) {
          errorMessage = errJson.detail.map((d: { msg?: string }) => d.msg || "").filter(Boolean).join("; ") || errorMessage;
        } else {
          errorMessage = String(errJson.detail);
        }
      }
    } catch {
      // Non-JSON error body fallback
    }

    throw new ApiClientError(errorMessage, errorCode, res.status);
  }

  return (await res.json()) as RunCreatedResponse;
}

export async function getReport(runId: string): Promise<Report> {
  const url = `${getApiBaseUrl()}/runs/${encodeURIComponent(runId)}/report`;

  let res: Response;
  try {
    res = await fetch(url, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Network error";
    throw new ApiClientError(
      `Unable to reach ExitLens backend at ${getApiBaseUrl()}. (${msg})`,
      "network_error",
      0
    );
  }

  if (!res.ok) {
    let errorCode = "unknown_error";
    let errorMessage = `Failed to fetch report (HTTP ${res.status})`;

    try {
      const errJson = await res.json();
      if (errJson?.error) {
        errorCode = errJson.error.code || errorCode;
        errorMessage = errJson.error.message || errorMessage;
      }
    } catch {
      // Non-JSON error body
    }

    throw new ApiClientError(errorMessage, errorCode, res.status);
  }

  return (await res.json()) as Report;
}

export async function checkBackendHealth(): Promise<{ ok: boolean; message?: string }> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/health`, {
      method: "GET",
      cache: "no-store",
    });
    if (res.ok) {
      return { ok: true };
    }
    return { ok: false, message: `Status ${res.status}` };
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Connection failed";
    return { ok: false, message: msg };
  }
}
