"""Unit and integration test suite for the ExitLens backend (v1 Contract + Boxes B, D, E)."""

import json
import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

import main
from models import Evidence, FrictionSignal
from orchestrator import (
    detect_barrier,
    normalise_and_build_report,
    resolve_effective_start_url,
    should_use_live_tinyfish,
)
from scoring import compute_extra_steps_weight, score_signals


class ScoringEngineTests(unittest.TestCase):
    def test_graduated_extra_steps_weights(self) -> None:
        self.assertEqual(compute_extra_steps_weight(1), (0, "low"))
        self.assertEqual(compute_extra_steps_weight(2), (0, "low"))
        self.assertEqual(compute_extra_steps_weight(3), (5, "low"))
        self.assertEqual(compute_extra_steps_weight(5), (15, "medium"))
        self.assertEqual(compute_extra_steps_weight(7), (25, "high"))
        self.assertEqual(compute_extra_steps_weight(8), (30, "high"))
        self.assertEqual(compute_extra_steps_weight(12), (30, "high"))

    def test_evidence_gating_and_deduplication(self) -> None:
        ev = [Evidence(id="ev_1", step=3, kind="text", content="Observed buried cancel link")]
        signals = [
            FrictionSignal(
                id="sig_1",
                indicator="hidden_cancel",
                title="First hidden cancel",
                severity="high",
                description="Buried link",
                evidence_ids=["ev_1"],
            ),
            FrictionSignal(
                id="sig_2",
                indicator="hidden_cancel",
                title="Duplicate hidden cancel",
                severity="high",
                description="Second instance in same category",
                evidence_ids=["ev_1"],
            ),
            FrictionSignal(
                id="sig_3",
                indicator="retention_offer",
                title="Unverified retention offer",
                severity="low",
                description="Missing evidence",
                evidence_ids=["ev_missing"],
            ),
        ]
        total, scored = score_signals(signals, ev, total_steps=4)
        self.assertEqual(scored[0].verified, True)
        self.assertEqual(scored[0].weight, 20)
        # Duplicate indicator stays verified=True but receives weight=0
        self.assertEqual(scored[1].verified, True)
        self.assertEqual(scored[1].weight, 0)
        # Missing evidence sets verified=False and weight=0
        self.assertEqual(scored[2].verified, False)
        self.assertEqual(scored[2].weight, 0)
        self.assertEqual(total, sum(s.weight for s in scored))
        self.assertEqual(total, 20)

    def test_max_score_across_all_six_indicators_is_100(self) -> None:
        ev = [Evidence(id="ev_1", step=8, kind="text", content="Verified evidence")]
        indicators = [
            "extra_steps",
            "hidden_cancel",
            "redirects",
            "forced_reason",
            "retention_offer",
            "unclear_copy",
        ]
        signals = [
            FrictionSignal(
                id=f"sig_{i}",
                indicator=ind,  # type: ignore[arg-type]
                title=ind,
                severity="medium",
                description=ind,
                evidence_ids=["ev_1"],
            )
            for i, ind in enumerate(indicators, start=1)
        ]
        total, scored = score_signals(signals, ev, total_steps=8)
        self.assertEqual(total, 100)
        self.assertEqual(total, sum(s.weight for s in scored))


class OrchestratorAndBarrierTests(unittest.TestCase):
    def test_detect_barrier_ignores_negated_mentions_when_not_blocked(self) -> None:
        result_json = {
            "blocked": False,
            "block_reason": "No captcha or cloudflare wall encountered",
            "stopped_at_button": "Confirm cancellation",
            "cancellation_completed": False,
            "findings": [
                {
                    "indicator": "hidden_cancel",
                    "title": "Hidden cancel",
                    "description": "Reached without captcha",
                    "step_number": 2,
                    "evidence_quote": "I still want to cancel",
                    "ccpa_pattern": "interface_interference",
                }
            ],
        }
        self.assertIsNone(detect_barrier(["Opened page", "Clicked settings"], result_json))

    def test_detect_barrier_catches_cloudflare_and_blocked_flag(self) -> None:
        self.assertIsNotNone(
            detect_barrier(["Clicked manage", "Cloudflare Error 1200 page shown"], None)
        )
        self.assertIsNotNone(
            detect_barrier([], {"blocked": True, "block_reason": "OTP required"})
        )

    def test_normaliser_filters_meta_steps_and_maps_extra_steps_to_subscription_trap(self) -> None:
        ts = datetime.now(timezone.utc)
        steps = [
            (1, "Navigate to account", ts),
            (2, "Click Settings", ts),
            (3, "Click Membership & billing", ts),
            (4, "Click Manage plan", ts),
            (5, "Dismiss retention offer", ts),
            (6, "Reach final confirm dialog", ts),
            (7, "Get full page content for final step analysis", ts),
            (8, "Submit cancellation journey audit findings", ts),
        ]
        result_json = {
            "blocked": False,
            "block_reason": None,
            "stopped_at_button": "Confirm cancellation",
            "cancellation_completed": False,
            "findings": [
                {
                    "indicator": "extra_steps",
                    "title": "Multi-step journey",
                    "description": "Took 6 UI steps",
                    "step_number": 1,
                    "evidence_quote": "Settings > Membership > Manage plan",
                    "ccpa_pattern": "interface_interference",
                }
            ],
        }
        report = normalise_and_build_report("run_test1", "StreamFlix India", steps, None, result_json)
        self.assertEqual(report.outcome, "completed_with_evidence")
        self.assertTrue(report.safety_gate_stopped)
        # 6 UI steps (meta steps 7 & 8 excluded) -> (6 - 2) * 5 = 20 pts
        self.assertEqual(report.friction_score, 20)
        self.assertEqual(report.friction_signals[0].step_refs, [1, 2, 3, 4, 5, 6])
        self.assertEqual(report.ccpa_alignment[0].pattern, "subscription_trap")

    def test_normaliser_handles_clean_two_step_fair_flow(self) -> None:
        ts = datetime.now(timezone.utc)
        steps = [
            (1, "Navigate to demo site for cancellation journey audit", ts),
            (2, "Understand page content before interacting", ts),
            (3, "Start the cancellation flow", ts),
            (4, "Visual inspection of confirmation screen layout", ts),
            (5, "Submit cancellation journey audit findings", ts),
        ]
        result_json = {
            "blocked": False,
            "block_reason": None,
            "stopped_at_button": "Confirm cancellation",
            "cancellation_completed": False,
            "findings": [],
        }
        report = normalise_and_build_report("run_fair", "QuickCart Pro", steps, None, result_json)
        self.assertEqual(report.outcome, "completed_with_evidence")
        self.assertEqual(report.friction_score, 0)
        self.assertEqual(report.friction_signals, [])
        self.assertEqual(len(report.evidence), 1)
        self.assertTrue(report.safety_gate_stopped)

    def test_should_use_live_tinyfish_respects_fallback_hosts_and_public_base(self) -> None:
        import os

        old_base = os.environ.pop("PUBLIC_DEMO_BASE_URL", None)
        try:
            self.assertFalse(should_use_live_tinyfish(None))
            self.assertFalse(should_use_live_tinyfish("https://example.in/account"))
            self.assertFalse(should_use_live_tinyfish("https://localhost:8000/demo-site/"))

            os.environ["PUBLIC_DEMO_BASE_URL"] = "https://demo123.lhr.life/"
            self.assertEqual(
                resolve_effective_start_url("GanaPlus Music", None),
                "https://demo123.lhr.life/demo-site/music.html",
            )
            self.assertEqual(
                resolve_effective_start_url("CineVeil VIP", "https://example.in/account"),
                "https://demo123.lhr.life/demo-site/blocked.html",
            )
        finally:
            if old_base is not None:
                os.environ["PUBLIC_DEMO_BASE_URL"] = old_base
            else:
                os.environ.pop("PUBLIC_DEMO_BASE_URL", None)


class ApiContractIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        main.MOCK_STEP_DELAY_SECONDS = 0.0
        self.client = TestClient(main.app)

    def test_health_and_presets_and_demo_sites(self) -> None:
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        presets = self.client.get("/presets").json()
        self.assertEqual(len(presets), 4)
        for p in presets:
            res = self.client.get(p["demo_path"])
            self.assertEqual(res.status_code, 200)

    def test_post_runs_approval_and_https_gates(self) -> None:
        r_unapproved = self.client.post(
            "/runs",
            json={
                "service": "StreamFlix India",
                "human_approved": False,
                "test_account_confirmed": True,
            },
        )
        self.assertEqual(r_unapproved.status_code, 409)
        self.assertEqual(r_unapproved.json()["error"]["code"], "approval_required")

        r_http = self.client.post(
            "/runs",
            json={
                "service": "StreamFlix India",
                "start_url": "http://example.in/cancel",
                "human_approved": True,
                "test_account_confirmed": True,
            },
        )
        self.assertEqual(r_http.status_code, 422)
        self.assertEqual(r_http.json()["error"]["code"], "invalid_start_url")

    def test_all_curated_presets_stream_and_report(self) -> None:
        cases = [
            ("StreamFlix India", "completed_with_evidence", "pre_cancellation_boundary", 65),
            ("GanaPlus Music", "completed_with_evidence", "pre_cancellation_boundary", 90),
            ("QuickCart Pro", "completed_with_evidence", "pre_cancellation_boundary", 0),
            ("CineVeil VIP", "human_required", "blocked", 0),
        ]
        for service, expected_outcome, expected_stop, expected_score in cases:
            with self.subTest(service=service):
                created = self.client.post(
                    "/runs",
                    json={
                        "service": service,
                        "human_approved": True,
                        "test_account_confirmed": True,
                    },
                )
                self.assertEqual(created.status_code, 201)
                run_id = created.json()["run_id"]

                events_res = self.client.get(f"/runs/{run_id}/events")
                self.assertEqual(events_res.status_code, 200)
                events = [
                    json.loads(line[6:])
                    for line in events_res.text.splitlines()
                    if line.startswith("data: ")
                ]
                self.assertGreaterEqual(len(events), 3)
                self.assertEqual(events[-2]["type"], "stopped")
                self.assertEqual(events[-2]["stop_reason"], expected_stop)
                self.assertEqual(events[-1]["type"], "report_ready")

                report = self.client.get(f"/runs/{run_id}/report").json()
                self.assertEqual(report["outcome"], expected_outcome)
                self.assertEqual(report["stop_reason"], expected_stop)
                self.assertEqual(report["friction_score"], expected_score)
                self.assertEqual(
                    report["friction_score"],
                    sum(s["weight"] for s in report["friction_signals"]),
                )


if __name__ == "__main__":
    unittest.main()
