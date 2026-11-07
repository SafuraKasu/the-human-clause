"""Deterministic consent and custody module (no LLM).

Answers: "may this requester see this category of this source's data right now, and why?"
Every grant change and every access decision is appended to an immutable-by-API log, which the
orchestrator folds into the audit trail.

Rules implemented (configuration, not legal advice; the Policy agent supplies the legal analysis):
  - Patients and data custodians always see their own data.
  - Other access needs an active grant for (grantee org, source org, category, purpose).
  - Revoked/expired/not-yet-active grants deny access. Revocation is effective from `revoked_at`.
  - A patient's opt-out from a named health-information exchange blocks exchange-channel access.
  - Emergency ("break-the-glass") access is allowed only for clinicians with a justification,
    is always flagged for review, and is BLOCKED when the patient has opted out of the source's
    exchange (rule_basis cites the DHA standard section 9.7 this mirrors). A blocked emergency
    request sets `escalate=True`: a human must decide; the system never overrides silently.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Callable, Iterable

DENIAL_PRIORITY = ["REVOKED", "EXPIRED", "CATEGORY_NOT_COVERED", "PURPOSE_NOT_COVERED", "NOT_YET_ACTIVE"]
OPT_OUT_BASIS = ("DHA/HISHD/ST-09 (Standards for Health Information Consent and Access Control, 2025) "
                 "section 9.7: PHI of an opted-out patient should not be retrieved using BTG access")


def _ts(x: "str | datetime | None") -> "datetime | None":
    return datetime.fromisoformat(x) if isinstance(x, str) else x


@dataclass(frozen=True)
class Requester:
    party_id: str
    org: str
    role: str  # clinician | regulator | patient | system


@dataclass
class Grant:
    grant_id: str
    patient_id: str
    grantee_org: str
    source_org: str
    categories: frozenset
    purpose: str
    granted_at: datetime
    expires_at: "datetime | None" = None
    revoked_at: "datetime | None" = None


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason_code: str
    reason: str
    rule_basis: str = ""
    grant_id: str = ""
    emergency: bool = False
    flagged_for_review: bool = False
    escalate: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class ConsentRegistry:
    def __init__(self, patient_id: str, on_event: "Callable[[dict], None] | None" = None,
                 block_emergency_on_opt_out: bool = True):
        self.patient_id = patient_id
        self.on_event = on_event
        self.block_emergency_on_opt_out = block_emergency_on_opt_out
        self.grants: dict[str, Grant] = {}
        self.opt_outs: dict[str, datetime] = {}  # exchange name -> opted out at
        self._log: list[dict] = []

    # ---- log -----------------------------------------------------------------------------
    @property
    def log(self) -> tuple:
        return tuple(self._log)

    def _record(self, kind: str, at: datetime, **details) -> None:
        entry = {"seq": len(self._log) + 1, "kind": kind, "at": at.isoformat(), **details}
        self._log.append(entry)
        if self.on_event:
            self.on_event(entry)

    # ---- patient actions -----------------------------------------------------------------
    def grant(self, grantee_org: str, source_org: str, categories: Iterable[str], purpose: str,
              at: "str | datetime", expires_at: "str | datetime | None" = None) -> Grant:
        at = _ts(at)
        g = Grant(f"G{len(self.grants) + 1:03d}", self.patient_id, grantee_org, source_org,
                  frozenset(categories), purpose, at, _ts(expires_at))
        self.grants[g.grant_id] = g
        self._record("grant_created", at, grant_id=g.grant_id, grantee_org=grantee_org, source_org=source_org,
                     categories=sorted(g.categories), purpose=purpose,
                     expires_at=g.expires_at.isoformat() if g.expires_at else None)
        return g

    def revoke_grant(self, grant_id: str, at: "str | datetime") -> Grant:
        at = _ts(at)
        g = self.grants[grant_id]
        if g.revoked_at is None:
            g.revoked_at = at
            self._record("grant_revoked", at, grant_id=grant_id, grantee_org=g.grantee_org, source_org=g.source_org)
        return g

    def revoke_where(self, at: "str | datetime", source_org: str | None = None,
                     grantee_org: str | None = None) -> list[str]:
        """Revoke every still-active grant matching the filters. Returns the revoked grant ids."""
        ids = [g.grant_id for g in self.grants.values() if g.revoked_at is None
               and (source_org is None or g.source_org == source_org)
               and (grantee_org is None or g.grantee_org == grantee_org)]
        for gid in ids:
            self.revoke_grant(gid, at)
        return ids

    def opt_out(self, exchange: str, at: "str | datetime") -> None:
        at = _ts(at)
        self.opt_outs[exchange] = at
        self._record("exchange_opt_out", at, exchange=exchange)

    # ---- decisions -----------------------------------------------------------------------
    def check(self, requester: Requester, category: str, source_org: str, at: "str | datetime",
              purpose: str = "care", emergency: bool = False, justification: str = "",
              exchange: str | None = None) -> Decision:
        at = _ts(at)
        d = self._decide(requester, category, source_org, at, purpose, emergency, justification, exchange)
        self._record("access_decision", at, requester=requester.party_id, requester_org=requester.org,
                     role=requester.role, category=category, source_org=source_org, purpose=purpose,
                     emergency_requested=emergency, justification=justification, exchange=exchange, **d.to_dict())
        return d

    def authorize_records(self, requester: Requester, records: list, at: "str | datetime",
                          purpose: str = "care", emergency: bool = False, justification: str = "") -> tuple:
        """Filter records (objects with .category, .source_org, optional .exchange). Returns (allowed, decisions)."""
        allowed, decisions = [], []
        for r in records:
            d = self.check(requester, r.category, r.source_org, at, purpose, emergency, justification,
                           getattr(r, "exchange", None))
            decisions.append(d)
            if d.allowed:
                allowed.append(r)
        return allowed, decisions

    def _opted_out(self, exchange: "str | None", at: datetime) -> bool:
        return bool(exchange and exchange in self.opt_outs and self.opt_outs[exchange] <= at)

    def _decide(self, req, category, source_org, at, purpose, emergency, justification, exchange) -> Decision:
        if req.role == "patient":
            return Decision(True, "PATIENT_SELF", "Patients can always see their own records.")
        if req.org == source_org:
            return Decision(True, "OWN_RECORDS", "A data custodian can always see its own records.")
        if self._opted_out(exchange, at):
            normal = Decision(False, "OPTED_OUT_OF_EXCHANGE",
                              f"The patient has opted out of the {exchange} exchange.")
        else:
            normal = self._normal(req, category, source_org, at, purpose)
        if normal.allowed or not emergency:
            return normal
        return self._emergency(req, justification, exchange, at, normal)

    def _normal(self, req, category, source_org, at, purpose) -> Decision:
        candidates = [g for g in self.grants.values()
                      if g.grantee_org == req.org and g.source_org == source_org]
        denials = []
        for g in candidates:
            if g.revoked_at is not None and g.revoked_at <= at:
                denials.append(("REVOKED", f"Consent was revoked on {g.revoked_at.date()}.", g))
            elif g.expires_at is not None and g.expires_at <= at:
                denials.append(("EXPIRED", f"The grant expired on {g.expires_at.date()}.", g))
            elif g.granted_at > at:
                denials.append(("NOT_YET_ACTIVE", "The grant is not active yet.", g))
            elif category not in g.categories:
                denials.append(("CATEGORY_NOT_COVERED", f"The grant does not cover '{category}'.", g))
            elif g.purpose != purpose:
                denials.append(("PURPOSE_NOT_COVERED", f"The grant is for '{g.purpose}', not '{purpose}'.", g))
            else:
                return Decision(True, "GRANTED", "An active patient grant covers this access.",
                                "Patient consent", g.grant_id)
        if not denials:
            return Decision(False, "NO_GRANT", f"No grant lets {req.org} see {source_org} records.")
        code, why, g = sorted(denials, key=lambda d: DENIAL_PRIORITY.index(d[0]))[0]
        return Decision(False, code, why, "Patient consent", g.grant_id)

    def _emergency(self, req, justification, exchange, at, normal: Decision) -> Decision:
        if req.role != "clinician":
            return Decision(False, "EMERGENCY_NOT_PERMITTED", "Only clinicians can request emergency access.",
                            emergency=True)
        if not justification.strip():
            return Decision(False, "EMERGENCY_JUSTIFICATION_REQUIRED",
                            "Emergency access needs a written justification.", emergency=True)
        if self.block_emergency_on_opt_out and self._opted_out(exchange, at):
            return Decision(False, "EMERGENCY_BLOCKED_BY_OPT_OUT",
                            f"Emergency access was not granted because the patient opted out of {exchange}. "
                            "A human decision is required.", OPT_OUT_BASIS, emergency=True,
                            flagged_for_review=True, escalate=True)
        return Decision(True, "EMERGENCY_OVERRIDE",
                        f"Emergency access allowed despite: {normal.reason} It is flagged for review.",
                        "Emergency (break-the-glass) access rule", emergency=True, flagged_for_review=True)
