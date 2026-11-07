"""Deterministic scenario state: applies events using the consent module and the safety engine.

This is the part of the scenario that is plain code. The agents and orchestrator will sit on top of
it (adding retrieval, explanation, gap analysis and the audit trail).
"""
from dataclasses import replace

from backend.consent.registry import ConsentRegistry, Requester
from backend.safety.engine import Assessment, Lab, Medication, Patient, SafetyEngine
from backend.scenario import fatima


class ScenarioState:
    def __init__(self, engine: SafetyEngine | None = None):
        self.engine = engine or SafetyEngine()
        self.registry = ConsentRegistry(fatima.PATIENT_ID)
        self.age: int | None = None
        self.meds: list[Medication] = []
        self.conditions: list[str] = []
        self.allergies: list[str] = []
        self.labs: dict[str, Lab] = {}
        self.withdrawn: dict[str, str] = {}  # source org -> withdrawn at
        self.limitations: list[str] = []
        for grantee in fatima.SOURCES:
            for source in fatima.SOURCES:
                if grantee != source:
                    self.registry.grant(grantee, source, fatima.GRANT_CATEGORIES, "care",
                                        fatima.GRANT_TIME, fatima.GRANT_EXPIRY)

    def engine_patient(self) -> Patient:
        """The patient as the platform may lawfully process them: sources withdrawn by the patient are excluded."""
        meds = [replace(m, ingredient=None) for m in self.meds if m.hospital not in self.withdrawn]
        return Patient(self.age, list(self.conditions), list(self.allergies), dict(self.labs), meds)

    def apply(self, event: fatima.Event) -> dict:
        handler = getattr(self, f"_on_{event.kind}", None)
        if handler:
            handler(event)
        decisions = {}
        for c in event.consent_checks:
            decisions[c["label"]] = self.registry.check(
                Requester(**c["requester"]), c["category"], c["source_org"], event.at, emergency=c["emergency"],
                justification=c["justification"], exchange=c["exchange"])
        assessment: Assessment = self.engine.assess(self.engine_patient())
        return {"consent": decisions, "assessment": assessment, "limitations": list(self.limitations)}

    def _on_records_arrive(self, event):
        self.age = event.payload.get("age", self.age)
        for up in event.payload["uploads"]:
            self.meds += [Medication(n, up["source_org"]) for n in up.get("medications", [])]
            self.conditions += [c for c in up.get("conditions", []) if c not in self.conditions]
            self.allergies += [a for a in up.get("allergies", []) if a not in self.allergies]

    def _on_lab_arrives(self, event):
        for name, v in event.payload["labs"].items():
            self.labs[name] = Lab(v["value"], v["date"])

    def _on_patient_withdraws(self, event):
        src = event.payload["revoke_source"]
        self.registry.revoke_where(event.at, source_org=src)
        self.registry.opt_out(event.payload["opt_out_exchange"], event.at)
        self.withdrawn[src] = event.at
        self.limitations.append(f"{src}: data withheld from assessment by the patient's choice (since {event.at[:10]}). "
                                "The safety assessment is incomplete.")
