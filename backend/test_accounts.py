"""Server-managed Dedicated Test Account Registry (Box A / v1 & v2 safety gate).

ExitLens never accepts passwords or raw credentials in API requests, and never audits a
real personal account. Every `test_account_ref` must resolve in this server-side registry
to an account classified as `dedicated_test`.
"""

from dataclasses import dataclass, field
import json
import os


@dataclass(frozen=True)
class TestAccountRecord:
    id: str
    service: str
    masked_identifier: str
    kind: str = "dedicated_test"
    profile_id: str | None = None
    credential_item_ids: list[str] = field(default_factory=list)


BUILTIN_TEST_ACCOUNTS: tuple[TestAccountRecord, ...] = (
    TestAccountRecord(
        id="tacct_streamflix_in",
        service="StreamFlix India",
        masked_identifier="audit.streamflix@test.exitlens.in",
        kind="dedicated_test",
    ),
    TestAccountRecord(
        id="tacct_ganaplus_in",
        service="GanaPlus Music",
        masked_identifier="audit.ganaplus@test.exitlens.in",
        kind="dedicated_test",
    ),
    TestAccountRecord(
        id="tacct_quickcart_in",
        service="QuickCart Pro",
        masked_identifier="audit.quickcart@test.exitlens.in",
        kind="dedicated_test",
    ),
    TestAccountRecord(
        id="tacct_cineveil_in",
        service="CineVeil VIP",
        masked_identifier="audit.cineveil@test.exitlens.in",
        kind="dedicated_test",
    ),
)


def _load_accounts_map() -> dict[str, TestAccountRecord]:
    env_profile = (os.getenv("TINYFISH_PROFILE_ID") or "").strip() or None
    env_creds = [
        c.strip()
        for c in (os.getenv("TINYFISH_CREDENTIAL_ITEM_IDS") or "").split(",")
        if c.strip()
    ]

    accounts: dict[str, TestAccountRecord] = {}
    for item in BUILTIN_TEST_ACCOUNTS:
        accounts[item.id] = TestAccountRecord(
            id=item.id,
            service=item.service,
            masked_identifier=item.masked_identifier,
            kind=item.kind,
            profile_id=item.profile_id or env_profile,
            credential_item_ids=list(item.credential_item_ids or env_creds),
        )

    # Optional JSON env override to register live external dedicated test accounts:
    # TEST_ACCOUNTS_JSON='[{"id":"tacct_live_1","service":"Live OTT","masked_identifier":"test@exitlens.in","profile_id":"prof_123"}]'
    raw_json = (os.getenv("TEST_ACCOUNTS_JSON") or "").strip()
    if raw_json:
        try:
            parsed = json.loads(raw_json)
            if isinstance(parsed, list):
                for entry in parsed:
                    if isinstance(entry, dict) and entry.get("id") and entry.get("service"):
                        acct_id = str(entry["id"]).strip()
                        creds = entry.get("credential_item_ids")
                        cred_list = (
                            [str(c).strip() for c in creds if str(c).strip()]
                            if isinstance(creds, list)
                            else env_creds
                        )
                        accounts[acct_id] = TestAccountRecord(
                            id=acct_id,
                            service=str(entry["service"]).strip(),
                            masked_identifier=str(
                                entry.get("masked_identifier") or f"{acct_id}@test.exitlens.in"
                            ).strip(),
                            kind=str(entry.get("kind") or "dedicated_test").strip(),
                            profile_id=(str(entry.get("profile_id") or "").strip() or env_profile),
                            credential_item_ids=cred_list,
                        )
        except Exception:  # noqa: BLE001 - ignore malformed env JSON
            pass

    return accounts


def list_dedicated_test_accounts() -> list[TestAccountRecord]:
    """Return all registered accounts classified as `dedicated_test`."""
    return [a for a in _load_accounts_map().values() if a.kind == "dedicated_test"]


def verify_dedicated_test_account(test_account_ref: str) -> TestAccountRecord | None:
    """Resolve `test_account_ref` iff it exists and is classified as `dedicated_test`."""
    ref = (test_account_ref or "").strip()
    if not ref:
        return None
    record = _load_accounts_map().get(ref)
    if record is None or record.kind != "dedicated_test":
        return None
    return record
