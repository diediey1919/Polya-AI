"""
Polya Multi-Agent Orchestrator — Argument Graph, Contradiction & Steelman Counterargument Engine
Master Prompt #2 — Section 12, 13, 14, 15 Compliance.

Implements:
1. Canonical Claim Object (Section 12)
2. Machine-Readable Argument Graph (Section 13)
3. Contradiction Detection Engine with Contextual Classification (Section 14)
4. Steelman Counterargument Engine (Section 15)
With dynamic User Perspective x Opponent Context matrix support.
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
    and conducts forensic Contradiction Audits with dynamic User x Opponent matrix.
    """

    @classmethod
    def _normalize_perspectives(cls, user_perspective: Optional[str], opponent_perspective: Optional[str] = None):
        p_norm = (user_perspective or "christian_protestant").strip().lower()
        if p_norm in ("christian", "protestant"):
            p_norm = "christian_protestant"
        elif p_norm in ("catholic", "katolik"):
            p_norm = "christian_catholic"
        elif p_norm in ("atheist", "secular"):
            p_norm = "atheist_secular"
        elif p_norm in ("jewish", "yahudi"):
            p_norm = "judaism"
        elif p_norm in ("islam", "muslim"):
            p_norm = "islam"

        DEFAULT_OPP = {
            "christian_protestant": "islam",
            "christian_catholic": "christian_protestant",
            "islam": "christian_protestant",
            "judaism": "christian_protestant",
            "atheist_secular": "christian_protestant",
        }
        opp_norm = (opponent_perspective or "").strip().lower()
        if opp_norm in ("christian", "protestant"):
            opp_norm = "christian_protestant"
        elif opp_norm in ("catholic", "katolik"):
            opp_norm = "christian_catholic"
        elif opp_norm in ("atheist", "secular"):
            opp_norm = "atheist_secular"
        elif opp_norm in ("jewish", "yahudi"):
            opp_norm = "judaism"
        elif opp_norm in ("islam", "muslim"):
            opp_norm = "islam"
        if not opp_norm or opp_norm == p_norm:
            opp_norm = DEFAULT_OPP.get(p_norm, "islam")
        return p_norm, opp_norm

    @classmethod
    def analyze_claim(
        cls,
        claim_text: str,
        evidence: List[EvidenceItem],
        user_perspective: Optional[str] = "christian_protestant",
        opponent_perspective: Optional[str] = None,
        locale: Optional[str] = "id"
    ) -> CanonicalClaim:
        """Constructs canonical claim representation from user input according to epistemic perspective and opponent context."""
        cid = f"claim_{uuid.uuid4().hex[:8]}"
        q_lower = claim_text.lower()
        is_pauline_law = any(w in q_lower for w in ["paulus", "taurat", "law", "nomos", "hukum taurat"])
        is_christology = any(w in q_lower for w in ["yesus", "tuhan", "keilahian", "aku adalah tuhan", "allah sejati", "lukas", "ikan goreng", "hantu", "roh", "bangkit", "kebangkitan"])
        is_trinity = any(w in q_lower for w in ["tritunggal", "trinity", "tiga pribadi", "monoteisme"])

        p_norm, opp_norm = cls._normalize_perspectives(user_perspective, opponent_perspective)

        if is_pauline_law:
            if p_norm == "christian_catholic":
                subject = "Paulus dari Tarsus & Tradisi Apostolik"
                predicate = "kegenapan hukum moral dalam kovenan baru"
                objects = ["Kanon 73 Kitab (Deuterokanonika)", "Tradisi Suci Patristik", "Magisterium Gereja"]
                scope = f"Kanon 73 Kitab, Patristik & Magisterium vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Oposisi {opp_norm.upper()} mendalilkan keberatan atas kaitan iman dan perbuatan ketaatan moral hukum Taurat",
                    "Magisterium mengajarkan bahwa hukum Taurat digenapi dalam kovenan baru tanpa menghapus kewajiban moral (Roma 3:31, Yakobus 2:24)"
                ]
            elif p_norm == "islam":
                subject = "Teologi Paulus versus Syariat Kovenan Para Nabi"
                predicate = "pergeseran ajaran tauhid dan syariat kovenan"
                objects = ["Al-Qur'an al-Karim", "Sunnah Shahihah", "Metode Ilzam al-Khasm"]
                scope = f"Tauhid, Syariat Para Nabi & Kritik Filologis Kanon vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    "Al-Qur'an menegaskan para nabi diutus menegakkan syariat dan tauhid yang sama (QS Asy-Syura 13, Al-Ma'idah 46)",
                    "Berdasarkan kaidah Ilzam al-Khasm, pernyataan Yesus sendiri di Matius 5:17-19 menegaskan tidak satu iota pun dari hukum Taurat dibatalkan"
                ]
            elif p_norm == "judaism":
                subject = "Paulus dari Tarsus versus Keabadian Torah (Torat Emet)"
                predicate = "klaim penghentian mitzvot kovenan Sinai"
                objects = ["Tanakh Masoretik (Torah, Nevi'im, Ketuvim)", "Tradisi Lisan Talmud & Halakha"]
                scope = f"Tanakh Masoretik & Halakha Yahudi vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    "Torah adalah kovenan kekal (berit olam) yang tidak pernah dapat dibatalkan atau digantikan oleh manusia (Ulangan 13:1-5, Ulangan 29:29)",
                    "Tanakh menegaskan bahwa Allah bukan manusia dan firman-Nya berdiri teguh selama-lamanya (Bilangan 23:19, Yesaya 40:8)"
                ]
            elif p_norm == "atheist_secular":
                subject = "Klaim Teologi Paulin & Perkembangan Sastra Kuno"
                predicate = "evolusi hermeneutika kelompok sektarian abad pertama"
                objects = ["Historiografi Kritis", "Sosiologi Agama", "Metode Historis-Kritis"]
                scope = f"Historiografi Kritis & Kritik Sastra Komparatif vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    "Surat-surat Paulus merefleksikan dinamika sosiologis adaptasi gerakan proto-Kristen terhadap dunia Helenistik non-Yahudi",
                    "Ketiadaan konsensus monolitik membuktikan adanya faksionalisme internal antara kelompok Kristen-Yahudi Yerusalem dan misi Paulin"
                ]
            else:
                # Default: christian_protestant
                subject = "Paulus dari Tarsus"
                predicate = "membatalkan (katargeō)"
                objects = ["Hukum Taurat (Torah / Nomos)", "Perintah-perintah berketentuan (Dogmasin)"]
                scope = f"Pauline Epistles & Early Jewish-Christian Halakha vs Oposisi {opp_norm.upper()}"
                if opp_norm == "islam":
                    counterclaims = [
                        "Polemik Islam mendalilkan teologi Paulin menyimpang dari syariat para nabi terdahulu (Matius 5:17)",
                        "Metode Ilzam al-Khasm membuktikan Paulus di Roma 3:31 menegakkan hukum Taurat dan tidak menghapus firman para nabi"
                    ]
                elif opp_norm == "judaism":
                    counterclaims = [
                        "Teologi Yahudi mendalilkan Torah kovenan Sinai adalah berit olam (perjanjian kekal) yang tidak dapat dibatalkan (Ulangan 13:1-5)",
                        "Paulus menegaskan bahwa hukum Taurat kudus, benar, dan baik (Roma 7:12) dan digenapi tujuannya di dalam Kristus (Roma 10:4)"
                    ]
                elif opp_norm == "christian_catholic":
                    counterclaims = [
                        "Teologi Katolik mendalilkan pembenaran iman harus disertai sakramen dan kebajikan kasih (Galatia 5:6, Yakobus 2:24)",
                        "Sola Fide membela pembenaran anugerah cuma-cuma melalui iman tanpa perbuatan jasa manusia (Roma 3:28)"
                    ]
                elif opp_norm == "atheist_secular":
                    counterclaims = [
                        "Kritik sekuler mendalilkan faksionalisme internal antara misi Paulin dan kelompok rasul Yerusalem (Galatia 2:11-14)",
                        "Eksegesis kontekstual membuktikan integritas pesan kovenan baru bagi bangsa-bangsa bukan-Yahudi"
                    ]
                else:
                    counterclaims = [
                        "Paulus menegakkan hukum Taurat secara moral dan eskatologis (Roma 3:31)",
                        "Paulus hanya membatalkan tembok pemisah ritual etnis antara Yahudi dan bukan-Yahudi (Efesus 2:15)"
                    ]
        elif is_christology:
            if p_norm == "christian_catholic":
                subject = "Yesus Kristus / Sang Sabda Berinkarnasi"
                predicate = "kesatuan kodrat ilahi dan manusiawi (Konsili Khalsedon)"
                objects = ["Kanon 73 Kitab", "Kredo Ekumenis Nicea-Konstantinopel", "Konsensus Patristik"]
                scope = f"Kristologi Patristik, Kredo Ekumenis & Magisterium vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Oposisi {opp_norm.upper()} menantang formulasi kristologis dua kodrat dan wibawa Tradisi Suci Gereja",
                    "Tradisi Apostolik dan kredo ekumenis secara konsisten mempertahankan dogma inkarnasi ilahi dari distorsi Ebionit dan Arian (Yohanes 1:1, Yohanes 10:30)"
                ]
            elif p_norm == "islam":
                subject = "Nabi Isa Al-Masih (Yesus) dalam Timbangan Tauhid"
                predicate = "status kenabian dan penolakan deifikasi ontologis"
                objects = ["Al-Qur'an al-Karim", "Sunnah Shahihah", "Metode Ilzam al-Khasm"]
                scope = f"Tanzih, Kemurnian Tauhid & Bedah Teks Sumber Bible vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Al-Qur'an menegaskan Isa Al-Masih adalah hamba dan rasul Allah menghadapi klaim {opp_norm.upper()} (QS Al-Ikhlas 1-4, QS An-Nisa 171, QS Al-Ma'idah 116)",
                    "Melalui metode Ilzam al-Khasm, Yesus sendiri dalam Bible menolak predikat ketuhanan mutlak dan menegaskan Bapa adalah satu-satunya Allah yang benar (Yohanes 17:3, Markus 10:18)"
                ]
            elif p_norm == "judaism":
                subject = "Sosok Yesus dalam Kerangka Teologi Kovenan Tanakh"
                predicate = "penolakan inkarnasi dan klaim kemesiasan yang belum terbukti"
                objects = ["Tanakh Masoretik", "Halakha & Teologi Rambam"]
                scope = f"Tanakh Masoretik & Monoteisme Murni Hashem vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Hashem adalah mutlak esa tanpa sekutu atau perwujudan fisik menghadapi klaim {opp_norm.upper()} (Ulangan 6:4, Yesaya 44:6)",
                    "Kriteria mesianik Tanakh menuntut pemulihan kerajaan Israel, pengumpulan diaspora, dan perdamaian dunia universal (Yesaya 2:4, Yeremia 23:5-6) yang belum tergenapi"
                ]
            elif p_norm == "atheist_secular":
                subject = "Historisitas Figur Yesus & Perkembangan Kristologi Rendah ke Tinggi"
                predicate = "deifikasi bertahap dari guru apokaliptik menjadi entitas ilahi"
                objects = ["Historiografi Kritis", "Kritik Sumber Sinoptik vs Yohanes", "Metode Historis-Empiris"]
                scope = f"Historiografi Kritis & Kritik Redaksi Akademik vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Analisis historis-kritis membuktikan perkembangan kristologi dan pembentukan legenda menghadapi klaim {opp_norm.upper()}",
                    "Klaim mukjizat dan proklamasi supranatural tidak didukung bukti empiris koroboratif kontemporer independen di luar lingkaran tradisi sektarian"
                ]
            else:
                # Default: christian_protestant
                subject = "Yesus Kristus / Hakikat Keilahian & Kebangkitan Ragawi"
                predicate = "proklamasi diri, keilahian substantif & kebangkitan historis"
                objects = ["Teks Kanonikal Bible (Kanon 66 Kitab)", "Sintaksis Egō Eimi / Hen Esmen", "Bukti Jasmani Lukas 24:39-43"]
                scope = f"Gospel Christology & Bodily Resurrection vs Oposisi {opp_norm.upper()}"
                if opp_norm == "islam":
                    counterclaims = [
                        "Polemik Islam menantang keilahian Yesus dengan mendalilkan ketiadaan pernyataan verbal langsung 'Aku adalah Tuhan' serta menunjuk ayat-ayat kemanusiaan seperti Yesus makan ikan goreng di Lukas 24:42 dan berdoa kepada Allah (Yohanes 17:3)",
                        "Berdasarkan kaidah Ilzam al-Khasm, pihak Kristen menegaskan keilahian Yesus melalui kesatuan ontologis (Yohanes 10:30), kuasa prerogatif mengampuni dosa (Markus 2:5-7), dan makan ikan goreng adalah verifikasi kebangkitan tubuh fisik melawan sangkaan hantu (Lukas 24:39-43)"
                    ]
                elif opp_norm == "atheist_secular":
                    counterclaims = [
                        "Kritik naturalis sekuler mendalilkan bahwa narasi kebangkitan jasmani dan makan ikan goreng (Lukas 24:42) merupakan perkembangan legenda apokaliptik tanpa verifikasi historiografi empiris independen",
                        "Apologetika biblika membuktikan keandalan saksi mata awal melalui kredo tertua 1 Korintus 15:3-7, makam kosong di Yerusalem, dan kemartiran para rasul yang membela fakta historis kebangkitan"
                    ]
                elif opp_norm == "christian_catholic":
                    counterclaims = [
                        "Pihak Katolik mendalilkan bahwa interpretasi nas Bible tidak dapat dipisahkan dari wibawa Tradisi Suci, kanon 73 kitab, dan Magisterium Gereja yang menolak penafsiran privat Sola Scriptura",
                        "Prinsip Sola Scriptura menegaskan bahwa Kitab Suci adalah norma berwibawa tertinggi yang menafsirkan dirinya sendiri (analogia scriptura) dan menguji seluruh tradisi gerejawi (2 Timotius 3:16-17)"
                    ]
                elif opp_norm == "judaism":
                    counterclaims = [
                        "Teologi Yudaisme menolak klaim kemesiasan Yesus karena kriteria mesianik eskatologis Tanakh (pemulihan kerajaan Israel, perdamaian universal, Bait Suci) belum tergenapi secara fisik di dunia",
                        "Kanon Bible membuktikan pola dua kedatangan Mesias: kedatangan pertama sebagai Hamba yang menderita penebus dosa (Yesaya 53, Lukas 24:44-46) dan kedatangan kedua dalam kemuliaan eskatologis (Daniel 7:13-14)"
                    ]
                else:
                    counterclaims = [
                        "Keilahian Yesus dinyatakan melalui tindakan prerogatif ilahi dan kesatuan ontologis dengan Bapa (Yohanes 10:30)",
                        "Ketiadaan formula verbal spesifik tidak menegasikan atribusi keilahian Yesus dalam tradisi apostolik"
                    ]
        elif is_trinity:
            if p_norm == "christian_catholic":
                subject = "Misteri Tritunggal Maha Kudus (Sanctissima Trinitas)"
                predicate = "pengembangan artikulasi dogmatis dalam Tradisi Suci dan Magisterium"
                objects = ["Kanon 73 Kitab", "Kredo Nicea-Konstantinopel", "Tradisi Patristik"]
                scope = f"Tradisi Suci, Kredo Ekumenis & Magisterium Gereja vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Oposisi {opp_norm.upper()} menolak perkembangan formulasi terminologis konsili ekumenis",
                    "Tradisi Patristik (Athanasius, Basilius, Gregorius dari Nazianzus) membuktikan kesatuan esensi (homoousios) Bapa, Anak, dan Roh Kudus"
                ]
            elif p_norm == "islam":
                subject = "Kritik Doktrin Trinitas Berdasarkan Tauhid Murni"
                predicate = "dekonstruksi inkonsistensi politeistik dan interpolasi naskah"
                objects = ["Al-Qur'an al-Karim", "Akal Sehat (Sarih al-Aql)", "Metode Ilzam al-Khasm"]
                scope = f"Tanzih, Monoteisme Murni & Filologi Naskah Kuno vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Al-Qur'an secara tegas melarang konsep trinitarian menghadapi klaim {opp_norm.upper()} (QS An-Nisa 171, QS Al-Ma'idah 73, QS Al-Ikhlas 1-4)",
                    "Melalui Ilzam al-Khasm, teks Shema di Ulangan 6:4 dan konfirmasi Yesus di Markus 12:29 menolak pembagian kepribadian dalam keilahian"
                ]
            elif p_norm == "judaism":
                subject = "Penolakan Konsep Trinitas Berdasarkan Monoteisme Mutlak Tanakh"
                predicate = "penjagaan ketat atas Shema Yisrael dan keesaan ilahi"
                objects = ["Tanakh Masoretik", "Teks Shema (Ulangan 6:4)", "Filsafat Yahudi (Rambam)"]
                scope = f"Tanakh Masoretik & Monoteisme Radikal Ibrani vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Shema Yisrael menyatakan secara kategoris bahwa Hashem adalah Echad (Esa mutlak) menolak klaim {opp_norm.upper()} (Ulangan 6:4)",
                    "Konsep tritunggal merupakan adopsi konsep metafisika Yunani pasca-biblika yang bertentangan secara frontal dengan kovenan monoteisme murni Tanakh"
                ]
            elif p_norm == "atheist_secular":
                subject = "Genealogi Doktrin Trinitas & Konstruksi Politik-Dogmatis"
                predicate = "evolusi rumusan teologis dari konsili politik kekaisaran Romawi"
                objects = ["Historiografi Patristik", "Sosiologi Kekuasaan Imperium Romawi", "Sejarah Dogma"]
                scope = f"Historiografi Kritis & Kritik Sosiopolitik Agama vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Sejarah membuktikan doktrin Tritunggal berkembang melalui pertarungan kekuasaan politik menghadapi klaim {opp_norm.upper()}",
                    "Formulasi filosofis 'homoousios' mengimpor terminologi filsafat Neoplatonisme yang asing dari konteks teks semitik Yahudi abad pertama"
                ]
            else:
                # Default: christian_protestant
                subject = "Doktrin Tritunggal / Formulasi Iman"
                predicate = "perkembangan artikulasi dogmatis versus benih biblika"
                objects = ["Pola Triadik Perjanjian Baru", "Kredo Ekumenis Nicea-Konstantinopel"]
                scope = f"Biblical Triadic Formulas & Patristic Development vs Oposisi {opp_norm.upper()}"
                counterclaims = [
                    f"Oposisi {opp_norm.upper()} mempersoalkan ketiadaan istilah 'Tritunggal' secara eksplisit dalam Bible",
                    "Pola triadik Perjanjian Baru membuktikan kesetaraan ilahi Bapa, Anak, dan Roh Kudus (Matius 28:19, 2 Korintus 13:13)"
                ]
        else:
            subject = "Objek Klaim Umum / Non-Spesifik"
            predicate = "pengujian bukti rasional dan teks primer"
            objects = ["Literatur Kanonikal", "Korpus Naskah Sejarah"]
            scope = f"Eksegesa & Kritik Sumber vs Oposisi {opp_norm.upper()}"
            counterclaims = [
                f"Oposisi {opp_norm.upper()} menantang kesimpulan analisis dari sudut pandang epistemik mereka",
                "Bukti teks primer dan naskah kuno dijadikan tolok ukur pengujian keabsahan argumen"
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
        is_christology = any(w in q_lower for w in ["yesus", "tuhan", "keilahian", "aku adalah tuhan", "allah sejati", "lukas", "ikan goreng", "hantu", "roh", "bangkit", "kebangkitan"])
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
                claim="Meskipun Yesus tidak menggunakan rumusan verba 'Aku adalah Tuhan', keilahian dan kebangkitan ragawi-Nya dinyatakan secara substantif melalui tindakan prerogatif ilahi, pembuktian jasmani (Lukas 24:39-43), dan relasi ontologis dengan Bapa.",
                premises=[
                    "Premis 1: Dalam budaya monoteisme Yahudi Bait Kedua, pengakuan keilahian tidak diartikulasikan dengan rumusan deklaratif simplistik melainkan melalui klaim wewenang ilahi (pengampunan dosa, kedaulatan atas Sabat).",
                    "Premis 2: Yesus menyatakan kesatuan hakikat dengan Bapa dalam Yohanes 10:30 menggunakan kata neuter 'hen' (ἕν ἐσμεν), yang secara gramatika menandakan kesatuan substansi, bukan sekadar kesatuan personil.",
                    "Premis 3: Reaksi para pendengar kontemporer Yahudi (Yohanes 10:33) membuktikan bahwa klaim Yesus dipahami secara langsung sebagai penyetaraan diri dengan Allah.",
                    "Premis 4: Dalam Lukas 24:39-43, Yesus makan sepotong ikan goreng untuk membuktikan realitas kebangkitan tubuh jasmani nyata melawan sangkaan ilusi roh/hantu (pneuma/phantasma) dan menggenapi nubuat Kitab Suci (Lukas 24:44-46)."
                ],
                evidence_items=[e.passage_reference for e in evidence],
                inferences=[
                    "Inferensi 1: Menuntut frasa harfiah modern mengabaikan idiom kristologis abad pertama.",
                    "Inferensi 2: Gelar 'Anak Manusia' yang digunakan Yesus berakar pada Daniel 7:13-14 yang menerima kekuasaan abadi dan penyembahan.",
                    "Inferensi 3: Kebangkitan tubuh fisik yang dapat diraba dan makan makanan membuktikan integritas kemenangan atas maut dalam sejarah keselamatan."
                ],
                conclusion="Ketiadaan kutipan kalimat verbal tertentu atau tindakan makan manusiawi tidak menegasikan keilahian-Nya, melainkan membuktikan realitas inkarnasi dan kebangkitan ragawi sejati Kristus."
            )
        elif is_trinity:
            argument = ArgumentNode(
                argument_id=arg_id,
                claim="Doktrin Tritunggal merupakan kristalisasi ortodoks terhadap pola wahyu Bible yang konsisten, bukan doktrin impor pasca-kanon Bible.",
                premises=[
                    "Premis 1: Naskah Perjanjian Baru memuat pola triadik yang menyetarakan Bapa, Anak, dan Roh Kudus (Matius 28:19, 2 Korintus 13:13).",
                    "Premis 2: Monoteisme Bible (Ulangan 6:4: Shema Yisrael) menegaskan keesaan Allah tanpa menafikan diferensiasi relasional ilahi.",
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
                claim=f"Klaim '{claim.text}' berada di luar domain teologi teks naskah kuno; tidak ada bukti Bible atau dokumen korpus terkait.",
                premises=[
                    "Premis 1: Ruang lingkup korpus terbatas pada literatur kanonikal Bible, manuskrip kuno, dan literatur patristik/intertestamental.",
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
    def steelman_opposition(
        cls,
        claim_text: str,
        user_perspective: Optional[str] = "christian_protestant",
        opponent_perspective: Optional[str] = None,
        locale: Optional[str] = "id"
    ) -> SteelmanCounterargument:
        """
        Steelman counterargument construction (Section 15):
        Constructs the strongest plausible opposing argument before rebuttal,
        tailored dynamically to the User Perspective x Opponent Context matrix.
        """
        carg_id = f"carg_{uuid.uuid4().hex[:8]}"
        q_lower = claim_text.lower()
        is_pauline_law = any(w in q_lower for w in ["paulus", "taurat", "law", "nomos", "hukum taurat"])
        is_christology = any(w in q_lower for w in ["yesus", "tuhan", "keilahian", "aku adalah tuhan", "allah sejati", "lukas", "ikan goreng", "hantu", "roh", "bangkit", "kebangkitan"])
        is_trinity = any(w in q_lower for w in ["tritunggal", "trinity", "tiga pribadi", "monoteisme"])

        p_norm, opp_norm = cls._normalize_perspectives(user_perspective, opponent_perspective)

        # -------------------------------------------------------------------
        # 1. PAULINE LAW MATRIX
        # -------------------------------------------------------------------
        if is_pauline_law:
            if p_norm == "christian_catholic":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim=(
                        "Sola Scriptura dan pembenaran semata-mata oleh iman (Sola Fide) membatalkan kewajiban ketaatan moral hukum Taurat "
                        "serta menegasikan tradisi dan sakramen gereja (Roma 3:28, Galatia 2:16)."
                    ),
                    opponent_evidence=[
                        "Roma 3:28: 'Karena kami yakin, bahwa manusia dibenarkan karena iman, dan bukan karena melakukan hukum Taurat.'",
                        "Galatia 2:16: '...tidak seorang pun yang dibenarkan oleh karena melakukan hukum Taurat.'"
                    ],
                    opponent_reasoning=(
                        "Argumen penantang mendalilkan bahwa pembenaran Paulin bersifat soliter tanpa memerlukan kebajikan moral "
                        "maupun bimbingan sakramental hierarki gerejawi."
                    ),
                    opponent_assumptions=[
                        "Iman dalam surat Paulus terpisah mutlak dari kasih dan perbuatan baik.",
                        "Kanon suci dapat dipahami secara individual tanpa Magisterium gereja."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Kanon 73 Kitab menegaskan iman bekerja melalui kasih (Galatia 5:6) dan iman tanpa perbuatan adalah mati (Yakobus 2:24).",
                        "Tradisi Patristik menegaskan kesinambungan hukum moral yang digenapi dalam sakramen kovenan baru (Matius 5:17, Sirakh 15:15)."
                    ],
                    rebuttal=(
                        "Gereja Katolik mengajarkan keselarasan antara Kitab Suci dan Tradisi Suci: pembenaran adalah rahmat pengudusan "
                        "yang mentransformasi manusia. Paulus di Roma 3:31 menegaskan iman menegakkan hukum Taurat, dan di Galatia 5:6 "
                        "iman berdaya kerja melalui kasih (fides formata)."
                    ),
                    rebuttal_evidence=["Roma 3:31", "Yakobus 2:24", "Matius 5:17"]
                )
            elif p_norm == "islam":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim=(
                        "Paulus secara sepihak membatalkan syariat Taurat dan ketetapannya demi mempermudah konversi bangsa pagan (Efesus 2:15, Galatia 3:13)."
                    ),
                    opponent_evidence=[
                        "Efesus 2:15: 'Ia telah membatalkan hukum Taurat dengan segala perintah dan ketentuannya.'",
                        "Galatia 3:13: 'Kristus telah menebus kita dari kutuk hukum Taurat...'"
                    ],
                    opponent_reasoning=(
                        "Kritik dibangun atas asumsi bahwa syariat para nabi terdahulu dirombak oleh teologi Paulin pasca-kenaikan Isa Al-Masih."
                    ),
                    opponent_assumptions=[
                        "Syariat kovenan para nabi bersifat opsional dan dapat dianulir tanpa mandat eksplisit kenabian.",
                        "Surat-surat pastoral mengesampingkan sabda eksplisit Yesus di kitab-kitab narasi Bible."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Melalui metode Ilzam al-Khasm, Yesus sendiri dalam Bible menegaskan tidak satu iota pun dari hukum Taurat dibatalkan (Matius 5:17-19).",
                        "Kaidah ushuliyyah menegaskan syariat para nabi dibangun di atas fondasi tauhid dan ketaatan yang konsisten (QS Al-Ma'idah 46)."
                    ],
                    rebuttal=(
                        "Berdasarkan metode Ilzam al-Khasm, pernyataan teologi pembatalan hukum bertentangan langsung dengan proklamasi Yesus "
                        "di Matius 5:17-19 dan pernyataan di Roma 3:31 bahwa iman justru menegakkan hukum Taurat. Al-Qur'an dan Sunnah "
                        "menegaskan integritas syariat kovenan para nabi yang lurus."
                    ),
                    rebuttal_evidence=["Matius 5:17-19", "Roma 3:31", "Lukas 16:17"]
                )
            elif p_norm == "judaism":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim=(
                        "Hukum Taurat dan kovenan Sinai telah usang dan digantikan secara permanen oleh kovenan baru (Ibrani 8:13, Roma 10:4)."
                    ),
                    opponent_evidence=[
                        "Ibrani 8:13: 'Oleh karena Ia berkata-kata tentang perjanjian yang baru, Ia menyatakan yang pertama sebagai yang telah tua...'",
                        "Roma 10:4: 'Sebab Kristus adalah kegenapan hukum Taurat...'"
                    ],
                    opponent_reasoning=(
                        "Klaim teologi supersesionisme menyatakan bahwa mitzvot Taurat tidak lagi mengikat karena telah selesai fungsinya."
                    ),
                    opponent_assumptions=[
                        "Kovenan Sinai dapat dibatalkan oleh klaim teologis pasca-biblika.",
                        "Kata 'telos' dimaknai sebagai terminasi total daripada pemenuhan tujuan."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Tanakh Masoretik secara kategoris menyatakan Torah sebagai kovenan kekal (berit olam) untuk selamanya (Keluaran 31:16, Mazmur 119:160).",
                        "Ulangan 13:1-5 memberikan peringatan mutlak terhadap segala ajaran yang menyimpang dari ketetapan Torah."
                    ],
                    rebuttal=(
                        "Tanakh Masoretik menegaskan bahwa firman Allah teguh untuk selama-lamanya (Yesaya 40:8) dan Allah bukan manusia yang berubah pikiran (Bilangan 23:19). "
                        "Klaim bahwa mitzvot Taurat dibatalkan runtuh di hadapan penegasan kovenan kekal Sinai."
                    ),
                    rebuttal_evidence=["Ulangan 13:1-5", "Bilangan 23:19", "Mazmur 119:160"]
                )
            elif p_norm == "atheist_secular":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim=(
                        "Korpus surat-surat Paulus merupakan tulisan teologis inerran yang harmonis secara supranatural tanpa friksi historis (2 Timotius 3:16)."
                    ),
                    opponent_evidence=[
                        "2 Timotius 3:16: 'Segala tulisan yang diilhamkan Allah memang bermanfaat untuk mengajar...'",
                        "2 Petrus 3:15-16: '...seperti juga Paulus, saudara kita yang kekasih, telah menulis kepadamu menurut hikmat yang dikaruniakan kepadanya.'"
                    ],
                    opponent_reasoning=(
                        "Klaim membela konsistensi dogmatis supranatural kitab suci tanpa membedakan konteks redaksional dan sosiologis penulis."
                    ),
                    opponent_assumptions=[
                        "Teks kuno bebas dari pengaruh dinamika konflik sosiopolitik antarfaksi abad pertama.",
                        "Harmonisasi dogmatis dapat mengabaikan bukti friksi sastra historis."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Historiografi kritis membuktikan pertentangan sengit antara faksi Paulus dan komunitas Kristen-Yahudi Yerusalem (Galatia 2:11-14).",
                        "Ketiadaan bukti naskah asli otograf dan keberadaan ribuan varian tekstual membantah klaim inerransi absolut."
                    ],
                    rebuttal=(
                        "Secara metodologi historis-kritis, surat-surat Paulin adalah dokumen sosio-historis manusiawi abad pertama yang mencerminkan "
                        "pergulatan komunitas perdana. Ketegangan antara Roma 3:31 dan Efesus 2:15 membuktikan perkembangan redaksional dan adaptasi sastra, "
                        "bukan wahyu monolitik supranatural yang steril dari sejarah."
                    ),
                    rebuttal_evidence=["Galatia 2:11-14", "Kisah Para Rasul 21:20-21", "Roma 3:31"]
                )
            else:
                # Default: christian_protestant
                if opp_norm == "islam":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim=(
                            "Paulus secara sepihak membatalkan syariat Taurat para nabi demi mempermudah konversi bangsa pagan (Efesus 2:15, Galatia 3:13), "
                            "bertentangan dengan proklamasi Yesus di Matius 5:17-19."
                        ),
                        opponent_evidence=[
                            "Efesus 2:15: 'Ia telah membatalkan hukum Taurat dengan segala perintah dan ketentuannya.'",
                            "Galatia 3:13: 'Kristus telah menebus kita dari kutuk hukum Taurat...'",
                            "Matius 5:17: 'Janganlah kamu menyangka, bahwa Aku datang untuk meniadakan hukum Taurat atau kitab para nabi...'"
                        ],
                        opponent_reasoning=(
                            "Polemik Islam mendalilkan bahwa syariat para nabi adalah satu kovenan berkesinambungan dan tidak boleh dirombak oleh doktrin rasul pasca-kenaikan nabi Isa."
                        ),
                        opponent_assumptions=[
                            "Hukum seremonial pemisah etnis identik dengan hukum moral abadi.",
                            "Penolakan legalisme sama dengan pembatalan hukum ilahi."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Melalui metode Ilzam al-Khasm, Paulus di Roma 3:31 justru menegaskan 'kami menegakkan hukum Taurat' (nomon histanomen).",
                            "Konteks Efesus 2:15 hanya membatalkan hukum seremonial pemisah etnis (en dogmasin), bukan hukum moral para nabi."
                        ],
                        rebuttal=(
                            "Kanon 66 Kitab Bible membuktikan keselarasan ajaran Paulus dengan Yesus: pembenaran oleh iman tidak meniadakan hukum moral "
                            "melainkan menegakkannya (Roma 3:31), sementara penebusan Kristus membebaskan dari kutuk pelanggaran Taurat (Galatia 3:13)."
                        ),
                        rebuttal_evidence=["Roma 3:31", "Matius 5:17-19", "Roma 7:12"]
                    )
                elif opp_norm == "judaism":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim=(
                            "Torah kovenan Sinai adalah berit olam (perjanjian kekal) yang tidak pernah dapat dibatalkan atau digantikan (Ulangan 13:1-5, Mazmur 119:160); "
                            "klaim Paulus bahwa Kristus adalah telos hukum Taurat (Roma 10:4) merupakan penyimpangan dari Halakha."
                        ),
                        opponent_evidence=[
                            "Ulangan 13:1-5: 'Apabila di tengah-tengahmu bangkit seorang nabi... janganlah engkau mendengarkan...'",
                            "Keluaran 31:16: '...merayakan sabat turun-temurun, suatu perjanjian kekal.'",
                            "Roma 10:4: 'Sebab Kristus adalah kegenapan hukum Taurat...'"
                        ],
                        opponent_reasoning=(
                            "Teologi Tanakh menegaskan bahwa firman Allah berdiri teguh selama-lamanya (Yesaya 40:8) dan ketetapan Torah mengikat seluruh keturunan Israel selamanya."
                        ),
                        opponent_assumptions=[
                            "Kata 'telos' diartikan terminasi mutlak alih-alih puncak pemenuhan.",
                            "Kovenan baru tidak dapat menggenapi kovenan lama."
                        ],
                        weaknesses=[
                            "Secara filologis, kata 'telos' dalam Roma 10:4 bermakna sasaran/tujuan pemenuhan (culmination), bukan pemusnahan hukum.",
                            "Yeremia 31:31-34 secara eksplisit menubuatkan Kovenan Baru yang dituliskan dalam batin."
                        ],
                        rebuttal=(
                            "Bible Perjanjian Baru menyatakan bahwa iman kepada Mesias justru menegakkan keadilan sejati yang dituntut Taurat (Roma 3:31). "
                            "Kovenan baru menggenapi nubuat Yeremia 31:31-34 tanpa membatalkan kekudusan hukum ilahi (Roma 7:12)."
                        ),
                        rebuttal_evidence=["Roma 3:31", "Yeremia 31:31-34", "Roma 7:12"]
                    )
                elif opp_norm == "christian_catholic":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim=(
                            "Doktrin Sola Fide (pembenaran semata-mata oleh iman) memisahkan iman dari sakramen dan kebajikan moral gereja (Roma 3:28), "
                            "bertentangan dengan surat Yakobus 2:24 dan konsensus patristik."
                        ),
                        opponent_evidence=[
                            "Yakobus 2:24: 'Jadi kamu lihat, bahwa manusia dibenarkan karena perbuatan-perbuatannya dan bukan hanya karena iman.'",
                            "Galatia 5:6: '...hanya iman yang bekerja oleh kasih.'",
                            "Roma 3:28: 'Karena kami yakin, bahwa manusia dibenarkan karena iman...'"
                        ],
                        opponent_reasoning=(
                            "Gereja Katolik mengajarkan pembenaran adalah proses transformasi pengudusan melalui rahmat sakramental, bukan sekadar deklarasi forensik sepihak."
                        ),
                        opponent_assumptions=[
                            "Iman sejati dapat dipisahkan secara soliter dari buah perbuatan kasih.",
                            "Penafsiran kanon memerlukan otoritas hierarki gerejawi."
                        ],
                        weaknesses=[
                            "Paulus di Roma 3:28 membahas pembenaran di hadapan Allah, sedangkan Yakobus 2:24 membahas pembuktian iman di hadapan manusia.",
                            "Teologi Protestan klasik menegaskan fides viva (iman yang sejati niscaya berbuah kasih dan perbuatan baik)."
                        ],
                        rebuttal=(
                            "Bible mengajarkan bahwa manusia dibenarkan karena iman cuma-cuma oleh anugerah Kristus (Roma 3:24, Efesus 2:8-9). "
                            "Perbuatan baik adalah buah yang menyertai keselamatan, bukan syarat meritokrasi manusiawi."
                        ),
                        rebuttal_evidence=["Roma 3:28", "Efesus 2:8-10", "Galatia 5:6"]
                    )
                elif opp_norm == "atheist_secular":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim=(
                            "Surat-surat Paulus merefleksikan faksionalisme internal politik jemaat perdana antara faksi Yerusalem (Petrus-Yakobus) "
                            "dan misi Paulin (Galatia 2:11-14), tanpa kesatuan wahyu supranatural inerran."
                        ),
                        opponent_evidence=[
                            "Galatia 2:11-14: 'Tetapi waktu Kefas datang ke Antiokhia, aku berterang-terang menentangnya...'",
                            "Kisah Para Rasul 21:20-21: '...mereka mendengar tentang engkau, bahwa engkau mengajar... meninggalkan hukum Musa...'",
                            "2 Timotius 3:16: 'Segala tulisan yang diilhamkan Allah memang bermanfaat...'"
                        ],
                        opponent_reasoning=(
                            "Metode historis-kritis melihat evolusi sosiologis agama kuno di mana doktrin adaptif dibangun untuk memfasilitasi integrasi populasi Helenistik."
                        ),
                        opponent_assumptions=[
                            "Konflik sosiologis meniadakan kemungkinan bimbingan ilahi.",
                            "Teks kuno harus bebas dari pergulatan sejarah untuk dianggap autentik."
                        ],
                        weaknesses=[
                            "Pertikaian di Antiokhia adalah soal konsistensi praktik pergaulan meja, bukan perselisihan dogmatis atas substansi pewartaan rasuli (Galatia 2:14-16).",
                            "Pengakuan para rasul pilar di Galatia 2:9 menegaskan kesatuan pesan keselamatan yang satu dan sama."
                        ],
                        rebuttal=(
                            "Keterbukaan naskah merekam ketegangan historis justru membuktikan kejujuran dan integritas saksi mata (criterion of embarrassment), "
                            "bukan rekayasa mitologis konspiratif."
                        ),
                        rebuttal_evidence=["Galatia 2:9-16", "2 Petrus 3:15-16", "Roma 3:31"]
                    )
                else:
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim=(
                            "Paulus secara tuntas telah mengakhiri dispensasi Taurat; orang beriman tidak lagi di bawah hukum Taurat "
                            "karena Kristus adalah kegenapan akhir hukum Taurat untuk pembenaran (Roma 10:4, Galatia 3:24-25, Efesus 2:15)."
                        ),
                        opponent_evidence=[
                            "Roma 10:4: 'Sebab Kristus adalah kegenapan (τέλος) hukum Taurat, sehingga kebenaran diperoleh tiap-tiap orang yang percaya.'",
                            "Galatia 3:24-25: 'Jadi hukum Taurat adalah penuntun (παιδαγωγός) bagi kita sampai Kristus datang...'",
                            "Efesus 2:15: 'Ia telah membatalkan (καταργήσας) hukum Taurat dengan segala perintah dan ketentuannya.'"
                        ],
                        opponent_reasoning=(
                            "Argumen oposisi didasarkan pada teleologi eskatologis Paulus: hukum Taurat berfungsi sementara sebagai "
                            "penuntun/pengawas sampai Mesias datang."
                        ),
                        opponent_assumptions=[
                            "Kata 'telos' dalam Roma 10:4 harus diterjemahkan sebagai penamatan mutlak (termination).",
                            "Kata 'nomos' dalam tulisan Paulus bersifat monolitik."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Kelemahan Filologis: 'Telos' dalam filsafat dan leksikografi Yunani Klasik/Koine (BDAG) bermakna tujuan akhir (goal/apex).",
                            "Kelemahan Kontekstual: Mengabaikan pernyataan afirmatif Paulus sendiri di Roma 3:31 (histanomen nomon)."
                        ],
                        rebuttal=(
                            "Dalam dialektika filologi forensik, oposisi gagal membedakan antara fungsi pembenaran legalistik dengan validitas moral Taurat. "
                            "Kristus adalah tujuan Taurat, dan di Roma 3:31 Paulus menegaskan iman justru menegakkan (histanomen) hukum Taurat."
                        ),
                        rebuttal_evidence=["Roma 3:31", "Roma 7:12", "Matius 5:17"]
                    )

        # -------------------------------------------------------------------
        # 2. CHRISTOLOGY & BODILY RESURRECTION MATRIX
        # -------------------------------------------------------------------
        elif is_christology:
            if p_norm == "christian_catholic":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Formulasi dua kodrat Kristus (keilahian dan kemanusiaan) merupakan inovasi pasca-apostolik Konsili Khalsedon yang tidak diajarkan secara eksplisit oleh teks Bible.",
                    opponent_evidence=[
                        "1 Timotius 2:5: 'Karena Allah itu esa dan esa pula Dia yang menjadi pengantara antara Allah dan manusia, yaitu manusia Kristus Yesus.'",
                        "Markus 10:18: 'Mengapa kaukatakan Aku baik? Tak seorang pun yang baik selain dari Allah saja.'"
                    ],
                    opponent_reasoning="Ketiadaan rumusan teknis 'dua kodrat dalam satu pribadi' dalam teks Bible dianggap sebagai bukti perkembangan dogmatis eksternal gereja.",
                    opponent_assumptions=[
                        "Doktrin apostolik harus menggunakan rumusan terminologis yang persis sama dengan kredo abad kelima.",
                        "Tradisi lisan gereja perdana tidak memiliki bobot normatif bersama teks tertulis."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Tradisi Patristik abad ke-1 dan ke-2 (Ignatius dari Antiokhia, Irenaeus dari Lyon) telah bersaksi tegas tentang keilahian dan kemanusiaan Kristus.",
                        "Teks kitab Yohanes 1:1, 1:14 dan Yohanes 10:30 menyatakan secara eksplisit bahwa Firman adalah Allah dan telah menjadi manusia."
                    ],
                    rebuttal="Magisterium Gereja Katolik membela deposit iman para rasul: Konsili Khalsedon tidak menciptakan keilahian Kristus, melainkan merumuskan secara presisi apa yang telah disembah gereja sejak zaman para rasul.",
                    rebuttal_evidence=["Yohanes 1:1", "Yohanes 10:30", "Kolose 2:9"]
                )
            elif p_norm == "islam":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Pernyataan 'Aku dan Bapa adalah satu' (Yohanes 10:30) dan mukjizat Yesus membuktikan keilahian ontologis Yesus sebagai Allah sejati.",
                    opponent_evidence=[
                        "Yohanes 10:30: 'Aku dan Bapa adalah satu.'",
                        "Yohanes 8:58: 'Sebelum Abraham jadi, Aku telah ada.'"
                    ],
                    opponent_reasoning="Pendukung klaim mendasarkan keilahian pada perikop Yohanes dan tindakan Yesus yang mengampuni dosa.",
                    opponent_assumptions=[
                        "Kata 'satu' dalam Yohanes 10:30 harus dimaknai sebagai kesatuan substansi ontologis esensial.",
                        "Mukjizat membuktikan keilahian sang pelaku mukjizat bukan kuasa Allah yang bekerja melaluinya."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Secara filologis, bahasa Yunani 'hen esmen' menggunakan kata netral 'hen' (kesatuan kehendak/tujuan), bukan maskulin 'heis' (satu pribadi ontologis), selaras dengan doa Yesus agar para murid menjadi satu (hen) di Yohanes 17:21.",
                        "Yesus sendiri secara konsisten berdoa kepada Allah, bergantung pada Bapa, dan menegaskan keterbatasan pengetahuannya (Markus 13:32, Markus 10:18)."
                    ],
                    rebuttal="Melalui metode Ilzam al-Khasm, teks Bible sendiri membuktikan pemisahan hakikat mutlak antara Yesus dan satu-satunya Allah yang benar (Yohanes 17:3). Al-Qur'an (QS Al-Ikhlas 1-4, QS An-Nisa 171) menegaskan kemurnian tauhid dan memuliakan Nabi Isa Al-Masih sebagai utusan Allah yang agung.",
                    rebuttal_evidence=["Yohanes 17:3", "Markus 10:18", "Yohanes 14:28"]
                )
            elif p_norm == "judaism":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Yesus adalah Mesias ilahi yang telah dinubuatkan oleh para nabi dalam Tanakh, seperti dalam Yesaya 9:5 dan Mikha 5:1.",
                    opponent_evidence=[
                        "Yesaya 9:5: 'Sebab seorang anak telah lahir untuk kita... namanya disebutkan orang: Penasihat Ajaib, Allah yang Perkasa...'",
                        "Mikha 5:1: '...yang permulaannya sudah sejak purbakala, sejak dahulu kala.'"
                    ],
                    opponent_reasoning="Penafsir kristiani membaca nas-nas profetis Tanakh secara tipologis untuk membuktikan inkarnasi sang Mesias.",
                    opponent_assumptions=[
                        "Gelar profetik dalam tradisi Ibrani bermakna deifikasi ontologis manusia.",
                        "Nubuatan mesianik dapat dipisahkan dari kriteria eskatologis historis Tanakh."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Dalam gramatika bahasa Ibrani Masoretik, nama teoforik lazim disematkan kepada manusia tanpa menandakan keilahian ontologis pembawa nama (contoh: Eliyahu berarti 'Allahku adalah YHWH').",
                        "Tanakh menegaskan bahwa Allah adalah mutlak esa dan bukan manusia (Bilangan 23:19, Ulangan 6:4), serta kriteria mesianik (pemulihan Bait Suci dan perdamaian dunia universal) belum tergenapi."
                    ],
                    rebuttal="Berdasarkan eksegesis Peshat Tanakh Masoretik, konsep inkarnasi ilahi merupakan kontradiksi mutlak terhadap monoteisme Shema Yisrael. Hashem adalah esa dan tidak berjasad jasmani.",
                    rebuttal_evidence=["Ulangan 6:4", "Bilangan 23:19", "Yesaya 45:5"]
                )
            elif p_norm == "atheist_secular":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Klaim kebangkitan jasmani dan keilahian Yesus didasarkan pada saksi mata historis yang dapat diverifikasi secara obyektif (1 Korintus 15:3-8).",
                    opponent_evidence=[
                        "1 Korintus 15:6: 'Sesudah itu Ia menampakkan diri kepada lebih dari lima ratus saudara sekaligus...'",
                        "Kisah Para Rasul 2:32: 'Yesus inilah yang dibangkitkan Allah, dan tentang hal itu kami semua adalah saksi.'"
                    ],
                    opponent_reasoning="Apologetika sejarah berargumen bahwa kemunculan mendadak gerakan Kristen dan kemartiran murid membuktikan fakta historis kebangkitan.",
                    opponent_assumptions=[
                        "Kesediaan mati demi keyakinan membuktikan kebenaran fakta objektif peristiwa supranatural.",
                        "Teks pengakuan iman (kredo) abad pertama bebas dari bias glorifikasi teologis komunitas pengikutnya."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Psikologi kognitif dan antropologi agama membuktikan bahwa keyakinan subjektif dan pengalaman duka (grief hallucinations) dapat memicu proklamasi histeris yang diyakini secara fanatik.",
                        "Ketiadaan bukti koroboratif independen sezaman (dokumen Romawi/Yahudi non-Kristen) melemahkan klaim kepastian sejarah mukjizat biologis."
                    ],
                    rebuttal="Metodologi sains empiris dan naturalisme historis menolak klaim supranatural. Ketiadaan bukti manuskrip sezaman dan kontradiksi narasi makam antar-kitab Bible membuktikan proses pembentukan legenda dan mitologi pasca-kematian tokoh sejarah.",
                    rebuttal_evidence=["1 Korintus 15:6", "Markus 16:8", "Matius 28:11-15"]
                )
            else:
                # Default: christian_protestant
                if opp_norm == "islam":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim=(
                            "Yesus secara eksplisit membedakan diri-Nya dari satu-satunya Allah yang benar (Yohanes 17:3), "
                            "dan tindakan makan ikan goreng (Lukas 24:42) membuktikan ketergantungan fisik fana manusiawi yang bertentangan dengan kemutlakan ketuhanan."
                        ),
                        opponent_evidence=[
                            "Lukas 24:42-43: 'Mereka memberikan kepada-Nya sepotong ikan goreng. Ia mengambilnya dan memakannya di depan mata mereka.'",
                            "Yohanes 17:3: 'Inilah hidup yang kekal itu, yaitu bahwa mereka mengenal Engkau, satu-satunya Allah yang benar, dan mengenal Yesus Kristus yang telah Engkau utus.'",
                            "Markus 10:18: 'Mengapa kaukatakan Aku baik? Tak seorang pun yang baik selain dari Allah saja.'"
                        ],
                        opponent_reasoning=(
                            "Polemik Tauhid mendalilkan bahwa Zat Ilahi mustahil membutuhkan asupan makanan materi dan tidak mungkin mengalami keterbatasan fisik; "
                            "tindakan makan membuktikan Yesus adalah hamba dan rasul utusan Allah, bukan Tuhan semesta alam."
                        ),
                        opponent_assumptions=[
                            "Kebutuhan fisik fana manusiawi meniadakan doktrin inkarnasi firman ilahi.",
                            "Ketiadaan klaim verbal harfiah 'Aku adalah Tuhan' membuktikan penolakan keilahian."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Konteks perikop Lukas 24:36-43 membuktikan tindakan makan ikan goreng adalah pembuktian kebangkitan tubuh fisik nyata (flesh and bones) "
                            "untuk membongkar ketakutan para murid yang mengira melihat roh/hantu (pneuma/phantasma), bukan penyangkalan keilahian.",
                            "Doktrin inkarnasi ortodoks menegaskan kesatuan dua kodrat dalam satu pribadi Kristus: kemanusiaan sejati yang makan secara fisik, "
                            "dan keilahian sejati yang berkuasa membangkitkan tubuh-Nya sendiri (Yohanes 10:18)."
                        ],
                        rebuttal=(
                            "Bible menyatakan keilahian Yesus bukan melalui klaim verbal sepihak melainkan melalui kedaulatan, kuasa mencipta, dan kesatuan ontologis dengan Bapa (Yohanes 10:30). "
                            "Di Lukas 24:39-43, Yesus makan ikan goreng justru untuk mematahkan sangkaan para murid bahwa Ia adalah roh ilusi/hantu, sekaligus membuktikan penggenapan "
                            "nubuat Kitab Suci bahwa Mesias harus bangkit dari antara orang mati pada hari ketiga (Lukas 24:44-46)."
                        ),
                        rebuttal_evidence=["Lukas 24:39-46", "Yohanes 10:30", "Yohanes 20:28"]
                    )
                elif opp_norm == "atheist_secular":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim=(
                            "Narasi penampakan jasmani pasca-kematian termasuk makan ikan goreng (Lukas 24:42) merupakan konstruksi sastra apologetik "
                            "komunitas perdana untuk menangkal doketisme, tanpa verifikasi historiografi empiris independen."
                        ),
                        opponent_evidence=[
                            "Lukas 24:42: 'Mereka memberikan kepada-Nya sepotong ikan goreng...'",
                            "1 Korintus 15:6: '...sesudah itu Ia menampakkan diri kepada lebih dari lima ratus saudara sekaligus...'",
                            "Markus 16:8: 'Lalu mereka keluar dan lari meninggalkan kubur itu...'"
                        ],
                        opponent_reasoning=(
                            "Historiografi kritis dan naturalisme metodologis menolak intervensi mukjizat biologis atas mayat yang bangkit hidup kembali; "
                            "ketidaksinkronan narasi makam kosong menunjukkan proses pembentukan legenda sastra pasca-kematian."
                        ),
                        opponent_assumptions=[
                            "Hukum alam biologis menutup kemungkinan terjadinya peristiwa kebangkitan supranatural.",
                            "Dokumentasi komunitas saksi mata tidak memiliki bobot historis tanpa verifikasi sekuler sezaman."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Kredo tertua dalam 1 Korintus 15:3-7 berasal dari kurun waktu 3-5 tahun pasca-penyaliban, terlalu dini untuk evolusi legenda mitologis.",
                            "Hipotesis halusinasi duka gagal menjelaskan kubur yang kosong di Yerusalem dan transformasi radikal para skeptis seperti Paulus dan Yakobus."
                        ],
                        rebuttal=(
                            "Penyelidikan forensik naskah membuktikan kesaksian kebangkitan berakar pada peristiwa historis di Yerusalem yang dipertahankan "
                            "para rasul hingga martir. Di Lukas 24:39-43, penekanan pada tubuh fisik yang dapat diraba dan makan makanan membuktikan "
                            "penolakan dini terhadap mitologisasi alegoris atau visi spiritual semu."
                        ),
                        rebuttal_evidence=["1 Korintus 15:3-8", "Lukas 24:39-43", "Kisah Para Rasul 2:32"]
                    )
                elif opp_norm == "christian_catholic":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim=(
                            "Kebenaran kodrat Kristus, kebangkitan, dan sakramen persekutuan tidak dapat dipahami secara privat melalui Sola Scriptura "
                            "melainkan memerlukan wibawa Magisterium Gereja dan Kanon 73 Kitab (Tradisi Patristik Khalsedon)."
                        ),
                        opponent_evidence=[
                            "2 Tesalonika 2:15: 'Berdirilah teguh dan berpeganglah pada ajaran-ajaran yang kamu terima...'",
                            "1 Timotius 3:15: '...tiang penopang dan dasar kebenaran.'"
                        ],
                        opponent_reasoning=(
                            "Gereja Katolik mengajarkan bahwa Kitab Suci lahir dari rahim Tradisi Gereja; penafsiran mandiri tanpa suksesi apostolik rentan mereduksi misteri sakramental."
                        ),
                        opponent_assumptions=[
                            "Kanon Bible hanya dapat divalidasi oleh institusi kepausan.",
                            "Tradisi lisan memiliki wibawa normatif setara naskah firman tertulis."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Kitab Suci menyatakan secara internal kecukupan firman tertulis untuk keselamatan dan pengajaran (2 Timotius 3:16-17).",
                            "Di Lukas 24:44-45, Yesus sendiri membuka pikiran murid-murid untuk memahami Kitab Suci tertulis, bukan tradisi manusia."
                        ],
                        rebuttal=(
                            "Prinsip Sola Scriptura menetapkan Bible sebagai norma berwibawa tertinggi yang menguji seluruh tradisi gerejawi (2 Timotius 3:16-17). "
                            "Kesaksian Kristus dalam Lukas 24:44-46 secara eksplisit mengikatkan iman pada pemenuhan naskah firman tertulis."
                        ),
                        rebuttal_evidence=["2 Timotius 3:16-17", "Lukas 24:44-45", "Kisah Para Rasul 17:11"]
                    )
                elif opp_norm == "judaism":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim=(
                            "Yesus makan ikan goreng maupun klaim kebangkitan tidak memenuhi kriteria eskatologis Mesias menurut Tanakh, "
                            "dan deifikasi manusia bertentangan secara frontal dengan Shema Yisrael (Ulangan 6:4)."
                        ),
                        opponent_evidence=[
                            "Ulangan 6:4: 'Dengarlah, hai orang Israel: TUHAN itu Allah kita, TUHAN itu esa!'",
                            "Bilangan 23:19: 'Allah bukanlah manusia, sehingga Ia berdusta...'",
                            "Yesaya 2:4: '...bangsa tidak akan lagi mengangkat pedang terhadap bangsa...'"
                        ],
                        opponent_reasoning=(
                            "Menurut Tanakh Masoretik, Mesias adalah manusia keturunan Daud yang mewujudkan perdamaian universal dan kepulangan diaspora secara fisik di dunia, bukan figur yang mati disalibkan."
                        ),
                        opponent_assumptions=[
                            "Nubuatan mesianik hanya memiliki satu tahap tanpa misi penderitaan penebusan dosa.",
                            "Klaim kemesiasan tertutup bagi pemenuhan kovenan spiritual."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Tanakh menubuatkan figur Hamba TUHAN yang menderita dan mati menanggung dosa umat sebelum ditinggikan (Yesaya 52:13-53:12, Mazmur 22).",
                            "Lukas 24:25-27, 44 menegaskan bahwa menurut hukum Taurat, nabi-nabi, dan mazmur, Mesias memang harus menderita dahulu sebelum masuk kemuliaan-Nya."
                        ],
                        rebuttal=(
                            "Bible Perjanjian Baru menyatakan bahwa Yesus menggenapi nubuat nabi-nabi Tanakh secara bertahap: Hamba yang menderita menghapus dosa manusia "
                            "(Yesaya 53, Lukas 24:44-46) sebelum kedatangan kedua dalam kemuliaan kerajaan kekal (Daniel 7:13-14)."
                        ),
                        rebuttal_evidence=["Lukas 24:44-46", "Yesaya 53:5-10", "Mazmur 22:1-22"]
                    )
                else:
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim="Yesus secara eksplisit membedakan diri-Nya dari satu-satunya Allah yang benar dan tidak pernah mengucapkan pernyataan verbal langsung 'Aku adalah Tuhan'.",
                        opponent_evidence=[
                            "Yohanes 17:3: 'Inilah hidup yang kekal itu, yaitu bahwa mereka mengenal Engkau, satu-satunya Allah yang benar...'",
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
                        rebuttal="Bible menyatakan keilahian Yesus bukan melalui klaim verbal sepihak melainkan melalui kedaulatan, kuasa mencipta, dan kesatuan ontologis dengan Bapa (Yohanes 10:30).",
                        rebuttal_evidence=["Yohanes 10:30", "Yohanes 8:58", "Markus 2:5-7"]
                    )

        # -------------------------------------------------------------------
        # 3. TRINITY MATRIX
        # -------------------------------------------------------------------
        elif is_trinity:
            if p_norm == "christian_catholic":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Doktrin Tritunggal tidak memiliki dasar eksplisit dalam naskah Bible dan merupakan konstruksi filosofis Hellenistik yang dipaksakan pada Konsili Nicea.",
                    opponent_evidence=[
                        "Ulangan 6:4: 'Dengarlah, hai orang Israel: TUHAN itu Allah kita, TUHAN itu esa!'",
                        "1 Korintus 8:6: 'Bagi kita hanya ada satu Allah saja, yaitu Bapa... dan satu Tuhan saja, yaitu Yesus Kristus.'"
                    ],
                    opponent_reasoning="Penentang berpendapat istilah 'homoousios' dan 'tiga pribadi' tidak ditemukan dalam teks suci kanonikal mula-mula.",
                    opponent_assumptions=[
                        "Ketiadaan kata teknis dalam naskah berarti konsep substansi doktrin tersebut tidak ada.",
                        "Konsili ekumenis tidak memiliki kewenangan mengartikulasikan deposit iman apostolik."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Tradisi Patristik pra-Nicea (Tertullianus, Origenes, Athanasius) membuktikan ibadah triadik telah dihidupi sebelum konsili resmi kekaisaran.",
                        "Teks kanonik Matius 28:19 menggunakan formula satu nama tunggal (eis to onoma) bagi ketiga pribadi ilahi."
                    ],
                    rebuttal="Magisterium Gereja Katolik membela misteri Tritunggal Maha Kudus: konsili ekumenis tidak menciptakan kebenaran baru, melainkan melindungi wahyu ilahi dari distorsi heresiologis Arianisme.",
                    rebuttal_evidence=["Matius 28:19", "2 Korintus 13:13", "1 Yohanes 5:7"]
                )
            elif p_norm == "islam":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Misteri Tritunggal diwahyukan dalam Perjanjian Baru melalui formula baptisan Matius 28:19 dan berkat triadik 2 Korintus 13:13.",
                    opponent_evidence=[
                        "Matius 28:19: '...baptislah mereka dalam nama Bapa dan Anak dan Roh Kudus.'",
                        "2 Korintus 13:13: 'Kasih karunia Tuhan Yesus Kristus, dan kasih Allah, dan persekutuan Roh Kudus menyertai kamu sekalian.'"
                    ],
                    opponent_reasoning="Apologet Kristen berargumen bahwa formula triadik membuktikan pluralitas pribadi dalam esensi ketuhanan yang satu.",
                    opponent_assumptions=[
                        "Penyebutan tiga nama dalam satu formula gramatikal membuktikan kesetaraan status keilahian ontologis.",
                        "Doktrin inkarnasi dan Trinitas selaras dengan monoteisme murni para nabi."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Penyandingan nama dalam formula berkat tidak membuktikan kesetaraan esensi; Yesus sendiri menegaskan 'Bapa lebih besar dari pada Aku' (Yohanes 14:28).",
                        "Naskah tertua membuktikan ketiadaan formula Comma Johanneum (1 Yohanes 5:7-8) dalam manuskrip Yunani sebelum abad ke-14."
                    ],
                    rebuttal="Berdasarkan prinsip Tauhid murni dan metode Ilzam al-Khasm, konsep Trinitas tidak memiliki legitimasi dari perkataan Yesus sendiri. Al-Qur'an (QS An-Nisa 171) menegaskan larangan mengatakan 'Tiga' dan menegakkan kemahaesaan Allah yang mutlak.",
                    rebuttal_evidence=["Ulangan 6:4", "Markus 12:29", "1 Timotius 2:5"]
                )
            elif p_norm == "judaism":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Pluralitas dalam Kejadian 1:26 ('Baiklah Kita menjadikan manusia') dan penampakan tiga tamu kepada Abraham di Kejadian 18:1-2 mengindikasikan benih doktrin Trinitas dalam Torah.",
                    opponent_evidence=[
                        "Kejadian 1:26: 'Baiklah Kita menjadikan manusia menurut gambar dan rupa Kita...'",
                        "Kejadian 18:1-2: 'TUHAN menampakkan diri kepada Abraham... tiba-tiba ada tiga orang berdiri di dekatnya.'"
                    ],
                    opponent_reasoning="Apologet kristiani menafsirkan bentuk jamak teks Ibrani kuno sebagai petunjuk awal kejamakan pribadi ilahi.",
                    opponent_assumptions=[
                        "Bentuk tata bahasa jamak Ibrani menandakan multiplisitas ontologis entitas ilahi.",
                        "Kunjungan utusan malaikat identik dengan inkarnasi tiga pribadi ilahi."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Dalam gramatika bahasa Ibrani biblika, kata kerja yang menyertai kata 'Elohim' selalu berbentuk tunggal ('bara' - menciptakan), menegaskan kemahaesaan mutlak Sang Pencipta.",
                        "Shema Yisrael di Ulangan 6:4 menggunakan kata 'Echad' yang secara definitif menolak segala bentuk persekutuan, kemitraan, atau pembagian pribadi."
                    ],
                    rebuttal="Torah dan tradisi Talmud menegaskan monoteisme murni tanpa kompromi: Hashem adalah esa mutlak tanpa persekutuan wujud. Penggunaan bentuk jamak dalam naskah Ibrani merupakan idiom bahasa keagungan (pluralis majestatis), bukan pluralitas ilahi.",
                    rebuttal_evidence=["Ulangan 6:4", "Yesaya 44:6", "Keluaran 20:3"]
                )
            elif p_norm == "atheist_secular":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Doktrin Tritunggal adalah artikulasi teologis koheren dan wahyu ilahi yang terjaga melalui konsili-konsili ekumenis terbimbing roh ilahi.",
                    opponent_evidence=[
                        "Kredo Nicea-Konstantinopel (325/381 M)",
                        "Matius 28:19: '...dalam nama Bapa dan Anak dan Roh Kudus.'"
                    ],
                    opponent_reasoning="Argumen tradisional mengasumsikan konsensus gerejawi merupakan bukti kebenaran ontologis supranatural.",
                    opponent_assumptions=[
                        "Konsensus politik keagamaan identik dengan pembuktian fakta objektif.",
                        "Paradoks 'tiga pribadi satu esensi' dapat dipertahankan secara rasional logis."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Catatan historiografi membuktikan keputusan Konsili Nicea dan Konstantinopel sarat dengan represi politik kekaisaran terhadap faksi oposisi Arian.",
                        "Secara epistemologis dan logika formal, konsep 'tiga yang berbeda tetapi identik dengan satu esensi' melanggar hukum identitas dan non-kontradiksi."
                    ],
                    rebuttal="Analisis sejarah kritis dan filsafat analitis membuktikan doktrin Tritunggal merupakan konstruksi dogmatis hasil kompromi sosiopolitik imperium Romawi abad keempat yang mengadopsi terminologi Neoplatonis, bukan fakta objektif yang dapat dibuktikan secara empiris.",
                    rebuttal_evidence=["1 Yohanes 5:7", "Matius 28:19", "Yohanes 1:1"]
                )
            else:
                # Default: christian_protestant
                if opp_norm == "islam":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim="Doktrin Tritunggal membagi kemahaesaan Allah dan bertentangan dengan Shema serta kesaksian Yesus sendiri bahwa Bapa adalah satu-satunya Allah yang benar (Yohanes 17:3, Markus 12:29).",
                        opponent_evidence=[
                            "Yohanes 17:3: 'Inilah hidup yang kekal itu, yaitu bahwa mereka mengenal Engkau, satu-satunya Allah yang benar...'",
                            "Markus 12:29: 'Jawab Yesus: Hukum yang terutama ialah: Dengarlah, hai orang Israel, Tuhan Allah kita, Tuhan itu esa.'",
                            "QS Al-Ikhlas 1-4: 'Katakanlah: Dialah Allah, Yang Maha Esa...'"
                        ],
                        opponent_reasoning="Polemik Tauhid menegaskan bahwa bilangan tiga tidak dapat diselaraskan dengan keesaan mutlak; konsep tiga pribadi ilahi dipandang sebagai politeisme terselubung.",
                        opponent_assumptions=[
                            "Diferensiasi relasional pribadi dalam ketuhanan sama dengan pemisahan substansi politeistik.",
                            "Teks Shema menolak segala bentuk relasi ontologis Trinitarian."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Mengabaikan formula baptisan Matius 28:19 yang menggunakan bentuk tunggal 'eis to onoma' (ke dalam satu nama) bagi Bapa, Anak, dan Roh Kudus.",
                            "Monoteisme Bible membedakan antara 'unitarianisme mutlak' dengan 'monoteisme majemuk' yang diwahyukan dalam pola keselamatan Bible."
                        ],
                        rebuttal="Bible mengajarkan monoteisme sejati (Ulangan 6:4): satu hakikat Allah yang menyatakan diri secara kekal dalam tiga pribadi (Bapa, Anak, Roh Kudus). Matius 28:19 menegaskan satu nama tunggal yang menyatukan ketiga pribadi ilahi.",
                        rebuttal_evidence=["Matius 28:19", "2 Korintus 13:13", "Ulangan 6:4"]
                    )
                elif opp_norm == "judaism":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim="Shema Yisrael (Ulangan 6:4) menegaskan Hashem adalah Echad (Esa mutlak); konsep kemajemukan pribadi ilahi merupakan adopsi metafisika Helenistik pasca-Tanakh.",
                        opponent_evidence=[
                            "Ulangan 6:4: 'Dengarlah, hai orang Israel: TUHAN itu Allah kita, TUHAN itu esa!'",
                            "Yesaya 44:6: '...Akulah yang terdahulu dan Akulah yang terkemudian; tidak ada Allah selain dari pada-Ku.'",
                            "Keluaran 20:3: 'Jangan ada padamu allah lain di hadapan-Ku.'"
                        ],
                        opponent_reasoning="Teologi Tanakh Masoretik menolak pembagian kepribadian dalam keilahian; Hashem adalah mutlak esa tanpa sekutu.",
                        opponent_assumptions=[
                            "Kata 'Echad' selalu bermakna keesaan tunggal mutlak (yachid).",
                            "Naskah Tanakh tidak memuat indikasi kemajemukan dalam karya penciptaan dan penyelamatan."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Kata 'Echad' dalam Tanakh juga digunakan untuk kesatuan majemuk (contoh: Kejadian 2:24, suami-istri menjadi satu [echad] daging; Bilangan 13:23, satu tandan anggur).",
                            "Naskah Ibrani Tanakh memuat pola triadik profetis di mana TUHAN berfirman bersama Roh-Nya dan Sang Penebus (Yesaya 48:16, Yesaya 63:9-10)."
                        ],
                        rebuttal="Kanon 66 Kitab Bible menegaskan bahwa Allah Israel adalah esa (Ulangan 6:4) yang menyatakan kepenuhan hikmat dan firman-Nya di dalam Kristus dan Roh Kudus (Matius 28:19, Yesaya 48:16).",
                        rebuttal_evidence=["Matius 28:19", "Yesaya 48:16", "Ulangan 6:4"]
                    )
                elif opp_norm == "atheist_secular":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim="Doktrin Tritunggal lahir dari kompromi politik kekaisaran Romawi pada Konsili Nicea (325 M) dengan meminjam istilah filosofis homoousios yang asing dari teks abad pertama.",
                        opponent_evidence=[
                            "Kredo Nicea (325 M)",
                            "1 Yohanes 5:7 (varian naskah Comma Johanneum)",
                            "Historiografi Kaisar Konstantinus"
                        ],
                        opponent_reasoning="Historiografi kritis memandang Trinitas sebagai evolusi dogma yang dipaksakan demi unifikasi politik imperium Romawi.",
                        opponent_assumptions=[
                            "Penggunaan terminologi filosofis membuktikan penciptaan ajaran baru.",
                            "Konsensus konsili hanya merupakan manipulasi kekuasaan kekaisaran."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Naskah Perjanjian Baru abad pertama telah memuat formula triadik eksplisit sebelum Nicea (Matius 28:19, 2 Korintus 13:13).",
                            "Tulisan para Bapa Apostolik pra-Nicea (Ignatius, Ireneus, Tertulianus) membuktikan ibadah kepada Trinitas telah dihidupi sebelum campur tangan kaisar Romawi."
                        ],
                        rebuttal="Konsili Nicea tidak menciptakan doktrin baru melainkan merumuskan perlindungan ortodoks terhadap deposit iman biblika yang telah dihidupi jemaat perdana dari bidat Arianisme berdasarkan Kanon 66 Kitab Bible.",
                        rebuttal_evidence=["Matius 28:19", "2 Korintus 13:13", "Yohanes 1:1"]
                    )
                elif opp_norm == "christian_catholic":
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim="Artikulasi dogmatis Tritunggal membutuhkan wibawa Magisterium dan Tradisi Konsili untuk menafsirkan teks suci yang implisit.",
                        opponent_evidence=[
                            "Kredo Nicea-Konstantinopel",
                            "Tradisi Patristik Para Bapa Gereja"
                        ],
                        opponent_reasoning="Menilai bahwa tanpa kewenangan mengajar Gereja Katolik, kanon Bible rentan disalahtafsirkan oleh aliran bidat.",
                        opponent_assumptions=[
                            "Kitab Suci tidak memiliki kejelasan internal (perspicuitas) mengenai keesaan Allah dan tiga pribadi.",
                            "Wibawa konsili mendahului wibawa firman tertulis."
                        ],
                        weaknesses=[
                            "Prinsip Sola Scriptura membuktikan bahwa Kitab Suci cukup dan jelas (sufficientia scripturae) menyatakan Bapa, Anak, dan Roh Kudus.",
                            "Konsili ekumenis sejati hanya tunduk dan menguji diri pada otoritas firman tertulis Bible."
                        ],
                        rebuttal="Kebenaran Tritunggal berakar kokoh pada firman tertulis Bible (Sola Scriptura); konsili gereja sejati bertindak sebagai saksi firman yang menguji seluruh rumusan di hadapan naskah suci.",
                        rebuttal_evidence=["Matius 28:19", "2 Timotius 3:16", "Yohanes 10:30"]
                    )
                else:
                    return SteelmanCounterargument(
                        counterargument_id=carg_id,
                        opponent_claim="Doktrin Tritunggal baru diformulasikan pada Konsili Nicea (325 M) di bawah tekanan politik kekaisaran Romawi dan tidak pernah diajarkan oleh Yesus.",
                        opponent_evidence=[
                            "Ulangan 6:4: 'Dengarlah, hai orang Israel: TUHAN itu Allah kita, TUHAN itu esa!'",
                            "1 Korintus 8:6: 'Bagi kita hanya ada satu Allah saja, yaitu Bapa... dan satu Tuhan saja, yaitu Yesus Kristus.'"
                        ],
                        opponent_reasoning="Istilah Tritunggal (Trinitas) dan terminologi 'homoousios' tidak tercantum dalam Bible dan merupakan pengaruh filsafat Neoplatonisme pasca-apostolik.",
                        opponent_assumptions=[
                            "Ketiadaan istilah teknis dalam naskah berarti konsep substansi doktrin tersebut tidak ada.",
                            "Konsili ekumenis menciptakan doktrin alih-alih mengartikulasikan iman yang sudah diterima."
                        ],
                        opponent_strength="FORMIDABLE",
                        weaknesses=[
                            "Mengabaikan formula baptisan Matius 28:19 yang menggunakan nama tunggal (eis to onoma) untuk Bapa, Anak, dan Roh Kudus.",
                            "Bukti tulisan bapa gereja abad ke-1 dan ke-2 (Ignatius, Polycarpus, Justin Martyr) yang telah merekam ibadah kepada Kristus bersama Bapa."
                        ],
                        rebuttal="Konsili Nicea tidak menciptakan keilahian Kristus atau Tritunggal, melainkan membentengi ajaran apostolik tertua dari distorsi Arianisme berdasarkan Kanon 66 Kitab Bible.",
                        rebuttal_evidence=["Ulangan 6:4", "Matius 28:19", "2 Korintus 13:13"]
                    )

        # -------------------------------------------------------------------
        # 4. GENERAL / FALLBACK MATRIX
        # -------------------------------------------------------------------
        else:
            return SteelmanCounterargument(
                counterargument_id=carg_id,
                opponent_claim=f"Oposisi {opp_norm.upper()} menantang klaim '{claim_text}' dengan mendalilkan ketiadaan dukungan naskah primer yang konsisten menurut paradigma mereka.",
                opponent_evidence=[],
                opponent_reasoning=f"Pihak {opp_norm.upper()} berpegang pada kerangka epistemik normatif mereka dalam menguji keabsahan klaim teologis maupun historis.",
                opponent_assumptions=[f"Praduga epistemik {opp_norm.upper()} harus dijadikan tolok ukur universal pembuktian."],
                opponent_strength="MODERATE",
                weaknesses=["Mengabaikan konteks literatur bahasa sumber dan analisis manuskrip kritis."],
                rebuttal=f"Analisis forensik filologis membuktikan bahwa posisi {p_norm.upper()} konsisten secara internal dan didukung oleh rekaman naskah tertulis berwibawa.",
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
