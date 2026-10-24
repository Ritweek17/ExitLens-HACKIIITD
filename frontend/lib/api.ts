/**
 * ExitLens API Client & TypeScript Definitions
 * Strictly maps to backend/models.py and docs/api-contract.md
 */

export type EventType = "step" | "stopped" | "report_ready" | "error";

export type StopReason =
  | "pre_cancellation_boundary"
  | "blocked"
  | "account_verification_failed"
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
  test_account_ref?: string;
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
  test_account_ref?: string | null;
  account_verified?: boolean;
  streaming_url?: string | null;
  friction_signals: FrictionSignal[];
  evidence: Evidence[];
  ccpa_alignment: CcpaAlignment[];
  limitations: string[];
}

export interface ServicePreset {
  id: string;
  service: string;
  category: string;
  demo_path: string;
  default_start_url?: string | null;
  default_test_account_ref?: string | null;
  description: string;
  expected_outcome: AuditOutcome;
}

export interface TestAccountPublic {
  id: string;
  service: string;
  masked_identifier: string;
  kind: "dedicated_test";
  has_cloud_credentials: boolean;
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
  if (data.test_account_ref?.trim()) {
    payload.test_account_ref = data.test_account_ref.trim();
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

async function fetchCollection<T>(path: string): Promise<T[]> {
  let res: Response;
  try {
    res = await fetch(`${getApiBaseUrl()}${path}`, {
      method: "GET",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Network error";
    throw new ApiClientError(`Unable to reach ExitLens backend at ${getApiBaseUrl()}. (${msg})`, "network_error", 0);
  }
  if (!res.ok) {
    throw new ApiClientError(`Failed to load ${path.slice(1)} (HTTP ${res.status})`, "request_failed", res.status);
  }
  return (await res.json()) as T[];
}

export function fetchPresets(): Promise<ServicePreset[]> {
  return fetchCollection<ServicePreset>("/presets");
}

export function fetchTestAccounts(): Promise<TestAccountPublic[]> {
  return fetchCollection<TestAccountPublic>("/test-accounts");
}

export async function stopRun(
  runId: string,
  reason: StopReason = "user_stopped"
): Promise<{ run_id: string; status: "stopped"; stop_reason: StopReason }> {
  let res: Response;
  try {
    res = await fetch(`${getApiBaseUrl()}/runs/${encodeURIComponent(runId)}/stop`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ reason }),
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Network error";
    throw new ApiClientError(`Unable to reach ExitLens backend at ${getApiBaseUrl()}. (${msg})`, "network_error", 0);
  }
  if (!res.ok) {
    let errorCode = "request_failed";
    let errorMessage = `Failed to stop audit (HTTP ${res.status})`;
    try {
      const body = await res.json();
      errorCode = body?.error?.code || errorCode;
      errorMessage = body?.error?.message || errorMessage;
    } catch {
      // Keep the HTTP status message when the server has no JSON error body.
    }
    throw new ApiClientError(errorMessage, errorCode, res.status);
  }
  return (await res.json()) as { run_id: string; status: "stopped"; stop_reason: StopReason };
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
