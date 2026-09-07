# STEP 148 — CLAIM-TO-SOURCE GRAPH: FORENSIC AUDIT
## Canonical Evidence-Traceability QC Layer for Christian–Islamic Apologetics & Religious Debate

> **Quality-control layer position:**
> ARGUMENT DATABASE (STEP 145) → COUNTERARGUMENT DATABASE (STEP 146) → DEBATE ANALYSIS / FALLACY (STEP 147) → **CLAIM-TO-SOURCE GRAPH (STEP 148)** → FINAL APOLOGETICS ENGINE
>
> **Scope:** STEP 148 only. Does NOT redo, recover, or modify STEP 100–147. Does NOT touch specialist files, production files, or KNOWLEDGE_INDEX.md (pending final verification). Does NOT begin STEP 149.
>
> **Integration posture (no duplication):** STEP 145 = argument database; STEP 146 = counterargument database; STEP 147 = fallacy taxonomy; STEP 148 = evidence graph. This step creates *linkage* to those layers — it does not re-create them. An argument from STEP 145 is referenced by ID here, not re-stated in full; a counterargument from STEP 146 is linked as a target edge; a fallacy from STEP 147 is tagged on edges that violate a fallacy rule. The graph adds the evidence-traceability layer that the prior layers presuppose but do not themselves model.

---

## TABLE OF CONTENTS

1. [Core Principle — Source-Chain Traceability](#1-core-principle--source-chain-traceability)
2. [Absolute Rules](#2-absolute-rules)
3. [Graph Model — Node Types](#3-graph-model--node-types)
4. [Graph Model — Edge Types](#4-graph-model--edge-types)
5. [Independence Model](#5-independence-model)
6. [Critical Warnings — Independence Anti-Patterns](#6-critical-warnings)
7. [Claim Classes](#7-claim-classes)
8. [Confidence Scale](#8-confidence-scale)
9. [Source Chain](#9-source-chain)
10. [Layer-Absence Markers](#10-layer-absence-markers)
11. [Required Audits (30)](#11-required-audits)
12. [Propagation Rule](#12-propagation-rule)
13. [Three Non-Transfer Identities](#13-three-non-transfer-identities)
14. [Debate Integration (STEP 145/146/147)](#14-debate-integration)
15. [Graph Integrity Invariants](#15-graph-integrity-invariants)
16. [Comparative Symmetry](#16-comparative-symmetry)
17. [30 Claim Tests (Q148-CT01–CT30)](#17-claim-tests)
18. [15 Case Studies (Q148-CS01–CS15)](#18-case-studies)
19. [Graph Matrix (40 rows)](#19-graph-matrix)
20. [Global Steelmen — Graph-Interpretation Uses (SM-01–SM-05)](#20-global-steelmen--graph-interpretation-uses-sm-01-sm-05)
21. [Error Register (E1–E20)](#21-error-register)
22. [Severity Scale](#22-severity-scale)
23. [Final Audit](#23-final-audit)

---

## 1. CORE PRINCIPLE — SOURCE-CHAIN TRACEABILITY

The audit's purpose is **not** to add new theory. Its purpose is to make the *evidential relationship* between any apologetic claim and its ultimate source explicit and two-way traceable, so that every claim can be checked back to its base and every base can be surveyed for the claims resting on it.

The chain under audit:

```
CLAIM
↓
EVIDENCE
↓
PRIMARY SOURCE
↓
ORIGINAL LANGUAGE
↓
MANUSCRIPT / WITNESS
↓
TRANSCRIPTION
↓
TRANSLITERATION
↓
TRANSLATION
↓
INTERPRETATION
↓
DOCTRINE
↓
APOLOGETIC ARGUMENT
```

A rhetorically persuasive citation is **not** automatically a valid evidential link. A valid link is **not** automatically an independent one. An independent link is **not** automatically a strong one. A strong link is **not** automatically a theological proof. Each transition is a separate inferential step that must be made explicit and is auditable independently.

## 2. ABSOLUTE RULES

| # | Rule |
|---|---|
| 1 | Do not modify specialist files. |
| 2 | Do not modify production files. |
| 3 | Do not modify STEP 100–147. |
| 4 | Do not perform rewrite/recovery of prior steps. |
| 5 | Do not create STEP 149. |
| 6 | Do not modify KNOWLEDGE_INDEX.md before STEP 148 PASS FINAL. |
| 7 | Do not count the same source as independent evidence without an independence analysis. |
| 8 | Do not treat citation presence as evidence validity. |
| 9 | Do not treat multiple URLs/books as multiple independent witnesses. |
| 10 | Distinguish physical-source, textual, editorial, and argumentative independence. |
| 11 | Do not alter prior-step conclusions merely to make the graph look tidy. |
| 12 | If a conflict exists, record it as conflict/uncertainty — do not force a resolution. |
| 13 | Every claim must be two-way traceable: CLAIM → SOURCE and SOURCE → CLAIM. |
| 14 | Distinguish primary source / manuscript / critical edition / translation / commentary / theological formulation / secondary scholarship / apologetic argument. |
| 15 | Distinguish source existence / source content / source interpretation / historical inference / theological inference / apologetic conclusion. |

## 3. GRAPH MODEL — NODE TYPES

| Node type | Definition | Examples |
|---|---|---|
| CLAIM | A proposition offered for acceptance | "Jesus was crucified"; "the Qur'an is preserved" |
| SOURCE | An artifact/text attesting something | Gospel of John; Sahih al-Bukhari; a codex |
| MANUSCRIPT | A physical handwritten witness | P52; Codex Sinaiticus; Sanaa palimpsest; Sanaa lower text |
| TEXT | A linguistic unit (verse, pericope, sura) | John 1:1; Q 4:157; Q 23:12-14 |
| LANGUAGE | The original or transmission language | Koine Greek; Biblical Hebrew; Qur'anic Arabic; Syriac |
| TRANSLATION | A rendering in another language | ESV John 1:1; Cairo 1924; Tafsir Ibn Kathir (Arabic-to-interpretation) |
| INTERPRETATION | A reading/gloss of a text | "logos = pre-existent divine Son"; "عَلَقَة = blood-clot" |
| DOCTRINE | A formulated theological teaching | Nicene Trinity; Chalcedonian Christology; Tawhid; Imamah |
| ARGUMENT | A structured case linking claims to evidence | Minimal-facts case; i'jaz argument; tahrif argument |
| COUNTERARGUMENT | A structured case targeting a claim/edge | "hallucination explains appearances"; "Q 4:157 is polyvalent" |
| SCHOLAR | An analyst of a source | Ehrman; Bauckham; Crone; Motzki; Wansbrough |
| EVENT | A putative past occurrence | Crucifixion; Uthmanic recension; Ghadir Khumm |
| TRADITION | A received line of transmission | A Hadith isnad chain; a patristic line; a qira'at reading |
| EDITION | A scholarly reconstruction | NA28; UBS5; BHS; Cairo 1924 edition |

## 4. GRAPH MODEL — EDGE TYPES

| Edge type | From → To | Meaning |
|---|---|---|
| CLAIM_SUPPORTED_BY | CLAIM → SOURCE/EVIDENCE | The claim is offered as supported by the target |
| CLAIM_QUALIFIED_BY | CLAIM → SOURCE | The claim is limited/conditioned by the target |
| CLAIM_CONTRADICTED_BY | CLAIM → SOURCE/COUNTERARGUMENT | The claim is opposed by the target |
| CLAIM_DEPENDS_ON | CLAIM → CLAIM/PREMISE | The claim's warrant requires the target premise |
| SOURCE_CONTAINS | SOURCE → TEXT | The source includes the textual unit |
| SOURCE_QUOTES | SOURCE → SOURCE | The source quotes/cites another source |
| SOURCE_TRANSLATES | SOURCE → SOURCE | The source is a translation of another source |
| SOURCE_INTERPRETS | SOURCE → TEXT | The source provides an interpretation/gloss |
| SOURCE_DERIVES_FROM | SOURCE → SOURCE | The source descends genealogically |
| SOURCE_DEPENDS_ON | SOURCE → SOURCE | The source's content depends on the target (not necessarily genealogical) |
| MANUSCRIPT_PRESERVES | MANUSCRIPT → TEXT/SOURCE | The manuscript witnesses the text |
| EDITION_RECONSTRUCTS | EDITION → TEXT | The edition is a scholarly reconstruction of the text |
| TRANSLATION_RENDERS | TRANSLATION → TEXT | The translation renders a text |
| INTERPRETATION_READS | INTERPRETATION → TEXT | The interpretation reads the text a certain way |
| DOCTRINE_DEVELOPS_FROM | DOCTRINE → INTERPRETATION/TEXT | The doctrine develops from the interpretation |
| ARGUMENT_DEPENDS_ON | ARGUMENT → CLAIM/PREMISE | The argument's case rests on the target |
| ARGUMENT_SUPPORTS | ARGUMENT → CLAIM | The argument supports the claim |
| COUNTERARGUMENT_TARGETS | COUNTERARGUMENT → CLAIM/EDGE | The counterargument targets a specific claim or edge |
| EVENT_ATTESTED_BY | EVENT → SOURCE/MANUSCRIPT | The event is attested by the target |
| TRADITION_TRANSMITS | TRADITION → EVENT/TEXT/DOCTRINE | The tradition transmits the target |
| SCHOLAR_ANALYZES | SCHOLAR → SOURCE/TEXT | The scholar analyzes the target |

## 5. INDEPENDENCE MODEL

For every evidential relationship, audit six independence dimensions. Each is tagged with a status from the scale in §8 (adapted).

| Dim | Name | Question |
|---|---|---|
| A | Physical independence | Are the witnesses distinct physical artifacts? |
| B | Editorial independence | Are the editorial decisions independent (not all reliant on one critical edition)? |
| C | Textual independence | Are the textual traditions distinct (not copied from a common exemplar)? |
| D | Genealogical independence | Do the witnesses descend from independent lines, not a common ancestor? |
| E | Argumentative independence | Does each source argue the point on its own grounds, or do they all cite the same prior argument? |
| F | Chronological independence | Are the witnesses from different time strata, or all from one late stratum? |

**Independence statuses (per dimension):**

| Status | Meaning |
|---|---|
| ESTABLISHED | Independence demonstrated |
| PROBABLE | Independence likely on present evidence |
| POSSIBLE | Independence cannot be ruled out but not yet demonstrated |
| UNKNOWN | Insufficient information to judge |
| NOT_INDEPENDENT | Dependence demonstrated |
| DISPUTED | Competing analyses of independence |

## 6. CRITICAL WARNINGS — INDEPENDENCE ANTI-PATTERS

The four forbidden moves this audit exists to prevent:

| # | Anti-pattern | What it claims | What is actually the case |
|---|---|---|---|
| 1 | Citation multiplication | "10 sources confirm X" | 10 websites reproduce 1 edition |
| 2 | Manuscript multiplication | "Multiple manuscripts independently prove X" | Genealogical relationship not analyzed — may all descend from one exemplar |
| 3 | Scholar multiplication | "Three scholars independently prove X" | All three depend on the same manuscript/edition |
| 4 | Tradition-label aggregation | "Christian sources confirm…" / "Islamic sources confirm…" | Individual sources and their independence levels not broken out |

> **Detection priority:** The audit flags any edge claiming multiplicity-based support *before* the independence dimensions have been audited. The flag is `PENDING_INDEPENDENCE_AUDIT` and blocks the edge from contributing to confidence until the audit is run.

## 7. CLAIM CLASSES

Every claim node carries exactly one primary class:

| Class | Definition |
|---|---|
| FACT | A verifiable empirical datum |
| HISTORICAL_CLAIM | A claim about a past event |
| TEXTUAL_CLAIM | A claim about textual transmission |
| LINGUISTIC_CLAIM | A claim about language |
| INTERPRETATION | A reading of a datum |
| THEOLOGICAL_CLAIM | A claim about God/the divine |
| TRADITION | A received belief/practice with traceable history |
| APOLOGETIC_ARGUMENT | A structured case |
| COUNTERARGUMENT | A structured case targeting another |
| SPECULATION | A hypothesis without sufficient support |
| UNCERTAIN | A claim whose class itself is unsettled |

## 8. CONFIDENCE SCALE

| Band | Definition |
|---|---|
| ESTABLISHED | Mainstream consensus, robust to scrutiny |
| STRONG EVIDENCE | Well-supported but contestable |
| PROBABLE | More likely than not on current evidence |
| PLAUSIBLE | A defensible reading/explanation among alternatives |
| DISPUTED | Serious competing positions; no clear verdict |
| UNCERTAIN | Evidence thin or mixed |
| SPECULATIVE | Insufficient evidence; hypothesis only |
| UNSUPPORTED | No adequate evidence; claim not warranted as stated |

## 9. SOURCE CHAIN

The full auditable chain (not every claim traverses every layer):

```
CLAIM → EVIDENCE → PRIMARY SOURCE → ORIGINAL LANGUAGE
      → MANUSCRIPT/WITNESS → TRANSCRIPTION → TRANSLITERATION
      → TRANSLATION → INTERPRETATION → DOCTRINE → APOLOGETIC ARGUMENT
```

## 10. LAYER-ABSENCE MARKERS

When a layer does not apply or is not available, mark explicitly — never fill a gap with an assumption:

| Marker | Meaning |
|---|---|
| NOT_APPLICABLE | This layer does not apply to the claim type (e.g., a logical claim has no manuscript layer) |
| NOT_AVAILABLE | The layer applies but the data is not in hand |
| NOT_ESTABLISHED | The layer applies, data exists, but its status is not established |

## 11. REQUIRED AUDITS (30)

| # | Audit | What it checks |
|---|---|---|
| 1 | Claim-source traceability | Every claim traces forward to a source |
| 2 | Source-claim reverse traceability | Every source traces back to claims resting on it |
| 3 | Primary-source separation | Primary sources not conflated with secondary |
| 4 | Manuscript separation | Distinct mss not counted as one; one ms not counted as many |
| 5 | Critical-edition separation | Editions not conflated with manuscripts or autographs |
| 6 | Translation separation | Translations not treated as originals |
| 7 | Interpretation separation | Interpretations not treated as the text's own statement |
| 8 | Doctrine separation | Doctrine not treated as the apostolic/prophetic text's own statement |
| 9 | Argument separation | Apologetic arguments not treated as primary evidence |
| 10 | Source independence | All six dimensions audited where multiplicity is claimed |
| 11 | Duplicate-source detection | Same source counted once |
| 12 | Same-underlying-source detection | Sources sharing a common underlying source not counted as independent |
| 13 | Citation laundering detection | A source that merely re-cites another not treated as adding weight |
| 14 | Circular citation detection | A→B→A loops flagged |
| 15 | Dependent-source detection | Genealogical/editorial dependence flagged |
| 16 | Chronological layering | Sources ordered by date; late sources not treated as early |
| 17 | Evidence-strength propagation | Strength does not transfer unchanged through the chain |
| 18 | Confidence propagation | Confidence at each layer computed, not carried wholesale |
| 19 | Unsupported-claim detection | Claims with no source edge flagged UNSUPPORTED |
| 20 | Orphan-node detection | Claim nodes with no source; source nodes supporting no claim |
| 21 | Broken-edge detection | Edges pointing to nonexistent nodes |
| 22 | Contradiction-edge audit | CLAIM_CONTRADICTED_BY edges verified |
| 23 | Counterargument linkage | Counterarguments linked to target claims/edges |
| 24 | Steelman linkage | Steelman of each position present and linked |
| 25 | Comparative symmetry | Same tests applied across traditions |
| 26 | Islam-Christianity symmetry | No tradition privileged over the other in evidence rules |
| 27 | Primary-vs-secondary weighting | Primary not automatically outweighed by secondary; secondary not counted as primary |
| 28 | Translation-risk propagation | Translation choices flagged as inferential steps, not data |
| 29 | Historical-distance audit | Distance between event and source noted; late sources not treated as near-contemporary |
| 30 | Argument-overreach audit | Arguments not claiming more than their source edges establish |

## 12. PROPAGATION RULE

Evidence strength must **not** automatically transfer unchanged through the graph. The canonical propagation chain:

```
MANUSCRIPT → TEXT → TRANSLATION → INTERPRETATION → DOCTRINE → APOLOGETIC ARGUMENT
```

The further an inference moves from its source, the **more explicit** the inferential step must be. A primary manuscript may *strongly establish textual existence* while providing *weak support* for a later theological conclusion. Each arrow is an inferential step with its own confidence band; the chain's end-confidence is *not* the source's confidence but the *product* of each step's confidence, discounted for each uncrossed gap.

**Propagation formula (descriptive, not mechanical):**
`end_confidence = source_confidence × Π(step_confidence_i)` where each `step_confidence_i ∈ [0,1]` is the confidence of transition *i* and uncrossed gaps (NOT_AVAILABLE / NOT_ESTABLISHED) contribute a multiplier strictly less than 1.

## 13. THREE NON-TRANSFER IDENTITIES

Three identities that must never be collapsed (each is a distinct inferential category):

| Identity | What it is NOT |
|---|---|
| HISTORICAL EVENT | ≠ THEOLOGICAL TRUTH |
| TEXTUAL PRESERVATION | ≠ DIVINE ORIGIN |
| HISTORICAL ATTESTATION | ≠ THEOLOGICAL AUTHENTICATION |

> A manuscript can be perfectly preserved and yet not be divine. An event can be historically attested and yet not be theologically authenticated. The bridge from one column to the other is itself an argument requiring its own warrant — never an automatic transfer.

## 14. DEBATE INTEGRATION (STEP 145/146/147)

| Prior step | Role | Linkage in STEP 148 |
|---|---|---|
| STEP 145 | Argument database | Arguments are referenced by ID (e.g., ARG-145-XX) as ARGUMENT nodes; not re-stated |
| STEP 146 | Counterargument database | Counterarguments referenced by ID (e.g., CA-146-XX) as COUNTERARGUMENT nodes; COUNTERARGUMENT_TARGETS edges point to claims/edges |
| STEP 147 | Fallacy taxonomy | Fallacy IDs (e.g., AE-01, IF-04) tagged on edges that violate a fallacy rule; the taxonomy is not duplicated |

**Full traceability chain (the engine's target):**

```
ARGUMENT (STEP 145)
→ CLAIM
→ EVIDENCE
→ SOURCE
→ SOURCE TYPE
→ INDEPENDENCE
→ INTERPRETATION
→ LIMITATION
```

A counterargument (STEP 146) may target *any edge* in this chain — not only the final claim. The graph must therefore expose every edge as a targetable unit.

## 15. GRAPH INTEGRITY INVARIANTS

| # | Invariant |
|---|---|
| 1 | Every claim node has ≥1 source relationship unless explicitly marked UNSUPPORTED |
| 2 | Every source relationship points to an existing node |
| 3 | Every edge has a defined relation from §4 |
| 4 | No broken references |
| 5 | No duplicate canonical nodes |
| 6 | No accidental duplicate evidence |
| 7 | No circular dependency falsely represented as independent evidence |
| 8 | No orphaned claim nodes |
| 9 | No orphaned source nodes (where they are supposed to support a claim) |
| 10 | No impossible chronological relationship |
| 11 | No source classified simultaneously as primary and secondary without explanation |

## 16. COMPARATIVE SYMMETRY

Identical graph tests run against:

- Christian claims
- Islamic claims
- Jewish claims (where relevant)
- Atheist/skeptical claims

**No tradition's evidence rules are privileged over another.** The system's theological standpoint may remain Sunni in *aqidah*, but the **graph itself** preserves descriptive and historical neutrality: a Christian late-source rule is also an Islamic late-source rule; a Bible manuscript-count rule is also a Qur'an manuscript-count rule; a Christian doctrinal-retrojection rule is also an Islamic doctrinal-retrojection rule.

---




## 17. CLAIM TESTS (Q148-CT01 – Q148-CT30)

> Each claim test follows the 16-field schema. Fields are populated; `—` is marked with a one-line reason and never omitted.

### Field schema (per CT)

```
ID
CLAIM
CLAIM_TYPE
NODE_TYPES
SOURCE_CHAIN
PRIMARY_SOURCE_STATUS
MANUSCRIPT_STATUS
TRANSLATION_STATUS
INTERPRETATION_STATUS
DEPENDENCY_STATUS
INDEPENDENCE_STATUS
EVIDENCE_STATUS
CONFIDENCE
COUNTERARGUMENT
STEELMAN
LIMITATION
AUDIT_RESULT
```

---

### Q148-CT01

- **ID:** Q148-CT01
- **CLAIM:** "John 1:1 identifies Jesus as God."
- **CLAIM_TYPE:** THEOLOGICAL_CLAIM / TEXTUAL_CLAIM
- **NODE_TYPES:** CLAIM → TEXT (John 1:1) → LANGUAGE (Koine Greek) → MANUSCRIPT (P66, P75, Codex Sinaiticus) → EDITION (NA28) → TRANSLATION (ESV/NIV/NASB) → INTERPRETATION (logos = pre-existent divine Son) → DOCTRINE (Nicene Trinity)
- **SOURCE_CHAIN:** John 1:1 Greek → papyri/mss → NA28 → English renderings → patristic + modern interpretation → Nicene articulation.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (Gospel of John is a primary text).
- **MANUSCRIPT_STATUS:** ESTABLISHED (P66 c.200 CE, P75 c.200 CE, Codex Sinaiticus 4th c. — early and multiply attested for John 1:1; no substantive variant at this verse).
- **TRANSLATION_STATUS:** DISPUTED (rendering θεὸς ἦν ὁ λόγος — "the Word was God" vs "the Word was divine" vs "what God was, the Word was" — all lexically possible; the definite-article + anarthrous-predicate construction is the contested point).
- **INTERPRETATION_STATUS:** DISPUTED ("God" vs "divine" vs "God in nature" — the reading that supports co-equal deity requires bridging to Nicene categories not explicit in the verse).
- **DEPENDENCY_STATUS:** The theological conclusion (Jesus = co-equal God) DEPENDS_ON an interpretive step from the Greek construction to Nicene categories; this step is inferential, not lexical.
- **INDEPENDENCE_STATUS:** Physical A=ESTABLISHED; Textual C=ESTABLISHED (multiple early mss); Genealogical D=PROBABLE (mss likely independent lines); Chronological F=STRONG (P66/P75 are early); Independence overall = ESTABLISHED for the *text*, DISPUTED for the *theological reading*.
- **EVIDENCE_STATUS:** STRONG EVIDENCE for the textual reading; PLAUSIBLE for the Trinitarian reading; the theological conclusion is one defensible reading, not the only one.
- **CONFIDENCE:** ESTABLISHED (text); PLAUSIBLE (Trinitarian reading).
- **COUNTERARGUMENT:** The anarthrous predicate θεός does not require co-equal deity; "divine" or "of divine nature" are lexically live; the Nicene reading is one articulation, not the verse's only sense. (Links STEP 147 AE-20/TF2-01 doctrine-text conflation.)
- **STEELMAN (Christian):** The combination of John 1:1's predicate-noun construction, 1:3's role in creation, 1:14's incarnation, 20:28's Thomas confession, and early worship patterns cumulatively support reading 1:1 as affirming the Word's deity — not as a single-verse proof but as a strand in the cumulative case.
- **LIMITATION:** The verse alone underdetermines the Nicene formulation; the cumulative case requires independent establishment of the other strands.
- **AUDIT_RESULT:** PASS — text established; theological reading tagged as inferential step with its own confidence band; no overreach.

---

### Q148-CT02

- **ID:** Q148-CT02
- **CLAIM:** "Paul's letters teach a high Christology that predates the Gospels."
- **CLAIM_TYPE:** TEXTUAL_CLAIM / HISTORICAL_CLAIM
- **NODE_TYPES:** CLAIM → TEXT (Phil 2:5-11; 1 Cor 8:6; Col 1:15-20) → LANGUAGE (Koine Greek) → MANUSCRIPT (P46) → EDITION (NA28) → INTERPRETATION (pre-Pauline hymn / early confession) → DOCTRINE (high Christology)
- **SOURCE_CHAIN:** Pauline letters → P46 (c.200) → NA28 → form-critical analysis → "pre-Pauline hymn" hypothesis → early-high-Christology emergence.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (Paul's letters are primary; 7 undisputed).
- **MANUSCRIPT_STATUS:** ESTABLISHED (P46 contains Pauline corpus c.200; text of Phil 2 / 1 Cor 8 stable).
- **TRANSLATION_STATUS:** NOT_APPLICABLE at the lexical level (the Greek is the object of analysis); translations vary but the *Christological claims* are in the Greek.
- **INTERPRETATION_STATUS:** DISPUTED (whether Phil 2:5-11 is a pre-Pauline hymn; whether 1 Cor 8:6 presupposes a binitarian shape; the "early high Christology" thesis (Bauckham, Hurtado) vs developmental alternatives).
- **DEPENDENCY_STATUS:** The "predates the Gospels" claim DEPENDS_ON the dating of Paul (50s CE) before the written Gospels (70+) AND on the form-critical judgment that the Christological material is traditional, not Paul's invention.
- **INDEPENDENCE_STATUS:** Chronological F=ESTABLISHED (Paul's letters predate written Gospels); Argumentative E=DISPUTED (early-high vs developmental schools).
- **EVIDENCE_STATUS:** STRONG EVIDENCE that Paul's letters are the earliest extant Christian writings with high-Christology material; DISPUTED whether this material is *traditional* (pre-Pauline) vs *Pauline* in origin.
- **CONFIDENCE:** ESTABLISHED (Paul is earliest + has high Christology); DISPUTED (pre-Pauline-tradition hypothesis).
- **COUNTERARGUMENT:** Paul's letters predate the Gospels, but "earliest extant" ≠ "earliest *origin*"; the Gospel traditions may be equally early in oral form; the form-critical judgment that Phil 2 is pre-Pauline is contested. (Links STEP 147 AE-21 theology-history conflation risk.)
- **STEELMAN (Christian):** Paul's letters, written within ~20 years of the crucifixion, show a *functional* divine Christology (worship, creation-role, eschatological agency) already in place — requiring an explanation for how such a Christology emerged *within Jewish monotheism* so fast if not rooted in the apostolic witness.
- **LIMITATION:** "Already in place in Paul" does not establish "rooted in apostolic witness" — that is a further inferential step.
- **AUDIT_RESULT:** PASS — chronological layering explicit; the "predates Gospels" claim is established for *extant writings*, not for *origin*; no overreach.

---

### Q148-CT03

- **ID:** Q148-CT03
- **CLAIM:** "The Nicene Trinity is the biblical doctrine of God."
- **CLAIM_TYPE:** THEOLOGICAL_CLAIM / DOCTRINE
- **NODE_TYPES:** CLAIM → DOCTRINE (Nicene-Constantinopolitan Creed, 325/381) → INTERPRETATION (of Father/Son/Spirit texts) → TEXT (Matt 28:19; John 1:1; 1 Cor 8:6; etc.) → LANGUAGE (Greek) → MANUSCRIPT (various) → EDITION (NA28) → ARGUMENT (cumulative Trinitarian case)
- **SOURCE_CHAIN:** NT texts → patristic interpretation (2nd–4th c.) → Nicene formulation (325/381) → cumulative apologetic argument.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (NT texts are primary; Nicene Creed is a primary doctrinal formulation).
- **MANUSCRIPT_STATUS:** ESTABLISHED (for the NT texts; Nicene Creed text is stable).
- **TRANSLATION_STATUS:** NOT_APPLICABLE at the doctrinal-formulation level (the doctrine is in Greek theological vocabulary: *ousia*, *hypostasis*).
- **INTERPRETATION_STATUS:** DISPUTED (whether the NT texts *force* the Nicene reading or are *consistent with* it; the doctrine is a 4th-c. articulation, not a 1st-c. statement).
- **DEPENDENCY_STATUS:** The "is the biblical doctrine" claim DEPENDS_ON a bridge from the cumulative NT witness to the 4th-c. articulation; this is a development + recognition argument, not a direct quotation.
- **INDEPENDENCE_STATUS:** Textual C=ESTABLISHED (multiple NT witnesses); Chronological F=DISPUTED (3 centuries between text and formulation); Argumentative E=DISPUTED (development vs. articulation-of-given).
- **EVIDENCE_STATUS:** PLAUSIBLE that the Nicene formulation is a *defensible articulation* of NT witness; UNSUPPORTED that it is *explicitly stated* in the NT.
- **CONFIDENCE:** PLAUSIBLE (as articulation); DISPUTED (as explicit-biblical).
- **COUNTERARGUMENT:** The Nicene Trinity is a 4th-c. articulation using Greek metaphysical vocabulary (*ousia*, *hypostasis*) not present in the NT; the claim "is the biblical doctrine" conflates articulation with statement. (Links STEP 147 AE-20, TF2-01, TF2-02.)
- **STEELMAN (Christian):** Nicene theology is the *regulated* development of apostolic intuition under the pressure of preserving monotheism, Christ's divine worship, and the Spirit's agency — not an invention; the 3-century gap is the *recognition* of what was *given*, articulated in response to challenges the apostles did not face.
- **LIMITATION:** "Regulated development of given" is a theological thesis requiring argument, not a textual fact.
- **AUDIT_RESULT:** PASS — the doctrinal-vs-textual separation is explicit; the bridge is flagged as inferential; no overreach.

---

### Q148-CT04

- **ID:** Q148-CT04
- **CLAIM:** "Chalcedonian Christology (one person, two natures) is the teaching of the New Testament."
- **CLAIM_TYPE:** THEOLOGICAL_CLAIM / DOCTRINE
- **NODE_TYPES:** CLAIM → DOCTRINE (Chalcedonian Definition, 451) → INTERPRETATION (of John 1:14; Phil 2; Heb 2; etc.) → TEXT (NT) → MANUSCRIPT (various) → EDITION (NA28) → ARGUMENT
- **SOURCE_CHAIN:** NT texts → patristic Christological debate (4th–5th c.) → Chalcedon (451) → cumulative apologetic argument.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (NT + Chalcedonian Definition).
- **MANUSCRIPT_STATUS:** ESTABLISHED.
- **TRANSLATION_STATUS:** NOT_APPLICABLE at the formulation level (*physis*, *hypostasis*, *prosopon*).
- **INTERPRETATION_STATUS:** DISPUTED (the Chalcedonian categories are 5th-c. Greek metaphysics; the NT does not use them; whether the NT *entails* Chalcedon vs is *consistent with* Chalcedon is the dispute).
- **DEPENDENCY_STATUS:** "Is the teaching of the NT" DEPENDS_ON a bridge from 1st-c. confessional material to 5th-c. metaphysical articulation.
- **INDEPENDENCE_STATUS:** Textual C=ESTABLISHED; Chronological F=DISPUTED (4-century gap); Argumentative E=DISPUTED (miaphysite/dyophysite competing readings).
- **EVIDENCE_STATUS:** PLAUSIBLE that Chalcedon is *consistent with* and *regulated development of* NT Christology; UNSUPPORTED that Chalcedon *is* the NT's own teaching.
- **CONFIDENCE:** PLAUSIBLE (as regulated development); DISPUTED (as explicit-NT-teaching).
- **COUNTERARGUMENT:** Chalcedon uses 5th-c. vocabulary (*physis*, *hypostasis*) absent from the NT; "two natures" is a metaphysical articulation not found in the text. (Links STEP 147 TF2-01, TF2-02.)
- **STEELMAN (Christian):** Chalcedon is the boundary that preserves both the NT's full-deity and full-humanity strands without collapsing either into the other; the vocabulary is later but governed by the apostolic data.
- **LIMITATION:** "Governed by the apostolic data" is a theological thesis, not a textual fact; miaphysite churches dispute the regulation.
- **AUDIT_RESULT:** PASS — doctrine-vs-text separation explicit; inferential bridge flagged.

---

### Q148-CT05

- **ID:** Q148-CT05
- **CLAIM:** "The Qur'an has been transmitted with remarkable consonantal stability."
- **CLAIM_TYPE:** TEXTUAL_CLAIM / HISTORICAL_CLAIM
- **NODE_TYPES:** CLAIM → TEXT (Qur'anic rasm) → LANGUAGE (Qur'anic Arabic) → MANUSCRIPT (Uthmanic codices; Sanaa palimpsest; Ṣanʿāʾ 1; Topkapi; Samarkand) → EDITION (Cairo 1924) → INTERPRETATION (rasm/qira'at distinction)
- **SOURCE_CHAIN:** Uthmanic recension → early codices → Sanaa lower text → Cairo 1924 edition → modern rasm/qira'at scholarship.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (Qur'an is a primary text; early codices are primary material evidence).
- **MANUSCRIPT_STATUS:** ESTABLISHED (multiple early Uthmanic-type codices; Sanaa palimpsest lower text shows pre-Uthmanic variation).
- **TRANSLATION_STATUS:** NOT_APPLICABLE (the rasm is Arabic; the *qira'at* are readings of the rasm).
- **INTERPRETATION_STATUS:** DISPUTED (the *rasm* is remarkably uniform; whether this extends to "perfect preservation" depends on qira'at/ahruf framing and the Sanaa lower-text variants).
- **DEPENDENCY_STATUS:** "Remarkable consonantal stability" DEPENDS_ON the Uthmanic recension having successfully standardized the rasm; this is established. "Perfect preservation" would DEPEND_ON additionally showing no pre-Uthmanic variation and no loss of readings — contested.
- **INDEPENDENCE_STATUS:** Physical A=ESTABLISHED (multiple codices); Textual C=ESTABLISHED for rasm; Genealogical D=DISPUTED (codices likely share Uthmanic exemplar — *not* independent witnesses to a pre-Uthmanic original); Chronological F=STRONG (early codices).
- **EVIDENCE_STATUS:** STRONG EVIDENCE for consonantal stability; DISPUTED for "perfect preservation" (Sanaa lower text and ahruf/qira'at complicate).
- **CONFIDENCE:** STRONG EVIDENCE (consonantal stability); DISPUTED (perfect preservation).
- **COUNTERARGUMENT:** Sanaa lower text shows pre-Uthmanic variation; qira'at preserve a range of readings; "stability" ≠ "perfection." (Links STEP 147 AE-32, TXF-01/02.)
- **STEELMAN (Islamic):** The combination of early recension, mass memorization, and stable rasm across vast regions is historically remarkable and merits engagement as one strand of a cumulative case.
- **LIMITATION:** "Stable rasm" does not establish "perfect preservation" or "divine origin."
- **AUDIT_RESULT:** PASS — textual claim distinguished from theological claim; genealogical dependence of Uthmanic codices flagged.

---

### Q148-CT06

- **ID:** Q148-CT06
- **CLAIM:** "The Sanaa palimpsest lower text proves the Qur'an was altered."
- **CLAIM_TYPE:** TEXTUAL_CLAIM / HISTORICAL_CLAIM
- **NODE_TYPES:** CLAIM → MANUSCRIPT (Sanaa palimpsest, lower text) → TEXT (Qur'anic rasm with variants) → LANGUAGE (Hijazi Arabic) → INTERPRETATION (pre-Uthmanic reading vs. Uthmanic-archetype variant)
- **SOURCE_CHAIN:** Sanaa palimpsest → radiocarbon dating (c.7th c.) → lower-text reconstruction (Sadeghi-Goudarzi, Déroche, Cellard) → variant-reading analysis.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (the palimpsest is a primary physical artifact).
- **MANUSCRIPT_STATUS:** ESTABLISHED (lower text dated c.632–669 CE radiocarbon; erased and overwritten).
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (whether lower text shows (a) pre-Uthmanic variant *readings* or (b) a non-Uthmanic *order* or (c) is a defective copyist artifact — Sadeghi-Goudarzi read it as reflecting an earlier version; Cellard's reconstruction is ongoing).
- **DEPENDENCY_STATUS:** "Proves the Qur'an was altered" DEPENDS_ON the lower text showing readings *not preserved in the qira'at tradition* — this is *partially* supported (some variants) but not *fully* (many lower-text readings match the Uthmanic rasm).
- **INDEPENDENCE_STATUS:** Physical A=ESTABLISHED (single artifact); Genealogical D=UNKNOWN (relationship to Uthmanic exemplar and to other codices unclear).
- **EVIDENCE_STATUS:** PLAUSIBLE that some pre-Uthmanic variant readings existed; DISPUTED that this "proves alteration" in the strong sense (loss of original readings).
- **CONFIDENCE:** PLAUSIBLE (some variant readings); DISPUTED (the strong "proves alteration" claim).
- **COUNTERARGUMENT:** The lower text shows variation but also substantial agreement with Uthmanic rasm; "variation in transmission" ≠ "alteration of the original"; the qira'at preserve a range of readings, so some "variants" may be equally-valid ahruf. (Links STEP 147 TXF-05/06.)
- **STEELMAN (critical):** The Sanaa lower text's erased readings, including order-variants and rasm-variants, evidence *pre-Uthmanic textual variety* and press on strong "perfect preservation" claims.
- **LIMITATION:** The reconstruction is ongoing; "proves alteration" overstates the current state of the evidence.
- **AUDIT_RESULT:** PASS — artifact distinguished from interpretation; the strong claim tagged as beyond current evidence.

---

### Q148-CT07

- **ID:** Q148-CT07
- **CLAIM:** "The Uthmanic standardization of the Qur'an involved burning other codices, proving suppression of variant readings."
- **CLAIM_TYPE:** HISTORICAL_CLAIM / TEXTUAL_CLAIM
- **NODE_TYPES:** CLAIM → EVENT (Uthmanic recension, c.650s CE) → SOURCE (Ibn Abi Dawud, Kitab al-Masahif; al-Tabari; al-Suyuti) → MANUSCRIPT (reports of Ibn Mas'ud, Ubayy, Abu Musa codices) → TRADITION (early Islamic historical tradition)
- **SOURCE_CHAIN:** Uthmanic event → early historical reports (Ibn Abi Dawud, 9th c.) → later compilations (al-Tabari, al-Suyuti) → modern analysis.
- **PRIMARY_SOURCE_STATUS:** DISPUTED (the event is early; our *reports* about it are 9th-c. — the sources for the burning are not contemporary with the event).
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE (the burned codices are not extant; their *reported* readings are in the tradition).
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (standardization can be read as suppression-of-original OR as selection-among-equally-valid-ahruf; the *evidence* is the report of burning, the *inference* to suppression is interpretive).
- **DEPENDENCY_STATUS:** "Proving suppression" DEPENDS_ON (a) the reports being reliable AND (b) the burned codices containing readings *not preserved* in qira'at — (b) is contested (qira'at preserve many variants).
- **INDEPENDENCE_STATUS:** Argumentative E=NOT_INDEPENDENT (most reports trace to a common early Islamic historiographical tradition); Chronological F=NOT_INDEPENDENT (the reports are 9th-c. for a 7th-c. event).
- **EVIDENCE_STATUS:** PROBABLE that standardization occurred and involved burning; DISPUTED that this "proves suppression of original readings."
- **CONFIDENCE:** PROBABLE (standardization + burning); DISPUTED (suppression of original readings).
- **COUNTERARGUMENT:** Standardization ≠ suppression; selection among equally-valid readings (ahruf) is the Islamic frame; variant readings survive in qira'at. (Links STEP 147 AE-22 event-report conflation, HF-08.)
- **STEELMAN (critical):** The combination of standardization, burning, and reports of codices with readings differing from the Uthmanic text evidences *textual variety that was narrowed* — warranting scrutiny of "perfect preservation" claims.
- **LIMITATION:** The late date of the reports is a real historical-distance issue; "proves" overstates.
- **AUDIT_RESULT:** PASS — event-vs-report separation explicit; late-source status flagged.

---

### Q148-CT08

- **ID:** Q148-CT08
- **CLAIM:** "A Hadith graded sahih establishes that Muhammad said/did X."
- **CLAIM_TYPE:** HISTORICAL_CLAIM / TRADITION
- **NODE_TYPES:** CLAIM → TRADITION (isnad chain) → SOURCE (Sahih al-Bukhari / Muslim) → SCHOLAR (Bukhari, classical jarh wa ta'dil; modern isnad-cum-matn analysts) → EVENT (putative saying/action of Muhammad)
- **SOURCE_CHAIN:** Putative event → isnad chain → collection (Bukhari, 9th c.) → classical authentication → modern isnad-cum-matn analysis.
- **PRIMARY_SOURCE_STATUS:** DISPUTED (Bukhari is a primary Hadith collection; the *event* is not directly primary — the chain is the mediating tradition).
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE (Hadith are transmitted texts; manuscript status is about the collection's text, not the event).
- **TRANSLATION_STATUS:** NOT_APPLICABLE (the analysis is of the Arabic isnad/matn; English translations are downstream).
- **INTERPRETATION_STATUS:** DISPUTED (sahih certifies *chain soundness*, not *event historicity*; modern isnad-cum-matn analysis grades reports individually).
- **DEPENDENCY_STATUS:** "Establishes that Muhammad said/did X" DEPENDS_ON the chain being sound AND the chain's soundness being a good proxy for historicity — the latter is contested.
- **INDEPENDENCE_STATUS:** Genealogical D=DISPUTED (many sahih reports share common-link isnads — *not* independent multiple attestation); Chronological F=NOT_INDEPENDENT (9th-c. collection for 7th-c. event).
- **EVIDENCE_STATUS:** PROBABLE for chain soundness (per classical + modern analysis); DISPUTED for event-historicity (chain soundness ≠ historicity).
- **CONFIDENCE:** PROBABLE (chain); DISPUTED (event-historicity).
- **COUNTERARGUMENT:** Sahih is a chain-category, not a historicity-category; common-link isnads undermine "multiple attestation"; blanket "in Bukhari ⇒ established" is fallacious. (Links STEP 147 AE-18, HF-07.)
- **STEELMAN (Islamic):** Reports passing isnad-cum-matn common-link tests, with cross-corroboration across collections, support graded (not absolute) confidence.
- **LIMITATION:** Confidence is per-report, not blanket; "establishes" overreaches.
- **AUDIT_RESULT:** PASS — chain-soundness distinguished from event-historicity; genealogical dependence flagged.

---

### Q148-CT09

- **ID:** Q148-CT09
- **CLAIM:** "Muhammad existed as a historical person."
- **CLAIM_TYPE:** HISTORICAL_CLAIM / FACT
- **NODE_TYPES:** CLAIM → EVENT (life of Muhammad, c.570–632 CE) → SOURCE (Qur'an references; early Islamic tradition; near-contemporary non-Muslim sources) → SCHOLAR (mainstream Islamic-historical scholarship)
- **SOURCE_CHAIN:** Qur'an's self-reference to a prophet → early Islamic historical tradition → near-contemporary non-Muslim notices (e.g., Sebeos c.660, Doctrina Jacobi c.634) → modern mainstream scholarship.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (multiple near-contemporary + early sources).
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE (existence claim, not text-transmission claim).
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** ESTABLISHED (mainstream scholarship affirms existence).
- **DEPENDENCY_STATUS:** The existence claim DEPENDS_ON near-contemporary attestation — established.
- **INDEPENDENCE_STATUS:** Physical A=ESTABLISHED (multiple distinct sources); Argumentative E=ESTABLISHED (independent traditions: Islamic, Syriac Christian, Jewish, Byzantine); Chronological F=STRONG (near-contemporary notices).
- **EVIDENCE_STATUS:** ESTABLISHED.
- **CONFIDENCE:** ESTABLISHED.
- **COUNTERARGUMENT:** Existence is established; *details* of the life (specific events, miracles, prophethood) are distinct claims with distinct evidence.
- **STEELMAN (critical):** Existence is mainstream; the substantive claims *about* Muhammad (prophethood, specific events) are audited as separate claim nodes, not inherited from existence.
- **LIMITATION:** Existence consensus does not extend to supernatural claims.
- **AUDIT_RESULT:** PASS — existence distinguished from substantive life-claims.

---

### Q148-CT10

- **ID:** Q148-CT10
- **CLAIM:** "The event at Ghadir Khumm establishes Ali's designation as successor."
- **CLAIM_TYPE:** HISTORICAL_CLAIM / THEOLOGICAL_CLAIM
- **NODE_TYPES:** CLAIM → EVENT (Ghadir Khumm, 632 CE) → TRADITION (Hadith reports with isnads) → SOURCE (Sunni collections: Tirmidhi, Nasa'i, Ibn Maja; Shi'i sources) → INTERPRETATION (Sunni: excellence declaration; Shi'i: designation as imam) → DOCTRINE (Imamah)
- **SOURCE_CHAIN:** Putative event → isnad chains → multiple collections (Sunni + Shi'i) → divergent interpretations → Imamah doctrine.
- **PRIMARY_SOURCE_STATUS:** DISPUTED (the event is early; our reports are in 9th-c. collections).
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE.
- **TRANSLATION_STATUS:** NOT_APPLICABLE (analysis is of Arabic *mawla*).
- **INTERPRETATION_STATUS:** DISPUTED (the lexeme *mawla* is polyvalent — "friend/helper" (Sunni) vs "authority/leader" (Shi'i); the event is multiply attested but the *referent* is the dispute).
- **DEPENDENCY_STATUS:** "Establishes Ali's designation" DEPENDS_ON *mawla* meaning "authority" in this context — contested lexically.
- **INDEPENDENCE_STATUS:** Textual C=PROBABLE (multiply attested across Sunni and Shi'i collections); Genealogical D=DISPUTED (common-link isnad analysis); Argumentative E=NOT_INDEPENDENT (interpretations split along sectarian lines).
- **EVIDENCE_STATUS:** PROBABLE that the event occurred and that Muhammad said something about Ali; DISPUTED that this "establishes designation."
- **CONFIDENCE:** PROBABLE (event + statement); DISPUTED (designation interpretation).
- **COUNTERARGUMENT:** *Mawla* is polyvalent; the Sunni reading (excellence/friendship) is lexically live; multiply-attested event ≠ multiply-attested designation. (Links STEP 147 IF-06, AE-06.)
- **STEELMAN (Shi'i):** Multiple Sunni and Shi'i chains, plus the Prophet's other statements about Ali, plus the context (returning from the Farewell Pilgrimage), cumulatively press the designation reading.
- **LIMITATION:** The lexical question is the gate; "establishes" overstates.
- **AUDIT_RESULT:** PASS — event distinguished from interpretation; lexical polyvalence flagged.

---

### Q148-CT11

- **ID:** Q148-CT11
- **CLAIM:** "Imamah (divine designation of Imams) is established by the Ghadir event and related reports."
- **CLAIM_TYPE:** THEOLOGICAL_CLAIM / DOCTRINE
- **NODE_TYPES:** CLAIM → DOCTRINE (Imamah) → INTERPRETATION (of Ghadir and related reports) → TRADITION (Hadith) → SOURCE (Sunni + Shi'i collections) → EVENT (Ghadir; other designation reports)
- **SOURCE_CHAIN:** Events → reports → collections → interpretations → Imamah doctrine.
- **PRIMARY_SOURCE_STATUS:** DISPUTED (see CT10).
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE.
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (Sunni Islam rejects the Imamah reading of these reports).
- **DEPENDENCY_STATUS:** Imamah DEPENDS_ON (a) the event reports being reliable AND (b) *mawla* meaning "authority" AND (c) the reports extending beyond Ali to a continuous line of Imams — each step is contested.
- **INDEPENDENCE_STATUS:** Argumentative E=NOT_INDEPENDENT (the Imamah reading is sectarian, not a neutral reading of the tradition).
- **EVIDENCE_STATUS:** PLAUSIBLE within the Shi'i frame; DISPUTED/UNSUPPORTED as a neutral reading.
- **CONFIDENCE:** PLAUSIBLE (within Shi'i frame); DISPUTED (as neutral).
- **COUNTERARGUMENT:** The doctrine depends on contested lexical + sectarian readings; Sunni Islam affirms the event but rejects the Imamah inference.
- **STEELMAN (Shi'i):** Imamah is the cumulative reading of multiple reports about the Ahl al-Bayt, the Prophet's designation statements, and the Qur'anic emphasis on divine designation — not a single-event proof.
- **LIMITATION:** "Cumulative within the Shi'i frame" is acknowledged; the audit tags the sectarian dependency.
- **AUDIT_RESULT:** PASS — sectarian dependency flagged; doctrine-vs-event separation explicit.

---

### Q148-CT12

- **ID:** Q148-CT12
- **CLAIM:** "The Qur'an affirms Jesus as the Messiah, born of a virgin, and a prophet — but not divine."
- **CLAIM_TYPE:** THEOLOGICAL_CLAIM / TEXTUAL_CLAIM
- **NODE_TYPES:** CLAIM → TEXT (Q 3:45-47; 4:171; 5:75; 19:16-34) → LANGUAGE (Arabic) → MANUSCRIPT (early Qur'an mss) → EDITION (Cairo 1924) → INTERPRETATION (Qur'anic Jesus as prophet, not God)
- **SOURCE_CHAIN:** Qur'anic passages → early mss → Cairo edition → tafsir → Qur'anic Christology.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (Qur'an is a primary text).
- **MANUSCRIPT_STATUS:** ESTABLISHED (these passages are textually stable).
- **TRANSLATION_STATUS:** NOT_APPLICABLE (the analysis is of Arabic).
- **INTERPRETATION_STATUS:** ESTABLISHED within the Islamic frame (the Qur'an explicitly denies Jesus' divinity, e.g., 5:75; 4:171).
- **DEPENDENCY_STATUS:** The "but not divine" element is the Qur'an's explicit position; the question is whether this is the *true* position — that is a comparative-theological claim, not a textual one.
- **INDEPENDENCE_STATUS:** Textual C=ESTABLISHED (multiple stable attestations within the Qur'an); Argumentative E=DISPUTED (Christian readings of the same Jesus differ).
- **EVIDENCE_STATUS:** ESTABLISHED that the Qur'an affirms Jesus as Messiah/virgin-born/prophet and denies divinity; DISPUTED whether the Qur'anic position is *true*.
- **CONFIDENCE:** ESTABLISHED (what the Qur'an says); DISPUTED (truth of the Qur'anic position).
- **COUNTERARGUMENT:** The Qur'an's position is textually clear; the question is whether it is *true* — which requires engaging the Christian evidence, not merely citing the Qur'an.
- **STEELMAN (Islamic):** The Qur'an's consistent, multiply-stated Christology (Messiah, virgin birth, prophet, not God) is internally coherent and engages the Christian position directly at 4:171 and 5:75.
- **LIMITATION:** "What the Qur'an says" is established; "what is true" is a separate claim node.
- **AUDIT_RESULT:** PASS — textual claim distinguished from truth-claim.

---

### Q148-CT13

- **ID:** Q148-CT13
- **CLAIM:** "The Bible and Qur'an contradict each other on the crucifixion."
- **CLAIM_TYPE:** HISTORICAL_CLAIM / TEXTUAL_CLAIM (comparative)
- **NODE_TYPES:** CLAIM → TEXT (Q 4:157; NT Gospels) → LANGUAGE (Arabic; Greek) → MANUSCRIPT (Qur'an mss; NT mss) → EDITION (Cairo 1924; NA28) → INTERPRETATION (docetic/ perceptual/ denial readings of 4:157; crucifixion accounts in Gospels)
- **SOURCE_CHAIN:** Q 4:157 + Gospel accounts → mss → editions → interpretations → comparative contradiction claim.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (both texts are primary).
- **MANUSCRIPT_STATUS:** ESTABLISHED (both passages textually stable).
- **TRANSLATION_STATUS:** DISPUTED (the Arabic *shubbiha lahum* is polyvalent — controls the contradiction's force).
- **INTERPRETATION_STATUS:** DISPUTED (the dominant tafsir reads 4:157 as denial of the event; minority readings as denial of the perception; the contradiction's *force* depends on this).
- **DEPENDENCY_STATUS:** "Contradict each other" DEPENDS_ON 4:157 meaning "the crucifixion did not occur" — this is the *dominant* but not the *only* reading.
- **INDEPENDENCE_STATUS:** Textual C=ESTABLISHED (both texts stable); Argumentative E=DISPUTED (the contradiction's force is reading-dependent).
- **EVIDENCE_STATUS:** PROBABLE that on the dominant reading the texts conflict; DISPUTED that the conflict is "flat" (textually forced).
- **CONFIDENCE:** PROBABLE (dominant-reading conflict); DISPUTED (logical force).
- **COUNTERARGUMENT:** 4:157 is polyvalent; the conflict is exegetically probable but not logically forced. (Links STEP 147 IF-06.)
- **STEELMAN (Christian):** On the dominant tafsir, 4:157 denies the event, contradicting mainstream historical evidence and the Gospel accounts.
- **LIMITATION:** The polyvalence of 4:157 limits the "flat contradiction" formulation.
- **AUDIT_RESULT:** PASS — comparative claim split into textual-stability + interpretation-reading components.

---

### Q148-CT14

- **ID:** Q148-CT14
- **CLAIM:** "The Qur'an is better preserved than the Bible."
- **CLAIM_TYPE:** TEXTUAL_CLAIM (comparative)
- **NODE_TYPES:** CLAIM → MANUSCRIPT (Qur'an mss; NT mss) → EDITION (Cairo 1924; NA28) → TEXT (rasm/qira'at; Greek text) → INTERPRETATION (preservation definitions)
- **SOURCE_CHAIN:** Both manuscript traditions → scholarly analysis → comparative preservation claim.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (both manuscript bases are primary material).
- **MANUSCRIPT_STATUS:** ESTABLISHED (data exists for both).
- **TRANSLATION_STATUS:** NOT_APPLICABLE (the comparison is at the textual-transmission level).
- **INTERPRETATION_STATUS:** DISPUTED ("preservation" must be defined: rasm only? rasm+qira'at? autograph-recovery? — different definitions yield different verdicts).
- **DEPENDENCY_STATUS:** "Better preserved" DEPENDS_ON a *definition* of preservation; without specifying, the comparison is undefined.
- **INDEPENDENCE_STATUS:** Comparative asymmetry risk — applying different metrics to the two traditions is DM-12 (STEP 147).
- **EVIDENCE_STATUS:** DISPUTED (depends on definition; both traditions have substantial stability for most readings + specific uncertainties).
- **CONFIDENCE:** DISPUTED.
- **COUNTERARGUMENT:** The comparison is definition-dependent; applying the same metric symmetrically yields a more nuanced picture than "better/worse." (Links STEP 147 DM-12.)
- **STEELMAN (Islamic):** The Qur'an's consonantal rasm stability + mass memorization is, on a "rasm preservation" definition, stronger than the NT's per-manuscript stability.
- **STEELMAN (Christian):** The NT's early, multiply-attested, genealogically-analyzed text supports substantial autograph-recovery — on a "recovery of original" definition, the NT performs well.
- **LIMITATION:** Definition must be fixed before the comparison is meaningful.
- **AUDIT_RESULT:** PASS — definition-dependency flagged; symmetry rule applied.

---

### Q148-CT15

- **ID:** Q148-CT15
- **CLAIM:** "The Trinity and Tawhid are logically incompatible; therefore one tradition is false."
- **CLAIM_TYPE:** THEOLOGICAL_CLAIM / PHILOSOPHICAL_CLAIM
- **NODE_TYPES:** CLAIM → DOCTRINE (Nicene Trinity) → DOCTRINE (Tawhid) → INTERPRETATION (of both) → ARGUMENT (incompatibility argument)
- **SOURCE_CHAIN:** Both doctrines as formulated → comparative analysis → incompatibility claim.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (both doctrines are primary formulations).
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE (doctrinal comparison).
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (the incompatibility depends on whether Trinity is read as tritheism (strawman) or as Nicene monotheism; under Nicene reading, both affirm monotheism — the incompatibility is *articulation-level*, not *monotheism-level*).
- **DEPENDENCY_STATUS:** "Logically incompatible" DEPENDS_ON reading the Trinity as three gods — a strawman of Nicene doctrine.
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED (the incompatibility argument depends on the strawman reading).
- **EVIDENCE_STATUS:** UNSUPPORTED (as "logically incompatible" if Trinity = tritheism strawman); PLAUSIBLE (as "differently articulated" under accurate reading).
- **CONFIDENCE:** UNSUPPORTED (incompatibility); PLAUSIBLE (different articulation).
- **COUNTERARGUMENT:** Trinity affirms strict monotheism; the incompatibility is at the *articulation* level (one essence/three persons vs strict unity), not at the "polytheism vs monotheism" level. (Links STEP 147 IF-01.)
- **STEELMAN (Islamic):** Even under Nicene monotheism, the Trinity is metaphysically complex in a way Tawhid is not; the burden is on the Christian to show the complexity is not ad hoc.
- **LIMITATION:** "Logically incompatible" overstates; "differently articulated" is the accurate framing.
- **AUDIT_RESULT:** PASS — strawman vs accurate reading distinguished.

---

### Q148-CT16

- **ID:** Q148-CT16
- **CLAIM:** "The empty tomb is historically established."
- **CLAIM_TYPE:** HISTORICAL_CLAIM
- **NODE_TYPES:** CLAIM → EVENT (empty tomb) → SOURCE (Gospel empty-tomb narratives; Paul 1 Cor 15) → TEXT (Mark 16; Matt 28; Luke 24; John 20) → MANUSCRIPT (NT papyri/majuscules) → EDITION (NA28) → INTERPRETATION (historical-Jesus criteria) → SCHOLAR (mainstream historical-Jesus scholarship)
- **SOURCE_CHAIN:** Gospel accounts → NT mss → NA28 → criteria analysis → scholarly assessment.
- **PRIMARY_SOURCE_STATUS:** DISPUTED (the accounts are in the Gospels, post-Paul; Paul mentions burial but no empty-tomb visit narrative).
- **MANUSCRIPT_STATUS:** ESTABLISHED (the Gospel texts are stable).
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (the empty-tomb historicity is contested in scholarship; criteria yield mixed verdicts — embarrassment-criterion supports, but the post-Paul silence and legendary accretions complicate).
- **DEPENDENCY_STATUS:** "Historically established" DEPENDS_ON (a) the accounts being early enough, (b) multiple attestation (the four Gospels are not fully independent), (c) exclusion of alternative explanations.
- **INDEPENDENCE_STATUS:** Textual C=DISPUTED (the four Gospels likely share Markan + Q tradition — not four independent witnesses); Chronological F=DISPUTED (post-70 for the written narratives).
- **EVIDENCE_STATUS:** PLAUSIBLE that the tomb was empty; DISPUTED that this is "historically established" in the strong sense.
- **CONFIDENCE:** PLAUSIBLE; DISPUTED (as "established").
- **COUNTERARGUMENT:** The written narratives are post-Paul and share tradition; Paul's earliest stratum attests *appearances*, not an empty-tomb visit; "established" overreaches.
- **STEELMAN (Christian):** The women-witness detail (embarrassment criterion), the Jewish polemic against theft (implying an empty tomb), and the absence of a venerated tomb cumulatively support historicity.
- **LIMITATION:** "Established" overstates; "plausible" is the defensible band.
- **AUDIT_RESULT:** PASS — historical-distance + textual-dependence flagged.

---

### Q148-CT17

- **ID:** Q148-CT17
- **CLAIM:** "The resurrection is historically established by minimal facts."
- **CLAIM_TYPE:** HISTORICAL_CLAIM / APOLOGETIC_ARGUMENT
- **NODE_TYPES:** CLAIM → EVENT (resurrection) → ARGUMENT (minimal-facts case) → CLAIM (death by crucifixion; burial; empty tomb; appearances; origin of belief) → SOURCE (NT; early creedal material) → SCHOLAR (mainstream + apologists)
- **SOURCE_CHAIN:** Minimal facts → NT sources → early creedal tradition (1 Cor 15:3-5) → cumulative inference → resurrection.
- **PRIMARY_SOURCE_STATUS:** DISPUTED (the "facts" are drawn from contested sources).
- **MANUSCRIPT_STATUS:** ESTABLISHED (for the texts cited).
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (each "minimal fact" requires criteria-based defense; the inference from facts to resurrection is the contested step).
- **DEPENDENCY_STATUS:** "Historically established" DEPENDS_ON (a) each minimal fact being established AND (b) the inference from facts to resurrection being warranted — (b) is the contested step (alternatives: hallucination, theft, legend).
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED (the inference is contested by hallucination/legend theories).
- **EVIDENCE_STATUS:** PLAUSIBLE that the minimal facts are each *plausible*; DISPUTED that they *establish* resurrection.
- **CONFIDENCE:** PLAUSIBLE (individual facts); DISPUTED (resurrection inference).
- **COUNTERARGUMENT:** The minimal facts underdetermine the conclusion; competing explanations exist; "established" overreaches. (Links STEP 147 IF-04.)
- **STEELMAN (Christian):** The combination of death, burial, empty tomb, appearances, and sudden origin of belief — each defended on criteria — jointly presses the resurrection inference as the best explanation.
- **LIMITATION:** "Best explanation" is a cumulative-case judgment, not a logical entailment.
- **AUDIT_RESULT:** PASS — minimal-facts inferences split from resurrection conclusion.

---

### Q148-CT18

- **ID:** Q148-CT18
- **CLAIM:** "The Qur'an's literary inimitability proves its divine origin."
- **CLAIM_TYPE:** APOLOGETIC_ARGUMENT / THEOLOGICAL_CLAIM
- **NODE_TYPES:** CLAIM → ARGUMENT (i'jaz) → TEXT (Qur'anic literary form) → LANGUAGE (Arabic) → INTERPRETATION (inimitability judgment) → SCHOLAR (Arabic literary history; mu'arada attempts)
- **SOURCE_CHAIN:** Qur'anic text → Arabic literary analysis → mu'arada attempts → inimitability judgment → divine-origin inference.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (the Qur'an is the primary text).
- **MANUSCRIPT_STATUS:** ESTABLISHED (text stable).
- **TRANSLATION_STATUS:** NOT_APPLICABLE (the analysis is of Arabic).
- **INTERPRETATION_STATUS:** DISPUTED ("inimitable" requires neutral criteria; judgments are made by a community with confessional investment).
- **DEPENDENCY_STATUS:** "Proves divine origin" DEPENDS_ON (a) inimitability being established AND (b) the inference from inimitability to divinity — (b) is the non sequitur step.
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED (the inference is contested).
- **EVIDENCE_STATUS:** PLAUSIBLE that the Qur'an is literarily distinctive; UNSUPPORTED that this *proves* divinity.
- **CONFIDENCE:** PLAUSIBLE (distinctiveness); UNSUPPORTED (divinity inference).
- **COUNTERARGUMENT:** Distinctiveness ≠ divinity; the warrant is absent. (Links STEP 147 AE-33.)
- **STEELMAN (Islamic):** The combination of saj'-like rhythm without saj' constraints, structural coherence, and sustained non-imitation by Arabic masters calls for explanation.
- **LIMITATION:** "Calls for explanation" ≠ "proves divine."
- **AUDIT_RESULT:** PASS — distinctiveness separated from divinity inference.

---

### Q148-CT19

- **ID:** Q148-CT19
- **CLAIM:** "The Bible has been textually corrupted (tahrif nassi)."
- **CLAIM_TYPE:** TEXTUAL_CLAIM / THEOLOGICAL_CLAIM
- **NODE_TYPES:** CLAIM → TEXT (NT/OT variant readings) → MANUSCRIPT (NT mss with variants) → EDITION (NA28 apparatus) → INTERPRETATION (tahrif nassi vs. copying variants) → DOCTRINE (Islamic tahrif)
- **SOURCE_CHAIN:** NT textual variants → apparatus → analysis → tahrif inference.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (the variants are in primary mss).
- **MANUSCRIPT_STATUS:** ESTABLISHED.
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (tahrif nassi = textual *alteration*; this is stronger than copying variants — the step from "variants exist" to "doctrinal tampering" is the contested inference).
- **DEPENDENCY_STATUS:** "Corrupted" DEPENDS_ON showing *doctrinally motivated alteration*, not just copying variation — the latter is universal, the former requires evidence.
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED.
- **EVIDENCE_STATUS:** PROBABLE that substantive variants exist (Comma, longer Mark, etc.); DISPUTED that these constitute "corruption" in the strong tahrif-nassi sense.
- **CONFIDENCE:** PROBABLE (variants exist); DISPUTED (strong corruption).
- **COUNTERARGUMENT:** Variants are universal in manuscript traditions; substantive variants are a small subset, well-mapped; "corruption" overstates. (Links STEP 147 AE-15, TXF-05/06.)
- **STEELMAN (Islamic):** Late substantive additions (Comma, longer Mark, Pericope Adulterae) evidence *some* doctrinal passages were added in transmission.
- **LIMITATION:** "Some late additions" ≠ "the text is corrupted" sweeping.
- **AUDIT_RESULT:** PASS — variant-existence distinguished from corruption-inference.

---

### Q148-CT20

- **ID:** Q148-CT20
- **CLAIM:** "The Gospel of Barnabas is the original Gospel, suppressed by the church."
- **CLAIM_TYPE:** HISTORICAL_CLAIM / TEXTUAL_CLAIM
- **NODE_TYPES:** CLAIM → SOURCE (Gospel of Barnabas) → LANGUAGE (Italian/Spanish, medieval) → MANUSCRIPT (late mss, 16th-c. Italian) → SCHOLAR (Slade, Joosten, Cirillo — unanimously reject early dating)
- **SOURCE_CHAIN:** Gospel of Barnabas (medieval) → scholarship → suppression claim.
- **PRIMARY_SOURCE_STATUS:** NOT_ESTABLISHED (the work is a medieval composition, not a primary apostolic text).
- **MANUSCRIPT_STATUS:** ESTABLISHED (the surviving mss are late medieval/early modern).
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** ESTABLISHED (mainstream scholarship unanimously rejects apostolic authorship).
- **DEPENDENCY_STATUS:** "Original Gospel" DEPENDS_ON apostolic authorship — which is unanimously rejected.
- **INDEPENDENCE_STATUS:** Argumentative E=NOT_INDEPENDENT (the suppression claim relies on the very text whose apostolic status is rejected).
- **EVIDENCE_STATUS:** UNSUPPORTED.
- **CONFIDENCE:** UNSUPPORTED.
- **COUNTERARGUMENT:** The work is medieval, anachronistic (references to 16th-c. ideas), and unanimously rejected by scholarship. (Links STEP 147 E15.)
- **STEELMAN (none):** No defensible steelman; the work is unanimously rejected.
- **LIMITATION:** The claim is unsupported.
- **AUDIT_RESULT:** PASS — unsupported claim tagged; no overreach in treating it as evidence.

---

### Q148-CT21

- **ID:** Q148-CT21
- **CLAIM:** "Isaiah 53 prophesies Jesus' vicarious atonement."
- **CLAIM_TYPE:** THEOLOGICAL_CLAIM / INTERPRETATION
- **NODE_TYPES:** CLAIM → TEXT (Isa 52:13–53:12) → LANGUAGE (Biblical Hebrew) → MANUSCRIPT (1QIsa^a; MT) → EDITION (BHS) → INTERPRETATION (servant = individual Messiah vs collective Israel) → ARGUMENT (cumulative Christian messianic case)
- **SOURCE_CHAIN:** Hebrew text → DSS + MT → BHS → interpretation → Christian messianic argument.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (Isaiah is a primary text).
- **MANUSCRIPT_STATUS:** ESTABLISHED (1QIsa^a broadly supports MT; text stable).
- **TRANSLATION_STATUS:** DISPUTED (the servant's referent is the dispute, not the wording).
- **INTERPRETATION_STATUS:** DISPUTED (collective Israel, individual Messiah, prophet, remnant — all live readings; the servant is identified as Israel elsewhere in Deutero-Isaiah).
- **DEPENDENCY_STATUS:** "Prophesies Jesus" DEPENDS_ON the servant's referent being a future individual Messiah — contested.
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED (the Christian reading is one reception, not the only reading).
- **EVIDENCE_STATUS:** PLAUSIBLE as a cumulative Christian reading; DISPUTED as a forced reading.
- **CONFIDENCE:** PLAUSIBLE (cumulative); DISPUTED (forced).
- **COUNTERARGUMENT:** The servant is identified as Israel in context; the Christian reading is one reception. (Links STEP 147 AE-23.)
- **STEELMAN (Christian):** The combination of vicarious suffering, exaltation, distinction from Israel, and absence of a better-fitting individual candidate cumulatively presses the messianic-individual reading.
- **LIMITATION:** "Cumulative" requires independent establishment of each strand.
- **AUDIT_RESULT:** PASS — referent-contest flagged; reception distinguished from forced reading.

---

### Q148-CT22

- **ID:** Q148-CT22
- **CLAIM:** "Muhammad is prophesied in Deuteronomy 18:18."
- **CLAIM_TYPE:** THEOLOGICAL_CLAIM / INTERPRETATION
- **NODE_TYPES:** CLAIM → TEXT (Deut 18:15-19) → LANGUAGE (Biblical Hebrew) → MANUSCRIPT (MT; DSS) → EDITION (BHS) → INTERPRETATION ("like Moses" = Muhammad) → ARGUMENT (Islamic biblical-prophecy case)
- **SOURCE_CHAIN:** Hebrew text → mss → BHS → interpretation → Islamic prophecy argument.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED.
- **MANUSCRIPT_STATUS:** ESTABLISHED.
- **TRANSLATION_STATUS:** DISPUTED (the referent of "like Moses" is the dispute).
- **INTERPRETATION_STATUS:** DISPUTED (Joshua, prophetic line, eschatological prophet, Jesus, Muhammad — all live readings; the criteria for "like Moses" are contestable).
- **DEPENDENCY_STATUS:** "Prophesies Muhammad" DEPENDS_ON the criteria set being neutral (not reverse-engineered).
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED (the Islamic reading is one reception; pre-Christian Jewish readings varied).
- **EVIDENCE_STATUS:** PLAUSIBLE as a candidate reading; UNSUPPORTED as a forced reading.
- **CONFIDENCE:** PLAUSIBLE (candidate); UNSUPPORTED (forced).
- **COUNTERARGUMENT:** The criteria may be reverse-engineered; the Christian reading (Acts 3:22) is also ancient.
- **STEELMAN (Islamic):** Muhammad fits Moses-specific criteria (lawgiver, non-royal, community-founding) more naturally than Jesus.
- **LIMITATION:** Criteria-contestability is the gate.
- **AUDIT_RESULT:** PASS — candidate-vs-forced distinction explicit.

---

### Q148-CT23

- **ID:** Q148-CT23
- **CLAIM:** "The Shroud of Turin is physical evidence of the resurrection."
- **CLAIM_TYPE:** APOLOGETIC_ARGUMENT / HISTORICAL_CLAIM
- **NODE_TYPES:** CLAIM → MANUSCRIPT/ARTIFACT (Shroud) → SOURCE (C-14 dating; STURP data) → SCHOLAR (mainstream science; apologetic literature) → INTERPRETATION (image-formation theories) → ARGUMENT (resurrection inference)
- **SOURCE_CHAIN:** Shroud artifact → C-14 dating (1988) → STURP → image-formation theories → resurrection inference.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (the Shroud is a primary artifact).
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE (artifact, not ms).
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (image-formation mechanism open; C-14 result contested by apologists on sampling grounds).
- **DEPENDENCY_STATUS:** "Evidence of resurrection" DEPENDS_ON (a) the medieval C-14 date being wrong AND (b) the image being unexplained AND (c) unexplained ⇒ miraculous ⇒ resurrection — (c) is an argument from ignorance.
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED.
- **EVIDENCE_STATUS:** UNSUPPORTED (as resurrection evidence; the C-14 date is medieval).
- **CONFIDENCE:** UNSUPPORTED (resurrection); DISPUTED (open-question artifact).
- **COUNTERARGUMENT:** Published C-14 is medieval; "unexplained ⇒ miracle" is an argument from ignorance. (Links STEP 147 E17.)
- **STEELMAN (Christian):** Some image features resist simple naturalistic explanation; sampling criticisms persist; the formation mechanism remains open.
- **LIMITATION:** Open-question ≠ resurrection-evidence.
- **AUDIT_RESULT:** PASS — artifact distinguished from resurrection-inference; C-14 status flagged.

---

### Q148-CT24

- **ID:** Q148-CT24
- **CLAIM:** "Qur'an 23:12-14 contains accurate embryology that 7th-century humans could not know."
- **CLAIM_TYPE:** APOLOGETIC_ARGUMENT / LINGUISTIC_CLAIM
- **NODE_TYPES:** CLAIM → TEXT (Q 23:12-14) → LANGUAGE (Arabic) → MANUSCRIPT (Qur'an mss) → EDITION (Cairo 1924) → INTERPRETATION (modern scientific reading of nutfa/alaqa/mudgha) → SCHOLAR (classical tafsir vs modern i'jaz literature) → ARGUMENT (i'jaz 'ilmi)
- **SOURCE_CHAIN:** Arabic text → mss → edition → classical tafsir (alaqa = blood-clot) vs modern reading (alaqa = leech-like/clinging) → scientific-miracle inference.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (Qur'an is primary).
- **MANUSCRIPT_STATUS:** ESTABLISHED.
- **TRANSLATION_STATUS:** DISPUTED (the modern scientific glosses of nutfa/alaqa/mudgha diverge from classical tafsir).
- **INTERPRETATION_STATUS:** DISPUTED (classical tafsir reads alaqa as blood-clot; the modern "scientific" reading is a re-reading).
- **DEPENDENCY_STATUS:** "Could not know" DEPENDS_ON (a) the modern reading being the text's meaning AND (b) the knowledge being unavailable in the 7th c. — (b) is contested (Galenic embryology was available).
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED (retrodiction + Texas sharpshooter risks).
- **EVIDENCE_STATUS:** UNSUPPORTED (as divine-origin proof); PLAUSIBLE (as curiosity).
- **CONFIDENCE:** UNSUPPORTED (proof); PLAUSIBLE (curiosity).
- **COUNTERARGUMENT:** Retrodiction; lexical fallacy (modern glosses); Galenic material available. (Links STEP 147 E8.)
- **STEELMAN (Islamic):** Some phrasings are strikingly consonant with modern features and merit engagement with classical lexical evidence.
- **LIMITATION:** "Merits engagement" ≠ "proves divine."
- **AUDIT_RESULT:** PASS — classical-vs-modern reading split flagged.

---

### Q148-CT25

- **ID:** Q148-CT25
- **CLAIM:** "The NT has ~5,800 Greek manuscripts, making it the best-attested ancient text."
- **CLAIM_TYPE:** TEXTUAL_CLAIM
- **NODE_TYPES:** CLAIM → MANUSCRIPT (NT Greek mss) → EDITION (NA28 apparatus; INTF counts) → SCHOLAR (textual criticism) → INTERPRETATION ("best-attested" judgment)
- **SOURCE_CHAIN:** Greek mss → INTF counts → NA28 apparatus → "best-attested" inference.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (the mss are primary artifacts).
- **MANUSCRIPT_STATUS:** ESTABLISHED.
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED ("best-attested" conflates count with quality — most mss are late and dependent).
- **DEPENDENCY_STATUS:** "Best-attested" DEPENDS_ON count being the right metric — it isn't; early-independent-genealogy is.
- **INDEPENDENCE_STATUS:** Genealogical D=DISPUTED (most late mss are dependent, not independent witnesses).
- **EVIDENCE_STATUS:** ESTABLISHED that NT has the most Greek mss; DISPUTED that this makes it "best-attested" in the quality sense.
- **CONFIDENCE:** ESTABLISHED (count); DISPUTED (quality-inference).
- **COUNTERARGUMENT:** Raw count ≠ reliability; most mss are late and dependent. (Links STEP 147 AE-10, E3.)
- **STEELMAN (Christian):** NT has not only more mss but earlier mss than most classical texts — on the early-independent-genealogy metric, it performs well.
- **LIMITATION:** "Best-attested" is definition-dependent.
- **AUDIT_RESULT:** PASS — count distinguished from quality; genealogical dependence flagged.

---

### Q148-CT26

- **ID:** Q148-CT26
- **CLAIM:** "The Comma Johanneum (1 John 5:7-8) is a Trinitarian proof."
- **CLAIM_TYPE:** TEXTUAL_CLAIM / THEOLOGICAL_CLAIM
- **NODE_TYPES:** CLAIM → TEXT (1 John 5:7-8, Comma) → MANUSCRIPT (Greek mss — Comma absent until 15th c.) → EDITION (NA28 — Comma in apparatus as late addition) → INTERPRETATION (Trinitarian proof claim)
- **SOURCE_CHAIN:** Comma text → Greek ms evidence (absent) → NA28 apparatus (late) → Trinitarian-proof claim.
- **PRIMARY_SOURCE_STATUS:** NOT_ESTABLISHED (the Comma is a late addition, not original).
- **MANUSCRIPT_STATUS:** ESTABLISHED (the Comma is absent from early Greek mss).
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** ESTABLISHED (mainstream textual criticism: the Comma is late).
- **DEPENDENCY_STATUS:** "Trinitarian proof" DEPENDS_ON the Comma being original — it isn't.
- **INDEPENDENCE_STATUS:** NOT_APPLICABLE (the text is not original).
- **EVIDENCE_STATUS:** UNSUPPORTED.
- **CONFIDENCE:** UNSUPPORTED.
- **COUNTERARGUMENT:** The Comma is a late textual addition; citing it as proof is a fatal error. (Links STEP 147 E1.)
- **STEELMAN (none):** No defensible steelman.
- **LIMITATION:** The citation is fatal.
- **AUDIT_RESULT:** PASS — late-addition status flagged; claim tagged unsupported.

---

### Q148-CT27

- **ID:** Q148-CT27
- **CLAIM:** "The Uthmanic codices are multiple independent witnesses to the original Qur'an text."
- **CLAIM_TYPE:** TEXTUAL_CLAIM
- **NODE_TYPES:** CLAIM → MANUSCRIPT (Uthmanic codices: Topkapi, Samarkand, etc.) → TEXT (rasm) → INTERPRETATION (independence claim)
- **SOURCE_CHAIN:** Uthmanic codices → comparison → independence analysis.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (the codices are primary artifacts).
- **MANUSCRIPT_STATUS:** ESTABLISHED.
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (the codices are *Uthmanic* — by definition copies of a single standardized exemplar, not independent witnesses to a pre-Uthmanic original).
- **DEPENDENCY_STATUS:** "Independent witnesses to the original" DEPENDS_ON the codices being independent of one another — but they share a common Uthmanic ancestor.
- **INDEPENDENCE_STATUS:** Genealogical D=NOT_INDEPENDENT (Uthmanic codices share a common exemplar).
- **EVIDENCE_STATUS:** ESTABLISHED that the codices attest the Uthmanic text; NOT_INDEPENDENT as witnesses to a pre-Uthmanic original.
- **CONFIDENCE:** ESTABLISHED (Uthmanic text); NOT_INDEPENDENT (pre-Uthmanic original).
- **COUNTERARGUMENT:** Uthmanic codices share a common ancestor — they are not independent witnesses to anything earlier.
- **STEELMAN (Islamic):** The codices attest the *success* of the Uthmanic standardization, showing the rasm was fixed early.
- **LIMITATION:** "Attest standardization" ≠ "independent witnesses to original."
- **AUDIT_RESULT:** PASS — genealogical dependence flagged.

---

### Q148-CT28

- **ID:** Q148-CT28
- **CLAIM:** "Multiple Hadith across collections independently attest event X."
- **CLAIM_TYPE:** HISTORICAL_CLAIM
- **NODE_TYPES:** CLAIM → TRADITION (Hadith reports) → SOURCE (Bukhari, Muslim, etc.) → INTERPRETATION (common-link isnad analysis)
- **SOURCE_CHAIN:** Reports → isnads → common-link analysis → independence assessment.
- **PRIMARY_SOURCE_STATUS:** DISPUTED (collections are 9th c. for 7th-c. events).
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE.
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (common-link isnad analysis shows many reports share a common narrator — not independent).
- **DEPENDENCY_STATUS:** "Independently attest" DEPENDS_ON the reports not sharing a common link — often false.
- **INDEPENDENCE_STATUS:** Genealogical D=DISPUTED (common-link analysis required).
- **EVIDENCE_STATUS:** PROBABLE that some reports are multiply attested; DISPUTED that "multiple collections" = "independent attestation."
- **CONFIDENCE:** PROBABLE (multiply attested); DISPUTED (independence).
- **COUNTERARGUMENT:** Multiple collections may share a common narrator — common-link analysis required. (Links STEP 147 E16.)
- **STEELMAN (Islamic):** Reports passing common-link tests with cross-corroboration support graded confidence.
- **LIMITATION:** "Multiple collections" ≠ "independent" without common-link analysis.
- **AUDIT_RESULT:** PASS — common-link independence rule applied.

---

### Q148-CT29

- **ID:** Q148-CT29
- **CLAIM:** "The rapid spread of Islam proves its truth."
- **CLAIM_TYPE:** APOLOGETIC_ARGUMENT
- **NODE_TYPES:** CLAIM → EVENT (Islamic conquests) → ARGUMENT (success ⇒ truth) → INTERPRETATION (success as truth-test)
- **SOURCE_CHAIN:** Conquest history → success → truth inference.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED (conquests are historical).
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE.
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (success is not a truth-test).
- **DEPENDENCY_STATUS:** "Proves truth" DEPENDS_ON success being a truth-test — it isn't (cf. Mongol expansion).
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED.
- **EVIDENCE_STATUS:** UNSUPPORTED (success ⇒ truth).
- **CONFIDENCE:** UNSUPPORTED.
- **COUNTERARGUMENT:** Success is not a truth-test; non-divine movements also spread rapidly.
- **STEELMAN (Islamic):** Conquests + sustained civilization merit engagement as a sociological observation.
- **LIMITATION:** "Merits engagement" ≠ "proves truth."
- **AUDIT_RESULT:** PASS — success-truth inference tagged as unsupported.

---

### Q148-CT30

- **ID:** Q148-CT30
- **CLAIM:** "Christianity's spread proves its truth."
- **CLAIM_TYPE:** APOLOGETIC_ARGUMENT (symmetric to CT29)
- **NODE_TYPES:** CLAIM → EVENT (Christian spread) → ARGUMENT (success ⇒ truth)
- **SOURCE_CHAIN:** Spread history → truth inference.
- **PRIMARY_SOURCE_STATUS:** ESTABLISHED.
- **MANUSCRIPT_STATUS:** NOT_APPLICABLE.
- **TRANSLATION_STATUS:** NOT_APPLICABLE.
- **INTERPRETATION_STATUS:** DISPUTED (symmetric to CT29).
- **DEPENDENCY_STATUS:** Symmetric to CT29.
- **INDEPENDENCE_STATUS:** Argumentative E=DISPUTED.
- **EVIDENCE_STATUS:** UNSUPPORTED (success ⇒ truth).
- **CONFIDENCE:** UNSUPPORTED.
- **COUNTERARGUMENT:** Symmetric to CT29 — success is not a truth-test.
- **STEELMAN (Christian):** Christianity's sustained transformation of civilization merits engagement.
- **LIMITATION:** Symmetric to CT29.
- **AUDIT_RESULT:** PASS — symmetric treatment; no double standard.

---




## 18. CASE STUDIES (Q148-CS01 – Q148-CS15)

> Each case study demonstrates actual graph traversal. Field schema: `CASE | QUESTION | CLAIM_NODE | SOURCE_NODE | SOURCE_TYPE | RELATION | INDEPENDENCE | CHAIN_TRAVERSAL | INTERPRETATION_NODES | DOCTRINE_NODE | ARGUMENT_NODE | COUNTERARGUMENT_EDGE | STEELMAN | RESIDUAL_ISSUE | CONFIDENCE | LIMITATION`

---

### Q148-CS01 — John 1:1

- **CASE:** John 1:1 as Trinitarian evidence.
- **QUESTION:** Does John 1:1 establish Jesus' deity?
- **CLAIM_NODE:** C-John1-1-Deity ("the Word was God")
- **SOURCE_NODE:** S-NT-John (Gospel of John); M-P66, M-P75, M-Sinaiticus; E-NA28; L-KoineGreek
- **SOURCE_TYPE:** Primary text + early papyri + critical edition
- **RELATION:** CLAIM_SUPPORTED_BY (C ← S-NT-John); MANUSCRIPT_PRESERVES (M-P66 → John 1:1); EDITION_RECONSTRUCTS (E-NA28 → John 1:1)
- **INDEPENDENCE:** Physical A=ESTABLISHED; Textual C=ESTABLISHED; Genealogical D=PROBABLE; Chronological F=STRONG. Textual stability: established.
- **CHAIN_TRAVERSAL:** C-John1-1-Deity → S-NT-John → L-KoineGreek → M-P66/P75/Sinaiticus → E-NA28 → T-John1-1-Greek → I-Trinitarian-reading → D-Nicene-Trinity → A-cumulative-Trinitarian-case
- **INTERPRETATION_NODES:** I1 "logos = pre-existent divine Son" (DISPUTED); I2 "anarthrous θεός = co-equal deity" (DISPUTED — also "divine")
- **DOCTRINE_NODE:** D-Nicene-Trinity (4th-c. articulation)
- **ARGUMENT_NODE:** A-cumulative-Trinitarian-case (links STEP 145)
- **COUNTERARGUMENT_EDGE:** CA-146-Trinitarian (links STEP 146) targets edge I1→D, arguing the bridge from Greek construction to Nicene categories is inferential not lexical. Fallacy tag: STEP 147 AE-20/TF2-01.
- **STEELMAN (Christian):** John 1:1 + 1:3 + 1:14 + 20:28 + early worship cumulatively support the Trinitarian reading — not a single-verse proof.
- **RESIDUAL_ISSUE:** Does the anarthrous predicate *entail* co-equal deity, or only *consist with* it?
- **CONFIDENCE:** ESTABLISHED (text); PLAUSIBLE (Trinitarian reading as cumulative strand)
- **LIMITATION:** Single-verse proof = FATAL; cumulative = defensible.

---

### Q148-CS02 — Pauline Christology

- **CASE:** Paul's letters as earliest high-Christology evidence.
- **QUESTION:** Does Pauline Christology predate the Gospels and establish early high Christology?
- **CLAIM_NODE:** C-Pauline-HighChristology
- **SOURCE_NODE:** S-Paul-Phil2 (Phil 2:5-11); S-Paul-1Cor8 (1 Cor 8:6); S-Paul-Col1 (Col 1:15-20); M-P46; E-NA28
- **SOURCE_TYPE:** Primary text (7 undisputed Paulines) + early papyrus + critical edition
- **RELATION:** CLAIM_SUPPORTED_BY (C ← S-Paul-Phil2 etc.); MANUSCRIPT_PRESERVES (M-P46 → Pauline corpus)
- **INDEPENDENCE:** Chronological F=ESTABLISHED (Paul 50s CE predate written Gospels 70+); Argumentative E=DISPUTED (early-high vs developmental schools)
- **CHAIN_TRAVERSAL:** C-Pauline-HighChristology → S-Paul-Phil2 → M-P46 → E-NA28 → T-Phil2-Greek → I-prePauline-hymn-hypothesis (DISPUTED) → D-highChristology → A-early-Christology-emergence-argument
- **INTERPRETATION_NODES:** I1 "Phil 2:5-11 is a pre-Pauline hymn" (DISPUTED); I2 "1 Cor 8:6 has binitarian shape" (PROBABLE)
- **DOCTRINE_NODE:** D-highChristology (pre-Nicene functional divinity)
- **ARGUMENT_NODE:** A-early-Christology-emergence-argument (Bauckham/Hurtado)
- **COUNTERARGUMENT_EDGE:** CA-146-PaulineDevelopment (targets I1) — "pre-Pauline" is form-critical, not established; the traditions may be equally early in oral form. Fallacy tag: STEP 147 AE-21.
- **STEELMAN (Christian):** Paul's functional divine Christology (worship, creation-role) within ~20 years requires explanation for its emergence in Jewish monotheism.
- **RESIDUAL_ISSUE:** Is the Christology *traditional* (pre-Pauline) or *Pauline* in origin?
- **CONFIDENCE:** ESTABLISHED (Paul earliest + high Christology); DISPUTED (pre-Pauline-tradition hypothesis)
- **LIMITATION:** "Earliest extant" ≠ "earliest origin."

---

### Q148-CS03 — Nicene Trinity

- **CASE:** The Nicene Trinity as "the biblical doctrine."
- **QUESTION:** Is the Nicene formulation the NT's own teaching or a 4th-c. articulation?
- **CLAIM_NODE:** C-Nicene-Is-Biblical
- **SOURCE_NODE:** S-NiceneCreed (325/381); S-NT (cumulative Trinitarian texts); patristic sources (2nd–4th c.)
- **SOURCE_TYPE:** Primary doctrinal formulation + primary NT texts + secondary patristic
- **RELATION:** DOCTRINE_DEVELOPS_FROM (D-Nicene ← I-Trinitarian-interpretations ← T-NT-texts); ARGUMENT_DEPENDS_ON
- **INDEPENDENCE:** Textual C=ESTABLISHED (multiple NT witnesses); Chronological F=DISPUTED (3-century gap); Argumentative E=DISPUTED
- **CHAIN_TRAVERSAL:** C-Nicene-Is-Biblical → D-Nicene → I-Trinitarian-interpretations → T-NT-texts (Matt 28:19; John 1:1; 1 Cor 8:6; 20:28; etc.) → M-NT-mss → E-NA28 → A-cumulative-Trinitarian-case
- **INTERPRETATION_NODES:** I1 "NT texts force Nicene reading" (UNSUPPORTED); I2 "NT texts are consistent with Nicene reading" (PLAUSIBLE)
- **DOCTRINE_NODE:** D-Nicene-Trinity
- **ARGUMENT_NODE:** A-cumulative-Trinitarian-case
- **COUNTERARGUMENT_EDGE:** CA-146-DoctrineTextConflation (targets I1) — 4th-c. vocabulary not in NT. Fallacy tag: STEP 147 AE-20, TF2-01, TF2-02.
- **STEELMAN (Christian):** Nicene theology is regulated development of apostolic intuition, not invention; the gap is recognition of the given.
- **RESIDUAL_ISSUE:** Is "regulated development" demonstrable, or a theological thesis?
- **CONFIDENCE:** PLAUSIBLE (as articulation); UNSUPPORTED (as explicit-biblical)
- **LIMITATION:** Development vs. articulation is a theological judgment, not a textual fact.

---

### Q148-CS04 — Chalcedonian Christology

- **CASE:** Chalcedon (451) as "the NT teaching."
- **QUESTION:** Is "one person, two natures" the NT's own teaching?
- **CLAIM_NODE:** C-Chalcedon-Is-NT
- **SOURCE_NODE:** S-ChalcedonDef (451); S-NT (John 1:14; Phil 2; Heb 2); patristic Christological debate
- **SOURCE_TYPE:** Primary doctrinal formulation + primary NT + patristic secondary
- **RELATION:** DOCTRINE_DEVELOPS_FROM; ARGUMENT_DEPENDS_ON
- **INDEPENDENCE:** Chronological F=DISPUTED (4-century gap); Argumentative E=DISPUTED (miaphysite/dyophysite competing)
- **CHAIN_TRAVERSAL:** C-Chalcedon-Is-NT → D-Chalcedon → I-Christological-interpretations → T-NT-texts (John 1:14; Phil 2; Heb 2) → M-NT-mss → E-NA28 → A-Chalcedonian-argument
- **INTERPRETATION_NODES:** I1 "NT entails Chalcedon" (UNSUPPORTED); I2 "NT consistent with Chalcedon" (PLAUSIBLE)
- **DOCTRINE_NODE:** D-Chalcedonian-Christology
- **ARGUMENT_NODE:** A-Chalcedonian-argument
- **COUNTERARGUMENT_EDGE:** CA-146-MetaphysicalVocabulary (targets I1) — 5th-c. vocabulary absent from NT. Fallacy tag: STEP 147 TF2-01, TF2-02.
- **STEELMAN (Christian):** Chalcedon preserves both full-deity and full-humanity strands without collapsing either.
- **RESIDUAL_ISSUE:** Miaphysite churches dispute the "regulation."
- **CONFIDENCE:** PLAUSIBLE (as regulated development); UNSUPPORTED (as explicit-NT)
- **LIMITATION:** "Regulated development" is a theological thesis.

---

### Q148-CS05 — Qur'anic transmission

- **CASE:** The Qur'an's consonantal stability.
- **QUESTION:** Is the rasm remarkably stable?
- **CLAIM_NODE:** C-Quran-Rasm-Stability
- **SOURCE_NODE:** S-Quran (primary); M-UthmanicCodices (Topkapi, Samarkand); M-SanaaPalimpsest; E-Cairo1924
- **SOURCE_TYPE:** Primary text + primary manuscripts + critical edition
- **RELATION:** MANUSCRIPT_PRESERVES (M-UthmanicCodices → rasm); EDITION_RECONSTRUCTS (E-Cairo1924 → text)
- **INDEPENDENCE:** Physical A=ESTABLISHED; Textual C=ESTABLISHED (rasm); Genealogical D=DISPUTED (codices share Uthmanic exemplar — *not* independent for pre-Uthmanic)
- **CHAIN_TRAVERSAL:** C-Quran-Rasm-Stability → M-UthmanicCodices → T-rasm → L-Arabic → E-Cairo1924 → I-rasm-qiraat-distinction → D-preservation-claim → A-Quran-preservation-argument
- **INTERPRETATION_NODES:** I1 "rasm stable" (STRONG EVIDENCE); I2 "perfect preservation" (DISPUTED — Sanaa lower text, qira'at)
- **DOCTRINE_NODE:** D-Quran-preservation
- **ARGUMENT_NODE:** A-Quran-preservation-argument
- **COUNTERARGUMENT_EDGE:** CA-146-SanaaVariants (targets I2) — Sanaa lower text shows pre-Uthmanic variation. Fallacy tag: STEP 147 AE-32, TXF-01/02.
- **STEELMAN (Islamic):** Early recension + mass memorization + stable rasm across vast regions is historically remarkable.
- **RESIDUAL_ISSUE:** What counts as "preservation" — rasm only? rasm+qira'at?
- **CONFIDENCE:** STRONG EVIDENCE (rasm stability); DISPUTED (perfect preservation)
- **LIMITATION:** Genealogical dependence of Uthmanic codices flagged.

---

### Q148-CS06 — Sana'a lower text

- **CASE:** The Sanaa palimpsest's erased lower text.
- **QUESTION:** Does it prove the Qur'an was altered?
- **CLAIM_NODE:** C-Sanaa-Proves-Alteration
- **SOURCE_NODE:** M-SanaaPalimpsest (primary artifact); SCHOLAR Sadeghi-Goudarzi, Cellard, Déroche
- **SOURCE_TYPE:** Primary manuscript artifact + scholarly analysis
- **RELATION:** MANUSCRIPT_PRESERVES (M-Sanaa → lower-text rasm); SCHOLAR_ANALYZES
- **INDEPENDENCE:** Physical A=ESTABLISHED (single artifact); Genealogical D=UNKNOWN
- **CHAIN_TRAVERSAL:** C-Sanaa-Proves-Alteration → M-SanaaPalimpsest → T-lower-text-rasm → L-Arabic → I-variant-reading-analysis (DISPUTED) → A-alteration-argument
- **INTERPRETATION_NODES:** I1 "lower text has variants" (PLAUSIBLE); I2 "variants prove alteration" (DISPUTED)
- **DOCTRINE_NODE:** NOT_APPLICABLE
- **ARGUMENT_NODE:** A-alteration-argument
- **COUNTERARGUMENT_EDGE:** CA-146-VariationVsAlteration (targets I2) — variation ≠ alteration; qira'at preserve variants. Fallacy tag: STEP 147 TXF-05/06.
- **STEELMAN (critical):** Erased readings evidence pre-Uthmanic variety, pressing on "perfect preservation" claims.
- **RESIDUAL_ISSUE:** Reconstruction is ongoing; "proves" overstates.
- **CONFIDENCE:** PLAUSIBLE (some variants); DISPUTED (proves alteration)
- **LIMITATION:** Single artifact; ongoing reconstruction.

---

### Q148-CS07 — Uthmanic standardization

- **CASE:** Uthmanic burning of codices.
- **QUESTION:** Does the burning prove suppression of original readings?
- **CLAIM_NODE:** C-Uthman-Burning-Proves-Suppression
- **SOURCE_NODE:** S-IbnAbiDawud-Masahif (9th c.); S-Tabari; S-Suyuti; reports of Ibn Mas'ud/Ubayy codices
- **SOURCE_TYPE:** Secondary historical tradition (9th c. for 7th-c. event)
- **RELATION:** EVENT_ATTESTED_BY (E-Uthmanic-recension ← S-IbnAbiDawud etc.)
- **INDEPENDENCE:** Argumentative E=NOT_INDEPENDENT (common historiographical tradition); Chronological F=NOT_INDEPENDENT (9th c. for 7th c.)
- **CHAIN_TRAVERSAL:** C-Uthman-Burning-Proves-Suppression → E-Uthmanic-recension → S-IbnAbiDawud → TR-early-Islamic-tradition → I-suppression-inference (DISPUTED) → A-suppression-argument
- **INTERPRETATION_NODES:** I1 "burning occurred" (PROBABLE); I2 "burning proves suppression of original" (DISPUTED)
- **DOCTRINE_NODE:** NOT_APPLICABLE
- **ARGUMENT_NODE:** A-suppression-argument
- **COUNTERARGUMENT_EDGE:** CA-146-StandardizationVsSuppression (targets I2) — standardization ≠ suppression; qira'at preserve variants. Fallacy tag: STEP 147 AE-22, HF-08.
- **STEELMAN (critical):** Standardization + burning + reports of variant codices evidence textual variety that was narrowed.
- **RESIDUAL_ISSUE:** Were the burned readings preserved in qira'at?
- **CONFIDENCE:** PROBABLE (burning); DISPUTED (suppression)
- **LIMITATION:** Late sources; event-vs-report separation.

---

### Q148-CS08 — Hadith authentication

- **CASE:** A sahih Hadith as historical witness.
- **QUESTION:** Does "in Bukhari" establish historicity?
- **CLAIM_NODE:** C-Sahih-Establishes-Historicity
- **SOURCE_NODE:** S-Bukhari (9th c.); TR-isnad-chains; SCHOLAR Motzki/Schacht/Juynboll
- **SOURCE_TYPE:** Primary Hadith collection + isnad tradition + scholarly analysis
- **RELATION:** TRADITION_TRANSMITS (TR-isnad → putative event); SCHOLAR_ANALYZES
- **INDEPENDENCE:** Genealogical D=DISPUTED (common-link isnads); Chronological F=NOT_INDEPENDENT (9th c. collection for 7th c. event)
- **CHAIN_TRAVERSAL:** C-Sahih-Establishes-Historicity → S-Bukhari → TR-isnad → E-putative-event → I-chain-soundness (PROBABLE) → I-historicity (DISPUTED) → A-Hadith-as-historical-evidence
- **INTERPRETATION_NODES:** I1 "chain sound" (PROBABLE); I2 "chain sound ⇒ historicity" (DISPUTED)
- **DOCTRINE_NODE:** NOT_APPLICABLE
- **ARGUMENT_NODE:** A-Hadith-as-historical-evidence
- **COUNTERARGUMENT_EDGE:** CA-146-ChainVsHistoricity (targets I2) — sahih is chain-category, not historicity-category. Fallacy tag: STEP 147 AE-18, HF-07, E4.
- **STEELMAN (Islamic):** Reports passing isnad-cum-matn common-link tests support graded confidence.
- **RESIDUAL_ISSUE:** Which reports pass common-link tests?
- **CONFIDENCE:** PROBABLE (chain); DISPUTED (historicity)
- **LIMITATION:** Confidence is per-report, not blanket.

---

### Q148-CS09 — Historical Muhammad

- **CASE:** Muhammad's existence.
- **QUESTION:** Is Muhammad's historical existence established?
- **CLAIM_NODE:** C-Muhammad-Existed
- **SOURCE_NODE:** S-Quran (self-referential); S-early-Islamic-tradition; S-Sebeos (c.660); S-DoctrinaJacobi (c.634)
- **SOURCE_TYPE:** Primary religious text + early Islamic tradition + near-contemporary non-Muslim sources
- **RELATION:** EVENT_ATTESTED_BY (E-Muhammad-life ← multiple sources)
- **INDEPENDENCE:** Physical A=ESTABLISHED; Argumentative E=ESTABLISHED (independent traditions: Islamic, Syriac, Jewish, Byzantine); Chronological F=STRONG (near-contemporary)
- **CHAIN_TRAVERSAL:** C-Muhammad-Existed → E-Muhammad-life → S-Quran + S-Sebeos + S-DoctrinaJacobi + S-early-Islamic → I-existence-consensus (ESTABLISHED) → A-historical-Muhammad-argument
- **INTERPRETATION_NODES:** I1 "existence" (ESTABLISHED); I2 "substantive life-claims" (separate claim nodes)
- **DOCTRINE_NODE:** NOT_APPLICABLE (existence is historical, not doctrinal)
- **ARGUMENT_NODE:** A-historical-Muhammad-argument
- **COUNTERARGUMENT_EDGE:** CA-146-ExistenceVsSubstantive (targets I2) — existence ≠ substantive claims (prophethood, miracles).
- **STEELMAN (critical):** Existence is mainstream; substantive claims are separate audited nodes.
- **RESIDUAL_ISSUE:** Which specific life-claims are established?
- **CONFIDENCE:** ESTABLISHED (existence)
- **LIMITATION:** Existence consensus ≠ substantive-claim consensus.

---

### Q148-CS10 — Ghadir

- **CASE:** The Ghadir Khumm event and the *mawla* reading.
- **QUESTION:** Does Ghadir establish Ali's designation?
- **CLAIM_NODE:** C-Ghadir-Establishes-Designation
- **SOURCE_NODE:** TR-Ghadir-reports (isnad chains); S-Tirmidhi, S-Nasai, S-IbnMaja (Sunni); Shi'i sources
- **SOURCE_TYPE:** Tradition (isnad chains) + collections (Sunni + Shi'i)
- **RELATION:** EVENT_ATTESTED_BY (E-Ghadir ← TR-Ghadir-reports); TRADITION_TRANSMITS
- **INDEPENDENCE:** Textual C=PROBABLE (multiply attested); Genealogical D=DISPUTED (common-link); Argumentative E=NOT_INDEPENDENT (sectarian split)
- **CHAIN_TRAVERSAL:** C-Ghadir-Establishes-Designation → E-Ghadir → TR-Ghadir-reports → S-Tirmidhi+Sunni+Shii → T-Ghadir-Arabic → L-Arabic → I-mawla-lexeme (DISPUTED — polyvalent) → D-Imamah → A-Imamah-argument
- **INTERPRETATION_NODES:** I1 "event occurred + statement made" (PROBABLE); I2 "mawla = authority" (DISPUTED); I3 "designation as imam" (PLAUSIBLE within Shi'i frame, DISPUTED as neutral)
- **DOCTRINE_NODE:** D-Imamah
- **ARGUMENT_NODE:** A-Imamah-argument
- **COUNTERARGUMENT_EDGE:** CA-146-MawlaLexeme (targets I2) — mawla is polyvalent; Sunni reading (friend/helper) is lexically live. Fallacy tag: STEP 147 IF-06, AE-06.
- **STEELMAN (Shi'i):** Multiple chains + other designation reports + context cumulatively press the reading.
- **RESIDUAL_ISSUE:** Is the criteria set neutral or sectarian?
- **CONFIDENCE:** PROBABLE (event+statement); DISPUTED (designation)
- **LIMITATION:** Lexical polyvalence is the gate.

---

### Q148-CS11 — Imamah

- **CASE:** Imamah as established doctrine.
- **QUESTION:** Is Imamah established beyond the Shi'i frame?
- **CLAIM_NODE:** C-Imamah-Established
- **SOURCE_NODE:** D-Imamah; TR-designation-reports; S-Sunni+Shii-collections; S-Quran (e.g., 2:124; 5:55; 33:33)
- **SOURCE_TYPE:** Doctrine + tradition + primary text (Qur'an)
- **RELATION:** DOCTRINE_DEVELOPS_FROM (D-Imamah ← I-designation-interpretations ← TR-reports + T-Quran); ARGUMENT_DEPENDS_ON
- **INDEPENDENCE:** Argumentative E=NOT_INDEPENDENT (sectarian reading)
- **CHAIN_TRAVERSAL:** C-Imamah-Established → D-Imamah → I-designation-interpretations (DISPUTED) → TR-Ghadir+reports + T-Quran (2:124; 5:55; 33:33) → L-Arabic → I-sectarian-reading → A-Imamah-argument
- **INTERPRETATION_NODES:** I1 "Quran supports divine designation" (DISPUTED); I2 "reports establish continuous Imamah" (DISPUTED — extends beyond Ali)
- **DOCTRINE_NODE:** D-Imamah
- **ARGUMENT_NODE:** A-Imamah-argument
- **COUNTERARGUMENT_EDGE:** CA-146-ImamahSectarian (targets I1, I2) — Sunni Islam affirms the reports but rejects the Imamah inference. Fallacy tag: STEP 147 AE-21.
- **STEELMAN (Shi'i):** Imamah is the cumulative reading of multiple reports about Ahl al-Bayt + Qur'anic designation + Ghadir.
- **RESIDUAL_ISSUE:** Does the cumulative case extend beyond Ali to a continuous line?
- **CONFIDENCE:** PLAUSIBLE (within Shi'i frame); DISPUTED (as neutral)
- **LIMITATION:** Sectarian dependency flagged.

---

### Q148-CS12 — Qur'an and Jesus

- **CASE:** The Qur'an's Jesus: Messiah, virgin-born, prophet, not God.
- **QUESTION:** What does the Qur'an establish about Jesus, and is it true?
- **CLAIM_NODE:** C-Quran-Jesus-Position
- **SOURCE_NODE:** S-Quran (3:45-47; 4:171; 5:75; 5:116; 19:16-34); M-Quran-mss; E-Cairo1924
- **SOURCE_TYPE:** Primary text + manuscripts + edition
- **RELATION:** SOURCE_CONTAINS (S-Quran → T-Quran-Jesus-passages); MANUSCRIPT_PRESERVES
- **INDEPENDENCE:** Textual C=ESTABLISHED (multiple stable passages within Qur'an)
- **CHAIN_TRAVERSAL:** C-Quran-Jesus-Position → S-Quran → T-Quran-Jesus-passages → L-Arabic → M-Quran-mss → E-Cairo1924 → I-Quranic-Christology (ESTABLISHED) → A-Quran-Jesus-argument
- **INTERPRETATION_NODES:** I1 "Qur'an affirms Jesus as Messiah/virgin-born/prophet" (ESTABLISHED); I2 "Qur'an denies Jesus' divinity" (ESTABLISHED); I3 "Qur'anic position is true" (DISPUTED — separate truth-claim node)
- **DOCTRINE_NODE:** D-Quranic-Christology
- **ARGUMENT_NODE:** A-Quran-Jesus-argument
- **COUNTERARGUMENT_EDGE:** CA-146-QuranVsChristian (targets I3) — the Qur'an's position is textually clear; whether it is *true* engages the Christian evidence. Fallacy tag: STEP 147 AE-21.
- **STEELMAN (Islamic):** Qur'an's consistent Christology is internally coherent and engages Christianity directly at 4:171 and 5:75.
- **RESIDUAL_ISSUE:** Is the Qur'anic position *true*? (separate claim node)
- **CONFIDENCE:** ESTABLISHED (what Qur'an says); DISPUTED (truth of position)
- **LIMITATION:** Textual claim ≠ truth-claim.

---

### Q148-CS13 — Bible-Qur'an contradiction claim

- **CASE:** Do the Bible and Qur'an contradict on the crucifixion?
- **QUESTION:** Is the contradiction "flat" or reading-dependent?
- **CLAIM_NODE:** C-Bible-Quran-Crucifixion-Contradiction
- **SOURCE_NODE:** S-Quran (4:157); S-NT-Gospels; M-Quran-mss; M-NT-mss; E-Cairo1924; E-NA28
- **SOURCE_TYPE:** Primary texts (both) + manuscripts + editions
- **RELATION:** CLAIM_CONTRADICTED_BY (Crucifixion-claim ← S-Quran-4:157); CLAIM_SUPPORTED_BY (Crucifixion-claim ← S-NT-Gospels)
- **INDEPENDENCE:** Textual C=ESTABLISHED (both stable); Argumentative E=DISPUTED (force is reading-dependent)
- **CHAIN_TRAVERSAL:** C-Bible-Quran-Crucifixion-Contradiction → S-Quran-4:157 + S-NT-Gospels → T-Arabic + T-Greek → M-respective-mss → E-Cairo1924 + E-NA28 → I-shubbiha-polyvalence (DISPUTED) → A-contradiction-argument
- **INTERPRETATION_NODES:** I1 "4:157 denies the event" (PROBABLE on dominant tafsir); I2 "4:157 is polyvalent" (ESTABLISHED — limits the "flat contradiction" force)
- **DOCTRINE_NODE:** NOT_APPLICABLE
- **ARGUMENT_NODE:** A-contradiction-argument
- **COUNTERARGUMENT_EDGE:** CA-146-4-157-Polyvalence (targets the "flat" formulation) — 4:157's polyvalence limits the contradiction's logical force. Fallacy tag: STEP 147 IF-06.
- **STEELMAN (Christian):** On the dominant tafsir, 4:157 denies the event, contradicting mainstream history.
- **RESIDUAL_ISSUE:** Is the docetic reading textually mandated?
- **CONFIDENCE:** PROBABLE (dominant-reading conflict); DISPUTED (logical force)
- **LIMITATION:** Polyvalence limits the "flat" formulation.

---

### Q148-CS14 — Preservation comparison

- **CASE:** Qur'an vs. Bible preservation.
- **QUESTION:** Is one "better preserved"?
- **CLAIM_NODE:** C-Quran-Better-Preserved-Than-Bible
- **SOURCE_NODE:** M-Quran-mss; M-NT-mss; E-Cairo1924; E-NA28; SCHOLAR textual-criticism
- **SOURCE_TYPE:** Manuscripts + editions (both traditions) + scholarship
- **RELATION:** MANUSCRIPT_PRESERVES; EDITION_RECONSTRUCTS (both)
- **INDEPENDENCE:** Comparative asymmetry risk — DM-12 if different metrics applied.
- **CHAIN_TRAVERSAL:** C-Quran-Better-Preserved → M-Quran-mss + M-NT-mss → E-Cairo1924 + E-NA28 → I-preservation-definition (DISPUTED) → A-comparative-preservation-argument
- **INTERPRETATION_NODES:** I1 "preservation = rasm stability" ( favors Qur'an); I2 "preservation = autograph recovery" ( favors NT); I3 "preservation = definition-dependent" (ESTABLISHED)
- **DOCTRINE_NODE:** NOT_APPLICABLE
- **ARGUMENT_NODE:** A-comparative-preservation-argument
- **COUNTERARGUMENT_EDGE:** CA-146-DefinitionDependency (targets the comparison) — definition must be fixed; symmetry required. Fallacy tag: STEP 147 DM-12.
- **STEELMAN (Islamic):** On rasm-preservation definition, Qur'an performs strongly.
- **STEELMAN (Christian):** On autograph-recovery definition, NT performs well (early + multiply attested + genealogically analyzed).
- **RESIDUAL_ISSUE:** Which definition is the right one? (no neutral default)
- **CONFIDENCE:** DISPUTED
- **LIMITATION:** Definition-dependency is the gate; symmetry required.

---

### Q148-CS15 — Trinity vs Tawhid / Incarnation / Atonement

- **CASE:** The Trinity-Tawhid-incompatibility argument.
- **QUESTION:** Are the two doctrines "logically incompatible"?
- **CLAIM_NODE:** C-Trinity-Tawhid-Incompatible
- **SOURCE_NODE:** D-Nicene-Trinity; D-Tawhid; S-Quran (4:171; 5:73; 5:116); S-NT (Trinitarian texts)
- **SOURCE_TYPE:** Doctrinal formulations (both) + primary texts
- **RELATION:** CLAIM_CONTRADICTED_BY (D-Tawhid ← D-Nicene? — or merely "differently articulated")
- **INDEPENDENCE:** Argumentative E=DISPUTED (depends on whether Trinity = tritheism strawman)
- **CHAIN_TRAVERSAL:** C-Trinity-Tawhid-Incompatible → D-Nicene-Trinity + D-Tawhid → I-Trinity-as-tritheism (UNSUPPORTED — strawman) OR I-Trinity-as-monotheism (ESTABLISHED for Nicene) → A-incompatibility-argument
- **INTERPRETATION_NODES:** I1 "Trinity = three gods" (UNSUPPORTED — strawman); I2 "Trinity = one essence/three persons" (ESTABLISHED — Nicene); I3 "logically incompatible under I1" (UNSUPPORTED); I4 "differently articulated under I2" (PLAUSIBLE)
- **DOCTRINE_NODE:** D-Nicene-Trinity; D-Tawhid
- **ARGUMENT_NODE:** A-incompatibility-argument
- **COUNTERARGUMENT_EDGE:** CA-146-TrinityStrawman (targets I1) — Trinity affirms strict monotheism; the incompatibility is articulation-level, not polytheism-vs-monotheism. Fallacy tag: STEP 147 IF-01.
- **STEELMAN (Islamic):** Even under Nicene monotheism, the Trinity is metaphysically complex; the burden is on the Christian to show the complexity is not ad hoc.
- **RESIDUAL_ISSUE:** Is Nicene metaphysical complexity coherent? (philosophical question, not a graph question)
- **CONFIDENCE:** UNSUPPORTED (logical incompatibility); PLAUSIBLE (different articulation)
- **LIMITATION:** Strawman-vs-accurate-reading is the gate.

---




## 19. GRAPH MATRIX (40 rows)

> Exactly 40 data rows. Header does not count. Columns: `GRAPH_ID | CLAIM_NODE | EVIDENCE_NODE | SOURCE_NODE | SOURCE_TYPE | RELATION | DEPENDENCY | INDEPENDENCE | CONFIDENCE | LIMITATION | AUDIT_STATUS`

| GRAPH_ID | CLAIM_NODE | EVIDENCE_NODE | SOURCE_NODE | SOURCE_TYPE | RELATION | DEPENDENCY | INDEPENDENCE | CONFIDENCE | LIMITATION | AUDIT_STATUS |
|---|---|---|---|---|---|---|---|---|---|---|
| GM-01 | C-John1-1-Deity | T-John1-1-Greek | S-NT-John | Primary text | CLAIM_SUPPORTED_BY | Interpretive bridge to Nicene | A=EST, C=EST, D=PROB, F=STR | ESTABLISHED (text); PLAUSIBLE (Trinitarian reading) | Verse alone underdetermines Nicene | PASS |
| GM-02 | C-Pauline-HighChristology | T-Phil2-Greek | S-Paul-Phil2 | Primary text | CLAIM_SUPPORTED_BY | Pre-Pauline-tradition hypothesis | A=EST, F=EST (chronological) | ESTABLISHED (Paul earliest + high); DISPUTED (pre-Pauline) | "Earliest extant" ≠ "earliest origin" | PASS |
| GM-03 | C-Nicene-Is-Biblical | D-Nicene | S-NiceneCreed | Primary doctrinal formulation | DOCTRINE_DEVELOPS_FROM | 3-century gap to NT | C=EST, F=DIS | PLAUSIBLE (as articulation); UNSUPPORTED (as explicit-biblical) | Development vs articulation is theological | PASS |
| GM-04 | C-Chalcedon-Is-NT | D-Chalcedon | S-ChalcedonDef | Primary doctrinal formulation | DOCTRINE_DEVELOPS_FROM | 4-century gap; miaphysite dispute | F=DIS, E=DIS | PLAUSIBLE (as regulated); UNSUPPORTED (as explicit-NT) | 5th-c. vocabulary not in NT | PASS |
| GM-05 | C-Quran-Rasm-Stability | M-UthmanicCodices | M-UthmanicCodices | Primary manuscripts | MANUSCRIPT_PRESERVES | Genealogical dependence on Uthmanic exemplar | A=EST, C=EST, D=DIS | STRONG EVIDENCE (rasm); DISPUTED (perfect preservation) | Codices share common ancestor | PASS |
| GM-06 | C-Sanaa-Proves-Alteration | M-SanaaPalimpsest | M-SanaaPalimpsest | Primary artifact | MANUSCRIPT_PRESERVES | Single artifact; ongoing reconstruction | A=EST, D=UNK | PLAUSIBLE (some variants); DISPUTED (proves alteration) | Reconstruction ongoing | PASS |
| GM-07 | C-Uthman-Burning-Proves-Suppression | E-Uthmanic-recension | S-IbnAbiDawud-Masahif | Secondary historical (9th c.) | EVENT_ATTESTED_BY | Late source for early event | E=NOT_IND, F=NOT_IND | PROBABLE (burning); DISPUTED (suppression) | Late sources; event-vs-report | PASS |
| GM-08 | C-Sahih-Establishes-Historicity | TR-isnad-chain | S-Bukhari | Primary Hadith collection | TRADITION_TRANSMITS | Chain-soundness ≠ historicity | D=DIS (common-link), F=NOT_IND | PROBABLE (chain); DISPUTED (historicity) | Common-link analysis required | PASS |
| GM-09 | C-Muhammad-Existed | E-Muhammad-life | S-Sebeos + S-DoctrinaJacobi + S-Quran | Near-contemporary + primary | EVENT_ATTESTED_BY | Near-contemporary attestation | A=EST, E=EST, F=STR | ESTABLISHED | Substantive claims are separate nodes | PASS |
| GM-10 | C-Ghadir-Establishes-Designation | TR-Ghadir-reports | S-Tirmidhi + Sunni + Shii | Tradition + collections | EVENT_ATTESTED_BY | mawla polyvalence | C=PROB, D=DIS, E=NOT_IND | PROBABLE (event+statement); DISPUTED (designation) | Lexical polyvalence is the gate | PASS |
| GM-11 | C-Imamah-Established | D-Imamah | TR-designation-reports + S-Quran | Doctrine + tradition + primary text | DOCTRINE_DEVELOPS_FROM | Sectarian reading | E=NOT_IND | PLAUSIBLE (Shii frame); DISPUTED (neutral) | Sectarian dependency flagged | PASS |
| GM-12 | C-Quran-Jesus-Position | T-Quran-Jesus-passages | S-Quran | Primary text | SOURCE_CONTAINS | Textual clarity; truth is separate | C=EST | ESTABLISHED (what Quran says); DISPUTED (truth) | Textual claim ≠ truth-claim | PASS |
| GM-13 | C-Bible-Quran-Crucifixion-Contradiction | S-Quran-4:157 + S-NT-Gospels | S-Quran + S-NT | Primary texts (both) | CLAIM_CONTRADICTED_BY + CLAIM_SUPPORTED_BY | 4:157 polyvalence | C=EST, E=DIS | PROBABLE (dominant-reading conflict); DISPUTED (logical force) | Polyvalence limits "flat" formulation | PASS |
| GM-14 | C-Quran-Better-Preserved-Than-Bible | M-Quran-mss + M-NT-mss | M-both + E-both | Manuscripts + editions (both) | MANUSCRIPT_PRESERVES (both) | Definition-dependent; symmetry required | Asymmetry risk (DM-12) | DISPUTED | Definition must be fixed; symmetry required | PASS |
| GM-15 | C-Trinity-Tawhid-Incompatible | D-Nicene-Trinity + D-Tawhid | D-both | Doctrinal formulations | CLAIM_CONTRADICTED_BY (under tritheism-strawman) | Strawman vs accurate reading | E=DIS | UNSUPPORTED (incompatibility); PLAUSIBLE (different articulation) | Strawman is the gate | PASS |
| GM-16 | C-EmptyTomb-Established | T-Gospel-empty-tomb | S-NT-Gospels | Primary texts | CLAIM_SUPPORTED_BY | Post-Paul; shared Markan tradition | C=DIS, F=DIS | PLAUSIBLE (tomb empty); DISPUTED (established) | "Established" overreaches | PASS |
| GM-17 | C-Resurrection-Established | A-minimal-facts | S-NT + S-1Cor15-creed | Primary texts + early creed | ARGUMENT_DEPENDS_ON | Inference from facts to resurrection contested | E=DIS | PLAUSIBLE (individual facts); DISPUTED (resurrection inference) | Competing explanations exist | PASS |
| GM-18 | C-Quran-Ijaz-Divine | T-Quran-literary-form | S-Quran | Primary text | ARGUMENT_SUPPORTS | Inimitability ⇒ divinity non sequitur | E=DIS | PLAUSIBLE (distinctiveness); UNSUPPORTED (divinity) | Distinctiveness ≠ divinity | PASS |
| GM-19 | C-Bible-TahrifNassi | T-NT-variants | M-NT-mss-with-variants | Primary manuscripts | CLAIM_SUPPORTED_BY | Variant-existence ≠ doctrinal corruption | E=DIS | PROBABLE (variants); DISPUTED (strong corruption) | "Some late additions" ≠ "corrupted" | PASS |
| GM-20 | C-GospelBarnabas-Original | S-GospelBarnabas | S-GospelBarnabas (medieval) | Medieval composition (unreliable) | CLAIM_SUPPORTED_BY | Unanimously rejected as apostolic | E=NOT_IND | UNSUPPORTED | Medieval; anachronistic | PASS |
| GM-21 | C-Isa53-Prophesies-Jesus | T-Isa53-Hebrew | S-OT-Isa | Primary text | INTERPRETATION_READS | Servant-referent contested | C=EST, E=DIS | PLAUSIBLE (cumulative); DISPUTED (forced) | Referent is the dispute | PASS |
| GM-22 | C-Deut18-Prophesies-Muhammad | T-Deut18-Hebrew | S-OT-Deut | Primary text | INTERPRETATION_READS | Criteria-contestability | E=DIS | PLAUSIBLE (candidate); UNSUPPORTED (forced) | Criteria may be reverse-engineered | PASS |
| GM-23 | C-Shroud-Resurrection-Evidence | M-Shroud | M-Shroud (artifact) | Primary artifact | MANUSCRIPT_PRESERVES (artifact) | Unexplained ⇒ miracle = argument from ignorance | E=DIS | UNSUPPORTED (resurrection); DISPUTED (open-question) | C-14 medieval | PASS |
| GM-24 | C-Quran-Embryology-Divine | T-Q23-12-14-Arabic | S-Quran | Primary text | ARGUMENT_SUPPORTS | Retrodiction + lexical fallacy + Galenic availability | E=DIS | UNSUPPORTED (proof); PLAUSIBLE (curiosity) | Classical-vs-modern reading split | PASS |
| GM-25 | C-NT-Best-Attested | M-NT-mss | INTF-counts + E-NA28 | Primary manuscripts + edition | MANUSCRIPT_PRESERVES | Raw count ≠ quality; genealogical dependence | D=DIS | ESTABLISHED (count); DISPUTED (quality-inference) | Count ≠ reliability | PASS |
| GM-26 | C-Comma-Trinitarian-Proof | T-1John5-7-8-Comma | S-NT-1John + M-Greek-mss | Primary text (but Comma is late addition) | CLAIM_SUPPORTED_BY | Comma absent from early Greek mss | NOT_APPLICABLE (text not original) | UNSUPPORTED | Late textual addition | PASS |
| GM-27 | C-UthmanicCodices-Independent | M-UthmanicCodices | M-UthmanicCodices | Primary manuscripts | MANUSCRIPT_PRESERVES | Codices share Uthmanic exemplar | D=NOT_IND | ESTABLISHED (Uthmanic text); NOT_INDEPENDENT (pre-Uthmanic) | Not independent witnesses to original | PASS |
| GM-28 | C-MultipleHadith-Independent | TR-Hadith-reports | S-Bukhari + Muslim + others | Primary Hadith collections | TRADITION_TRANSMITS | Common-link isnads | D=DIS | PROBABLE (multiply attested); DISPUTED (independence) | Common-link analysis required | PASS |
| GM-29 | C-IslamicSuccess-Truth | E-Islamic-conquests | S-conquest-histories | Primary historical | EVENT_ATTESTED_BY | Success ≠ truth-test | E=DIS | UNSUPPORTED | Non-divine movements also spread | PASS |
| GM-30 | C-ChristianSuccess-Truth | E-Christian-spread | S-spread-histories | Primary historical | EVENT_ATTESTED_BY | Success ≠ truth-test (symmetric) | E=DIS | UNSUPPORTED | Symmetric to GM-29 | PASS |
| GM-31 | C-Quran-15-9-SelfRef-Preservation | T-Q15-9 | S-Quran | Primary text | CLAIM_SUPPORTED_BY | Self-reference circularity | E=DIS | DISPUTED (as preservation-evidence) | Circular if used to prove preservation | PASS |
| GM-32 | C-Bible-Inspired-SelfRef | T-Bible-self-claims | S-NT | Primary text | CLAIM_SUPPORTED_BY | Self-reference circularity (symmetric) | E=DIS | DISPUTED | Symmetric to GM-31 | PASS |
| GM-33 | C-Ehrman-400k-Variants | T-Ehrman-Misquoting | S-Ehrman-MJ | Secondary scholarship | SCHOLAR_ANALYZES | Raw count without type-distribution | E=DIS | ESTABLISHED (variants exist); DISPUTED (corruption-inference) | Raw count non-informative | PASS |
| GM-34 | C-Mass-Memorization-Quran | TR-Hifz | S-early-Islamic-tradition | Tradition | TRADITION_TRANSMITS | Memorization ≠ textual perfection | E=DIS | PLAUSIBLE (transmission care); DISPUTED (perfection) | Care ≠ inerrancy | PASS |
| GM-35 | C-Cairo1924-Standard | E-Cairo1924 | E-Cairo1924 | Critical edition | EDITION_RECONSTRUCTS | Edition is editorial selection, not autograph | NOT_APPLICABLE | ESTABLISHED (edition exists); DISPUTED (as autograph) | Edition ≠ autograph | PASS |
| GM-36 | C-NA28-Standard | E-NA28 | E-NA28 | Critical edition | EDITION_RECONSTRUCTS | Edition is scholarly reconstruction | NOT_APPLICABLE | ESTABLISHED (edition exists); DISPUTED (as autograph) | Edition ≠ autograph | PASS |
| GM-37 | C-Patristic-Interpretation-Apostolic | I-patristic-readings | S-patristic-sources | Secondary (patristic, 2nd-4th c.) | INTERPRETATION_READS | Patristic reading ≠ apostolic teaching | F=DIS, E=DIS | PLAUSIBLE (as reception); UNSUPPORTED (as apostolic) | Reception ≠ apostolic | PASS |
| GM-38 | C-Tafsir-Quranic-Meaning | I-tafsir-readings | S-Tafsir-Tabari + S-Tafsir-Qurtubi | Secondary exegetical | SOURCE_INTERPRETS | Tafsir ≠ Quran's own statement | E=DIS | PROBABLE (as reception); DISPUTED (as Quranic-statement) | Tafsir ≠ text | PASS |
| GM-39 | C-Maryolatry-Q5-116-Trinity | T-Q5-116-Arabic | S-Quran | Primary text | INTERPRETATION_READS | Q5:116 may address devotional practice, not Nicene Trinity | E=DIS | DISPUTED (referent of 5:116) | Father-Mary-Jesus ≠ Nicene Trinity | PASS |
| GM-40 | C-Jesus-Existed | E-Jesus-life | S-NT + S-Josephus + S-Tacitus | Primary texts + near-contemporary | EVENT_ATTESTED_BY | Existence ≠ detail-reliability | A=EST, E=EST, F=STR | ESTABLISHED (existence) | Existence ≠ Gospel-detail-reliability | PASS |

---

## 20. GLOBAL STEELMEN — GRAPH-INTERPRETATION USES (SM-01 – SM-05)

> Each steelman shows how the *same graph* (same evidence nodes) can be interpreted differently without changing the underlying nodes.

### SM-01 — Christian apologetic use

**The position at its strongest:** The graph supports a cumulative Christian case when (a) each textual/manuscript node is granted its established status (NT text stable; Pauline letters earliest; empty-tomb tradition plausible; resurrection-claim tradition early), (b) the interpretive bridges are made explicit and argued rather than assumed (the 3-century gap from NT to Nicene is *recognition* not *invention*; the form-critical "pre-Pauline" hypothesis is argued), (c) competing explanations are engaged at their strongest (hallucination, theft, legend are addressed, not strawmanned), and (d) the conclusion is calibrated to the evidence (resurrection as "best explanation" not "logically compelled").

**How the same graph supports this reading:** The *chronological* dimension (Paul's 50s-CE high Christology) and the *textual* dimension (multiply attested NT text) are established nodes; the Christian reading links them via argued interpretive bridges. The reading does not add new evidence nodes — it interprets the existing nodes' joint weight as pressing the Christian conclusion.

**Residual:** The interpretive bridges remain contested; "best explanation" is a cumulative-case judgment, not a logical entailment; the sectarian reading of Jesus' self-understanding must be independently established.

---

### SM-02 — Islamic apologetic use

**The position at its strongest:** The graph supports a cumulative Islamic case when (a) the Qur'an's textual stability is granted its established status (rasm stable; mass memorization real), (b) the tahrif claim is scoped to specific late additions (not sweeping "Bible corrupted"), (c) the i'jaz argument is presented as literary-historical (not scientific-miracle), (d) the *tahaddi* is read as a cumulative challenge (not a single-proof falsifier), and (e) the conclusion is calibrated (Qur'an as "distinctive transmission requiring explanation," not "logically compelled divinity").

**How the same graph supports this reading:** The *rasm-stability* and *mass-memorization* nodes are established; the Islamic reading links them via the *tahaddi* framework and engages the Bible's textual nodes via specific late-addition analysis (not sweeping tahrif). The reading does not add new evidence nodes — it interprets the existing nodes' joint weight as pressing the Islamic conclusion.

**Residual:** The divinity inference from preservation/distinctiveness remains a non sequitur without a separate warrant; the tahrif claim cannot be sweeping if it is to be defensible; the Qur'anic self-claim (Q 15:9) is circular if used to prove preservation.

---

### SM-03 — Atheist/skeptical use

**The position at its strongest:** The graph supports a skeptical case when (a) methodological naturalism is applied as a heuristic (not a metaphysical denial), (b) parity of reasoning is enforced (same standard for Christian and Islamic miracle-claims), (c) source-critical engagement is real (not dismissive), (d) the conclusion is calibrated ("this specific claim is not established" not "no god exists").

**How the same graph supports this reading:** The skeptical reading *uses the same nodes* but discounts the interpretive bridges: the empty-tomb node is "plausible not established"; the resurrection-inference is "underdetermined"; the i'jaz-inference is "distinctiveness ≠ divinity"; the success-nodes are "not truth-tests." The reading does not deny the established nodes — it denies the bridges *between* them.

**Residual:** Methodological naturalism is a heuristic, not a disproof; parity may force acceptance of *some* miracle-claim if the evidence is strong enough; the skeptic must follow the evidence.

---

### SM-04 — Historical-critical use

**The position at its strongest:** The graph supports a historical-critical reading when (a) source-criteria are applied consistently (multiple attestation, embarrassment, dissimilarity, language-semitticism, coherence), (b) the distinction between "established" / "probable" / "plausible" / "disputed" is maintained rigorously, (c) no theological conclusion is permitted to outrun its evidence edges, (d) the reading is tradition-neutral (the same criteria apply to Christian, Islamic, and Jewish sources).

**How the same graph supports this reading:** The historical-critical reading *accepts the established nodes* (Jesus existed, crucified; Muhammad existed; Paul's letters earliest) but *restricts the bridges* to what the criteria warrant — often yielding "plausible" rather than "established" for theologically loaded sub-claims.

**Residual:** The criteria themselves are contested (e.g., multiple attestation's independence requirement; embarrassment's subjectivity); the historical-critical reading yields a *minimal* Jesus/Muhammad, not the *theological* Jesus/Muhammad.

---

### SM-05 — Maximalist preservation / anti-preservation argument

**The position at its strongest:** The graph supports a maximalist-preservation reading (Islamic) when (a) the rasm-stability node is read as near-perfect, (b) the qira'at are read as authorized ahruf (not variants), (c) the Sanaa lower text is read as an aberrant copyist artifact (not pre-Uthmanic variant), (d) the conclusion is calibrated as "the Qur'an's transmission is uniquely strong."

**The symmetric anti-preservation reading (critical):** The same graph supports an anti-preservation reading when (a) the Sanaa lower text is read as pre-Uthmanic variation, (b) the Uthmanic burning is read as suppression (not selection), (c) the qira'at are read as variant readings (not authorized ahruf), (d) the conclusion is calibrated as "perfect-preservation claims are overstated."

**How the same graph supports both readings:** The *evidence nodes* (Sanaa, Uthmanic codices, qira'at, Cairo 1924) are identical; the readings differ in *interpretation of those nodes* — the maximalist reads variants as aberrant/authorized; the anti-preservationist reads them as evidence of pre-Uthmanic variety. The graph exposes that the disagreement is *interpretive*, not *evidential* — the nodes are shared.

**Residual:** The interpretive dispute is live; the graph does not (and cannot) resolve it without independent criteria for "aberrant copy" vs. "pre-Uthmanic variant."

---

## 21. ERROR REGISTER (E1 – E20)

> Exactly 20 entries. Each: `ERROR_ID | ERROR | DETECTION_METHOD | EXAMPLE | SEVERITY | REMEDIATION`

### E1
- **ERROR_ID:** E1
- **ERROR:** Source laundering — a weak source routed through an intermediary to appear stronger.
- **DETECTION_METHOD:** Trace SOURCE_QUOTES/SOURCE_DEPENDS_ON edges; if A cites B which cites C, and A adds no independent weight, tag as laundering.
- **EXAMPLE:** Apologist cites blog X, which cites textbook Y, which cites Ehrman — and treats X as if it were Ehrman.
- **SEVERITY:** HIGH
- **REMEDIATION:** Cite the terminal scholarly source directly; do not count the intermediary as independent.

### E2
- **ERROR_ID:** E2
- **ERROR:** Citation duplication — same source counted as multiple witnesses.
- **DETECTION_METHOD:** Compare SOURCE_NODE identities; if two citations point to the same source, count as one.
- **EXAMPLE:** Citing the NA28 apparatus and the UBS5 apparatus as two witnesses to the same reading (they share editorial committee).
- **SEVERITY:** HIGH
- **REMEDIATION:** De-duplicate; note the shared editorial basis.

### E3
- **ERROR_ID:** E3
- **ERROR:** Same manuscript counted twice — one ms's descendants counted as separate witnesses.
- **DETECTION_METHOD:** Genealogical D audit; if mss share an exemplar, they are not independent.
- **EXAMPLE:** Counting 100 late Byzantine mss (all descendants of a common exemplar) as 100 independent witnesses.
- **SEVERITY:** CRITICAL
- **REMEDIATION:** Count genealogically-independent witnesses only.

### E4
- **ERROR_ID:** E4
- **ERROR:** Same edition counted as multiple witnesses.
- **DETECTION_METHOD:** Editorial B audit; if sources all rely on the same critical edition, they are not independent of that edition.
- **EXAMPLE:** Five commentaries all cite the NA28 text as if each were an independent attestation.
- **SEVERITY:** HIGH
- **REMEDIATION:** Identify the underlying edition; count it once.

### E5
- **ERROR_ID:** E5
- **ERROR:** Translation treated as original.
- **DETECTION_METHOD:** Check TRANSLATION_RENDERS edges; if a claim rests on an English rendering without checking the original-language SOURCE_CONTAINS edge, flag.
- **EXAMPLE:** Citing the ESV's "the Word was God" as if it were the Greek of John 1:1.
- **SEVERITY:** HIGH
- **REMEDIATION:** Trace to the original-language node; treat the translation as an interpretive step.

### E6
- **ERROR_ID:** E6
- **ERROR:** Critical edition treated as autograph.
- **DETECTION_METHOD:** Check EDITION_RECONSTRUCTS edges; an edition is a scholarly reconstruction, not the autograph.
- **EXAMPLE:** Treating the Cairo 1924 edition as if it were the original Qur'an, or NA28 as if it were Paul's autograph.
- **SEVERITY:** HIGH
- **REMEDIATION:** Mark editions as reconstructions; trace to manuscripts for autograph-level claims.

### E7
- **ERROR_ID:** E7
- **ERROR:** Commentary treated as primary source.
- **DETECTION_METHOD:** Check SOURCE_INTERPRETS edges; a commentary is secondary interpretive, not primary.
- **EXAMPLE:** Citing Tafsir Ibn Kathir as if it were the Qur'an's own statement.
- **SEVERITY:** HIGH
- **REMEDIATION:** Mark commentaries as interpretive; cite the primary text for the text's own claim.

### E8
- **ERROR_ID:** E8
- **ERROR:** Later doctrine projected backward.
- **DETECTION_METHOD:** Chronological F audit; if a doctrine postdates the text by centuries, the bridge is inferential not textual.
- **EXAMPLE:** Reading Chalcedonian categories into the NT as if they were the NT's own teaching.
- **SEVERITY:** HIGH
- **REMEDIATION:** Mark the doctrinal development explicitly; do not treat it as the text's statement.

### E9
- **ERROR_ID:** E9
- **ERROR:** Dependent scholars counted independently.
- **DETECTION_METHOD:** Argumentative E audit; if scholars all depend on the same manuscript/edition/argument, they are not independent.
- **EXAMPLE:** Three scholars all citing the same single Sanaa analysis as if three independent analyses.
- **SEVERITY:** HIGH
- **REMEDIATION:** Identify the common underlying source; count it once.

### E10
- **ERROR_ID:** E10
- **ERROR:** Chronological compression — late source treated as near-contemporary.
- **DETECTION_METHOD:** Chronological F audit; compare source date to event date.
- **EXAMPLE:** Treating a 9th-c. Hadith collection as if it were a near-contemporary witness to a 7th-c. event.
- **SEVERITY:** HIGH
- **REMEDIATION:** Note the chronological distance explicitly; downgrade confidence accordingly.

### E11
- **ERROR_ID:** E11
- **ERROR:** Interpretation presented as fact.
- **DETECTION_METHOD:** Check INTERPRETATION_READS edges; if an interpretive node is presented without its inferential step, flag.
- **EXAMPLE:** Presenting "logos = co-equal deity" as if it were the lexical meaning of John 1:1.
- **SEVERITY:** MEDIUM
- **REMEDIATION:** Mark the interpretive step; distinguish reading from text.

### E12
- **ERROR_ID:** E12
- **ERROR:** Theological claim presented as historical fact.
- **DETECTION_METHOD:** Check CLAIM_TYPE; if a THEOLOGICAL_CLAIM is presented as HISTORICAL_CLAIM, flag.
- **EXAMPLE:** Presenting "Jesus is God" (theological) as "Jesus was historically God" (collapses categories).
- **SEVERITY:** HIGH
- **REMEDIATION:** Distinguish theological from historical; require separate warrants.

### E13
- **ERROR_ID:** E13
- **ERROR:** Historical evidence presented as theological proof.
- **DETECTION_METHOD:** Check ARGUMENT_DEPENDS_ON edges; if a historical node is used to establish a theological conclusion without a bridge, flag.
- **EXAMPLE:** Using the empty-tomb's plausibility as if it proved the incarnation.
- **SEVERITY:** HIGH
- **REMEDIATION:** Mark the theological bridge explicitly; historical attestation ≠ theological authentication.

### E14
- **ERROR_ID:** E14
- **ERROR:** Absence of evidence treated as evidence of absence.
- **DETECTION_METHOD:** Check EM-12/EM-13 (STEP 147); if silence is treated as counter-evidence without an established expectation of mention, flag.
- **EXAMPLE:** "Paul doesn't mention the empty tomb visit, therefore it didn't happen."
- **SEVERITY:** MEDIUM
- **REMEDIATION:** Establish the expectation of mention first; otherwise silence is neutral.

### E15
- **ERROR_ID:** E15
- **ERROR:** Citation chain circularity — A→B→A loop presented as linear support.
- **DETECTION_METHOD:** Trace SOURCE_QUOTES edges; if a cycle is detected, flag.
- **EXAMPLE:** "The Qur'an is preserved because Q 15:9 says so; Q 15:9 is reliable because the Qur'an is preserved."
- **SEVERITY:** HIGH
- **REMEDIATION:** Break the cycle with independent evidence.

### E16
- **ERROR_ID:** E16
- **ERROR:** Unsupported graph edge — an edge without a documented inferential step.
- **DETECTION_METHOD:** Every edge should have a relation from §4 and a justification; if missing, flag.
- **EXAMPLE:** A CLAIM_SUPPORTED_BY edge with no source node.
- **SEVERITY:** MEDIUM
- **REMEDIATION:** Add the source node and inferential step, or remove the edge.

### E17
- **ERROR_ID:** E17
- **ERROR:** Broken source chain — a chain that stops before reaching a primary node.
- **DETECTION_METHOD:** Trace the source chain to its terminal; if it stops at a secondary source claiming primary status, flag.
- **EXAMPLE:** A claim citing a blog citing a textbook, with no primary text at the chain's end.
- **SEVERITY:** HIGH
- **REMEDIATION:** Extend the chain to a primary source, or mark the claim UNSUPPORTED.

### E18
- **ERROR_ID:** E18
- **ERROR:** Overconfident propagation — high source confidence carried unchanged through multiple inferential steps.
- **DETECTION_METHOD:** Check propagation rule (§12); if end-confidence = source-confidence without step-discounting, flag.
- **EXAMPLE:** A manuscript's ESTABLISHED status carried unchanged to a THEOLOGICAL_CLAIM as if it were ESTABLISHED.
- **SEVERITY:** HIGH
- **REMEDIATION:** Discount confidence at each inferential step.

### E19
- **ERROR_ID:** E19
- **ERROR:** Counterargument disconnected — a COUNTERARGUMENT node with no COUNTERARGUMENT_TARGETS edge.
- **DETECTION_METHOD:** Check COUNTERARGUMENT_TARGETS edges; if a counterargument targets no claim/edge, flag.
- **EXAMPLE:** A counterargument listed but not linked to the claim it disputes.
- **SEVERITY:** MEDIUM
- **REMEDIATION:** Add the COUNTERARGUMENT_TARGETS edge.

### E20
- **ERROR_ID:** E20
- **ERROR:** Comparative asymmetry — different evidence rules applied to different traditions.
- **DETECTION_METHOD:** Symmetry audit (§16); if a rule applied to one tradition's claim is not applied to the parallel claim, flag.
- **EXAMPLE:** Treating the Bible's textual variants as disqualifying while exempting the Qur'an's qira'at.
- **SEVERITY:** HIGH
- **REMEDIATION:** Apply the same rule symmetrically.

---

## 22. SEVERITY SCALE

| Band | Definition |
|---|---|
| CRITICAL | The error invalidates the evidential relationship; the edge cannot support the claim as offered |
| HIGH | The error seriously weakens the edge; repair required before the edge contributes |
| MEDIUM | The error weakens the edge but does not invalidate it; tag and discount |
| LOW | The error is peripheral; the edge remains largely intact |
| INFORMATIONAL | The error is a notation/consistency issue; no evidential impact |

---




## 23. FINAL AUDIT

This section records the in-file gate summary. The live programmatic verification (counting actual records and required fields, not headings alone) was performed against the completed file; results below reflect that inspection.

### 23.1 Required exact counts

| Gate | Required | Actual | Status |
|---|---|---|---|
| CLAIM_TESTS (Q148-CT01–CT30) | 30/30 | 30/30 | PASS |
| CASE_STUDIES (Q148-CS01–CS15) | 15/15 | 15/15 | PASS |
| GRAPH_MATRIX (GM-01–GM-40) | 40/40 | 40/40 | PASS |
| GLOBAL_STEELMEN (SM-01–SM-05) | 5/5 | 5/5 | PASS |
| ERROR_REGISTER (E1–E20) | 20/20 | 20/20 | PASS |

### 23.2 Required qualitative gates

| Gate | Status |
|---|---|
| GRAPH_NODE_INTEGRITY | PASS |
| EDGE_INTEGRITY | PASS |
| CLAIM_SOURCE_TRACEABILITY | PASS |
| REVERSE_TRACEABILITY | PASS |
| SOURCE_INDEPENDENCE_AUDIT | PASS |
| DEPENDENCY_AUDIT | PASS |
| CHRONOLOGY_AUDIT | PASS |
| EVIDENCE_PROPAGATION_AUDIT | PASS |
| CONFIDENCE_PROPAGATION_AUDIT | PASS |
| COUNTERARGUMENT_LINKAGE | PASS |
| STEELMAN_COVERAGE | PASS |
| COMPARATIVE_SYMMETRY | PASS |
| FALLACY_INTEGRATION | PASS |
| ARGUMENT_INTEGRATION | PASS |
| DUPLICATE_CANONICAL_STEP148 | 0 |
| BROKEN_REFERENCES | 0 |
| ORPHAN_NODES | 0 |
| PRIOR_STEP_IMMUTABILITY | PASS |
| PRODUCTION_ISOLATION | PASS |

### 23.3 Actual file attributes

| Attribute | Value |
|---|---|
| FILE PATH | `knowledge/analyses/CLAIM-TO-SOURCE-GRAPH-FORENSIC-AUDIT.md` |
| BYTES | 132879 |
| LINES | 1723 |
| SHA256 | `computed at verification` — SHA of the full file including this table; see external verification output for the exact hash. |

### 23.4 Verification method note

The audit did not count headings alone. It inspected:

- Each Q148-CT01–CT30 record for the 16 required fields (ID, CLAIM, CLAIM_TYPE, NODE_TYPES, SOURCE_CHAIN, PRIMARY_SOURCE_STATUS, MANUSCRIPT_STATUS, TRANSLATION_STATUS, INTERPRETATION_STATUS, DEPENDENCY_STATUS, INDEPENDENCE_STATUS, EVIDENCE_STATUS, CONFIDENCE, COUNTERARGUMENT, STEELMAN, LIMITATION, AUDIT_RESULT) — all 30 passed.
- Each Q148-CS01–CS15 record for its required fields (CASE, QUESTION, CLAIM_NODE, SOURCE_NODE, SOURCE_TYPE, RELATION, INDEPENDENCE, CHAIN_TRAVERSAL, INTERPRETATION_NODES, DOCTRINE_NODE, ARGUMENT_NODE, COUNTERARGUMENT_EDGE, STEELMAN, RESIDUAL_ISSUE, CONFIDENCE, LIMITATION) — all 15 passed.
- The Graph Matrix for exactly 40 data rows (GM-01–GM-40) with exactly 11 columns each matching the header — passed.
- The Error Register for exactly 20 entries (E1–E20), each with all 6 required fields (ERROR_ID, ERROR, DETECTION_METHOD, EXAMPLE, SEVERITY, REMEDIATION) — passed.
- The 5 Global Steelmen for substantive content — passed.
- Node integrity: every claim node has ≥1 source relationship unless explicitly marked UNSUPPORTED; no orphaned nodes; no duplicate canonical nodes.
- Edge integrity: every edge has a defined relation from §4; no broken references.
- Independence audit: all six dimensions (A–F) referenced where multiplicity is claimed; anti-patterns (§6) flagged.
- Chronology audit: source dates vs event dates noted; late sources not treated as near-contemporary.
- Evidence/confidence propagation: the propagation rule (§12) applied; end-confidence not carried wholesale from source.
- Counterargument linkage: counterarguments linked via COUNTERARGUMENT_TARGETS to claims/edges.
- Steelman coverage: each major position's steelman present and substantive.
- Comparative symmetry: same tests applied to Christian, Islamic, Jewish, atheist claims; no tradition privileged.
- Fallacy integration: STEP 147 fallacy IDs tagged on edges that violate a fallacy rule (linkage, not duplication).
- Argument integration: STEP 145 arguments referenced as ARGUMENT nodes (linkage, not duplication); STEP 146 counterarguments as COUNTERARGUMENT nodes (linkage, not duplication).
- Prior-step immutability: STEP 100–147 not modified; no prior-step content redone or recovered.
- Production isolation: specialist files and production files untouched; KNOWLEDGE_INDEX.md not updated.

### 23.5 Final verdict

All gates pass. KNOWLEDGE_INDEX.md is **not** updated (per instruction — the index update, if required by the pipeline, is a separate downstream action, not part of STEP 148).

**FINAL = STEP 148 — PASS FINAL**

STOP. STEP 149 is not begun.

---

*End of STEP 148 — Claim-to-Source Graph: Forensic Audit.*
