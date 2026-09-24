# DEBATE ARENA — FACT CHECK & EVIDENCE ENGINE

## STATUS
LOCKED SYSTEM SPECIFICATION

This document defines the Fact Check and Evidence Intelligence layer of Debate Arena.
It extends:
- `01_DEBATE_CORE_CONSTITUTION.md`
- `02_DEBATE_EVENT_STATE_ENGINE_PROTOCOL.md`
- `03_DEBATE_ROUND_ENGINE_RULES.md`
- `04_DEBATE_MODERATOR_REFEREE_ENGINE.md`
- `05_DEBATE_JUDGE_SCORING_ENGINE.md`

This document defines: **HOW FACTUAL CLAIMS AND EVIDENCE ARE IDENTIFIED, VERIFIED, EVALUATED, AND CONNECTED TO THE DEBATE.**

---

## 1. CORE PRINCIPLE
The Fact Check Engine evaluates factual claims. The Evidence Engine evaluates evidence. They support the Judge Engine without replacing it:
$$\text{CLAIM} \ne \text{EVIDENCE} \ne \text{SOURCE} \ne \text{ARGUMENT} \ne \text{CONCLUSION}$$
- A source can be reliable while a speaker's interpretation is flawed.
- A claim can be true while cited evidence is irrelevant.
- An argument can be logically valid while relying on an unverified premise.
- **UNVERIFIED IS NOT FALSE.**

---

## 2. ROLE SEPARATION
- **CLAIM ENGINE**: Identifies, classifies, and tracks claims.
- **SOURCE ANALYZER**: Evaluates source reliability, authority, and provenance.
- **EVIDENCE ENGINE**: Evaluates claim-evidence match, context, and evidentiary integrity.
- **FACT CHECK ENGINE**: Assesses factual verification status with nuanced non-binary ratings.
- **ARGUMENT ENGINE**: Integrates claims into argument structures.
- **JUDGE ENGINE**: Uses structured findings to evaluate debate performance.

---

## 3 & 4 & 5. CLAIM REGISTRY & CLASSIFICATION
- Unique claim IDs (`PRO-C001`, `CON-C001`).
- Types: `FACTUAL`, `STATISTICAL`, `HISTORICAL`, `SCIENTIFIC`, `LEGAL`, `ECONOMIC`, `CAUSAL`, `PREDICTIVE`, `DEFINITIONAL`, `COMPARATIVE`, `NORMATIVE`, `HYPOTHETICAL`.
- Normative/opinion statements are evaluated on reasoning/values by the Judge Engine—never improperly fact-checked as binary truth.

---

## 6 & 7 & 8 & 9. EVIDENCE REGISTRY & SOURCE EVALUATION
- Evidence IDs (`EVD-001`).
- Source Types: `PRIMARY_SOURCE`, `SECONDARY_SOURCE`, `ACADEMIC_SOURCE`, `GOVERNMENT_SOURCE`, `OFFICIAL_STATISTICS`, `COURT_DOCUMENT`, `PATRISTIC`, `MANUSCRIPT`, etc.
- Source Quality: Authority, transparency, methodology, peer review, and provenance.

---

## 10 to 16. CLAIM-EVIDENCE MATCH, CONTEXT & TEMPORALITY
- **Claim-Evidence Match**: Detects `OVERCLAIM` and `CLAIM_EVIDENCE_MISMATCH`.
- **Non-Binary Statuses**: `SUPPORTED`, `MOSTLY_SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `UNVERIFIED`, `OUTDATED`, `MISLEADING`, `CONFLICTING_EVIDENCE`.
- **Context & Temporal Validity**: Evaluates timeframe, population, geography, and recency. Outdated sources are not automatically false.

---

## 17 to 24. FORENSIC EVIDENCE CHECKS
- **Primary Source Preference**: Original uncial manuscripts, critical apparatus, and empirical datasets.
- **Quotation Integrity**: Detects altered, truncated, or misrepresented citations.
- **Cherry-Picking & Context Stripping**: Contextual evaluation of selective citation.
- **Correlation vs Causation**: Flags `CAUSALITY_OVERCLAIM` when associative data is cited as causal proof.
- **Conflicting Evidence**: Preserves nuance when credible sources disagree without manufacturing false certainty.

---

## 25 to 33. EVIDENCE LAUNDERING & SOURCE INDEPENDENCE
- Detects circular citation where multiple outlets repeat a single unverified original source ($A \leftarrow B \leftarrow C$ is 1 origin, not 3 independent confirmations).

---

## 34 to 47. SCORING INTEGRATION & EVIDENCE GRAPH
- Evidence Graph connects: $\text{SOURCE} \rightarrow \text{EVIDENCE} \rightarrow \text{CLAIM} \rightarrow \text{ARGUMENT} \rightarrow \text{CLASH} \rightarrow \text{SCORING}$.
- Integrates seamlessly into the 15-point `Evidence & Factuality` category in the Judge Engine.
- Does not create a competing second score system.

---

## 48 to 66. AUDIT TRAILS, POSITION-NEUTRALITY & DEFINITION OF DONE
- Complete immutable audit trails for every fact-check evaluation.
- Identical verification standards applied equally to Proposition and Opposition.
- Failure resilience: `FACT_CHECK_PENDING` without collapsing live debate or fabricating results.
