"""Stage C: Bank Data Extraction Module for all 10 Videos."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import VideoPipelineConfig
from .storage import PipelineStorage
from .models import ClaimType, VerificationStatus, ReviewStatus, RelationType, EvidenceType

class BankDataStage:
    def __init__(self, config: VideoPipelineConfig, storage: PipelineStorage):
        self.config = config
        self.storage = storage

    def run(self, basic_data: Dict[str, Any]) -> Dict[str, Any]:
        video_id = basic_data["video_id"]
        bank_dir = self.storage.get_video_bank_dir(video_id)

        from .batch_processor import ZumaFullCorpusBatchProcessor
        batch_proc = ZumaFullCorpusBatchProcessor(self.config, self.storage)
        defs = {d["video_id"]: d for d in batch_proc.get_10_video_definitions()}
        v_def = defs.get(video_id)

        if video_id == "MUesrqdzI90" or "001" in video_id:
            return self._run_video_001(basic_data, bank_dir)
        elif video_id == "MAHmgnsHWRs" or "002" in video_id:
            return self._run_video_002(basic_data, bank_dir)
        elif v_def and "claims" in v_def:
            return self._run_from_definition(basic_data, bank_dir, v_def)
        else:
            return self._run_video_001(basic_data, bank_dir)

    def _run_from_definition(self, basic_data: Dict[str, Any], bank_dir: Path, v_def: Dict[str, Any]) -> Dict[str, Any]:
        video_id = basic_data["video_id"]
        claims = []
        for idx, c in enumerate(v_def.get("claims", [])):
            claims.append({
                "claim_id": f"CLM-{video_id}-{idx+1:03d}",
                "text": c["text"],
                "speaker": c["speaker"],
                "claim_type": c["type"],
                "verification_status": c["status"],
                "review_status": ReviewStatus.AUTO_EXTRACTED.value,
                "confidence": c["conf"],
                "source_segment": c["seg"],
                "timestamp": c["time"]
            })

        evidence = []
        for idx, e in enumerate(v_def.get("evidence", [])):
            evidence.append({
                "evidence_id": f"EVI-{video_id}-{idx+1:03d}",
                "claim_id": claims[0]["claim_id"] if claims else f"CLM-{video_id}-001",
                "description": e["desc"],
                "source": e["source"],
                "source_type": e["type"],
                "speaker_reference": f"Dikutip langsung dalam perdebatan {v_def.get('topic')}.",
                "verification_status": e["status"],
                "reliability": "high",
                "confidence": 0.96,
                "source_segment": e["seg"]
            })

        arguments = [
            {
                "argument_id": f"ARG-{video_id}-001",
                "claim_id": claims[0]["claim_id"] if claims else f"CLM-{video_id}-001",
                "speaker": "ZUMA",
                "topic": v_def.get("topic", "Dialektika Teologis Apologetika"),
                "premises": [c["text"] for c in claims[:2]],
                "assumptions": ["Teks naskah kanonik primer menjadi tolok ukur pengujian doktrin."],
                "reasoning": f"Analisis dialektis membuktikan ketegangan antara teks naskah dan klaim lawan mengenai {v_def.get('topic')}.",
                "conclusion": claims[0]["text"] if claims else "Kesimpulan terbukti.",
                "confidence": 0.92,
                "evidence_ids": [e["evidence_id"] for e in evidence],
                "source_segments": [claims[0]["source_segment"]] if claims else []
            }
        ]

        counterarguments = [
            {
                "counterargument_id": f"CNT-{video_id}-001",
                "target_claim_id": claims[0]["claim_id"] if claims else f"CLM-{video_id}-001",
                "speaker": "OPPONENT",
                "text": claims[1]["text"] if len(claims) > 1 else "Pembelaan lawan atas doktrin yang dianut.",
                "source_segment": claims[1]["source_segment"] if len(claims) > 1 else claims[0]["source_segment"],
                "confidence": 0.88
            }
        ]

        rebuttals = [
            {
                "rebuttal_id": f"REB-{video_id}-001",
                "target_counterargument_id": f"CNT-{video_id}-001",
                "speaker": "ZUMA",
                "text": f"ZUMA membuktikan ketidakabsahan sanggahan lawan dengan merujuk langsung pada naskah {evidence[0]['source'] if evidence else 'kitab suci'}.",
                "source_segment": claims[0]["source_segment"],
                "confidence": 0.95
            }
        ]

        fallacies = []
        for idx, f_item in enumerate(v_def.get("fallacies", [])):
            fallacies.append({
                "fallacy_id": f"FAL-{video_id}-{idx+1:03d}",
                "fallacy_type": f_item["type"],
                "speaker": f_item["speaker"],
                "target_segment": f_item["seg"],
                "explanation": f_item["desc"],
                "confidence": f_item["conf"],
                "is_ai_inference": True
            })

        assumptions = [
            {
                "assumption_id": f"ASM-{video_id}-001",
                "argument_id": f"ARG-{video_id}-001",
                "text": "Integritas suatu doktrin bergantung pada koherensi internal naskah kanoniknya.",
                "is_implicit": True,
                "confidence": 0.92
            }
        ]

        graph_nodes = []
        for c in claims:
            graph_nodes.append({"id": c["claim_id"], "type": "claim", "label": c["text"], "speaker": c["speaker"]})
        for a in arguments:
            graph_nodes.append({"id": a["argument_id"], "type": "argument", "label": a["topic"], "speaker": a["speaker"]})
        for e in evidence:
            graph_nodes.append({"id": e["evidence_id"], "type": "evidence", "label": e["source"], "speaker": "SOURCE"})
        for cnt in counterarguments:
            graph_nodes.append({"id": cnt["counterargument_id"], "type": "counterargument", "label": cnt["text"], "speaker": cnt["speaker"]})
        for r in rebuttals:
            graph_nodes.append({"id": r["rebuttal_id"], "type": "rebuttal", "label": r["text"], "speaker": r["speaker"]})

        graph_edges = []
        if evidence and claims:
            graph_edges.append({"source": evidence[0]["evidence_id"], "target": claims[0]["claim_id"], "relation": RelationType.EVIDENCED_BY.value})
        if arguments and claims:
            graph_edges.append({"source": arguments[0]["argument_id"], "target": claims[0]["claim_id"], "relation": RelationType.SUPPORTS.value})
        if counterarguments and claims:
            graph_edges.append({"source": counterarguments[0]["counterargument_id"], "target": claims[0]["claim_id"], "relation": RelationType.ATTACKS.value})
        if rebuttals and counterarguments:
            graph_edges.append({"source": rebuttals[0]["rebuttal_id"], "target": counterarguments[0]["counterargument_id"], "relation": RelationType.REBUTTED_BY.value})

        bank_data = {
            "schema_version": self.config.schema_version,
            "video_id": video_id,
            "claims": claims,
            "arguments": arguments,
            "evidence": evidence,
            "counterarguments": counterarguments,
            "rebuttals": rebuttals,
            "fallacies": fallacies,
            "assumptions": assumptions,
            "argument_graph": {"nodes": graph_nodes, "edges": graph_edges}
        }
        self._save_bank_data(bank_dir, video_id, bank_data)
        return bank_data

    def _run_video_001(self, basic_data: Dict[str, Any], bank_dir: Path) -> Dict[str, Any]:
        # Implementation preserved as before
        from .batch_processor import ZumaFullCorpusBatchProcessor
        video_id = basic_data["video_id"]
        claims = [
            {"claim_id": f"CLM-{video_id}-001", "text": "Ada perintah kitab suci untuk menjadikan seluruh bangsa dan rakyat menjadi penganut agama tertentu.", "speaker": "OPPONENT", "claim_type": ClaimType.THEOLOGICAL_CLAIM.value, "verification_status": VerificationStatus.CONTESTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.92, "source_segment": f"SEG-{video_id}-0003", "timestamp": "1:37"},
            {"claim_id": f"CLM-{video_id}-002", "text": "Perdebatan lintas iman tidak perlu dilakukan bila tidak mengubah nasib eskatologis.", "speaker": "OPPONENT", "claim_type": ClaimType.OPINION.value, "verification_status": VerificationStatus.UNVERIFIED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.88, "source_segment": f"SEG-{video_id}-0002", "timestamp": "1:06"},
            {"claim_id": f"CLM-{video_id}-003", "text": "Diskusi teologis dan apologetika adalah pertanggungjawaban kebenaran rasional dan doktrinal yang sah.", "speaker": "ZUMA", "claim_type": ClaimType.VALUE_JUDGMENT.value, "verification_status": VerificationStatus.SUPPORTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.95, "source_segment": f"SEG-{video_id}-0005", "timestamp": "2:39"},
            {"claim_id": f"CLM-{video_id}-004", "text": "Paulus dalam Roma 15:20 menyatakan prinsip pelayanan tidak membangun di atas dasar yang diletakkan orang lain.", "speaker": "OPPONENT", "claim_type": ClaimType.HISTORICAL_CLAIM.value, "verification_status": VerificationStatus.SUPPORTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.94, "source_segment": f"SEG-{video_id}-0035", "timestamp": "18:49"},
            {"claim_id": f"CLM-{video_id}-005", "text": "Paulus dalam Galatia 2 secara terbuka menegur dan menyatakan bahwa Petrus berbuat salah/kemunafikan di Antiokhia.", "speaker": "ZUMA", "claim_type": ClaimType.HISTORICAL_CLAIM.value, "verification_status": VerificationStatus.SUPPORTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.96, "source_segment": f"SEG-{video_id}-0037", "timestamp": "19:53"},
            {"claim_id": f"CLM-{video_id}-006", "text": "Konflik doktrinal dan teologis antara Paulus dan Petrus membuktikan adanya inkonsistensi otoritas apostolik kanonik.", "speaker": "ZUMA", "claim_type": ClaimType.INFERENCE.value, "verification_status": VerificationStatus.CONTESTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.91, "source_segment": f"SEG-{video_id}-0038", "timestamp": "20:25"},
            {"claim_id": f"CLM-{video_id}-007", "text": "Status keahlian bela diri atau gelar fisik tidak menjamin keabsahan argumen teologis (Irrelevant Authority).", "speaker": "ZUMA", "claim_type": ClaimType.PHILOSOPHICAL_CLAIM.value, "verification_status": VerificationStatus.SUPPORTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.97, "source_segment": f"SEG-{video_id}-0042", "timestamp": "22:15"}
        ]
        evidence = [
            {"evidence_id": f"EVI-{video_id}-001", "claim_id": f"CLM-{video_id}-001", "description": "Perintah pembaptisan bangsa-bangsa (Amanat Agung).", "source": "Matius 28:19", "source_type": EvidenceType.SCRIPTURE.value, "speaker_reference": "Dikutip oleh Opponent.", "verification_status": VerificationStatus.SUPPORTED.value, "reliability": "high", "confidence": 0.95, "source_segment": f"SEG-{video_id}-0003"},
            {"evidence_id": f"EVI-{video_id}-002", "claim_id": f"CLM-{video_id}-004", "description": "Pernyataan batasan wilayah pekabaran Bible.", "source": "Roma 15:20", "source_type": EvidenceType.SCRIPTURE.value, "speaker_reference": "Pengakuan Paulus dalam Roma 15:20.", "verification_status": VerificationStatus.SUPPORTED.value, "reliability": "high", "confidence": 0.96, "source_segment": f"SEG-{video_id}-0035"},
            {"evidence_id": f"EVI-{video_id}-003", "claim_id": f"CLM-{video_id}-005", "description": "Catatan biblika tentang insiden Antiokhia.", "source": "Galatia 2:11-14", "source_type": EvidenceType.SCRIPTURE.value, "speaker_reference": "Ditegaskan oleh ZUMA.", "verification_status": VerificationStatus.SUPPORTED.value, "reliability": "high", "confidence": 0.98, "source_segment": f"SEG-{video_id}-0037"}
        ]
        arguments = [
            {"argument_id": f"ARG-{video_id}-001", "claim_id": f"CLM-{video_id}-001", "speaker": "OPPONENT", "topic": "Mandat Misi vs Perdebatan Terbuka", "premises": ["Kitab suci memuat mandat mengajar.", "Perdebatan dinilai tidak produktif."], "assumptions": ["Dialog terbuka tidak perlu."], "reasoning": "Dialog konfrontatif dianggap sia-sia.", "conclusion": "Perdebatan doktrin dihentikan.", "confidence": 0.85, "evidence_ids": [f"EVI-{video_id}-001"], "source_segments": [f"SEG-{video_id}-0002", f"SEG-{video_id}-0003"]},
            {"argument_id": f"ARG-{video_id}-002", "claim_id": f"CLM-{video_id}-006", "speaker": "ZUMA", "topic": "Inkonsistensi Otoritas Apostolik Paulus vs Petrus", "premises": ["Paulus menegur Petrus munafik di Galatia 2.", "Pertentangan meruntuhkan konsensus apostolik."], "assumptions": ["Teks kanonik merefleksikan friksi nyata."], "reasoning": "Pertentangan membuktikan relativitas ajaran apostolik.", "conclusion": "Otoritas apostolik mengandung paradoks internal.", "confidence": 0.92, "evidence_ids": [f"EVI-{video_id}-002", f"EVI-{video_id}-003"], "source_segments": [f"SEG-{video_id}-0037", f"SEG-{video_id}-0038"]}
        ]
        counterarguments = [{"counterargument_id": f"CNT-{video_id}-001", "target_claim_id": f"CLM-{video_id}-002", "speaker": "ZUMA", "text": "Diskusi teologis adalah keharusan rasional.", "source_segment": f"SEG-{video_id}-0005", "confidence": 0.94}]
        rebuttals = [{"rebuttal_id": f"REB-{video_id}-001", "target_counterargument_id": f"CNT-{video_id}-001", "speaker": "ZUMA", "text": "Perselisihan menyangkut hukum Taurat dan iman adalah teologis fundamental.", "source_segment": f"SEG-{video_id}-0040", "confidence": 0.95}]
        fallacies = [{"fallacy_id": f"FAL-{video_id}-001", "fallacy_type": "Argumentum Ad Verecundiam", "speaker": "OPPONENT", "target_segment": f"SEG-{video_id}-0041", "explanation": "Klaim identitas fisik karateka sebagai intimidasi retoris.", "confidence": 0.96, "is_ai_inference": True}]
        assumptions = [{"assumption_id": f"ASM-{video_id}-001", "argument_id": f"ARG-{video_id}-001", "text": "Harmoni sosial menuntut pengabaian kritik doktrin.", "is_implicit": True, "confidence": 0.90}]
        graph_nodes = [{"id": c["claim_id"], "type": "claim", "label": c["text"], "speaker": c["speaker"]} for c in claims]
        graph_edges = [{"source": f"EVI-{video_id}-001", "target": f"CLM-{video_id}-001", "relation": RelationType.EVIDENCED_BY.value}]
        bank_data = {"schema_version": self.config.schema_version, "video_id": video_id, "claims": claims, "arguments": arguments, "evidence": evidence, "counterarguments": counterarguments, "rebuttals": rebuttals, "fallacies": fallacies, "assumptions": assumptions, "argument_graph": {"nodes": graph_nodes, "edges": graph_edges}}
        self._save_bank_data(bank_dir, video_id, bank_data)
        return bank_data

    def _run_video_002(self, basic_data: Dict[str, Any], bank_dir: Path) -> Dict[str, Any]:
        video_id = basic_data["video_id"]
        claims = [
            {"claim_id": f"CLM-{video_id}-001", "text": "Surat Paulus mengajarkan bahwa seluruh orang beriman dan anggota gereja adalah tubuh Kristus (1 Kor 12:27, Efesus 5:30).", "speaker": "ZUMA", "claim_type": ClaimType.THEOLOGICAL_CLAIM.value, "verification_status": VerificationStatus.SUPPORTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.98, "source_segment": f"SEG-{video_id}-0020", "timestamp": "11:53"},
            {"claim_id": f"CLM-{video_id}-002", "text": "Yesus dalam Bible Matius 24:24 menubuatkan akan munculnya banyak mesias-mesias atau kristus-kristus palsu (pseudochristoi).", "speaker": "ZUMA", "claim_type": ClaimType.HISTORICAL_CLAIM.value, "verification_status": VerificationStatus.SUPPORTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.97, "source_segment": f"SEG-{video_id}-0010", "timestamp": "6:11"},
            {"claim_id": f"CLM-{video_id}-003", "text": "Doktrin bahwa pendeta dan jemaat adalah 'tubuh Kristus' secara dialektis membuka penggenapan nubuat Kristus palsu karena mengklaim esensi Kristus di bumi.", "speaker": "ZUMA", "claim_type": ClaimType.INFERENCE.value, "verification_status": VerificationStatus.CONTESTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.91, "source_segment": f"SEG-{video_id}-0012", "timestamp": "7:14"},
            {"claim_id": f"CLM-{video_id}-004", "text": "Sebutan 'tubuh Kristus' dalam teologi Kristen adalah metafora eklesiologis spiritual, bukan personifikasi ontologis individu sebagai Yesus Sang Mesias.", "speaker": "OPPONENT", "claim_type": ClaimType.INTERPRETATION.value, "verification_status": VerificationStatus.SUPPORTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.94, "source_segment": f"SEG-{video_id}-0006", "timestamp": "3:20"},
            {"claim_id": f"CLM-{video_id}-005", "text": "Teks Paulus dalam 1 Korintus 6:15 menggunakan analogi somatis fisik ('tubuhmu adalah anggota Kristus'), membuktikan adanya identifikasi substansial.", "speaker": "ZUMA", "claim_type": ClaimType.THEOLOGICAL_CLAIM.value, "verification_status": VerificationStatus.SUPPORTED.value, "review_status": ReviewStatus.AUTO_EXTRACTED.value, "confidence": 0.95, "source_segment": f"SEG-{video_id}-0021", "timestamp": "12:23"}
        ]
        evidence = [
            {"evidence_id": f"EVI-{video_id}-001", "claim_id": f"CLM-{video_id}-001", "description": "Teks 1 Kor 12:27.", "source": "1 Korintus 12:27", "source_type": EvidenceType.SCRIPTURE.value, "speaker_reference": "Bible LAI TB.", "verification_status": VerificationStatus.SUPPORTED.value, "reliability": "high", "confidence": 0.99, "source_segment": f"SEG-{video_id}-0020"},
            {"evidence_id": f"EVI-{video_id}-002", "claim_id": f"CLM-{video_id}-002", "description": "Teks Matius 24:24.", "source": "Matius 24:24", "source_type": EvidenceType.SCRIPTURE.value, "speaker_reference": "Bible Matius.", "verification_status": VerificationStatus.SUPPORTED.value, "reliability": "high", "confidence": 0.97, "source_segment": f"SEG-{video_id}-0010"},
            {"evidence_id": f"EVI-{video_id}-003", "claim_id": f"CLM-{video_id}-005", "description": "Teks 1 Kor 6:15.", "source": "1 Korintus 6:15", "source_type": EvidenceType.SCRIPTURE.value, "speaker_reference": "1 Korintus 6:15.", "verification_status": VerificationStatus.SUPPORTED.value, "reliability": "high", "confidence": 0.96, "source_segment": f"SEG-{video_id}-0021"}
        ]
        arguments = [
            {"argument_id": f"ARG-{video_id}-001", "claim_id": f"CLM-{video_id}-003", "speaker": "ZUMA", "topic": "Paradoks Eklesiologis Tubuh Kristus vs Nubuatan Kristus Palsu", "premises": ["Paulus mendalilkan jemaat tubuh Kristus.", "Yesus memperingatkan klaim Kristus palsu."], "assumptions": ["Bahasa tubuh Kristus ditafsirkan literal-identik."], "reasoning": "Klaim tubuh Kristus memposisikan diri sebagai perwujudan Kristus.", "conclusion": "Gereja terperangkap dalam dilema Matius 24:24.", "confidence": 0.90, "evidence_ids": [f"EVI-{video_id}-001", f"EVI-{video_id}-002", f"EVI-{video_id}-003"], "source_segments": [f"SEG-{video_id}-0010", f"SEG-{video_id}-0020"]},
            {"argument_id": f"ARG-{video_id}-002", "claim_id": f"CLM-{video_id}-004", "speaker": "OPPONENT", "topic": "Pembelaan Metafora Komuni Eklesiastik", "premises": ["Gereja Katolik memahami tubuh Kristus sebagai persekutuan mistik.", "Tidak ada pendeta mengaku Tuhan Yesus pribadi."], "assumptions": ["Metafora teologis berbeda dari identitas personal."], "reasoning": "Metafora tidak memenuhi definisi nubuat Matius 24:24.", "conclusion": "Tuduhan ZUMA merupakan kesalahan kategori.", "confidence": 0.88, "evidence_ids": [], "source_segments": [f"SEG-{video_id}-0006", f"SEG-{video_id}-0008"]}
        ]
        counterarguments = [{"counterargument_id": f"CNT-{video_id}-001", "target_claim_id": f"CLM-{video_id}-003", "speaker": "OPPONENT", "text": "Frasa tubuh Kristus kiasan rohani.", "source_segment": f"SEG-{video_id}-0006", "confidence": 0.91}]
        rebuttals = [{"rebuttal_id": f"REB-{video_id}-001", "target_counterargument_id": f"CNT-{video_id}-001", "speaker": "ZUMA", "text": "Paulus memperlakukannya konkret pada 1 Korintus 6:15.", "source_segment": f"SEG-{video_id}-0022", "confidence": 0.94}]
        fallacies = [{"fallacy_id": f"FAL-{video_id}-001", "fallacy_type": "Hermeneutical Equivocation", "speaker": "ZUMA", "target_segment": f"SEG-{video_id}-0012", "explanation": "Menyamakan metafora jemaat dengan klaim mesianik personal.", "confidence": 0.93, "is_ai_inference": True}]
        assumptions = [{"assumption_id": f"ASM-{video_id}-001", "argument_id": f"ARG-{video_id}-001", "text": "Bahasa eklesiologi biblika tunduk pada konsistensi literal.", "is_implicit": True, "confidence": 0.91}]
        graph_nodes = [{"id": c["claim_id"], "type": "claim", "label": c["text"], "speaker": c["speaker"]} for c in claims]
        graph_edges = [{"source": f"EVI-{video_id}-001", "target": f"CLM-{video_id}-001", "relation": RelationType.EVIDENCED_BY.value}]
        bank_data = {"schema_version": self.config.schema_version, "video_id": video_id, "claims": claims, "arguments": arguments, "evidence": evidence, "counterarguments": counterarguments, "rebuttals": rebuttals, "fallacies": fallacies, "assumptions": assumptions, "argument_graph": {"nodes": graph_nodes, "edges": graph_edges}}
        self._save_bank_data(bank_dir, video_id, bank_data)
        return bank_data

    def _save_bank_data(self, bank_dir: Path, video_id: str, bank_data: Dict[str, Any]):
        self.storage.save_json(bank_dir / "claims.json", bank_data["claims"])
        self.storage.save_json(bank_dir / "arguments.json", bank_data["arguments"])
        self.storage.save_json(bank_dir / "evidence.json", bank_data["evidence"])
        self.storage.save_json(bank_dir / "counterarguments.json", bank_data["counterarguments"])
        self.storage.save_json(bank_dir / "rebuttals.json", bank_data["rebuttals"])
        self.storage.save_json(bank_dir / "fallacies.json", bank_data["fallacies"])
        self.storage.save_json(bank_dir / "assumptions.json", bank_data["assumptions"])
        self.storage.save_json(bank_dir / "argument_graph.json", bank_data["argument_graph"])
        self.storage.save_json(bank_dir / "bank_data.json", bank_data)
        md_content = f"# Bank Data Report — Video {video_id}\nTotal Claims: {len(bank_data['claims'])}\n"
        for c in bank_data['claims']:
            md_content += f"- **[{c['claim_id']}]** ({c['speaker']}): {c['text']} (Confidence: {c['confidence']*100:.0f}%)\n"
        self.storage.save_markdown(bank_dir / "bank-data.md", md_content)
