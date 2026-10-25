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
    def analyze_claim(
        cls,
        claim_text: str,
        evidence: List[EvidenceItem],
        user_perspective: Optional[str] = "christian_protestant"
    ) -> CanonicalClaim:
        """Constructs canonical claim representation from user input according to epistemic perspective."""
        cid = f"claim_{uuid.uuid4().hex[:8]}"
        q_lower = claim_text.lower()
        is_pauline_law = any(w in q_lower for w in ["paulus", "taurat", "law", "nomos", "hukum taurat"])
        is_christology = any(w in q_lower for w in ["yesus", "tuhan", "keilahian", "aku adalah tuhan", "allah sejati"])
        is_trinity = any(w in q_lower for w in ["tritunggal", "trinity", "tiga pribadi", "monoteisme"])

        p_norm = (user_perspective or "christian_protestant").strip().lower()
        if p_norm in ("christian", "protestant"):
            p_norm = "christian_protestant"
        elif p_norm in ("catholic", "katolik"):
            p_norm = "christian_catholic"
        elif p_norm in ("atheist", "secular"):
            p_norm = "atheist_secular"
        elif p_norm in ("jewish", "yahudi"):
            p_norm = "judaism"

        if is_pauline_law:
            if p_norm == "christian_catholic":
                subject = "Paulus dari Tarsus & Tradisi Apostolik"
                predicate = "kegenapan hukum moral dalam kovenan baru"
                objects = ["Kanon 73 Kitab (Deuterokanonika)", "Tradisi Suci Patristik", "Magisterium Gereja"]
                scope = "Kanon 73 Kitab, Patristik & Magisterium"
                counterclaims = [
                    "Tradisi Patristik menegaskan kesinambungan hukum kodrat moral yang disempurnakan rahmat sakramental (Matius 5:17, Sirakh 15:15)",
                    "Magisterium mengajarkan bahwa hukum Taurat digenapi dalam kovenan baru tanpa menghapus kewajiban moral (Roma 3:31, Yakobus 2:24)"
                ]
            elif p_norm == "islam":
                subject = "Teologi Paulus versus Syariat Kovenan Para Nabi"
                predicate = "pergeseran ajaran tauhid dan syariat kovenan"
                objects = ["Al-Qur'an al-Karim", "Sunnah Shahihah", "Metode Ilzam al-Khasm"]
                scope = "Tauhid, Syariat Para Nabi & Kritik Filologis Kanon"
                counterclaims = [
                    "Al-Qur'an menegaskan para nabi diutus menegakkan syariat dan tauhid yang sama (QS Asy-Syura 13, Al-Ma'idah 46)",
                    "Berdasarkan kaidah Ilzam al-Khasm, pernyataan Yesus sendiri di Matius 5:17-19 menegaskan tidak satu iota pun dari hukum Taurat dibatalkan"
                ]
            elif p_norm == "judaism":
                subject = "Paulus dari Tarsus versus Keabadian Torah (Torat Emet)"
                predicate = "klaim penghentian mitzvot kovenan Sinai"
                objects = ["Tanakh Masoretik (Torah, Nevi'im, Ketuvim)", "Tradisi Lisan Talmud & Halakha"]
                scope = "Tanakh Masoretik & Halakha Yahudi"
                counterclaims = [
                    "Torah adalah kovenan kekal (berit olam) yang tidak pernah dapat dibatalkan atau digantikan oleh manusia (Ulangan 13:1-5, Ulangan 29:29)",
                    "Tanakh menegaskan bahwa Allah bukan manusia dan firman-Nya berdiri teguh selama-lamanya (Bilangan 23:19, Yesaya 40:8)"
                ]
            elif p_norm == "atheist_secular":
                subject = "Klaim Teologi Paulin & Perkembangan Sastra Kuno"
                predicate = "evolusi hermeneutika kelompok sektarian abad pertama"
                objects = ["Historiografi Kritis", "Sosiologi Agama", "Metode Historis-Kritis"]
                scope = "Historiografi Kritis & Kritik Sastra Komparatif"
                counterclaims = [
                    "Surat-surat Paulus merefleksikan dinamika sosiologis adaptasi gerakan proto-Kristen terhadap dunia Helenistik non-Yahudi",
                    "Ketiadaan konsensus monolitik membuktikan adanya faksionalisme internal antara kelompok Kristen-Yahudi Yerusalem dan misi Paulin"
                ]
            else:
                # Default: christian_protestant
                subject = "Paulus dari Tarsus"
                predicate = "membatalkan (katargeō)"
                objects = ["Hukum Taurat (Torah / Nomos)", "Perintah-perintah berketentuan (Dogmasin)"]
                scope = "Pauline Epistles & Early Jewish-Christian Halakha"
                counterclaims = [
                    "Paulus menegakkan hukum Taurat secara moral dan eskatologis (Roma 3:31)",
                    "Paulus hanya membatalkan tembok pemisah ritual etnis antara Yahudi dan bukan-Yahudi (Efesus 2:15)"
                ]
        elif is_christology:
            if p_norm == "christian_catholic":
                subject = "Yesus Kristus / Sang Sabda Berinkarnasi"
                predicate = "kesatuan kodrat ilahi dan manusiawi (Konsili Khalsedon)"
                objects = ["Kanon 73 Kitab", "Kredo Ekumenis Nicea-Konstantinopel", "Konsensus Patristik"]
                scope = "Kristologi Patristik, Kredo Ekumenis & Magisterium"
                counterclaims = [
                    "Tradisi Apostolik dan kredo ekumenis secara konsisten mempertahankan dogma inkarnasi ilahi dari distorsi Ebionit dan Arian (Yohanes 1:1, Yohanes 10:30)",
                    "Liturgi dan sakramen gereja perdana secara universal menyembah Kristus sebagai Allah sejati dan Manusia sejati"
                ]
            elif p_norm == "islam":
                subject = "Nabi Isa Al-Masih (Yesus) dalam Timbangan Tauhid"
                predicate = "status kenabian dan penolakan deifikasi ontologis"
                objects = ["Al-Qur'an al-Karim", "Sunnah Shahihah", "Metode Ilzam al-Khasm"]
                scope = "Tanzih, Kemurnian Tauhid & Bedah Teks Sumber Bible"
                counterclaims = [
                    "Al-Qur'an menegaskan Isa Al-Masih adalah hamba dan rasul Allah, bukan Tuhan atau anak Allah (QS Al-Ikhlas 1-4, QS An-Nisa 171, QS Al-Ma'idah 116)",
                    "Melalui metode Ilzam al-Khasm, Yesus sendiri dalam Bible menolak predikat ketuhanan mutlak dan menegaskan Bapa adalah satu-satunya Allah yang benar (Yohanes 17:3, Markus 10:18)"
                ]
            elif p_norm == "judaism":
                subject = "Sosok Yesus dalam Kerangka Teologi Kovenan Tanakh"
                predicate = "penolakan inkarnasi dan klaim kemesiasan yang belum terbukti"
                objects = ["Tanakh Masoretik", "Halakha & Teologi Rambam"]
                scope = "Tanakh Masoretik & Monoteisme Murni Hashem"
                counterclaims = [
                    "Hashem adalah mutlak esa tanpa sekutu, perwujudan fisik, atau pembagian pribadi (Ulangan 6:4, Yesaya 44:6)",
                    "Kriteria mesianik Tanakh menuntut pemulihan kerajaan Israel, pengumpulan diaspora, dan perdamaian dunia universal (Yesaya 2:4, Yeremia 23:5-6) yang belum tergenapi"
                ]
            elif p_norm == "atheist_secular":
                subject = "Historisitas Figur Yesus & Perkembangan Kristologi Rendah ke Tinggi"
                predicate = "deifikasi bertahap dari guru apokaliptik menjadi entitas ilahi"
                objects = ["Historiografi Kritis", "Kritik Sumber Sinoptik vs Yohanes", "Metode Historis-Empiris"]
                scope = "Historiografi Kritis & Kritik Redaksi Akademik"
                counterclaims = [
                    "Analisis historis-kritis membuktikan perkembangan kristologi dari kristologi rendah (Markus) menuju kristologi pra-eksistensi tinggi (Yohanes)",
                    "Klaim mukjizat dan proklamasi supranatural tidak didukung bukti empiris koroboratif kontemporer independen di luar lingkaran tradisi sektarian"
                ]
            else:
                # Default: christian_protestant
                subject = "Yesus Kristus / Hakikat Keilahian"
                predicate = "proklamasi diri / keilahian eksplisit"
                objects = ["Teks Injil Kanonikal", "Sintaksis Egō Eimi / Hen Esmen"]
                scope = "Gospel Christology & Johannine Texts"
                counterclaims = [
                    "Keilahian Yesus dinyatakan melalui tindakan prerogatif ilahi dan kesatuan ontologis dengan Bapa (Yohanes 10:30)",
                    "Ketiadaan formula verbal spesifik tidak menegasikan atribusi keilahian Yesus dalam tradisi apostolik"
                ]
        elif is_trinity:
            if p_norm == "christian_catholic":
                subject = "Misteri Tritunggal Maha Kudus (Sanctissima Trinitas)"
                predicate = "pengembangan artikulasi dogmatis dalam Tradisi Suci dan Magisterium"
                objects = ["Kanon 73 Kitab", "Kredo Nicea-Konstantinopel", "Tradisi Patristik"]
                scope = "Tradisi Suci, Kredo Ekumenis & Magisterium Gereja"
                counterclaims = [
                    "Konsili Nicea (325 M) dan Konstantinopel (381 M) adalah pembelaan terbimbing Roh Kudus terhadap kebenaran iman apostolik dari bidat Arianisme",
                    "Tradisi Patristik (Athanasius, Basilius, Gregorius dari Nazianzus) membuktikan kesatuan esensi (homoousios) Bapa, Anak, dan Roh Kudus"
                ]
            elif p_norm == "islam":
                subject = "Kritik Doktrin Trinitas Berdasarkan Tauhid Murni"
                predicate = "dekonstruksi inkonsistensi politeistik dan interpolasi naskah"
                objects = ["Al-Qur'an al-Karim", "Akal Sehat (Sarih al-Aql)", "Metode Ilzam al-Khasm"]
                scope = "Tanzih, Monoteisme Murni & Filologi Naskah Kuno"
                counterclaims = [
                    "Al-Qur'an secara tegas melarang konsep trinitarian dan menegaskan kemahaesaan Allah yang absolut (QS An-Nisa 171, QS Al-Ma'idah 73, QS Al-Ikhlas 1-4)",
                    "Melalui Ilzam al-Khasm, teks Shema di Ulangan 6:4 dan konfirmasi Yesus di Markus 12:29 menolak pembagian kepribadian dalam keilahian, serta naskah Comma Johanneum (1 Yohanes 5:7) terbukti interpolasi palsu"
                ]
            elif p_norm == "judaism":
                subject = "Penolakan Konsep Trinitas Berdasarkan Monoteisme Mutlak Tanakh"
                predicate = "penjagaan ketat atas Shema Yisrael dan keesaan ilahi"
                objects = ["Tanakh Masoretik", "Teks Shema (Ulangan 6:4)", "Filsafat Yahudi (Rambam)"]
                scope = "Tanakh Masoretik & Monoteisme Radikal Ibrani"
                counterclaims = [
                    "Shema Yisrael menyatakan secara kategoris bahwa Hashem adalah Echad (Esa mutlak), menolak segala bentuk pluralitas dalam hakikat ilahi (Ulangan 6:4)",
                    "Konsep tritunggal merupakan adopsi konsep metafisika Yunani pasca-biblika yang bertentangan secara frontal dengan kovenan monoteisme murni Tanakh"
                ]
            elif p_norm == "atheist_secular":
                subject = "Genealogi Doktrin Trinitas & Konstruksi Politik-Dogmatis"
                predicate = "evolusi rumusan teologis dari konsili politik kekaisaran Romawi"
                objects = ["Historiografi Patristik", "Sosiologi Kekuasaan Imperium Romawi", "Sejarah Dogma"]
                scope = "Historiografi Kritis & Kritik Sosiopolitik Agama"
                counterclaims = [
                    "Sejarah membuktikan doktrin Tritunggal berkembang melalui pertarungan kekuasaan politik dan imperial pada Konsili Nicea (325 M) dan Konsili Konstantinopel (381 M)",
                    "Formulasi filosofis 'homoousios' mengimpor terminologi filsafat Neoplatonisme yang asing dari konteks teks semitik Yahudi abad pertama"
                ]
            else:
                # Default: christian_protestant
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
    def steelman_opposition(cls, claim_text: str, user_perspective: Optional[str] = "christian_protestant") -> SteelmanCounterargument:
        """
        Steelman counterargument construction (Section 15):
        Constructs the strongest plausible opposing argument before rebuttal,
        tailored to the user's apologetics perspective and canonical standard.
        """
        carg_id = f"carg_{uuid.uuid4().hex[:8]}"
        q_lower = claim_text.lower()
        is_pauline_law = any(w in q_lower for w in ["paulus", "taurat", "law", "nomos", "hukum taurat"])
        is_christology = any(w in q_lower for w in ["yesus", "tuhan", "keilahian", "aku adalah tuhan", "allah sejati"])
        is_trinity = any(w in q_lower for w in ["tritunggal", "trinity", "tiga pribadi", "monoteisme"])

        p_norm = (user_perspective or "christian_protestant").strip().lower()
        if p_norm in ("christian", "protestant"):
            p_norm = "christian_protestant"
        elif p_norm in ("catholic", "katolik"):
            p_norm = "christian_catholic"
        elif p_norm in ("atheist", "secular"):
            p_norm = "atheist_secular"
        elif p_norm in ("jewish", "yahudi"):
            p_norm = "judaism"

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
                        "Surat-surat pastoral mengesampingkan sabda eksplisit Yesus di kitab-kitab Injil."
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
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim=(
                        "Paulus secara tuntas telah mengakhiri dispensasi Taurat; orang beriman tidak lagi di bawah hukum Taurat "
                        "karena Kristus adalah kegenapan akhir hukum Taurat untuk pembenaran (Roma 10:4, Galatia 3:24-25, Efesus 2:15)."
                    ),
                    opponent_evidence=[
                        "Roma 10:4: 'Sebab Kristus adalah kegenapan (τέλος) hukum Taurat, sehingga kebenaran diperoleh tiap-tiap orang yang percaya.'",
                        "Galatia 3:24-25: 'Jadi hukum Taurat adalah penuntun (παιDAγωγός) bagi kita sampai Kristus datang... Sekarang iman itu telah datang, kita tidak berada lagi di bawah pengawasan penuntun.'",
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
            if p_norm == "christian_catholic":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Formulasi dua kodrat Kristus (keilahian dan kemanusiaan) merupakan inovasi pasca-apostolik Konsili Khalsedon yang tidak diajarkan secara eksplisit oleh teks Injil.",
                    opponent_evidence=[
                        "1 Timotius 2:5: 'Karena Allah itu esa dan esa pula Dia yang menjadi pengantara antara Allah dan manusia, yaitu manusia Kristus Yesus.'",
                        "Markus 10:18: 'Mengapa kaukatakan Aku baik? Tak seorang pun yang baik selain dari Allah saja.'"
                    ],
                    opponent_reasoning="Ketiadaan rumusan teknis 'dua kodrat dalam satu pribadi' dalam teks Injil dianggap sebagai bukti perkembangan dogmatis eksternal gereja.",
                    opponent_assumptions=[
                        "Doktrin apostolik harus menggunakan rumusan terminologis yang persis sama dengan kredo abad kelima.",
                        "Tradisi lisan gereja perdana tidak memiliki bobot normatif bersama teks tertulis."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Tradisi Patristik abad ke-1 dan ke-2 (Ignatius dari Antiokhia, Irenaeus dari Lyon) telah bersaksi tegas tentang keilahian dan kemanusiaan Kristus.",
                        "Teks Injil Yohanes 1:1, 1:14 dan Yohanes 10:30 menyatakan secara eksplisit bahwa Firman adalah Allah dan telah menjadi manusia."
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
                    opponent_reasoning="Argumen apologetika minimal facts mendalilkan bahwa kebangkitan adalah hipotesis terbaik yang menjelaskan makam kosong dan keberanian murid-murid.",
                    opponent_assumptions=[
                        "Teks pengakuan iman konfesional identik dengan catatan forensik saksi mata independen.",
                        "Ketiadaan penjelasan naturalistik langsung otomatis memvalidasi mukjizat supranatural."
                    ],
                    opponent_strength="FORMIDABLE",
                    weaknesses=[
                        "Ketiadaan saksi koroboratif independen sezaman di luar komunitas pengikut gerakan keagamaan.",
                        "Perkembangan sastra Injil membuktikan evolusi tradisi dari penampakan visioner internal (Paulus) menjadi narasi jasmani yang semakin elaboratif di Injil-Injil belakangan."
                    ],
                    rebuttal="Prinsip beban pembuktian historis menuntut verifikasi empiris yang memadai untuk klaim supranatural. Ketiadaan bukti manuskrip sezaman dan kontradiksi narasi makam antar-Injil membuktikan proses pembentukan legenda dan mitologi pasca-kematian tokoh sejarah.",
                    rebuttal_evidence=["1 Korintus 15:6", "Markus 16:8", "Matius 28:11-15"]
                )
            else:
                # Default: christian_protestant
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
                    rebuttal="Bible menyatakan keilahian Yesus bukan melalui klaim verbal sepihak melainkan melalui kedaulatan, kuasa mencipta, dan kesatuan ontologis dengan Bapa (Yohanes 10:30).",
                    rebuttal_evidence=["Yohanes 10:30", "Yohanes 8:58", "Markus 2:5-7"]
                )
        elif is_trinity:
            if p_norm == "christian_catholic":
                return SteelmanCounterargument(
                    counterargument_id=carg_id,
                    opponent_claim="Doktrin Tritunggal tidak memiliki dasar eksplisit dalam naskah Alkitab dan merupakan konstruksi filosofis Hellenistik yang dipaksakan pada Konsili Nicea.",
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
                        "Penyebutan tiga subjek dalam satu kalimat identik dengan kesetaraan ontologis ketiganya.",
                        "Misteri trinitarian melampaui hukum logika non-kontradiksi."
                    ],
                    opponent_weaknesses=[
                        "Matius 28:19 dan 2 Korintus 13:13 tidak pernah menyebut istilah 'tiga pribadi satu hakikat' (hypostasis / ousia).",
                        "Ayat 1 Yohanes 5:7 (Comma Johanneum) yang memuat klaim tiga saksi surgawi terbukti secara filologis merupakan interpolasi palsu yang tidak ada dalam naskah kuno Codex Sinaiticus dan Codex Vaticanus."
                    ],
                    rebuttal="Melalui kaidah Ilzam al-Khasm, konsep Trinitas terbukti merupakan formulasi pasca-apostolik yang bertentangan dengan monoteisme murni Bible di Ulangan 6:4 dan Markus 12:29. Al-Qur'an secara tegas menegakkan tauhid mutlak (QS Al-Ikhlas 1-4, QS An-Nisa 171).",
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
