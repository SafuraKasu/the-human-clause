"""Deterministic medication-safety engine.

No LLM is involved in deciding whether a finding exists or how severe it is: findings come only
from records in the knowledge base (see demo_kb.json), and every finding carries its provenance.
The LLM layer may later *explain* findings; it never creates them.

    engine = SafetyEngine()
    assessment = engine.assess(patient, proposed=Medication(...))
"""
import json
from dataclasses import dataclass, field, asdict
from itertools import combinations
from pathlib import Path

KB_PATH = Path(__file__).with_name("demo_kb.json")
SEVERITY_ORDER = ["critical", "high", "moderate", "low", "informational"]

NO_ISSUE_STATEMENT = ("No known issue was found in the available knowledge base for the pairs and factors "
                      "checked. This is not proof that the combination is safe.")


@dataclass
class Medication:
    name: str
    hospital: str = ""
    status: str = "active"  # active | discontinued | uncertain
    ingredient: str | None = None  # filled by normalization


@dataclass
class Lab:
    value: float
    date: str = ""


@dataclass
class Patient:
    age: int | None = None
    conditions: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    labs: dict[str, Lab] = field(default_factory=dict)  # keys: "egfr", "potassium", ...
    medications: list[Medication] = field(default_factory=list)


@dataclass
class Finding:
    finding_id: str
    category: str  # interaction | duplication | contraindication | lab-rule | missing-data
    certainty: str  # established | potential | patient-specific | uncertain
    severity: str
    medications: list[str]
    title: str
    explanation: str
    patient_factors: list[str]
    missing_info: list[str]
    evidence: dict
    recommended_next_step: str


@dataclass
class Assessment:
    findings: list[Finding]
    pairs_checked: list[tuple[str, str]]
    medications_considered: list[str]
    ignored_medications: list[str]
    summary: str
    kb_version: str
    kb_label: str

    def to_dict(self) -> dict:
        return asdict(self)


class SafetyEngine:
    def __init__(self, kb_path: Path = KB_PATH):
        self.kb = json.loads(Path(kb_path).read_text(encoding="utf-8"))
        self.meta = self.kb["meta"]
        self._brand_to_ingredient = {}
        for ing, info in self.kb["ingredients"].items():
            self._brand_to_ingredient[ing] = ing
            for brand in info["brands"]:
                self._brand_to_ingredient[brand] = ing

    # ---- normalization -------------------------------------------------------------------
    def normalize(self, name: str) -> str | None:
        return self._brand_to_ingredient.get(name.strip().lower())

    def _class_of(self, ingredient: str) -> str:
        return self.kb["ingredients"][ingredient]["class"]

    def _evidence(self, record: dict, rationale: str) -> dict:
        return {"source": self.meta["source"], "reference_id": record["id"], "kb_version": self.meta["kb_version"],
                "last_updated": self.meta["last_updated"], "severity_rationale": rationale,
                "demonstration_data": True}

    @staticmethod
    def _has_condition(patient: Patient, condition: str) -> bool:
        return any(condition.lower() in c.lower() for c in patient.conditions)

    # ---- main entry ----------------------------------------------------------------------
    def assess(self, patient: Patient, proposed: Medication | None = None) -> Assessment:
        meds = [m for m in patient.medications if m.status == "active"]
        if proposed:
            meds = meds + [proposed]
        ignored = [m.name for m in patient.medications if m.status != "active"]

        resolved, unknown = [], []
        for m in meds:
            m.ingredient = self.normalize(m.name)
            (resolved if m.ingredient else unknown).append(m)

        findings: list[Finding] = []
        pairs_checked: list[tuple[str, str]] = []

        for m in unknown:
            findings.append(Finding(
                f"UNKNOWN:{m.name.lower()}", "missing-data", "uncertain", "informational", [m.name],
                f"{m.name} is not in the knowledge base",
                f"The knowledge base does not recognise '{m.name}', so it could not be checked.",
                [], [f"Active ingredient for '{m.name}'"],
                {"source": self.meta["source"], "reference_id": None, "kb_version": self.meta["kb_version"],
                 "last_updated": self.meta["last_updated"], "severity_rationale": "Not assessable",
                 "demonstration_data": True},
                "Ask a pharmacist to confirm the active ingredient and review this medicine."))

        for x, y in combinations(resolved, 2):
            pairs_checked.append((x.name, y.name))
            findings += self._check_pair(patient, x, y)

        for m in resolved:
            findings += self._check_single(patient, m)

        findings.sort(key=lambda f: (SEVERITY_ORDER.index(f.severity), f.finding_id))
        summary = (f"{len(findings)} finding(s) across {len(pairs_checked)} medication pair(s) checked."
                   if findings else NO_ISSUE_STATEMENT)
        return Assessment(findings, pairs_checked, [m.name for m in meds], ignored, summary,
                          self.meta["kb_version"], self.meta["label"])

    # ---- pair checks ---------------------------------------------------------------------
    def _check_pair(self, patient: Patient, x: Medication, y: Medication) -> list[Finding]:
        out = []
        a, b = x.ingredient, y.ingredient
        if a == b:
            out.append(Finding(
                f"DUP-SAME:{a}", "duplication", "potential", "moderate", [x.name, y.name],
                f"Same active ingredient listed twice ({a})",
                f"{x.name} and {y.name} both contain {a}. This may be intentional, so it is flagged for review.",
                [f"Prescribers: {x.hospital or 'unknown'} / {y.hospital or 'unknown'}"], [],
                {"source": self.meta["source"], "reference_id": None, "kb_version": self.meta["kb_version"],
                 "last_updated": self.meta["last_updated"],
                 "severity_rationale": "Duplicate ingredient detected by normalization", "demonstration_data": True},
                "Ask a doctor or pharmacist whether both prescriptions are intended."))
            return out
        ca, cb = self._class_of(a), self._class_of(b)
        if ca == cb and ca in self.kb["class_duplication"]:
            out.append(Finding(
                f"DUP-CLASS:{'+'.join(sorted([a, b]))}", "duplication", "potential", "moderate", [x.name, y.name],
                f"Two medicines from the same class ({ca})",
                f"{x.name} and {y.name} are both in the class '{ca}'. Taking two from the same class can add risk "
                f"without extra benefit, though some combinations are intentional.",
                [f"Prescribers: {x.hospital or 'unknown'} / {y.hospital or 'unknown'}"], [],
                {"source": self.meta["source"], "reference_id": None, "kb_version": self.meta["kb_version"],
                 "last_updated": self.meta["last_updated"],
                 "severity_rationale": f"Class duplication rule for '{ca}'", "demonstration_data": True},
                "Ask a doctor or pharmacist whether both are intended."))
        for rec in self.kb["interactions"]:
            if {rec["a"], rec["b"]} == {a, b}:
                severity, factors, why = rec["severity"], [], rec["rationale"]
                for mod in rec["modifiers"]:
                    if self._has_condition(patient, mod["condition"]):
                        severity = mod["severity"]
                        factors.append(f"Patient has {mod['condition']}: {mod['why']}")
                        why = f"{rec['rationale']} Escalated because of {mod['condition']}."
                out.append(Finding(
                    rec["id"], "interaction", rec["certainty"], severity, [x.name, y.name],
                    f"{a.capitalize()} + {b}: interaction",
                    rec["mechanism"], factors, [], self._evidence(rec, why),
                    "Discuss this combination with the prescribing doctor or a pharmacist. "
                    "Do not stop or change either medicine on your own."))
        return out

    # ---- single-medication checks (patient factors) --------------------------------------
    def _check_single(self, patient: Patient, m: Medication) -> list[Finding]:
        out = []
        cls = self._class_of(m.ingredient)
        for rec in self.kb["contraindications"]:
            if rec["ingredient_class"] != cls:
                continue
            if rec["type"] == "condition" and self._has_condition(patient, rec["condition"]):
                out.append(self._contra(rec, m, [f"Patient has {rec['condition']}"]))
            if rec["type"] == "allergy" and any(rec["allergy"].lower() in a.lower() for a in patient.allergies):
                out.append(self._contra(rec, m, [f"Recorded allergy: {rec['allergy']}"]))
        for rule in self.kb["lab_rules"]:
            if rule["ingredient"] != m.ingredient:
                continue
            lab = patient.labs.get(rule["lab"])
            if lab is None:
                out.append(Finding(
                    f"MISSING:{rule['id']}:{m.name.lower()}", "missing-data", "uncertain", "informational", [m.name],
                    f"Missing {rule['lab']} result for {m.name}", rule["missing_note"], [],
                    [f"Recent {rule['lab']} ({rule['unit']})"], self._evidence(rule, "Required lab value not on record"),
                    "Ask the care team to arrange or share a recent result. Do not change the medicine on your own."))
                continue
            tripped = lab.value < rule["threshold"] if rule["operator"] == "<" else lab.value > rule["threshold"]
            if tripped:
                out.append(Finding(
                    f"{rule['id']}:{m.name.lower()}", "lab-rule", rule["certainty"], rule["severity"], [m.name],
                    f"{m.name}: {rule['lab']} outside the safe range for this medicine", rule["explanation"],
                    [f"{rule['lab']} = {lab.value} {rule['unit']}" + (f" on {lab.date}" if lab.date else "")], [],
                    self._evidence(rule, f"Rule: {rule['lab']} {rule['operator']} {rule['threshold']}"),
                    "Contact the prescribing doctor or a pharmacist promptly. Do not stop the medicine on your own."))
        return out

    def _contra(self, rec: dict, m: Medication, factors: list[str]) -> Finding:
        return Finding(
            f"{rec['id']}:{m.name.lower()}", "contraindication", rec["certainty"], rec["severity"], [m.name],
            f"{m.name} may be unsuitable for this patient", rec["explanation"], factors, [],
            self._evidence(rec, f"Contraindication rule {rec['id']}"),
            "Check with the prescribing doctor or a pharmacist before taking this medicine.")
