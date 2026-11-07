# Master prompt (from teammate)

# MASTER BUILD PROMPT: AI-Powered Unified Health Record & Comprehensive Medication Safety Platform

## 1. Your Role

Act as a senior full-stack software engineer, AI/ML engineer, healthcare technology architect, database designer, and application security engineer.

Your task is to design and build a complete, functional MVP of an AI-powered healthcare platform.

Do not just create a project proposal, architecture document, or static UI mockup. Build the actual application, implement its core features, connect the frontend and backend, create the database, implement the AI and medication safety logic, and provide a working demonstration.

Think through the architecture before coding. Work systematically, test your implementation, and fix errors rather than leaving unfinished features.

If something cannot be implemented fully because an external API, clinical database, or hospital integration is unavailable, create a modular integration interface and a clearly labelled demonstration implementation.

Do not pretend that an unimplemented feature works.

---

# 2. Product Vision

Build a patient-first platform that acts as a unified personal health record, medication management assistant, and comprehensive medication safety monitoring system.

### The problem

Patients, particularly older adults with multiple chronic conditions, often visit several hospitals, clinics, and specialists.

Each healthcare provider maintains a separate record of the patient. This creates fragmented medical histories.

A patient may have:
- Prescriptions from multiple specialists.
- Different medications from different hospitals.
- Blood test reports and laboratory results.
- Diagnoses and medical conditions.
- Allergy records.
- Previous hospital visits and discharge summaries.
- Medication instructions that are difficult to remember.
- Different doctors who may not know what other doctors have prescribed.

This creates a serious medication safety problem.

A medication prescribed by one specialist may interact with another medication prescribed elsewhere. The risk may depend on the patient's age, medical conditions, kidney or liver function, dosage, allergies, and laboratory results.

Existing medication checkers often focus on isolated drug pairs and static interaction rules. They may miss more complex patient-specific risks, especially when multiple medications and medical conditions are involved.

Patients also struggle to manage their daily medication schedules and remember which medication to take, when to take it, and whether it should be taken with or without food.

### Our solution

Create one centralized, patient-controlled health profile that brings all these records together.

The patient uploads medical documents, prescriptions, laboratory reports, and other health records.

The platform extracts, organizes, and consolidates the information into a structured medical profile.

It then continuously evaluates the patient's medication list against their known health information to identify potential medication safety issues.

**The system must proactively check every medication against the patient's complete known medication and health profile and alert the patient to any clinically relevant potential safety issue.**

The patient can also:
- View their complete medical history in one place.
- See all their medications and prescriptions.
- Receive medication safety alerts.
- Follow a personalized medication schedule.
- Mark medications as taken or skipped.
- Receive reminders.
- Track medication adherence.
- Share their medical profile securely with a new doctor or hospital.

Doctors and pharmacists have a separate interface where they can review patient-authorized records, reconcile medications, understand identified risks, and check proposed prescriptions before prescribing them.

### Core differentiator

This is not simply a drug interaction checker.

It combines:

1. Unified personal health records.
2. AI-powered medical document extraction.
3. Comprehensive medication safety screening.
4. Patient-specific risk analysis.
5. Medication scheduling and adherence tracking.
6. Secure sharing between patients and healthcare providers.
7. Federated learning for privacy-preserving cross-institutional medication risk intelligence.

The product must be useful to patients even without federated learning. Federated learning is an additional research and intelligence layer.

---

# 3. Target Users and Roles

Implement role-based access for three main user types.

### A. Patient

Patients can:
- Register and log in.
- Create their health profile.
- Upload medical documents.
- Review extracted information.
- Manage their medications.
- View their medical history.
- Receive medication safety alerts.
- Manage their medication schedule.
- Track adherence.
- Share selected or complete records with clinicians.
- Revoke previously granted access.

### B. Doctor / Pharmacist

Healthcare professionals can:
- Register or access a clinician account.
- View patients who have explicitly shared records with them.
- Review medical histories.
- View current and historical medications.
- Review allergies, diagnoses, and laboratory results.
- Identify medication discrepancies.
- View comprehensive medication safety assessments.
- Enter proposed medications and run pre-prescription safety checks.
- Review supporting evidence and risk explanations.

Clinicians must not automatically access patient records without authorization.

### C. Research / System Administrator

This role provides access to:
- Federated learning demonstrations.
- Hospital node simulations.
- Model training rounds.
- Model performance comparisons.
- Research dashboards.
- Knowledge-base management.
- System monitoring.

Use synthetic data for the demonstration environment.

---

# 4. Core Module 1: Unified Personal Health Record

This is the foundation of the entire platform.

Create a centralized personal health profile that organizes all information collected from different healthcare providers.

### Patient profile

Include:
- Full name.
- Date of birth.
- Age, calculated from date of birth.
- Sex, where relevant to clinical interpretation.
- Blood group, if known.
- Height and weight, if available.
- Emergency contact.
- Known allergies.
- Chronic medical conditions.
- Relevant medical history.

Do not assume unknown values.

### Medical record categories

Organize records into:

1. Diagnoses and medical conditions.
2. Current medications.
3. Historical medications.
4. Prescriptions.
5. Allergies.
6. Laboratory results.
7. Medical reports.
8. Specialist notes.
9. Hospital admission and discharge summaries.
10. Procedures and surgeries.
11. Previous adverse medication reactions.
12. Other uploaded medical documents.

### Medical timeline

Create a chronological timeline showing:
- Hospital visits.
- Diagnoses.
- Prescriptions.
- Medication changes.
- Laboratory tests.
- Medical reports.
- Hospital admissions.
- Important health events.

Every record must preserve its source.

For example:

- Institution: Hospital A.
- Specialist: Cardiology.
- Document date: 12 October 2026.
- Record type: Prescription.
- Upload date: 15 October 2026.

Never silently overwrite an older medical record.

Maintain historical versions and distinguish between:
- Active.
- Discontinued.
- Replaced.
- Completed.
- Patient reports not taking.
- Uncertain status.

### Multiple healthcare providers

The platform must support records from multiple hospitals and specialists.

A patient should be able to see which institution prescribed each medication and when it was prescribed.

Do not assume that medications from different hospitals are automatically compatible.

---

# 5. Core Module 2: AI Medical Document Intelligence

Patients must be able to upload their existing medical records rather than manually entering everything.

### Supported documents

Support:
- PDF files.
- Scanned PDFs.
- JPG/JPEG images.
- PNG images.

Document types include:
- Prescriptions.
- Blood test reports.
- Laboratory results.
- Discharge summaries.
- Medical reports.
- Specialist consultation notes.
- Diagnosis reports.
- Other relevant medical documents.

### Processing pipeline

Implement this workflow:

1. Patient uploads a document.
2. Backend stores the original document securely.
3. OCR or document extraction processes the content.
4. AI extracts structured medical information.
5. Extracted data is validated against a structured schema.
6. Patient sees a review screen.
7. Patient confirms or corrects extracted information.
8. Verified information is added to the unified health profile.
9. Medication-related information triggers the comprehensive safety checker.

### Information to extract

For prescriptions:
- Medication name.
- Brand name.
- Active ingredient.
- Strength.
- Dosage.
- Frequency.
- Route of administration.
- Duration.
- Start date.
- End date.
- Instructions concerning food.
- Timing instructions.
- Prescribing doctor.
- Hospital or clinic.
- Prescription date.

For laboratory reports:
- Test name.
- Result.
- Unit.
- Reference range.
- Test date.
- Laboratory or institution.

For medical reports:
- Patient details.
- Diagnoses.
- Conditions.
- Symptoms.
- Relevant medical history.
- Allergies.
- Previous adverse reactions.
- Procedures.
- Clinical notes.

### Important extraction requirements

- Never invent missing medical information.
- Preserve original documents.
- Show extraction confidence.
- Flag ambiguous medication names and dosage instructions.
- Require patient confirmation before uncertain extracted information becomes an active medication.
- Preserve document provenance.
- Clearly distinguish AI-extracted information from manually verified information.

Create an abstraction layer for OCR and AI providers so different services can be integrated without rewriting the application.

If no API key is available, implement a deterministic demo extraction workflow using sample documents and structured sample responses.

---

# 6. Core Module 3: Comprehensive Medication Safety Intelligence

**This is one of the most important modules in the entire application. Do not restrict its scope to a predefined list of adverse outcomes.**

The platform must screen every medication in the patient's profile for any clinically relevant medication-related safety issue.

The system should automatically trigger a medication safety assessment whenever:
- A new medication is added.
- A prescription is uploaded and verified.
- A medication dosage changes.
- A medication is discontinued.
- A medication is marked as no longer being taken.
- Relevant laboratory results or medical conditions are updated.
- A clinician enters a proposed medication.

## A. Complete medication reconciliation

Consolidate medications from:
- Prescriptions.
- Medical reports.
- Specialist notes.
- Patient-entered medications.
- Over-the-counter medications.
- Vitamins.
- Herbal products.
- Dietary supplements.

For every medication, maintain:
- Brand name.
- Generic name.
- Active ingredient.
- Strength.
- Dosage.
- Frequency.
- Route.
- Duration.
- Start and end dates.
- Prescribing provider.
- Source document.
- Current status.

Identify potential discrepancies such as:
- Same active ingredient under different brand names.
- Duplicate prescriptions.
- Conflicting dosages.
- Multiple prescriptions for similar therapeutic purposes.
- Old prescriptions that may no longer be active.
- Discontinued medications still appearing in recent reports.
- Conflicting medication instructions.

Do not automatically classify every duplicate-looking medication as an error. Some combinations may be intentional. Flag them for review.

## B. Comprehensive safety screening

Whenever a medication is added or changed, screen it against the patient's entire active medication list and relevant medical profile.

The checker must support the following categories:

**1. Drug–drug interactions**

Identify potentially harmful interactions between two or more medications.

**2. Drug–food interactions**

Identify clinically relevant interactions involving foods, beverages, and dietary substances.

**3. Drug–supplement interactions**

Check interactions involving vitamins, herbal products, and dietary supplements.

**4. Therapeutic duplication**

Identify multiple medications containing the same active ingredient or medications with potentially overlapping therapeutic effects.

**5. Contraindications**

Identify medications that may be unsuitable because of:
- Existing medical conditions.
- Known allergies.
- Previous adverse reactions.
- Relevant clinical history.

**6. Dose-related risks**

Identify potentially inappropriate or unsafe:
- Dosages.
- Frequencies.
- Maximum daily doses.
- Duration of use.
- Route of administration.

Only apply dose limits when reliable references and sufficient patient information are available.

**7. Administration conflicts**

Identify conflicting instructions involving:
- Medication timing.
- Food requirements.
- Route.
- Frequency.
- Required spacing between medications.
- Conflicting prescription instructions.

**8. Patient-specific medication risks**

Evaluate relevant factors such as:
- Age.
- Kidney function.
- Liver function.
- Diagnoses.
- Allergies.
- Relevant laboratory values.
- Medication dosage.
- Medication duration.
- Existing health conditions.

**9. Adverse-effect risks**

Identify known adverse effects that may become more concerning when medications are combined or when the patient has particular health conditions.

**10. Other clinically recognized safety issues**

The architecture must support additional medication-related safety categories as the clinical knowledge base expands.

Do not restrict the checker to only these ten categories. They establish the minimum scope.

## C. Pairwise and multi-drug analysis

The system must not only evaluate medications in isolation.

It must:
- Check relevant interactions between every medication pair.
- Identify risks arising from combinations of three or more medications.
- Consider cumulative effects where supported by clinical evidence.
- Evaluate the complete medication profile against relevant patient-specific factors.

Do not assume that pairwise interaction checking alone is sufficient.

## D. Patient-specific risk assessment

The same combination may have different implications for different patients.

For example, a combination may require additional caution in a patient with impaired kidney function, a particular cardiovascular condition, or a relevant laboratory abnormality.

Use available patient information to contextualize the result.

The system should explain:
- Which medications are involved.
- What the potential issue is.
- Why it matters.
- Which patient-specific factors contribute.
- What information is missing.
- What evidence supports the finding.

## E. Patient alerts

**The patient must be alerted whenever the system identifies a clinically relevant potential medication safety issue.**

Alerts must be understandable to a non-medical user.

Each alert should include:

- Alert title.
- Medications involved.
- Type of issue.
- Severity.
- Plain-language explanation.
- Why this may matter to this patient.
- Supporting evidence or clinical reference.
- Recommended next step.
- Date and time identified.
- Whether the alert is new, reviewed, resolved, or dismissed.

Use these severity categories:

| Severity | Meaning |
|---|---|
| Critical | Potentially serious or life-threatening risk requiring urgent clinical attention. |
| High | Significant concern requiring prompt professional review. |
| Moderate | Relevant concern that should be discussed with a doctor or pharmacist. |
| Low | Minor or manageable concern with appropriate guidance. |
| Informational | Relevant medication information that does not necessarily indicate harm. |

Severity must be assigned using evidence-backed criteria, not arbitrary AI judgement.

The patient dashboard should prominently display unresolved high-priority alerts.

Avoid repeatedly displaying the same unchanged alert. Maintain alert history and notify the patient again when a relevant change occurs.

Do not generate alarming warnings for harmless combinations.

## F. Evidence and clinical knowledge base

Implement a modular medication knowledge layer that can integrate reliable clinical references and drug-interaction databases.

Potential integrations include:
- DrugBank, subject to licensing and access.
- RxNorm.
- OpenFDA drug information and labeling.
- Other reputable, maintained clinical drug-information sources.

Select suitable sources based on availability, licensing, coverage, and reliability.

Every alert must retain:
- Source name.
- Reference identifier, if available.
- Knowledge-base version.
- Last-updated date, where available.
- Supporting interaction description.
- Severity rationale.

Do not fabricate clinical references or claim that an interaction was found in a source that was not actually consulted.

If external databases are unavailable:
- Build a clearly labelled demonstration knowledge base.
- Use a small, curated set of synthetic or verified example interaction records.
- Keep the data separate from production clinical knowledge.
- Make the knowledge provider replaceable.
- Clearly label demo results as demonstration data.

Do not use an LLM as the sole authority for determining whether a medication combination is clinically dangerous.

Use deterministic, evidence-backed checking where possible. AI should help explain findings in understandable language, not invent clinical facts.

## G. Missing information and uncertainty

If a safe assessment cannot be completed because information is missing:
- Identify the missing information.
- Explain why it matters.
- Request verification where appropriate.
- Flag the medication or combination for review when justified.
- Do not assume missing laboratory values, dosages, or conditions.
- Do not fabricate risk levels.

Clearly distinguish:
- Established interaction.
- Potential interaction.
- Patient-specific concern.
- Uncertain finding requiring professional review.
- No known issue found in the available knowledge base.

**Important:** "No known issue found" must never be presented as proof that a medication combination is completely safe.

## H. Multi-outcome adverse risk pathways

In addition to comprehensive interaction screening, implement an extensible architecture for patient-specific adverse outcome assessment.

Include the following outcome pathways:

1. Acute Kidney Injury (AKI).
2. Drug-induced bleeding.
3. Cardiac arrhythmias.
4. Hypoglycemia.
5. Electrolyte abnormalities.
6. Drug-induced liver injury.

These are additional pathways, NOT the complete scope of medication safety screening.

Each pathway should have:
- Relevant medication exposures.
- Relevant patient conditions.
- Relevant laboratory values.
- Patient-specific contributing factors.
- Explainable assessment.
- Evidence-backed rules or a separately evaluated ML model.
- Missing-data handling.

Do not claim that every outcome has a clinically validated prediction model.

Use evidence-backed rules for demonstration where appropriate. Implement actual machine-learning models only when suitable datasets and evaluation procedures exist.

Clearly label the difference between:
- Deterministic interaction rules.
- Evidence-based clinical warnings.
- ML-generated risk predictions.

Never invent clinical probabilities or model performance figures.

## I. Clinician review and patient safety boundaries

The platform is a medication safety support and early-warning system, not a replacement for medical professionals.

- Never instruct patients to independently stop, start, increase, or decrease medication dosages.
- Never recommend doubling a dose after a missed medication.
- Direct patients to a qualified doctor or pharmacist when professional review is required.
- Display appropriate emergency guidance when symptoms suggest an emergency.
- Preserve clinician authority over treatment decisions.

---

# 7. Core Module 4: Personalized Medication Schedule and Adherence Tracking

Patients often struggle to remember which medication to take, when to take it, and whether it should be taken with food.

Build a practical daily medication management interface.

## A. Medication schedule

Generate a schedule using verified prescription instructions.

For each medication, display:
- Medication name.
- Dosage.
- Scheduled time.
- Frequency.
- Route.
- Before, with, or after food instructions, if verified.
- Duration.
- Source prescription.
- Prescribing provider.

Example interface:

| Time | Medication | Instructions | Status |
|---|---|---|---|
| 8:00 AM | Medication A | With breakfast | Pending |
| 1:00 PM | Medication B | After lunch | Taken |
| 9:00 PM | Medication C | As prescribed | Pending |

The example above is demonstration data only.

Do not infer medication timing or food requirements from the drug name alone.

If prescription instructions are missing or conflicting, display "Confirm with your pharmacist or doctor."

## B. Medication reminders

Implement:
- Daily schedule.
- Upcoming medication notifications.
- Taken / skipped / remind later actions.
- Medication history.
- Adherence tracking.
- Daily completion progress.

For the MVP, implement in-app reminders and a notification system. Keep the architecture ready for browser or mobile push notifications later.

## C. Adherence tracking

Patients should be able to:
- Mark a medication as taken.
- Mark it as skipped.
- Record the time taken.
- View previous adherence.
- Review missed doses.
- View weekly and monthly adherence summaries.

Never recommend taking an extra dose after a missed dose.

---

# 8. Core Module 5: Portable Health Records and Secure Sharing

A patient should not need to explain their entire medical history from memory every time they visit a new doctor.

Build a secure record-sharing feature.

## A. Patient sharing interface

Allow patients to generate a secure access link or code for a healthcare professional.

The patient should be able to select:
- Complete medical profile.
- Current medications.
- Historical medications.
- Prescriptions.
- Laboratory results.
- Allergies.
- Diagnoses.
- Medical reports.
- Medication safety assessments.

Support:
- Expiring access.
- Revocable access.
- Permission-based sharing.
- Access history.
- Secure access tokens.

## B. Clinician access

When a clinician opens an authorized patient profile, display:
- Patient overview.
- Current and historical medications.
- Medical conditions.
- Allergies.
- Relevant laboratory results.
- Previous prescriptions.
- Medical timeline.
- Medication safety alerts.
- Identified discrepancies.

## C. Audit logs

Record:
- Who accessed the profile.
- When it was accessed.
- Which record categories were accessed.
- Whether records were downloaded.
- When access expires.
- When access was revoked.

Never allow unauthorized access to patient records.

## D. Future interoperability

Design the internal data model with healthcare interoperability in mind.

Use FHIR-compatible structures where practical, particularly:
- Patient.
- Condition.
- Medication.
- MedicationRequest.
- MedicationStatement.
- Observation.
- DiagnosticReport.
- AllergyIntolerance.
- Practitioner.
- Organization.
- DocumentReference.

Implement export or mapping adapters where feasible.

Do not claim direct integration with real hospitals unless it has actually been implemented.

For the MVP, patient-uploaded documents are the primary data source. Direct hospital integrations are a future extension.

---

# 9. Core Module 6: Clinician Portal and Pre-Prescription Checking

Create a separate clinician dashboard.

The clinician should be able to review a patient's complete authorized medical profile before prescribing a medication.

### Clinician dashboard

Include:
- Assigned or shared patients.
- Patient search within authorized records.
- Patient medical overview.
- Medication list.
- Allergies.
- Medical conditions.
- Laboratory results.
- Medication history.
- Safety alerts.
- Medication discrepancies.

### Pre-prescription safety check

Allow the clinician to enter a proposed medication.

Fields:
- Medication.
- Active ingredient.
- Dosage.
- Frequency.
- Route.
- Duration.
- Instructions.

The system should evaluate the proposed medication against:
- All active medications.
- Known allergies.
- Diagnoses.
- Kidney function.
- Liver function.
- Relevant laboratory results.
- Known interaction records.
- Other available patient-specific information.

Return:
- Potential interactions.
- Contraindications.
- Duplicate therapy concerns.
- Dose-related risks.
- Relevant patient-specific concerns.
- Supporting evidence.
- Missing information.
- Suggested points for clinician review.

The clinician makes the final prescribing decision.

---

# 10. Core Module 7: Federated Learning and Cross-Hospital Intelligence

This is the research and technical differentiator of the platform.

The problem is that individual hospitals may not have enough data to identify rare or emerging medication-related safety patterns.

However, sharing raw patient records across hospitals creates privacy, regulatory, and governance challenges.

Implement a federated learning demonstration where multiple simulated hospitals collaboratively train a model without sending their raw patient records to a central server.

## A. Simulated hospital environment

Create three simulated healthcare institutions:

- Hospital A.
- Hospital B.
- Hospital C.

Each hospital must have:
- Its own synthetic patient dataset.
- Different patient distributions.
- Different medication profiles.
- Different disease distributions.
- Its own local model.
- A local training process.

Use synthetic data only.

## B. Federated training workflow

Implement:

1. Each hospital trains its model locally.
2. Local model updates are generated.
3. Model updates are transmitted to the aggregation server.
4. The server aggregates the updates using Federated Averaging (FedAvg) or another suitable method.
5. The global model is distributed back to participating hospitals.
6. Training continues for multiple rounds.
7. Model performance is evaluated.

Use Flower (FL) or a compatible federated learning framework.

The system must demonstrate that raw patient-level training records remain within their simulated hospital environments.

Clearly distinguish the federated learning data flow from the patient's personal health record storage and sharing. The patient-facing platform may store records centrally for the patient's own use, while federated training operates on separate institution-held datasets.

## C. Multi-outcome model architecture

Design the federated learning layer to support multiple adverse outcome tasks.

Potential model tasks:
- AKI risk.
- Bleeding risk.
- Arrhythmia risk.
- Hypoglycemia risk.
- Electrolyte abnormality risk.
- Drug-induced liver injury risk.

Use separate prediction heads or independently trained models where appropriate.

Do not force all outcomes into one poorly defined prediction label.

## D. Model comparison

Compare:

1. Hospital A's local model.
2. Hospital B's local model.
3. Hospital C's local model.
4. Federated global model.
5. Centralized training baseline, where appropriate and only for synthetic experimental comparison.

Evaluate using:
- AUROC.
- AUPRC.
- Precision.
- Recall.
- F1-score.
- Calibration.
- Sensitivity at selected specificity.

Use patient-level splits and appropriate temporal or institution-held-out validation where feasible.

Avoid data leakage.

Show actual evaluation results.

Do not hardcode claims that federated learning is always better than local training. The dashboard must display the actual experimental results.

## E. Federated learning dashboard

Create a research dashboard showing:
- Participating hospital nodes.
- Local training status.
- Number of local synthetic records.
- Training rounds.
- Model update status.
- Global aggregation status.
- Local versus global model performance.
- Evaluation metrics.
- Training history.

Use charts to make the training process understandable.

## F. Privacy and security

Federated learning does not automatically guarantee privacy.

Document and implement appropriate safeguards where feasible:
- Authenticated hospital nodes.
- Encrypted communication.
- Secure model update handling.
- Access control.
- Update validation.
- Secure aggregation where supported.
- Differential privacy where feasible.

If differential privacy or secure aggregation is not implemented, clearly state that limitation.

Do not claim that patient privacy is guaranteed merely because raw records are not transmitted.

## G. Emerging medication risk signals

Design an extension point for identifying emerging medication safety patterns across participating institutions.

For example:
- Repeated adverse outcome patterns associated with a particular medication combination.
- Potentially concerning patterns across multiple institutions.
- Changes in observed risk over time.

Treat these as signals requiring further investigation, not proof of causation.

Do not fabricate real-world adverse event findings.

---

# 11. Technology Stack

Use a practical, modern stack that can be developed and demonstrated locally.

### Frontend

- Next.js.
- React.
- TypeScript.
- Tailwind CSS.
- shadcn/ui.
- Lucide icons.
- Recharts for charts and dashboards.

### Backend

- Python.
- FastAPI.
- Pydantic.
- SQLAlchemy.
- REST APIs.

### Database

Prefer PostgreSQL.

SQLite is acceptable for an initial local prototype if PostgreSQL setup becomes a blocker. Structure the database so migration to PostgreSQL is straightforward.

### AI and document processing

Use:
- OCR/document extraction.
- LLM abstraction layer.
- Structured JSON outputs.
- Pydantic validation.
- Configurable AI provider integration.

Do not hardcode API keys.

Use environment variables.

### Machine learning

Use:
- Python.
- pandas.
- NumPy.
- scikit-learn.
- Flower.

Use other libraries only when justified.

### Deployment and development

Use:
- Docker.
- Docker Compose.
- Environment variables.
- Local file storage abstraction.
- Seed scripts.
- Database migrations.

The application must run locally using clear instructions.

---

# 12. Database Design

Create a normalized database schema that supports the full product.

Suggested entities:

### Authentication and users
- Users.
- PatientProfiles.
- ClinicianProfiles.
- Organizations.
- Roles.
- UserSessions.

### Medical records
- MedicalDocuments.
- ExtractedMedicalData.
- MedicalConditions.
- MedicalEvents.
- MedicalProcedures.
- MedicalHistory.

### Medication management
- Medications.
- MedicationIngredients.
- Prescriptions.
- MedicationStatements.
- MedicationSchedules.
- MedicationAdherence.
- MedicationInstructions.
- MedicationSources.

### Safety intelligence
- MedicationInteractions.
- InteractionEvidence.
- ClinicalKnowledgeSources.
- RiskAssessments.
- RiskContributingFactors.
- MedicationSafetyAlerts.
- AdverseOutcomeAssessments.
- KnowledgeBaseVersions.

### Laboratory and allergies
- LaboratoryResults.
- LaboratoryReferenceRanges.
- Allergies.
- AdverseReactions.

### Sharing and auditing
- SharedAccessGrants.
- AccessAuditLogs.
- Notifications.

### Federated learning
- HospitalFederatedNodes.
- FederatedTrainingRounds.
- FederatedModelUpdates.
- FederatedModels.
- ModelEvaluationResults.
- SyntheticHospitalDatasets.

Add appropriate:
- Primary keys.
- Foreign keys.
- Indexes.
- Timestamps.
- Status fields.
- Relationships.
- Data validation.

Use soft deletion or historical status management where appropriate for medical records.

---

# 13. UI/UX Requirements

The application must look like a professional healthcare product, not a generic admin dashboard.

Use a clean, modern, accessible healthcare interface.

### Design direction

- Minimal and professional.
- Clear visual hierarchy.
- Calm healthcare-oriented color palette.
- Readable typography.
- Consistent spacing.
- Responsive layout.
- Accessible controls.
- Clear charts and data visualization.
- Meaningful empty states.
- Useful loading states.
- Error handling.
- Clear status indicators.

Avoid overcrowded dashboards.

Do not make every section a separate card. Use a sensible layout and information hierarchy.

### Patient experience is the priority

The patient dashboard should make it immediately clear:

1. What is happening with my health profile?
2. What medications am I currently taking?
3. Are there any medication safety alerts I need to review?
4. What medications do I need to take today?
5. Have I completed my medication schedule?
6. Can I share my records with a doctor?

Safety alerts must be visible and understandable without requiring medical knowledge.

---

# 14. Required Application Pages

Implement the following pages.

## Patient application

1. Login.
2. Registration.
3. Patient onboarding.
4. Patient dashboard.
5. My health profile.
6. Medical history timeline.
7. Medical documents.
8. Document upload.
9. Extracted document review.
10. Current medications.
11. Medication details.
12. Medication safety dashboard.
13. Medication alert details.
14. Daily medication schedule.
15. Medication adherence history.
16. Laboratory results.
17. Allergies and medical conditions.
18. Share medical records.
19. Shared access history.
20. Notifications.
21. Settings.

## Clinician application

22. Clinician dashboard.
23. Authorized patient list.
24. Patient medical profile.
25. Medication reconciliation.
26. Medication safety assessment.
27. Pre-prescription checker.
28. Clinician access history.

## Research / administration application

29. Federated learning dashboard.
30. Hospital node management.
31. Model performance comparison.
32. Training round history.
33. Knowledge-base management.
34. System administration.

All pages must be connected to actual backend functionality where applicable.

Do not create buttons that do nothing.

---

# 15. Demo Patient and Synthetic Data

Create a realistic synthetic demonstration patient.

Example:

**Patient: Fatima Hassan**
- Age: 72.
- Medical history: Type 2 diabetes, hypertension, chronic kidney disease, and a cardiovascular condition.
- Receives treatment from three different synthetic healthcare providers.
- Has several prescriptions from different specialists.
- Has historical and active medications.
- Has relevant laboratory reports.
- Has at least one documented allergy or adverse reaction.
- Has a mixture of current, discontinued, and uncertain medication records.

Create synthetic records from:
- Hospital A.
- Hospital B.
- Hospital C.

The records should demonstrate the actual problem of fragmented medical information.

Include examples of:
- A prescription from one specialist.
- Another prescription from a different hospital.
- A laboratory report.
- A historical prescription.
- A medication discrepancy.
- A potentially relevant medication safety finding from the demonstration knowledge base.

Use clearly labelled synthetic data and clinically verified example interaction records where possible.

Do not use real patient data.

Do not invent clinical facts and present them as established medical evidence.

The demo should allow someone to upload records, review extracted information, build a unified profile, trigger medication checks, receive alerts, follow a medication schedule, and share the profile with a clinician.

---

# 16. Security, Privacy, and Healthcare Safety

Security is a core requirement, not a feature to add at the end.

Implement:

- Secure authentication.
- Password hashing.
- Role-based access control.
- Patient-authorized clinician access.
- Secure document storage.
- Input validation.
- API authorization checks.
- Protection against common web vulnerabilities.
- Secure session handling.
- Environment-based secrets.
- Audit logging.
- Expiring sharing tokens.
- Revocable access.
- Safe error handling.
- File type and size validation.
- Protection against unauthorized document access.

Never expose patient documents through publicly accessible file URLs.

Treat uploaded documents as untrusted input.

Do not allow document content to override system instructions or trigger unauthorized actions during AI processing.

Keep sensitive data out of application logs.

Use synthetic data for all demonstration and testing.

Document the security assumptions and limitations.

---

# 17. AI Implementation Requirements

Create a modular AI architecture.

Do not tightly couple the application to one model provider.

Implement:
- AI provider abstraction.
- Structured extraction outputs.
- Schema validation.
- Error handling.
- Retry handling where appropriate.
- Configurable model selection.
- Environment-based API configuration.

AI should be used for:
- Extracting information from medical documents.
- Organizing unstructured medical information.
- Explaining verified medication safety findings in plain language.
- Helping users understand their health records.

AI must not independently invent:
- Medication interactions.
- Dosage instructions.
- Food instructions.
- Clinical references.
- Laboratory values.
- Risk probabilities.
- Diagnoses.

The medication safety engine must be grounded in reliable clinical knowledge and deterministic checks wherever possible.

The AI explanation layer should only explain findings returned by the safety engine.

---

# 18. Development Plan

Build the project in phases, but continue through the phases rather than stopping after generating a plan.

## Phase 1: Project foundation

- Inspect the existing repository.
- Set up frontend and backend.
- Configure database.
- Implement authentication.
- Implement roles and permissions.
- Create database models and migrations.
- Establish frontend/backend communication.
- Create the main application layout.

## Phase 2: Unified health records

- Implement patient profile.
- Implement document upload.
- Implement document storage.
- Implement document extraction pipeline.
- Implement structured medical data.
- Implement patient verification.
- Implement medical timeline.
- Implement medication record consolidation.

## Phase 3: Medication safety engine

- Create medication knowledge schema.
- Implement medication normalization and active ingredient matching.
- Implement interaction checking.
- Implement drug–food and drug–supplement checking where data is available.
- Implement duplicate therapy checks.
- Implement contraindication checks.
- Implement dose-related checks where reliable data exists.
- Implement patient-specific risk analysis.
- Implement multi-drug risk assessment where supported.
- Implement evidence and severity classification.
- Implement patient alert generation.
- Implement alert history and updates.
- Create a demonstration knowledge base.
- Add comprehensive tests for the medication checker.

This phase must be treated as a priority.

## Phase 4: Medication schedule and adherence

- Implement verified prescription instructions.
- Generate medication schedules.
- Implement daily schedule interface.
- Implement taken/skipped/remind-later actions.
- Implement adherence history.
- Implement reminders.
- Implement schedule recalculation when prescriptions change.

## Phase 5: Clinician portal and record sharing

- Implement secure sharing grants.
- Implement expiry and revocation.
- Implement clinician authorization.
- Implement patient record viewer.
- Implement medication reconciliation.
- Implement pre-prescription safety checking.
- Implement access audit logs.

## Phase 6: Federated learning

- Generate synthetic hospital datasets.
- Implement local hospital training.
- Implement federated aggregation.
- Implement multiple training rounds.
- Implement global model distribution.
- Implement local versus federated model evaluation.
- Implement multi-outcome model architecture.
- Create research dashboard.
- Display actual experimental results.

## Phase 7: Testing and refinement

- Test complete patient workflows.
- Test clinician workflows.
- Test medication safety rules.
- Test authorization boundaries.
- Test document extraction.
- Test database relationships.
- Test API endpoints.
- Test frontend functionality.
- Fix errors.
- Improve responsiveness.
- Improve loading and error states.
- Verify setup instructions.

---

# 19. Required Tests and Acceptance Criteria

The MVP is not complete until the following workflows work.

## Patient workflow

- [ ] A patient can register and log in.
- [ ] A patient can create a health profile.
- [ ] A patient can upload medical documents.
- [ ] The system extracts structured medical information.
- [ ] The patient can review and correct extracted information.
- [ ] Verified records appear in the unified health profile.
- [ ] Records from different hospitals are organized together.
- [ ] Current and historical medications are distinguishable.
- [ ] The patient can view their complete medical timeline.

## Comprehensive medication safety workflow

- [ ] Adding a new medication automatically triggers a safety assessment.
- [ ] The new medication is checked against every relevant active medication.
- [ ] The system supports drug–drug interaction checking.
- [ ] The system supports drug–food interaction checking where reliable data exists.
- [ ] The system supports drug–supplement interaction checking where reliable data exists.
- [ ] The system identifies potential duplicate ingredients and overlapping therapies.
- [ ] The system identifies relevant contraindications.
- [ ] The system checks dosage and administration conflicts where sufficient information exists.
- [ ] The system considers patient-specific conditions and laboratory results.
- [ ] The system supports multi-drug risk analysis where evidence permits.
- [ ] The system identifies relevant risks across all supported categories, not only the six adverse outcomes.
- [ ] The system generates understandable, severity-ranked patient alerts.
- [ ] Each alert includes its supporting evidence or clearly identifies its demonstration-data status.
- [ ] The system identifies missing information rather than guessing.
- [ ] Updating or discontinuing a medication recalculates relevant safety assessments.
- [ ] Alerts are not repeatedly duplicated without a meaningful change.
- [ ] The system distinguishes no known issue from proof of safety.
- [ ] The system distinguishes clinical rules from ML-generated predictions.

## Medication management workflow

- [ ] The patient can view a daily medication schedule.
- [ ] Schedule instructions come from verified prescriptions or reliable references.
- [ ] Unclear food or timing instructions are flagged.
- [ ] The patient can mark medications as taken or skipped.
- [ ] Adherence history is stored.
- [ ] The patient can view adherence summaries.

## Clinician workflow

- [ ] A patient can share selected or complete records.
- [ ] The patient can revoke access.
- [ ] A clinician can access only authorized records.
- [ ] The clinician can review the patient's medication list.
- [ ] The clinician can review medication safety alerts.
- [ ] The clinician can enter a proposed medication.
- [ ] The system evaluates the proposed medication against the patient's known health profile.
- [ ] Access events are logged.

## Federated learning workflow

- [ ] Three simulated hospitals have separate synthetic datasets.
- [ ] Each hospital trains locally.
- [ ] Raw local patient training records are not sent to the central aggregator.
- [ ] The aggregator receives model updates.
- [ ] Multiple federated training rounds execute.
- [ ] A global model is produced.
- [ ] Local and federated model performance is compared.
- [ ] Metrics are calculated from actual evaluation results.
- [ ] The research dashboard displays training and evaluation results.
- [ ] The implementation documents privacy limitations.

---

# 20. Deliverables

At the end of development, provide:

1. Complete working source code.
2. Frontend application.
3. Backend application.
4. Database schema and migrations.
5. Synthetic demo dataset.
6. Medication safety demonstration knowledge base.
7. AI document extraction implementation.
8. Federated learning implementation.
9. Clinician portal.
10. Patient dashboard.
11. Research dashboard.
12. API documentation.
13. README with setup instructions.
14. `.env.example`.
15. Docker configuration.
16. Testing instructions.
17. Architecture documentation.
18. Security and privacy limitations.
19. Federated learning experiment instructions.
20. Known limitations and future development roadmap.

The README must explain:
- How to install dependencies.
- How to configure environment variables.
- How to start the database.
- How to run the backend.
- How to run the frontend.
- How to create synthetic data.
- How to log in using demo accounts.
- How to run the federated learning experiment.
- Which features require external API keys.

---

# 21. Instructions for Claude Code While Building

Follow these rules throughout development:

1. First inspect the repository and understand its current structure.
2. If the repository is empty, establish a clean project structure.
3. Before implementing, create a concise architecture and implementation checklist.
4. Do not stop after producing the architecture. Continue building.
5. Implement real backend functionality rather than hardcoded frontend-only demonstrations.
6. Connect every major frontend feature to its corresponding API and database functionality.
7. Do not create buttons or interactions that do nothing.
8. Use reusable components and maintainable code.
9. Validate all API inputs and outputs.
10. Handle loading, errors, empty states, and invalid data.
11. Use synthetic patient data for demonstrations.
12. Never fabricate clinical evidence or claim clinical validation.
13. Clearly label simulated and demonstration-only features.
14. Do not hardcode fake model metrics.
15. Keep medication safety logic modular and independently testable.
16. Keep external clinical data providers replaceable.
17. Keep AI providers configurable.
18. Make the application responsive.
19. Run tests after implementing each major module.
20. Fix errors before moving to the next phase.
21. Keep the README and setup instructions updated as the project evolves.
22. If a feature cannot be completed, document exactly what is missing and why. Do not pretend it is implemented.

### Final priority

Build a cohesive, working healthcare product with the patient experience at its center.

The most important workflow is:

**Patient uploads medical records → AI extracts and organizes the information → Patient verifies the records → Platform consolidates the complete medication list → Comprehensive medication safety engine checks for any clinically relevant issue → Patient receives clear alerts → Patient manages their daily medication schedule → Patient securely shares their health profile with a clinician.**

The clinician can then review the patient's complete authorized medical history and check proposed prescriptions before prescribing.

Behind this product, the federated learning system demonstrates how multiple hospitals can collaboratively improve medication-related risk intelligence without centralizing their raw patient training records.

Do not reduce this product to a simple drug interaction checker, a chatbot, or a static dashboard.

Build the full connected MVP.
