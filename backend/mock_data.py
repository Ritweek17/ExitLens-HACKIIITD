"""Mock run data, curated Indian OTT presets & demo fallback path (Box E)."""

from datetime import datetime, timezone

from models import CcpaAlignment, Evidence, FrictionSignal, Report, RunEvent, ServicePreset
from scoring import score_signals

PRESETS: list[ServicePreset] = [
    ServicePreset(
        id="streamflix",
        service="StreamFlix India",
        category="Video OTT",
        demo_path="/demo-site/",
        default_start_url="https://help.netflix.com/en/node/407",
        description="7-step buried cancellation flow with 11px muted link, 50% retention wall, and guilt-shaming copy.",
        expected_outcome="completed_with_evidence",
    ),
    ServicePreset(
        id="ganaplus",
        service="GanaPlus Music",
        category="Audio Streaming",
        demo_path="/demo-site/music.html",
        default_start_url="https://support.spotify.com/in-en/article/cancel-premium/",
        description="6-step UPI AutoPay exit with FAQ redirect loop, mandatory exit survey, ₹19 flash offer, and trick copy.",
        expected_outcome="completed_with_evidence",
    ),
    ServicePreset(
        id="quickcart",
        service="QuickCart Pro",
        category="Quick Commerce Membership",
        demo_path="/demo-site/fair.html",
        default_start_url="https://support.google.com/youtube/answer/6308278?hl=en-IN",
        description="Clean 2-step CCPA-compliant cancellation benchmark with equal visual hierarchy and zero dark patterns.",
        expected_outcome="completed_with_evidence",
    ),
    ServicePreset(
        id="cineveil",
        service="CineVeil VIP",
        category="Video OTT (Barrier Gate)",
        demo_path="/demo-site/blocked.html",
        default_start_url="https://www.netflix.com/youraccount",
        description="Simulates a Cloudflare Error 1200 / CAPTCHA + SMS OTP wall demonstrating Box E barrier detection.",
        expected_outcome="human_required",
    ),
]

MOCK_STEPS = [
    "Opened account page",
    "Clicked 'Settings'",
    "Clicked 'Membership & billing'",
    "Clicked 'Manage plan'",
    "Dismissed retention offer '50% off for 3 months'",
    "Reached 'Are you sure?' confirm-shaming dialog",
    "Found final 'Confirm cancellation' button - stopped (safety gate)",
]

GANAPLUS_STEPS = [
    "Opened My GanaPlus Plus account page",
    "Clicked 'Cancel Auto-Pay' - redirected to Help Center FAQ loop",
    "Returned to Account and opened 'Billing & AutoPay Settings'",
    "Clicked tiny 'Modify or terminate subscription' link and completed mandatory exit survey",
    "Declined '₹19/month flash retention offer'",
    "Reached final confirmation screen and stopped before 'Confirm cancellation' button (safety gate)",
]

QUICKCART_STEPS = [
    "Opened QuickCart Pro Membership Settings and clicked 'Cancel Membership'",
    "Reached Confirm Cancellation screen - stopped before clicking 'Confirm cancellation' (safety gate)",
]

CINEVEIL_STEPS = [
    "Opened CineVeil VIP Account Overview and clicked 'Manage Subscription & Billing'",
    "Encountered Cloudflare Error 1200 CAPTCHA & SMS OTP verification gate - stopped (blocked)",
]


def now() -> datetime:
    return datetime.now(timezone.utc)


def mock_step_event(step: int, label: str) -> RunEvent:
    return RunEvent(type="step", step=step, label=label, timestamp=now())


def resolve_preset_key(service: str, start_url: str | None = None) -> str:
    url_lower = (start_url or "").lower()
    svc_lower = (service or "").lower()
    if "music.html" in url_lower or "ganaplus" in svc_lower or "gaana" in svc_lower:
        return "ganaplus"
    if "fair.html" in url_lower or "quickcart" in svc_lower or "fair" in svc_lower:
        return "quickcart"
    if "blocked.html" in url_lower or "cineveil" in svc_lower or "blocked" in svc_lower:
        return "cineveil"
    return "streamflix"


def resolve_preset_demo_path(service: str, start_url: str | None = None) -> str:
    key = resolve_preset_key(service, start_url)
    for preset in PRESETS:
        if preset.id == key:
            return preset.demo_path
    return "/demo-site/"


def mock_steps_for_run(service: str, start_url: str | None = None) -> list[str]:
    key = resolve_preset_key(service, start_url)
    if key == "ganaplus":
        return GANAPLUS_STEPS
    if key == "quickcart":
        return QUICKCART_STEPS
    if key == "cineveil":
        return CINEVEIL_STEPS
    return MOCK_STEPS


def mock_report(run_id: str, service: str, start_url: str | None = None) -> Report:
    key = resolve_preset_key(service, start_url)
    ts = now()

    if key == "cineveil":
        return Report(
            run_id=run_id,
            service=service,
            outcome="human_required",
            friction_score=0,
            safety_gate_stopped=False,
            stop_reason="blocked",
            friction_signals=[],
            evidence=[
                Evidence(
                    id="ev_block",
                    step=2,
                    kind="text",
                    timestamp=ts,
                    content="Error 1200: Verify you are human. Bot detection triggered; CAPTCHA challenge and 6-digit SMS OTP required.",
                )
            ],
            ccpa_alignment=[],
            limitations=[
                "DEMO FALLBACK DATA - deterministic mock audit path.",
                "Barrier detected (Agent complete != verified outcome): Blocked by Cloudflare Error 1200 CAPTCHA and SMS OTP gate.",
                "Human intervention or an authenticated session is required to continue.",
            ],
        )

    if key == "quickcart":
        return Report(
            run_id=run_id,
            service=service,
            outcome="completed_with_evidence",
            friction_score=0,
            safety_gate_stopped=True,
            stop_reason="pre_cancellation_boundary",
            friction_signals=[],
            evidence=[
                Evidence(
                    id="ev_1",
                    step=2,
                    kind="text",
                    timestamp=ts,
                    content="Direct 2-step exit path ('Cancel Membership' -> 'Confirm cancellation') with equal button styling and clear billing cycle notice.",
                )
            ],
            ccpa_alignment=[],
            limitations=[
                "DEMO FALLBACK DATA - deterministic mock audit path.",
                "Safety gate enforced: stopped before clicking final 'Confirm cancellation' button.",
            ],
        )

    if key == "ganaplus":
        evidence = [
            Evidence(
                id="ev_1",
                step=2,
                kind="text",
                timestamp=ts,
                content="Clicking 'Cancel Auto-Pay' redirected to 'Help Center: How Auto-Pay Works' instead of cancellation controls.",
            ),
            Evidence(
                id="ev_2",
                step=3,
                kind="text",
                timestamp=ts,
                content="Primary button 'Keep UPI AutoPay Active' (18px green) vs 11px muted link 'Modify or terminate subscription'.",
            ),
            Evidence(
                id="ev_3",
                step=4,
                kind="text",
                timestamp=ts,
                content="'Submit mandatory survey & continue' button is disabled until a cancellation reason radio button is selected.",
            ),
            Evidence(
                id="ev_4",
                step=5,
                kind="text",
                timestamp=ts,
                content="Special Flash Offer! Ends in 02:00 - Stay on GanaPlus Unlimited for just ₹19/month for the next 2 months!",
            ),
            Evidence(
                id="ev_5",
                step=6,
                kind="text",
                timestamp=ts,
                content="Primary button reads 'Do not cancel my GanaPlus subscription' above tiny 'Confirm cancellation' link.",
            ),
        ]
        raw_signals = [
            FrictionSignal(
                id="sig_1",
                indicator="extra_steps",
                title="6 steps required to reach the UPI AutoPay cancellation boundary",
                severity="medium",
                description="Reaching the final cancellation control takes 6 navigation steps across redirect and survey screens.",
                step_refs=[1, 2, 3, 4, 5, 6],
                evidence_ids=["ev_1"],
            ),
            FrictionSignal(
                id="sig_2",
                indicator="redirects",
                title="'Cancel Auto-Pay' button redirects to a Help Center FAQ loop",
                severity="medium",
                description="Top-level cancel link misdirects the user to an informational FAQ page that loops back to Account.",
                step_refs=[2],
                evidence_ids=["ev_1"],
            ),
            FrictionSignal(
                id="sig_3",
                indicator="hidden_cancel",
                title="Exit control disguised as 'Modify or terminate subscription' in 11px grey text",
                severity="high",
                description="Actual cancellation path is buried inside Billing Settings in low-contrast 11px text.",
                step_refs=[3],
                evidence_ids=["ev_2"],
            ),
            FrictionSignal(
                id="sig_4",
                indicator="forced_reason",
                title="Mandatory exit survey blocks continuation until a reason is selected",
                severity="medium",
                description="Continue button stays disabled until the user completes a mandatory exit survey.",
                step_refs=[4],
                evidence_ids=["ev_3"],
            ),
            FrictionSignal(
                id="sig_5",
                indicator="retention_offer",
                title="Time-pressured ₹19/month flash offer interrupts exit",
                severity="low",
                description="An urgent countdown retention offer must be declined before reaching final confirmation.",
                step_refs=[5],
                evidence_ids=["ev_4"],
            ),
            FrictionSignal(
                id="sig_6",
                indicator="unclear_copy",
                title="Confusing negative phrasing ('Do not cancel my GanaPlus subscription')",
                severity="medium",
                description="Final screen highlights 'Do not cancel my GanaPlus subscription' as the primary button to induce misclicks.",
                step_refs=[6],
                evidence_ids=["ev_5"],
            ),
        ]
        total_score, scored_signals = score_signals(
            raw_signals, evidence, total_steps=len(GANAPLUS_STEPS)
        )
        ccpa = [
            CcpaAlignment(
                pattern="subscription_trap",
                signal_ids=["sig_1", "sig_2"],
                rationale="Top-level 'Cancel Auto-Pay' redirects to an FAQ loop, forcing a 6-step path to exit.",
            ),
            CcpaAlignment(
                pattern="interface_interference",
                signal_ids=["sig_3"],
                rationale="Visual hierarchy strongly favours 'Keep UPI AutoPay Active' over the 11px grey termination link.",
            ),
            CcpaAlignment(
                pattern="forced_action",
                signal_ids=["sig_4"],
                rationale="User cannot proceed to cancel without completing a mandatory reason selection survey.",
            ),
            CcpaAlignment(
                pattern="false_urgency",
                signal_ids=["sig_5"],
                rationale="Countdown timer ('Ends in 02:00') pressures the user during the cancellation flow.",
            ),
            CcpaAlignment(
                pattern="trick_question",
                signal_ids=["sig_6"],
                rationale="Prominent negative CTA ('Do not cancel...') creates ambiguity at the final step.",
            ),
        ]
        return Report(
            run_id=run_id,
            service=service,
            outcome="completed_with_evidence",
            friction_score=total_score,
            safety_gate_stopped=True,
            stop_reason="pre_cancellation_boundary",
            friction_signals=scored_signals,
            evidence=evidence,
            ccpa_alignment=ccpa,
            limitations=[
                "DEMO FALLBACK DATA - deterministic mock audit path.",
                "Safety gate enforced: stopped before clicking final 'Confirm cancellation' button.",
            ],
        )

    # Default profile: StreamFlix India / Example OTT
    evidence = [
        Evidence(
            id="ev_1",
            step=4,
            kind="text",
            timestamp=ts,
            content="Navigation path required 4 clicks across 3 nested menus: Account -> Settings -> Membership & billing -> Manage plan.",
        ),
        Evidence(
            id="ev_2",
            step=4,
            kind="text",
            timestamp=ts,
            content="Primary CTA is 'Keep my Premium plan' (20px red button); cancel link 'I still want to cancel' is 11px muted grey.",
        ),
        Evidence(
            id="ev_3",
            step=5,
            kind="text",
            timestamp=ts,
            content="Wait! Get 50% off for 3 months. Only for you, only today.",
        ),
        Evidence(
            id="ev_4",
            step=6,
            kind="text",
            timestamp=ts,
            content="Are you sure? You'll lose all your favourite shows forever, and your family will miss movie night.",
        ),
    ]
    raw_signals = [
        FrictionSignal(
            id="sig_1",
            indicator="extra_steps",
            title="7 steps required to reach the cancellation boundary",
            severity="high",
            description="Reaching the final cancellation control takes 7 navigation steps instead of a direct 1-2 click exit.",
            step_refs=[1, 2, 3, 4, 5, 6, 7],
            evidence_ids=["ev_1"],
        ),
        FrictionSignal(
            id="sig_2",
            indicator="hidden_cancel",
            title="Cancel option buried 3 menus deep with de-emphasized styling",
            severity="high",
            description="The cancel link is hidden under Settings > Membership & billing > Manage plan and styled in low-contrast 11px text.",
            step_refs=[2, 3, 4],
            evidence_ids=["ev_1", "ev_2"],
        ),
        FrictionSignal(
            id="sig_3",
            indicator="retention_offer",
            title="Retention discount wall interrupts the exit path",
            severity="low",
            description="A '50% off for 3 months' interstitial must be dismissed before reaching confirmation.",
            step_refs=[5],
            evidence_ids=["ev_3"],
        ),
        FrictionSignal(
            id="sig_4",
            indicator="unclear_copy",
            title="Guilt-tripping confirmation dialog (confirm-shaming)",
            severity="medium",
            description="The confirmation screen uses emotional guilt ('your family will miss movie night') while highlighting 'Stay and keep watching'.",
            step_refs=[6],
            evidence_ids=["ev_4"],
        ),
    ]
    total_score, scored_signals = score_signals(raw_signals, evidence, total_steps=len(MOCK_STEPS))

    ccpa = [
        CcpaAlignment(
            pattern="subscription_trap",
            signal_ids=["sig_1", "sig_2"],
            rationale="Cancellation requires navigating a 7-step buried path and visually subordinated controls.",
        ),
        CcpaAlignment(
            pattern="interface_interference",
            signal_ids=["sig_2"],
            rationale="Visual hierarchy strongly favours 'Keep my Premium plan' over the 11px grey cancel action.",
        ),
        CcpaAlignment(
            pattern="nagging",
            signal_ids=["sig_3"],
            rationale="Retention interstitial interrupts the user's explicit intent to cancel.",
        ),
        CcpaAlignment(
            pattern="confirm_shaming",
            signal_ids=["sig_4"],
            rationale="Dialog copy uses guilt to steer the user away from cancelling.",
        ),
    ]
    return Report(
        run_id=run_id,
        service=service,
        outcome="completed_with_evidence",
        friction_score=total_score,
        safety_gate_stopped=True,
        stop_reason="pre_cancellation_boundary",
        friction_signals=scored_signals,
        evidence=evidence,
        ccpa_alignment=ccpa,
        limitations=[
            "DEMO FALLBACK DATA - deterministic mock audit path.",
            "Safety gate enforced: stopped before clicking final 'Confirm cancellation' button.",
        ],
    )
