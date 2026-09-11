"""
Polya AI Runtime - Asymmetric Socratic Warfare (Module XIII)
Logic Inception Protocol: Maieutic Traps, Definitional Cornering, and Fatal Dilemma Synthesis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

@dataclass
class MaieuticStage:
    stage_number: int
    name: str
    prompt_question: str
    intent: str
    expected_ratification: str

@dataclass
class SemanticAnchor:
    term: str
    locked_definition: str
    original_claim_bailey: str
    turn_established: int

@dataclass
class ConstructiveDilemma:
    claim: str
    horn_1: str
    horn_1_consequence: str
    horn_2: str
    horn_2_consequence: str
    socratic_formulation: str
    entropy_convergence: str

class SocraticEngine:
    """
    Asymmetric Socratic Warfare Engine:
    Transforms declarative counter-arguments into weaponized Socratic Inceptions,
    prevents Motte-and-Bailey escapes, and synthesizes constructive dilemmas.
    """
    def __init__(self):
        self.anchors: Dict[str, SemanticAnchor] = {}

    def build_maieutic_trap(self, topic: str, target_claim: str, evidence_data: str) -> List[MaieuticStage]:
        """
        Constructs a 3-stage Maieutic Funnel:
        Stage 1: Benign Universal Probe
        Stage 2: Ratification without defensive arousal
        Stage 3: Mirror Application (Involuntary self-demolition)
        """
        top_l = topic.lower()
        if "manuskrip" in top_l or "tahrif" in top_l or "teks" in top_l:
            return [
                MaieuticStage(
                    stage_number=1,
                    name="BENIGN_UNIVERSAL_PROBE",
                    prompt_question="Dalam kajian filologi dan kritik teks kuno, apakah variasi ortografis (seperti ejaan huruf atau susunan kata minor) secara otomatis membuktikan bahwa isi doktrin asli telah sengaja dipalsukan?",
                    intent="Mengunci standar metodologi analisis teks kuno secara objektif.",
                    expected_ratification="Tidak, variasi minor adalah karakteristik alami semua naskah kuno yang disalin manual."
                ),
                MaieuticStage(
                    stage_number=2,
                    name="RATIFICATION_REINFORCEMENT",
                    prompt_question="Jika variasi ortografis itu alami, apakah kaidah tersebut juga berlaku adil dan setara bagi naskah tradisi Anda sendiri (misal ragam Qira'at atau varian naskah kuno)?",
                    intent="Memaksa pengakuan asas kesetaraan epistemologis (anti-standar ganda).",
                    expected_ratification="Ya, standar penilaian teks kuno harus konsisten dan seragam."
                ),
                MaieuticStage(
                    stage_number=3,
                    name="MIRROR_DELIVERY",
                    prompt_question=f"Jika kaidah tersebut disepakati universal, bagaimana Anda membenarkan klaim bahwa '{target_claim}' ketika data fisik ({evidence_data}) hanya menunjukkan variasi ortografis yang identik dengan naskah Anda?",
                    intent="Lawan terpaksa menyadari kontradiksi klaimnya melalui mulutnya sendiri.",
                    expected_ratification="Argumen klaim korupsi sepihak runtuh oleh standar yang baru disetujuinya."
                )
            ]
        elif "trinitas" in top_l or "monoteisme" in top_l or "ketuhanan" in top_l:
            return [
                MaieuticStage(
                    stage_number=1,
                    name="BENIGN_UNIVERSAL_PROBE",
                    prompt_question="Ketika kita membahas entitas yang bersifat Transenden dan Tak Terbatas, apakah esensi dan cara keberadaan-Nya harus selalu dapat dibatasi oleh analogi objek fisik materi di alam semesta?",
                    intent="Mengunci keterbatasan analogi materi terhadap esensi Ilahi.",
                    expected_ratification="Tentu tidak, Tuhan tidak sama dengan materi ciptaan-Nya."
                ),
                MaieuticStage(
                    stage_number=2,
                    name="RATIFICATION_REINFORCEMENT",
                    prompt_question="Apakah satu entitas dapat memiliki kompleksitas esensial yang melampaui aritmatika pembagian benda fisik tanpa kehilangan kesatuan keberadaan-Nya?",
                    intent="Membuka ruang kemungkinan ontologis non-antropomorfis.",
                    expected_ratification="Ya, realitas metafisik tidak tunduk pada pembagian materi ruang-waktu."
                ),
                MaieuticStage(
                    stage_number=3,
                    name="MIRROR_DELIVERY",
                    prompt_question=f"Jika esensi Ilahi tidak tunduk pada analogi materi, atas dasar logika apa Anda menyimpulkan bahwa '{target_claim}' merupakan kemustahilan matematis, padahal definisi yang digunakan merujuk pada kesatuan hakikat transenden?",
                    intent="Membongkar asumsi antropomorfisme yang mendasari penolakan lawan.",
                    expected_ratification="Penolakan yang didasarkan pada analogi pembagian materi gugur dengan sendirinya."
                )
            ]
        else:
            return [
                MaieuticStage(
                    stage_number=1,
                    name="BENIGN_UNIVERSAL_PROBE",
                    prompt_question="Apakah sebuah klaim historis dapat dianggap sahih hanya atas dasar asumsi tanpa adanya saksi tertulis atau bukti arkeologis kontemporer?",
                    intent="Menegakkan keharusan bukti primer dalam klaim sejarah.",
                    expected_ratification="Tidak, klaim sejarah memerlukan saksi bukti primer."
                ),
                MaieuticStage(
                    stage_number=2,
                    name="RATIFICATION_REINFORCEMENT",
                    prompt_question="Dan apakah beban pembuktian (burden of proof) selalu berada di pundak pihak yang membuat pernyataan positif atas suatu peristiwa?",
                    intent="Mengunci beban pembuktian pada pihak yang menegaskan klaim.",
                    expected_ratification="Ya, siapa yang mengklaim harus membuktikan."
                ),
                MaieuticStage(
                    stage_number=3,
                    name="MIRROR_DELIVERY",
                    prompt_question=f"Mengingat beban pembuktian ada pada penegasan positif, bukti kontemporer primer apa yang Anda miliki untuk menopang klaim '{target_claim}' di hadapan bukti kontra ({evidence_data})?",
                    intent="Mengunci lawan dalam ketiadaan bukti primer mereka sendiri.",
                    expected_ratification="Lawan tidak mampu menyodorkan saksi primer kontemporer."
                )
            ]

    def lock_definition(self, term: str, definition: str, bailey_claim: str = "", turn: int = 1):
        self.anchors[term.lower()] = SemanticAnchor(
            term=term,
            locked_definition=definition,
            original_claim_bailey=bailey_claim,
            turn_established=turn
        )

    def detect_motte_and_bailey(self, term: str, current_statement: str) -> Tuple[bool, str, str]:
        """
        Detects if the opponent is retreating from their original radical claim (Bailey)
        to a trivial, easily defensible position (Motte).
        """
        t_low = term.lower()
        if t_low not in self.anchors:
            return False, "", ""
        
        anchor = self.anchors[t_low]
        s_low = current_statement.lower()
        
        # Simple heuristic for shift towards softening terms
        softening_cues = ["maksud saya hanya", "hanya sekadar", "bukan berarti", "secara kiasan", "hanya menafsirkan", "intinya bukan"]
        if any(c in s_low for c in softening_cues):
            details = f"Lawan terdeteksi menggeser definisi '{term}' dari klaim radikal awal ('{anchor.original_claim_bailey}') menuju posisi perlindungan yang aman."
            counter_projection = (
                f"Di awal diskusi (Turn {anchor.turn_established}), Anda menegaskan definisi '{term}' sebagai: "
                f"\"{anchor.locked_definition}\" untuk membuktikan bahwa \"{anchor.original_claim_bailey}\". "
                f"Apakah sekarang Anda secara resmi menarik kembali definisi awal tersebut dan mengakui klaim radikal tersebut gugur?"
            )
            return True, details, counter_projection
            
        return False, "", ""

    def generate_fatal_dilemma(
        self,
        claim: str,
        horn_1_name: str,
        horn_1_effect: str,
        horn_2_name: str,
        horn_2_effect: str
    ) -> ConstructiveDilemma:
        socratic = (
            f"Terkait klaim '{claim}', secara analitis Anda dihadapkan pada dua kemungkinan mutlak:\n"
            f"1. Jika Anda memilih jalur [{horn_1_name}], maka konsekuensi tak terhindarkannya adalah: {horn_1_effect}.\n"
            f"2. Jika Anda memilih jalur [{horn_2_name}], maka konsekuensinya adalah: {horn_2_effect}.\n"
            f"Berdasarkan premis Anda sendiri, manakah di antara kedua opsi ini yang Anda pilih?"
        )
        convergence = f"Kedua cabang secara matematis dan historis bermuara pada runtuhnya klaim '{claim}'."
        
        return ConstructiveDilemma(
            claim=claim,
            horn_1=horn_1_name,
            horn_1_consequence=horn_1_effect,
            horn_2=horn_2_name,
            horn_2_consequence=horn_2_effect,
            socratic_formulation=socratic,
            entropy_convergence=convergence
        )
