"""
Polya Multi-Agent Orchestrator — Task Decomposition Engine
Master Prompt #2 — Section 5 Compliance.

Decomposes incoming user questions or apologetics claims into a strictly ordered,
DAG-structured execution plan with explicit dependency tracking, required agent roles,
evidence requirements, and verification criteria.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class ResearchTask:
    """Canonical Task Object conforming to Master Prompt #2 Section 5."""
    task_id: str
    parent_task_id: Optional[str]
    run_id: str
    thread_id: str
    objective: str
    agent_type: str
    priority: int  # 1 (Highest) to 10
    dependencies: List[str]
    status: TaskStatus
    input_data: Dict[str, Any]
    expected_output: str
    evidence_requirements: List[str]
    verification_requirements: List[str]
    assigned_agent: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "parent_task_id": self.parent_task_id,
            "run_id": self.run_id,
            "thread_id": self.thread_id,
            "objective": self.objective,
            "agent_type": self.agent_type,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "input": self.input_data,
            "expected_output": self.expected_output,
            "evidence_requirements": self.evidence_requirements,
            "verification_requirements": self.verification_requirements,
            "assigned_agent": self.assigned_agent,
            "output": self.output_data,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class TaskDecompositionEngine:
    """
    Decomposes user claims into actionable multi-agent research DAGs.
    Specifically calibrated for theological, apologetic, and philological inquiry.
    """

    @classmethod
    def decompose_claim(cls, claim_text: str, run_id: str, thread_id: str) -> List[ResearchTask]:
        """
        Decomposes claim into explicit ordered tasks.
        Example: 'Apakah Paulus membatalkan Taurat?'
        Produces a 10-point structured DAG with clear dependencies.
        """
        cid = uuid.uuid4().hex[:6]
        tasks: List[ResearchTask] = []

        # Task 1: Claim Identification & Scope Extraction
        t1_id = f"task_{cid}_01_claim_ident"
        tasks.append(ResearchTask(
            task_id=t1_id,
            parent_task_id=None,
            run_id=run_id,
            thread_id=thread_id,
            objective="Identify core theological claim, semantic subjects, predicates, and theological domain",
            agent_type="RESEARCH_AGENT",
            priority=1,
            dependencies=[],
            status=TaskStatus.READY,
            input_data={"claim": claim_text},
            expected_output="Normalized claim object with subject, predicate, scope, and theological domain",
            evidence_requirements=["Target claim literal text", "Theological scope definition"],
            verification_requirements=["Syntactic validity of claim"]
        ))

        # Task 2: Scripture Passage Retrieval (Pauline Corpus)
        t2_id = f"task_{cid}_02_pauline_passages"
        tasks.append(ResearchTask(
            task_id=t2_id,
            parent_task_id=t1_id,
            run_id=run_id,
            thread_id=thread_id,
            objective="Retrieve authoritative primary texts from Pauline epistles regarding Torah/Law (e.g. Roma 3:31, Roma 7:12, Roma 10:4, Galatia 3:10-13, Galatia 3:24-25, Efesus 2:15)",
            agent_type="SCRIPTURE_AGENT",
            priority=2,
            dependencies=[t1_id],
            status=TaskStatus.PENDING,
            input_data={"claim": claim_text, "focus": "pauline_epistles"},
            expected_output="List of primary Pauline passages with book, chapter, verse, and verified textual witnesses",
            evidence_requirements=["PRIMARY_SOURCE witnesses", "NA28 Greek / TR / LXX citations"],
            verification_requirements=["Complete book names (no abbreviations)", "Exact chapter and verse numbers"]
        ))

        # Task 3: Scripture Passage Retrieval (Torah & Gospel Baselines)
        t3_id = f"task_{cid}_03_torah_gospel_baseline"
        tasks.append(ResearchTask(
            task_id=t3_id,
            parent_task_id=t1_id,
            run_id=run_id,
            thread_id=thread_id,
            objective="Retrieve foundational Torah passages on law perpetuity (Ulangan 4:2, Ulangan 12:32, Keluaran 31:16-17) and Jesus' words in Matius 5:17-19",
            agent_type="SCRIPTURE_AGENT",
            priority=2,
            dependencies=[t1_id],
            status=TaskStatus.PENDING,
            input_data={"claim": claim_text, "focus": "torah_and_gospel"},
            expected_output="Primary passages establishing the baseline perpetual nature of Torah and historical sayings of Jesus",
            evidence_requirements=["Hebrew BHS / Masoretic Text", "Greek Gospels primary witnesses"],
            verification_requirements=["Exact scripture citations", "Canonical location validation"]
        ))

        # Task 4: Philological & Lexical Analysis (Koine Greek & Hebrew)
        t4_id = f"task_{cid}_04_philology"
        tasks.append(ResearchTask(
            task_id=t4_id,
            parent_task_id=t2_id,
            run_id=run_id,
            thread_id=thread_id,
            objective="Forensic morphological dissection of key Greek verbs and nouns: katargeo (Roma 3:31 vs Efesus 2:15), histemi (Roma 3:31), telos (Roma 10:4), and nomos semantic range vs Hebrew Torah",
            agent_type="PHILOLOGY_AGENT",
            priority=3,
            dependencies=[t2_id, t3_id],
            status=TaskStatus.PENDING,
            input_data={"terms": ["καταργέω", "ἵστημι", "τέλος", "νόμος", "תּוֹרָה"]},
            expected_output="Morphological parsed forms, lexical definitions (BDAG/HALOT), and semantic distinctions between annulment vs fulfillment vs establishment",
            evidence_requirements=["Lemma identification", "Morphological parsing", "Standard academic lexicons"],
            verification_requirements=["Distinction between TEXTUAL FACT and LINGUISTIC INTERPRETATION"]
        ))

        # Task 5: Historical & Contextual Analysis
        t5_id = f"task_{cid}_05_historical_context"
        tasks.append(ResearchTask(
            task_id=t5_id,
            parent_task_id=t1_id,
            run_id=run_id,
            thread_id=thread_id,
            objective="Analyze Second Temple Judaism context, circumcision controversies in Galatia, and Jerusalem Council decree (Kisah Para Rasul 15)",
            agent_type="HISTORY_AGENT",
            priority=3,
            dependencies=[t1_id],
            status=TaskStatus.PENDING,
            input_data={"topic": "second_temple_halakha_and_gentile_inclusion"},
            expected_output="Historical synthesis of Jewish-Gentile table fellowship and ritual boundary markers vs moral law",
            evidence_requirements=["Historical records", "Patristic/apostolic reception evidence"],
            verification_requirements=["Audit against anachronistic assumptions"]
        ))

        # Task 6: Contradiction & Tension Detection
        t6_id = f"task_{cid}_06_contradiction_detection"
        tasks.append(ResearchTask(
            task_id=t6_id,
            parent_task_id=t4_id,
            run_id=run_id,
            thread_id=thread_id,
            objective="Audit tensions between Roma 3:31 ('kami menegakkan hukum Taurat') and Efesus 2:15 / Galatia 3:13 ('membatalkan hukum Taurat'); classify contradiction level",
            agent_type="ARGUMENT_AGENT",
            priority=4,
            dependencies=[t4_id, t5_id],
            status=TaskStatus.PENDING,
            input_data={"compare": ["Roma 3:31", "Efesus 2:15", "Matius 5:17-19"]},
            expected_output="Contradiction classification (CONTEXTUAL_DIFFERENCE vs DIRECT_CONTRADICTION) with explicit resolution matrix",
            evidence_requirements=["Direct textual alignment", "Scope and genre boundary checks"],
            verification_requirements=["No premature declaration of contradiction without contextual audit"]
        ))

        # Task 7: Steelman Counterargument Construction
        t7_id = f"task_{cid}_07_steelman_counterarg"
        tasks.append(ResearchTask(
            task_id=t7_id,
            parent_task_id=t6_id,
            run_id=run_id,
            thread_id=thread_id,
            objective="Construct the strongest plausible opposing argument (e.g. Christian Pauline view that Christ is the end of the law for righteousness, ceremonial vs moral distinction)",
            agent_type="COUNTERARGUMENT_AGENT",
            priority=4,
            dependencies=[t6_id],
            status=TaskStatus.PENDING,
            input_data={"focus": "steelman_opposing_hermeneutics"},
            expected_output="Steelman counterargument with premises, primary proof-texts, underlying assumptions, and strength estimation",
            evidence_requirements=["Scholarly theological formulations", "Direct biblical proofs"],
            verification_requirements=["Zero strawman formulation"]
        ))

        # Task 8: Verification & Evidence Provenance Audit
        t8_id = f"task_{cid}_08_verification_audit"
        tasks.append(ResearchTask(
            task_id=t8_id,
            parent_task_id=t7_id,
            run_id=run_id,
            thread_id=thread_id,
            objective="Verify all passage citations, morphological forms, quotation accuracy, and provenance ledger links",
            agent_type="VERIFICATION_AGENT",
            priority=5,
            dependencies=[t7_id],
            status=TaskStatus.PENDING,
            input_data={"audit_targets": ["passages", "lemmas", "quotes"]},
            expected_output="Verification ledger with states (VERIFIED, SUPPORTED, DISPUTED) and provenance hashes",
            evidence_requirements=["Complete provenance ledger records", "Source registry checks"],
            verification_requirements=["Zero unverified assertions allowed"]
        ))

        # Task 9: Multi-Perspective Synthesis & Evaluation
        t9_id = f"task_{cid}_09_synthesis_evaluation"
        tasks.append(ResearchTask(
            task_id=t9_id,
            parent_task_id=t8_id,
            run_id=run_id,
            thread_id=thread_id,
            objective="Synthesize textual facts, competing interpretations, and multi-dimensional quality evaluation (Evidence Quality, Philological Accuracy, Debate Utility)",
            agent_type="SYNTHESIS_AGENT",
            priority=6,
            dependencies=[t8_id],
            status=TaskStatus.PENDING,
            input_data={"target": "holistic_exegetical_synthesis"},
            expected_output="Final Case File content, multi-dimensional evaluation scorecard, and epistemic confidence rating",
            evidence_requirements=["Calibrated evidence synthesis", "Provenance tracking"],
            verification_requirements=["No hallucinated facts or ungrounded conclusions"]
        ))

        # Task 10: ZUMA Debate Preparation & Strategic Formulation
        t10_id = f"task_{cid}_10_debate_preparation"
        tasks.append(ResearchTask(
            task_id=t10_id,
            parent_task_id=t9_id,
            run_id=run_id,
            thread_id=thread_id,
            objective="Formulate ZUMA strategic debate preparation: Socratic interrogation funnel, textual anchoring ('Buka Roma 3:31 dan Efesus 2:15'), constructive dilemmas, and cross-examination questions",
            agent_type="DEBATE_AGENT",
            priority=7,
            dependencies=[t9_id],
            status=TaskStatus.PENDING,
            input_data={"persona": "ZUMA", "enforce_bible_nomenclature": True},
            expected_output="Debate preparation package: Opening, Core Claims, Evidence, Strongest Opponent Argument, Cross-Examination Questions, Closing",
            evidence_requirements=["Strict Bible nomenclature", "Exact chapter and verse numbers", "No external open sources"],
            verification_requirements=["Strict adherence to Polya Law of Gravity (zero ad hominem, 100% argumentative rigor)"]
        ))

        return tasks
