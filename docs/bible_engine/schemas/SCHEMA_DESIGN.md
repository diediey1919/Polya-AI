# SCHEMA DESIGN DOCUMENT: POLYA PHILOLOGICAL BIBLE ENGINE
**Version**: Architecture v2.0 — FROZEN  
**Phase**: Phase 1, Task 1.1 (Schema Foundation)  
**Schema Implementation**: [`schemas/bible_engine/001_initial_schema.sql`](file:///home/ubuntu/Polya-AI/schemas/bible_engine/001_initial_schema.sql)  
**Status**: VALIDATED & IN-MEMORY TESTED  
**Date**: 2026-09-30  

---

## 1. Core Architectural Separation of Layers

The database schema strictly partitions data into four ontological tiers to prevent contamination:

```
[TIER 0 & 1: SOURCE WITNESSES & EDITIONS] (Level 0 / Level 1)
  ├── witnesses (א, B, P46, DSS) -> is_source_immutable = 1
  ├── critical_editions (NA28, UBS5, BHS) -> is_source_immutable = 1
  └── source_texts (Exact character streams with SHA-256 hash) -> is_immutable = 1
         │
         ▼
[TIER 2: DERIVED LINGUISTIC ANNOTATIONS] (Level 2)
  ├── tokens (Surface original, clean form, position offset)
  ├── lemmas (Lexicon mapping: BDAG, BDB, HALOT, Thayer, LSJ)
  ├── morphology_annotations (BibleHub standard grammatical tags)
  ├── clauses (Structural boundaries)
  └── syntax_trees (Head-dependent relational graphs)
         │
         ▼
[TIER 3: EVIDENCE & REFERENTIAL IDENTITIES] (Level 3)
  ├── evidence_ledger (Classes E1-E11, Epistemic Tiers T0-T4, status tags)
  ├── entities & entity_mentions (Distinguishes entity types & ontological classes)
  └── referential_relations (REFERENTIAL FIREWALL: blocks association -> identity)
         │
         ▼
[TIER 4: INTERPRETATION, EXEGESIS & SYNTHESIS] (Level 4 / Level 5)
  ├── claims & claim_evidence_links (Hypothesis testing, counter-evidence links)
  ├── translations (Guarded: is_primary_source = 0)
  ├── exegesis_reports (20-section template markdown & structured conclusions)
  └── validation_gate_results (V1-V10 verification gate audits)
```

---

## 2. Comprehensive Entity-Relationship Specification (20 Domains)

### 2.1 Corpus & Boundary Hierarchy
1. **`canons`**: Canon scoping (e.g. Protestant 66 books, Catholic 73, Orthodox 79).
2. **`testaments`**: Testament grouping (Old Testament, New Testament).
3. **`books`**: Book records with canonical ordering and standard un-abbreviated nomenclature (e.g. *Kejadian*, *Wahyu*).
4. **`sections`**: Major literary blocks within books with genre classification.
5. **`pericopes`**: Primary unit of exegesis with boundary confidence rating (`HIGH`, `MEDIUM`, `LOW`, `BOUNDARY_UNCERTAIN`).
6. **`passages`**: Canonical verse address index (`REV-19-08`) preserving numerical ordering.

### 2.2 Textual Witnesses & Critical Apparatus
7. **`witnesses`**: Primary manuscript witnesses (Codex Sinaiticus, Vaticanus, Papyri, Dead Sea Scrolls) with dating ranges, provenance hash, and immutability lock (`is_source_immutable = 1`).
8. **`critical_editions`**: Published critical editions (NA28, UBS5, BHS, TR).
9. **`source_texts`**: Exact, immutable character strings keyed by SHA-256 hashes.
10. **`variant_units`**: Disputed textual units per verse.
11. **`variant_readings`**: Competing readings (Reading A, Reading B) with external manuscript support and internal scribal evaluation.
12. **`variant_witness_attestations`**: Witness-to-reading mapping with correction flagging.

### 2.3 Linguistics: Tokens, Morphology, Syntax
13. **`lemmas`**: Normalized lexical dictionary forms mapped to academic lexicons.
14. **`tokens`**: Token-level stream preserving original punctuation, whitespace, and cleaned strings.
15. **`morphology_annotations`**: BibleHub/academic standard tags (Tense, Voice, Mood, Case, Gender, Number, Aspect) with analyzer provenance.
16. **`clauses`**: Clause units and subordinating conjunctions.
17. **`syntax_trees`**: Hierarchical dependency nodes separating grammatical roles (e.g. subject, predicate, modifier, genitive of source/possession).

### 2.4 Referential Engine & Identity Firewall
18. **`semantic_senses`**: Historical contextual sense definitions distinguishing Koine/Hebrew contemporary usage from modern doctrinal assumptions.
19. **`entities`**: Formal entity catalog categorizing ontological status (e.g. `LITERAL_ENTITY`, `PERSONIFICATION`, `METAPHOR`, `SYMBOL`).
20. **`entity_mentions`**: Mapping of tokens to entities.
21. **`referential_relations`**: **REFERENTIAL FIREWALL**. Enforces check constraint: `CHECK(relation_type != 'STRICT_IDENTITY' OR is_identity_established = 1)`. Blocks treating associative symbolism as grammatical identity without explicit copula/apposition.

### 2.5 Evidence Ledger, Claims, & Exegesis Reports
22. **`evidence_ledger`**: Relational ledger categorizing evidence `E1`–`E11`, epistemic tiers `TIER_0`–`TIER_4`, status tags (`[EXPLICIT]`, `[GRAMMATICALLY ESTABLISHED]`, etc.), and counter-evidence flags.
23. **`claims`**: Discrete claims tested against the text, tracking independence from dogma (`is_theology_independent`).
24. **`claim_evidence_links`**: Symmetrical linking of claims to supporting or contradictory evidence.
25. **`translations`**: Target translations with explicit constraint `is_primary_source = 0` to prevent translations from masquerading as source data.
26. **`exegesis_reports`**: Exegesis reports strictly adhering to the 20-section response template, with structured fields for Sections 16, 17, 18, and 19.
27. **`validation_gate_results`**: Audit records for the 10 validation gates (`V1_SOURCE_INTEGRITY` through `V10_20_SECTION_TEMPLATE_COMPLIANCE`).
28. **`audit_log`**: Tamper-evident ledger capturing every write, update, hash change, agent ID, and model provenance.
29. **`schema_migrations`**: Migration history and checksum ledger.

---

## 3. Critical Constraints & Architectural Safeguards Matrix

| Safeguard / Invariant | SQL Mechanism | Target Vulnerability Prevented |
| :--- | :--- | :--- |
| **Source Immutability** | `CHECK(is_immutable = 1)` and `UNIQUE(sha256_hash)` | Prevents AI or human users from altering canonical Greek/Hebrew strings. |
| **Translation Firewall** | `CHECK(is_primary_source = 0)` | Prevents modern translations (LAI TB, KJV, Vulgata) from overriding source grammar. |
| **Identity Firewall** | `CHECK(relation_type != 'STRICT_IDENTITY' OR is_identity_established = 1)` | Prevents conflating symbolic association (e.g. clothing = righteous deeds) into ontological identity. |
| **Epistemic Type Separation** | Explicit `epistemic_tier` and `evidence_class` ENUMs | Prevents theological interpretations (`TIER_4`) from masquerading as linguistic facts (`TIER_1`). |
| **Boundary Uncertainty** | `boundary_confidence` ENUM containing `BOUNDARY_UNCERTAIN` | Prevents manufacturing artificial certainty on ambiguous pericope boundaries. |
| **Counter-Evidence Enforcement** | `is_counter_evidence INTEGER NOT NULL CHECK(is_counter_evidence IN (0,1))` | Requires explicit tracking and retrieval of contradictory witnesses. |
| **Audit Provenance** | `audit_log` table with `agent_id`, `model_name`, `old_hash`, `new_hash` | Ensures complete forensic reproducibility across multi-agent executions. |
