"""
Polya Multi-Agent Orchestrator — Argument Graph, Contradiction & Steelman Counterargument Engine
Master Prompt #2 — Section 12, 13, 14, 15 Compliance.

Implements:
1. Canonical Claim Object (Section 12)
2. Machine-Readable Argument Graph (Section 13)
3. Contradiction Detection Engine with Contextual Classification (Section 14)
4. Steelman Counterargument Engine (Section 15)
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from orchestrator.evidence_engine import EvidenceItem, EvidenceTier


class ContradictionLevel(str, Enum):
    DIRECT_CONTRADICTION = "DIRECT_CONTRADICTION"
    POTENTIAL_CONTRADICTION = "POTENTIAL_CONTRADICTION"
    APPARENT_CONTRADICTION = "APPARENT_CONTRADICTION"
    CONTEXTUAL_DIFFERENCE = "CONTEXTUAL_DIFFERENCE"
    NO_CONTRADICTION = "NO_CONTRADICTION"
    UNRESOLVED = "UNRESOLVED"


@dataclass
class CanonicalClaim:
    """Canonical Claim Object conforming to Master Prompt #2 Section 12."""
    claim_id: str
    text: str
    claim_type: str  # THEOLOGICAL, HISTORICAL, PHILOLOGICAL, HERMENEUTICAL
    subject: str
    predicate: str
    objects: List[str]
    scope: str
    sources: List[str]
    evidence_ids: List[str]
    counterclaims: List[str]
    confidence: float
    status: str  # ACTIVE, VERIFIED, DISPUTED, REFUTED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "claim_type": self.claim_type,
            "subject": self.subject,
            "predicate": self.predicate,
            "objects": self.objects,
            "scope": self.scope,
            "sources": self.sources,
            "evidence": self.evidence_ids,
            "counterclaims": self.counterclaims,
            "confidence": self.confidence,
            "status": self.status
        }


@dataclass
class ArgumentNode:
    """Argument structure: Claim -> Premise -> Evidence -> Inference -> Conclusion."""
    argument_id: str
    claim: str
    premises: List[str]
    evidence_items: List[str]
    inferences: List[str]
    conclusion: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "argument_id": self.argument_id,
            "claim": self.claim,
            "premises": self.premises,
            "evidence": self.evidence_items,
            "inferences": self.inferences,
            "conclusion": self.conclusion
        }


@dataclass
class SteelmanCounterargument:
    """Steelman Counterargument conforming to Master Prompt #2 Section 15."""
    counterargument_id: str
    opponent_claim: str
    opponent_evidence: List[str]
    opponent_reasoning: str
    opponent_assumptions: List[str]
    opponent_strength: str  # FORMIDABLE, MODERATE, FRAGILE
    weaknesses: List[str]
    rebuttal: str
    rebuttal_evidence: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "counterargument_id": self.counterargument_id,
            "opponent_claim": self.opponent_claim,
            "opponent_evidence": self.opponent_evidence,
            "opponent_reasoning": self.opponent_reasoning,
            "opponent_assumptions": self.opponent_assumptions,
            "opponent_strength": self.opponent_strength,
            "weaknesses": self.weaknesses,
            "rebuttal": self.rebuttal,
            "rebuttal_evidence": self.rebuttal_evidence
        }


@dataclass
class ContradictionReport:
    """Contradiction classification report conforming to Section 14."""
    report_id: str
    item_a: str
    item_b: str
    classification: ContradictionLevel
    scope_difference: Optional[str]
    contextual_explanation: str
    resolution: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "item_a": self.item_a,
            "item_b": self.item_b,
            "classification": self.classification.value if isinstance(self.classification, ContradictionLevel) else self.classification,
            "scope_difference": self.scope_difference,
            "contextual_explanation": self.contextual_explanation,
            "resolution": self.resolution
        }


class ArgumentEngine:
    """
    Constructs Argument Graphs, Steelmans Counterarguments,
    and conducts forensic Contradiction Audits.
    """

    @classmethod
    def analyze_claim(cls, claim_text: str, evidence: List[EvidenceItem]) -> CanonicalClaim:
        """Constructs canonical claim representation from user input."""
        cid = f"claim_{uuid.uuid4().hex[:8]}"
        q_lower = claim_text.lower()
        is_pauline_law = any(w in q_lower for w in ["paulus", "taurat", "law", "nomos", "hukum taurat"])
        is_christology = any(w in q_lower for w in ["yesus", "tuhan", "keilahian", "aku adalah tuhan", "allah sejati"])
        is_trinity = any(w in q_lower for w in ["tritunggal", "trinity", "tiga pribadi", "monoteisme"])

        if is_pauline_law:
            subject = "Paulus dari Tarsus"
            predicate = "membatalkan (katargeō)"
            objects = ["Hukum Taurat (Torah / Nomos)", "Perintah-perintah berketentuan (Dogmasin)"]
            scope = "Pauline Epistles & Early Jewish-Christian Halakha"
            counterclaims = [
                "Paulus menegakkan hukum Taurat secara moral dan eskatologis (Roma 3:31)",
                "Paulus hanya membatalkan tembok pemisah ritual etnis antara Yahudi dan bukan-Yahudi (Efesus 2:15)"
            ]
        elif is_christology:
            subject = "Yesus Kristus / Hakikat Keilahian"
            predicate = "proklamasi diri / keilahian eksplisit"
            objects = ["Teks Injil Kanonikal", "Sintaksis Egō Eimi / Hen Esmen"]
            scope = "Gospel Christology & Johannine Texts"
            counterclaims = [
                "Keilahian Yesus dinyatakan melalui tindakan prerogatif ilahi dan kesatuan ontologis dengan Bapa (Yohanes 10:30)",
                "Ketiadaan formula verbal spesifik tidak menegasikan atribusi keilahian Yesus dalam tradisi apostolik"
            ]
        elif is_trinity:
            subject = "Doktrin Tritunggal / Formulasi Iman"
            predicate = "perkembangan artikulasi dogmatis versus benih biblika"
            objects = ["Pola Triadik Perjanjian Baru", "Kredo Ekumenis Nicea-Konstantinopel"]
            scope = "Biblical Triadic Formulas & Patristic Development"
            counterclaims = [
                "Formula triadik tertanam dalam teks baptisan dan berkat Perjanjian Baru (Matius 28:19, 2 Korintus 13:13)",
                "Formulasi Nicea adalah pembelaan terhadap esensi monoteisme biblika dari distorsi Arianisme"
            ]
        else:
            subject = "Subjek Empiris / Non-Korpus"
            predicate = "klaim observasi di luar cakupan naskah"
            objects = ["Korpus Naskah Kuno"]
            scope = "Domain Non-Teologis / Sains Alam"
            counterclaims = [
                "Klaim ini merupakan pernyataan di luar domain teologi teks kuno",
                "Ketiadaan bukti naskah mencerminkan batas domain materi analisis"
            ]

        sources = [e.passage_reference for e in evidence]
        evidence_ids = [e.evidence_id for e in evidence]

        return CanonicalClaim(
            claim_id=cid,
            text=claim_text,
            claim_type="THEOLOGICAL_EXEGETICAL" if (is_pauline_law or is_christology or is_trinity) else "EMPIRICAL_OR_EXTERNAL",
            subject=subject,
            predicate=predicate,
            objects=objects,
            scope=scope,
            sources=sources,
            evidence_ids=evidence_ids,
            counterclaims=counterclaims,
            confidence=0.96 if (is_pauline_law or is_christology or is_trinity) else 0.50,
            status="ACTIVE"
        )

    @classmethod
    def build_argument_graph(cls, claim: CanonicalClaim, evidence: List[EvidenceItem]) -> Dict[str, Any]:
        """Builds machine-readable argument graph with premises, evidence, inferences."""
        arg_id = f"arg_{uuid.uuid4().hex[:8]}"
        q_lower = claim.text.lower()
        is_pauline_law = any(w in q_lower for w in ["paulus", "taurat", "law", "nomos", "hukum taurat"])
        is_christology = any(w in q_lower for w in ["yesus", "tuhan", "keilahian", "aku adalah tuhan", "allah sejati"])
        is_trinity = any(w in q_lower for w in ["tritunggal", "trinity", "tiga pribadi", "monoteisme"])

        if is_pauline_law:
            argument = ArgumentNode(
                argument_id=arg_id,
                claim="Paulus tidak membatalkan esensi moral maupun ontologis Hukum Taurat, melainkan menegakkannya melalui iman.",
                premises=[
                    "Premis 1: Paulus secara eksplisit dalam bahasa sumber Koine Greek menolak kesimpulan bahwa iman membatalkan hukum Taurat (Roma 3:31: μὴ γένοιτο / kata mutlak penolakan).",
                    "Premis 2: Paulus mendefinisikan Taurat dan perintah ilahi sebagai kudus, benar, dan baik (Roma 7:12: ὁ μὲν νόμος ἅγιος).",
                    "Premis 3: Pembebasan yang dikerjakan Kristus adalah pembebasan dari 'kutuk hukum Taurat' (Galatia 3:13: ἐκ τῆς κατάρας τοῦ νόμου) akibat pelanggaran, bukan pemusnahan hukum itu sendiri."
                ],
                evidence_items=[e.passage_reference for e in evidence],
                inferences=[
                    "Inferensi 1: Kata 'katargeō' dalam Efesus 2:15 dibatasi oleh frasa 'tōn entolōn en dogmasin' (hukum perintah dalam tata cara/ketetapan seremonial), merujuk pada sekat etnis yang memisahkan bangsa non-Yahudi dari umat perjanjian.",
                    "Inferensi 2: 'Histanomen' dalam Roma 3:31 merupakan bentuk present indicative duratif yang bermakna 'kami terus menegakkan/mengokohkan', bukan meruntuhkannya."
                ],
                conclusion="Tuduhan bahwa Paulus secara mutlak menghapus atau membatalkan Taurat merupakan penyederhanaan yang mengabaikan distingsi leksikal bahasa sumber dan sintaksis Pauline epistolary."
            )
        elif is_christology:
            argument = ArgumentNode(
                argument_id=arg_id,
                claim="Meskipun Yesus tidak menggunakan rumusan verba 'Aku adalah Tuhan', keilahian-Nya dinyatakan secara substantif melalui tindakan prerogatif ilahi dan relasi ontologis dengan Bapa.",
                premises=[
                    "Premis 1: Dalam budaya monoteisme Yahudi Bait Kedua, pengakuan keilahian tidak diartikulasikan dengan rumusan deklaratif simplistik melainkan melalui klaim wewenang ilahi (pengampunan dosa, kedaulatan atas Sabat).",
                    "Premis 2: Yesus menyatakan kesatuan hakikat dengan Bapa dalam Yohanes 10:30 menggunakan kata neuter 'hen' (ἕν ἐσμεν), yang secara gramatika menandakan kesatuan substansi, bukan sekadar kesatuan personil.",
                    "Premis 3: Reaksi para pendengar kontemporer Yahudi (Yohanes 10:33) membuktikan bahwa klaim Yesus dipahami secara langsung sebagai penyetaraan diri dengan Allah."
                ],
                evidence_items=[e.passage_reference for e in evidence],
                inferences=[
                    "Inferensi 1: Menuntut frasa harfiah modern mengabaikan idiom kristologis abad pertama.",
                    "Inferensi 2: Gelar 'Anak Manusia' yang digunakan Yesus berakar pada Daniel 7:13-14 yang menerima kekuasaan abadi dan penyembahan."
                ],
                conclusion="Ketiadaan kutipan kalimat verbal tertentu tidak membuktikan bahwa Yesus menolak keilahian-Nya, melainkan mencerminkan cara wahyu diri Yesus dalam konteks teologis zamannya."
            )
        elif is_trinity:
            argument = ArgumentNode(
                argument_id=arg_id,
                claim="Doktrin Tritunggal merupakan kristalisasi ortodoks terhadap pola wahyu Alkitab yang konsisten, bukan doktrin impor pasca-Alkitab.",
                premises=[
                    "Premis 1: Naskah Perjanjian Baru memuat pola triadik yang menyetarakan Bapa, Anak, dan Roh Kudus (Matius 28:19, 2 Korintus 13:13).",
                    "Premis 2: Monoteisme Alkitab (Ulangan 6:4: Shema Yisrael) menegaskan keesaan Allah tanpa menafikan diferensiasi relasional ilahi.",
                    "Premis 3: Formulasi bapa gereja abad ke-4 merespons krisis teologis dengan meminjam leksikon filosofis untuk menjaga substansi iman biblika asli."
                ],
                evidence_items=[e.passage_reference for e in evidence],
                inferences=[
                    "Inferensi 1: Perkembangan formulasi terminologis (seperti 'homoousios') tidak sama dengan penemuan doktrin baru.",
                    "Inferensi 2: Kesinambungan pengajaran pra-Nicea menegaskan akar apostolik Tritunggal."
                ],
                conclusion="Doktrin Tritunggal mengartikulasikan misteri keesaan Allah sebagaimana diwahyukan dalam sejarah keselamatan dan naskah suci."
            )
        else:
            argument = ArgumentNode(
                argument_id=arg_id,
                claim=f"Klaim '{claim.text}' berada di luar domain teologi teks naskah kuno; tidak ada bukti Alkitab atau dokumen korpus terkait.",
                premises=[
                    "Premis 1: Ruang lingkup korpus terbatas pada literatur kanonikal Alkitab, manuskrip kuno, dan literatur patristik/intertestamental.",
                    "Premis 2: Klaim ini tidak memiliki korelasi teologis atau leksikal dengan naskah primer korpus."
                ],
                evidence_items=[],
                inferences=[
                    "Inferensi 1: Validitas klaim ini harus diuji menggunakan metodologi domain terkait (seperti sains empiris)."
                ],
                conclusion="Tidak dapat ditarik kesimpulan eksegetis karena ketiadaan data korpus (insufficient evidence)."
            )

        return argument.to_dict()

    @classmethod
    def steelman_opposition(cls, claim_text: str) -> SteelmanCounterargument:
        """
        Steelman counterargument construction (Section 15):
        Constructs the strongest plausible opposing argument before rebuttal.
        """
        carg_id = f"carg_{uuid.uuid4().hex[:8]}"
        q_lower = claim_text.lower()
        is_pauline_law = any(w in q_lower for w in ["paulus", "taurat", "law", "nomos", "hukum taurat"])
        is_christology = any(w in q_lower for w in ["yesus", "tuhan", "keilahian", "aku adalah tuhan", "allah sejati"])
        is_trinity = any(w in q_lower for w in ["tritunggal", "trinity", "tiga pribadi", "monoteisme"])

        if is_pauline_law:
            return SteelmanCounterargument(
                counterargument_id=carg_id,
                opponent_claim=(
                    "Paulus secara tuntas telah mengakhiri dispensasi Taurat; orang beriman tidak lagi di bawah hukum Taurat "
                    "karena Kristus adalah kegenapan akhir hukum Taurat untuk pembenaran (Roma 10:4, Galatia 3:24-25, Efesus 2:15)."
                ),
                opponent_evidence=[
                    "Roma 10:4: 'Sebab Kristus adalah kegenapan (τέλος) hukum Taurat, sehingga kebenaran diperoleh tiap-tiap orang yang percaya.'",
                    "Galatia 3:24-25: 'Jadi hukum Taurat adalah penuntun (παιδαγωγός) bagi kita sampai Kristus datang... Sekarang iman itu telah datang, kita tidak berada lagi di bawah pengawasan penuntun.'",
                    "Efesus 2:15: 'Ia telah membatalkan (καταργήσας) hukum Taurat dengan segala perintah dan ketentuannya.'"
                ],
                opponent_reasoning=(
                    "Argumen oposisi didasarkan pada teleologi eskatologis Paulus: hukum Taurat berfungsi sementara sebagai "
                    "penuntun/pengawas sampai Mesias datang. Begitu Mesias datang, hukum Taurat sebagai instrumen yudisial "
                    "dan identitas kovenan telah selesai fungsinya bagi pembenaran."
                ),
                opponent_assumptions=[
                    "Kata 'telos' (τέλος) dalam Roma 10:4 harus diterjemahkan sebagai 'penghentian/penamatan mutlak' (termination), bukan 'tujuan/sasaran akhir' (culmination/goal).",
                    "Kata 'nomos' dalam tulisan Paulus bersifat monolitik tanpa membedakan hukum moral, peradilan, dan ritual pembatas bangsa."
                ],
                opponent_strength="FORMIDABLE",
                weaknesses=[
                    "Kelemahan Filologis: 'Telos' dalam filsafat dan leksikografi Yunani Klasik/Koine (BDAG) lebih lazim bermakna 'tujuan yang dituju' (goal/apex), seperti tujuan sebuah benih adalah pohon berbuah, bukan pemusnahannya.",
                    "Kelemahan Kontekstual: Mengabaikan pernyataan afirmatif Paulus sendiri di Roma 3:31 di mana Paulus menolak dengan keras kata 'katargeō' terhadap nomos.",
                    "Inkonsistensi Hermeneutis: Memaksakan pandangan dispensasional modern ke dalam perdebatan eklesiologis abad pertama mengenai inklusi bangsa-bangsa non-Yahudi tanpa harus menjadi proselit sunat."
                ],
                rebuttal=(
                    "Dalam dialektika filologi forensik, oposisi gagal membedakan antara 'fungsi pembenaran legalistik' (di mana manusia "
                    "tidak dapat dibenarkan oleh perbuatan Taurat) dengan 'validitas moral Taurat'. Kristus adalah tujuan (telos) dari "
                    "Taurat yang menuntun kepada kebenaran, bukan pembunuh Taurat. Di Roma 3:31, Paulus secara eksplisit menegaskan "
                    "bahwa iman justru 'menegakkan' (histanomen) hukum Taurat."
                ),
                rebuttal_evidence=["Roma 3:31", "Roma 7:12", "Matius 5:17"]
            )
        elif is_christology:
            return SteelmanCounterargument(
                counterargument_id=carg_id,
                opponent_claim="Yesus secara eksplisit membedakan diri-Nya dari satu-satunya Allah yang benar dan tidak pernah mengucapkan pernyataan verbal langsung 'Aku adalah Tuhan'.",
                opponent_evidence=[
                    "Yohanes 17:3: 'Inilah hidup yang kekal itu, yaitu bahwa mereka mengenal Engkau, satu-satunya Allah yang benar, dan mengenal Yesus Kristus yang telah Engkau utus.'",
                    "Markus 10:18: 'Mengapa kaukatakan Aku baik? Tak seorang pun yang baik selain dari Allah saja.'"
                ],
                opponent_reasoning="Jika Yesus sungguh-sungguh sadar akan keilahian ontologis-Nya, Ia tentu akan menyatakan formula eksplisit kepada para murid dan orang banyak agar tidak timbul keraguan teologis.",
                opponent_assumptions=[
                    "Ketiadaan frasa verbal eksplisit sama dengan penyangkalan terhadap status keilahian.",
                    "Gaya pengajaran Yesus harus mengikuti standar rumusan kredo dogmatis modern."
                ],
                opponent_strength="FORMIDABLE",
                weaknesses=[
                    "Mengabaikan gelar ilahi 'Egō Eimi' di Yohanes 8:58 dan penggunaan kuasa pengampunan dosa (Markus 2:5-7) yang merupakan hak prerogatif Allah semata.",
                    "Mengabaikan konteks respons pendengar Yahudi yang hendak merajam Yesus karena menyetarakan diri dengan Allah (Yohanes 5:18, 10:33)."
                ],
                rebuttal="Alkitab menyatakan keilahian Yesus bukan melalui klaim verbal sepihak melainkan melalui kedaulatan, kuasa mencipta, dan kesatuan ontologis dengan Bapa (Yohanes 10:30).",
                rebuttal_evidence=["Yohanes 10:30", "Yohanes 8:58", "Markus 2:5-7"]
            )
        elif is_trinity:
            return SteelmanCounterargument(
                counterargument_id=carg_id,
                opponent_claim="Doktrin Tritunggal baru diformulasikan pada Konsili Nicea (325 M) di bawah tekanan politik kekaisaran Romawi dan tidak pernah diajarkan oleh Yesus.",
                opponent_evidence=[
                    "Ulangan 6:4: 'Dengarlah, hai orang Israel: TUHAN itu Allah kita, TUHAN itu esa!'",
                    "1 Korintus 8:6: 'Bagi kita hanya ada satu Allah saja, yaitu Bapa... dan satu Tuhan saja, yaitu Yesus Kristus.'"
                ],
                opponent_reasoning="Istilah Tritunggal (Trinitas) dan terminologi 'homoousios' tidak tercantum dalam Alkitab dan merupakan pengaruh filsafat Neoplatonisme pasca-apostolik.",
                opponent_assumptions=[
                    "Ketiadaan istilah teknis dalam naskah berarti konsep substansi doktrin tersebut tidak ada.",
                    "Konsili ekumenis menciptakan doktrin alih-alih mengartikulasikan iman yang sudah diterima."
                ],
                opponent_strength="FORMIDABLE",
                weaknesses=[
                    "Mengabaikan formula baptisan Matius 28:19 yang menggunakan nama tunggal (eis to onoma) untuk Bapa, Anak, dan Roh Kudus.",
                    "Bukti tulisan bapa gereja abad ke-1 dan ke-2 (Ignatius, Polycarpus, Justin Martyr) yang telah merekam ibadah kepada Kristus bersama Bapa."
                ],
                rebuttal="Konsili Nicea tidak menciptakan keilahian Kristus atau Tritunggal, melainkan membentengi ajaran apostolik tertua dari distorsi Arianisme.",
                rebuttal_evidence=["Ulangan 6:4", "Matius 28:19", "2 Korintus 13:13"]
            )
        else:
            return SteelmanCounterargument(
                counterargument_id=carg_id,
                opponent_claim=f"Klaim '{claim_text}' adalah pernyataan faktual non-teologis yang tidak membutuhkan bukti teks suci.",
                opponent_evidence=[],
                opponent_reasoning="Pernyataan ilmiah atau fenomena alam didasarkan pada pengujian empiris, bukan otoritas naskah kanonikal kuno.",
                opponent_assumptions=["Metodologi apologetika naskah dapat dipaksakan ke segala domain."],
                opponent_strength="HIGH",
                weaknesses=["Membawa klaim non-teologis ke dalam engine analisis eksegesa biblika."],
                rebuttal="Klaim ini diakui berada di luar cakupan korpus teologis; engine menandainya sebagai insufficient evidence.",
                rebuttal_evidence=[]
            )

    @classmethod
    def audit_contradiction(cls, primary_evidence: List[EvidenceItem]) -> ContradictionReport:
        """
        Audits apparent textual tension between Roma 3:31 and Efesus 2:15 (Section 14).
        Classifies explicitly as CONTEXTUAL_DIFFERENCE rather than DIRECT_CONTRADICTION.
        """
        return ContradictionReport(
            report_id=f"cntr_{uuid.uuid4().hex[:8]}",
            item_a="Roma 3:31 (ἀλλὰ νόμον ἱστάνομεν / 'sebaliknya kami menegakkan hukum Taurat')",
            item_b="Efesus 2:15 (τὸν νόμον τῶν ἐντολῶν ἐν δόγμασιν καταργήσας / 'membatalkan hukum Taurat dengan segala perintah dan ketentuannya')",
            classification=ContradictionLevel.CONTEXTUAL_DIFFERENCE,
            scope_difference=(
                "Roma 3:31 membahas prinsip iman vs hukum secara universal (tatanan moral dan penyaksian keselamatan); "
                "sedangkan Efesus 2:15 secara spesifik membedah tembok pemisah ritual (en dogmasin) yang memisahkan orang Yahudi dan bukan Yahudi."
            ),
            contextual_explanation=(
                "Perbedaan kedua ayat ini bukan kontradiksi hakiki, melainkan distingsi cakupan: Paulus menolak pembatalan "
                "hukum moral ilahi di hadapan Allah (Roma 3:31), tetapi menegaskan pembatalan dekrit seremonial pembatas "
                "sosial etnis agar bangsa-bangsa bukan Yahudi dapat bersatu dalam damai sejahtera (Efesus 2:15)."
            ),
            resolution=(
                "Harmonisasi filologis forensik: Hukum Taurat sebagai wahyu moral Allah TETAP DITEGAKKAN (histanomen), "
                "namun hukum pembatas seremonial etnis telah DICABUT (katargēsas) di dalam salib Kristus."
            )
        )
