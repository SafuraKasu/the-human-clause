# Competition Brief — ITU AI for Good Lab Hackathon: United Arab Emirates (2026)

> **Purpose of this file:** Give a coding agent accurate context about the competition, its official requirements, evaluation criteria, submission materials, and constraints. This is **not** the product specification or an instruction to implement every example mentioned below.
>
> **Source of truth:** [Official ITU event page and FAQs](https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/) (reviewed 7 November 2026). If this document and updated organizer communications disagree, follow the latest official instructions.

## 1. What is the competition?

The **AI for Good Lab Hackathon: United Arab Emirates**, organized under ITU's AI for Good initiative, challenges teams to develop and demonstrate **AI agent-based applications grounded in relevant national policies, regulations, strategies, standards, and institutional responsibilities**.

The initiative also aims to build a **collaborative, open, cross-domain and cross-national policy knowledge base and AI-agent infrastructure**, with coordination and leadership from the UAE. Participating communities include students, researchers, and professionals from different countries.

The organizers emphasize three interconnected goals:

1. **Domain-specific AI solutions:** Demonstrate useful agentic AI applications in fields such as healthcare, education, telecommunications, agriculture, and public services.
2. **Policy and regulatory alignment:** Show how AI applications interact with national laws, government strategies, institutional mandates, standards, and international best practices. Identify meaningful policy or standards gaps.
3. **Behavior under realistic conditions:** Evaluate agentic systems during progressively developing technical, operational, and regulatory failure scenarios where information is incomplete or arrives unevenly.

**Important scope clarification:** The use case does **not** have to solve a problem unique to the UAE. The competition requires relevant **country-level policy grounding** and accurate **international comparisons**. The official evaluation notes explicitly favor **domain-specific gaps and relevant global policy examples**, rather than recommendations narrowly restricted to one geography.

## 2. What participants are expected to build

Officially, participants are required to **build and demonstrate an AI agent-based solution** that uses a knowledge base assembled from relevant use-case documentation and is consistent with applicable country policies, standards, and regulations.

The challenge asks participants to address the following elements:

### A. Domain application
- Demonstrate a real, domain-specific use case with a clear application of agentic AI.
- Connect the application to relevant regulatory, strategic, and institutional context.

### B. Policy / regulatory knowledge base
- Build or contribute structured knowledge from **published, open country documents** applicable to the use case.
- Relevant material can include legislation, AI and digital strategies, cybersecurity and privacy rules, sector-specific regulations, institutional mandates, and relevant international commitments.
- Support retrieval of appropriate documents and passages when the agent encounters a question or scenario.
- The organizers provide [reference code for knowledge-base construction](https://github.com/CrashingGuru/ITUAIReadiness); participants may use the ITU Lab/Sandbox resources where access is granted.

**Distinction:** A technical or domain knowledge base alone is not a substitute for the competition's **policy, regulation, and strategy** knowledge base.

### C. AI-agent roles (examples given by organizers)
The official brief describes possible agent capabilities/roles, including:
- **Innovative application agent:** Uses domain and policy knowledge to demonstrate practical value.
- **Policy/legal adviser:** Retrieves relevant requirements during simulated errors; considers legal authority, institutional responsibilities, standards, and global examples.
- **Institutional participant:** Represents an actor such as a ministry, regulator, or technical authority in a simulation.
- **Multi-agent coordination:** Multiple agents with distinct mandates and information exchange independent assessments and coordinate responses.

These are **example roles/capabilities**, not a mandate to create a fixed number of agents. The solution should make agent behavior and authority clear.

### D. Progressive failure/error scenarios
- Design **interactive scenarios** in which events are released **sequentially**, rather than supplying all facts at once.
- Include realistic incomplete, conflicting, delayed, or unevenly distributed information.
- Evaluate both **technical behavior** and **policy/institutional behavior**.
- Give the system opportunities to identify regulatory conflicts, unclear mandates, coordination failures, or standards gaps.

### E. Traceability and oversight
- Maintain audit logs and explainable, reviewable decision records.
- Attribute policy conclusions to supporting sources.
- Make agent actions, referenced provisions, applicable checks, and institutional handoffs inspectable.
- The official brief uses the phrase *“chain-of-thought tracing”*. For an implementation, provide **auditable decision summaries, evidence references, action logs, and rule-check traces**; do not depend on exposing a model's hidden private reasoning.

### F. Alignment with ITU frameworks
The design and report must demonstrate alignment with:
- **[ITU-T Y.3172](https://www.itu.int/rec/T-REC-Y.3172/en)** — an ITU architectural framework for machine learning in future networks; explain the relevant architectural mapping, rather than only citing its name.
- **[ITU AI Readiness Framework](https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf)** — consider relevant readiness dimensions and document their relationship to the use case.

The event page specifically mentions these lenses:
- Open data and open-source management
- Generative AI content ecosystem
- Contextualization and regional development
- Domain-specific and cross-domain AI integration
- Human interaction and supervision
- AI policy and implementation opportunities
- AI for social inclusion
- Digital infrastructure and energy considerations

## 3. Official judging / evaluation criteria

**No numerical category weights are published on the event page.** Do not assume or invent a scoring distribution.

| Evaluation category | What the organizers say is assessed |
| --- | --- |
| **Knowledge-base quality** | Completeness, accuracy, and structure of ingested national material; relevant policy retrieval under query. |
| **Agent capability** | Relevance and accuracy of agent responses in simulated error scenarios; appropriate solutions that respect laws, institutional mandates, and coordination mechanisms. |
| **Policy, strategy, and standards gap identification** | Quality of identified gaps, ambiguities, conflicts, coordination problems, unclear responsibilities, and accurate comparisons with global policy examples. |
| **Auditability** | Transparency and reviewability of agent decisions through logs, traces, and source attribution. |
| **ITU alignment** | Clear reflection of ITU-T Y.3172 and the AI Readiness Framework in the proposed architecture and evaluation. |

**Nuance about accuracy:** The official FAQ states that **overall AI prototype accuracy is not a separate evaluation criterion**. But the published **agent-capability criterion explicitly evaluates relevance and accuracy of responses during error scenarios**. Do not interpret the FAQ as permission to ignore testing, factual reliability, or domain safety.

**Nuance about policy gaps:** The organizers explicitly emphasize the relevance of domain-specific policy gaps and the accuracy of global policy examples. A difference between two countries is not automatically a gap; recommendations should be evidenced.

## 4. Submission materials — first round

The official page lists:

1. **Technical report — maximum 5 pages.** Use the [official Word template](https://s41721.pcdn.co/wp-content/uploads/2022/06/AI-for-Good-Sandbox-Hackathon-submission-template.docx).
2. **GitHub repository** containing the relevant code.
3. **Knowledge base** containing applicable **policies, regulations, and strategies** (the event links a [reference repository](https://github.com/CrashingGuru/ITUAIReadiness)).
4. **Demo video — optional for first-round submission; maximum 7 minutes.** The video becomes **required if shortlisted**.

A functional AI-agent solution must be demonstrated or supported by the submitted materials. This is not a proposal-only competition.

### 4.1 Required report content (official FAQ)

The FAQ enumerates these eight items:

1. Short overall introduction to the agentic AI solution.
2. Description of the use case.
3. Requirements of the use case.
4. Mapping to **ITU-T Y.3172**.
5. Mapping to the **ITU AI Readiness Framework 2.0**.
6. Mapping of requirements to **local policies**.
7. Evaluation scenario covering **both technical solution and policy**.
8. Policy and standards gaps found through the mapping exercise.

### 4.2 Demo-video content (official FAQ)

If preparing the video, cover:

1. Hardware and software setup of the AI prototype.
2. Main functions.
3. Expected outcomes for each evaluation scenario.
4. **Actual observed outcomes** from the AI solution.

### 4.3 Code-publication rule

The FAQ says teams may publish **only essential code** in a public GitHub repository if they need to protect important components. However, the organizers caution that this **may influence judges' decisions**. Avoid claiming unavailable components are implemented.

## 5. Timeline

Dates shown on the official event page, as checked **7 November 2026**:

| Milestone | Date |
| --- | --- |
| Registration | **Applications closed** on the current event page |
| First-round submission deadline | **10 November 2026** |
| First-round evaluation | **11–18 November 2026** |
| Shortlist announcement | **18 November 2026** |
| Final evaluation, in person in Dubai | **8 December 2026** |
| Award ceremony, in person in Dubai | **10 December 2026** |

The final event is listed at the **Dubai Exhibition Centre, Expo City Dubai**. The organizers state that travel sponsorship is provided for selected overseas teams; do not assume this resolves individual visa requirements.

## 6. Participation and team rules

- **Maximum team size: 4 people**, including an internal mentor if one is counted as a team member (the page gives the examples of four participants or three participants plus one internal mentor).
- Team name and use-case domain could be changed **before final submission** without notifying the organizer, according to the FAQ.
- Participants may belong to multiple teams and submit multiple solutions.
- An idea used in another competition may be reused if this hackathon's specific requirements are met.
- The **Special Prize for Women's Team** requires a **woman team leader**.
- Only teams submitting a **valid solution** receive certificates of participation.
- At most **one prize per team**.

## 7. Prizes and possible follow-up

Officially listed prizes:

| Award | Value |
| --- | ---: |
| First / Grand Prize | CHF 1,500 |
| Second Prize | CHF 1,000 |
| Third Prize | CHF 600 |
| Judges' Prize | CHF 1,000 |
| Special Women's Team Prize | CHF 600 |

The Judges' Prize considers engagement and future potential in research, development, innovation, or standards. The organizers also mention possible follow-up through international showcases, ITU Study Groups, academic papers, and open-source contributions. These are **opportunities**, not guaranteed outcomes for any submission.

## 8. Competition-facing completion checklist

Use this as a **compliance checklist**, not as a request to add unrelated features to the product:

- [ ] A working, domain-specific **AI agent-based solution** is demonstrable.
- [ ] Relevant **national policy / regulatory / strategy** materials are assembled into a retrievable knowledge base.
- [ ] The application can cite or otherwise attribute applicable policy sources.
- [ ] Agent responsibilities, authorities, and coordination behavior are explicit.
- [ ] At least one evaluation scenario introduces events **progressively** and tests technical **and** policy behavior.
- [ ] Expected scenario outcomes and actual results can be compared.
- [ ] Agent actions and decisions have reviewable audit records and supporting evidence.
- [ ] Relevant policy/standards gaps and defensible global examples are documented.
- [ ] Architecture and report map to **Y.3172** and the **AI Readiness Framework**.
- [ ] Technical report addresses all **eight FAQ elements** and is **no longer than 5 pages**.
- [ ] GitHub repository and policy knowledge base are ready to submit.
- [ ] If shortlisted, a **maximum 7-minute video** demonstrates setup, main functions, expected outcomes, and actual outcomes.
- [ ] Claims in the submission reflect what was **actually implemented and evaluated**, not planned capabilities.

## 9. Official references

1. **Primary source — event brief, criteria, timeline, deliverables, FAQs:** https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/
2. **Official technical report template:** https://s41721.pcdn.co/wp-content/uploads/2022/06/AI-for-Good-Sandbox-Hackathon-submission-template.docx
3. **Competition reference knowledge-base code:** https://github.com/CrashingGuru/ITUAIReadiness
4. **ITU-T Y.3172:** https://www.itu.int/rec/T-REC-Y.3172/en
5. **ITU AI Readiness Framework linked on the event page:** https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf

---

**How to use this file:** Read it alongside the separate product/engineering requirements. The competition brief is the authority for **submission compliance and judging alignment**; the project specification defines **what the team is building**. Do not confuse the two.
