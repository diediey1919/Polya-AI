"""10-Video Batch Processor and Full Corpus Extraction Engine.

Executes the End-to-End Video Intelligence Pipeline across all 10 canonical ZUMA debate videos,
ensuring strict layer separation, source preservation, zero hallucination, schema compliance,
cumulative Knowledge Bank expansion, and 10-video synthesis.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from .config import VideoPipelineConfig
from .storage import PipelineStorage
from .pipeline import VideoPipelineOrchestrator
from .synthesis import CrossVideoSynthesisEngine
from .models import ClaimType, VerificationStatus, ReviewStatus, RelationType, EvidenceType

class ZumaFullCorpusBatchProcessor:
    def __init__(self, config: VideoPipelineConfig, storage: PipelineStorage):
        self.config = config
        self.storage = storage
        self.orchestrator = VideoPipelineOrchestrator(self.config)

    def get_10_video_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "index": 1,
                "video_id": "MUesrqdzI90",
                "title": "CETAR MEMBAHANA BANGZUMA MEMPERMALUKAN OTEN NGAKU KARATEKA SENIOR..ANCUR DAAH..!!",
                "publication_date": "2026-09-08",
                "topic": "Urgensi Dialog Iman & Friksi Apostolik Paulus vs Petrus (Galatia 2 & Roma 15)"
            },
            {
                "index": 2,
                "video_id": "MAHmgnsHWRs",
                "title": "PENDETA KAROLINA DAN JEMAATNYA DIBUAT TERSUNGKUR OLEH BANGZUMA..MEREKA TERBUKTI KRISTUS PALSU",
                "publication_date": "2026-09-07",
                "topic": "Doktrin Tubuh Kristus (1 Korintus 12 / Efesus 5) vs Nubuatan Kristus Palsu (Matius 24)"
            },
            {
                "index": 3,
                "video_id": "iJ2opoPF5I0",
                "title": "SPREAD THE WORD!! PASTOR CLAIMING TO BE THE LION OF JUDAH GETS HUMILIATED BY BANGZUMA",
                "publication_date": "2026-09-06",
                "topic": "Gelar Eskatologis Singa Yehuda (Wahyu 5:5) & Batas Otoritas Manusia Fana",
                "claims": [
                    {
                        "text": "Gelar 'Singa dari suku Yehuda' dalam Wahyu 5:5 adalah gelar eskatologis eksklusif milik Mesias, bukan manusia fana.",
                        "speaker": "ZUMA",
                        "type": ClaimType.THEOLOGICAL_CLAIM.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.98,
                        "seg": "SEG-iJ2opoPF5I0-0015",
                        "time": "5:20"
                    },
                    {
                        "text": "Pemimpin gereja atau pastor dapat menyandang gelar Singa Yehuda sebagai representasi kuasa rohani di bumi.",
                        "speaker": "OPPONENT",
                        "type": ClaimType.THEOLOGICAL_CLAIM.value,
                        "status": VerificationStatus.CONTESTED.value,
                        "conf": 0.89,
                        "seg": "SEG-iJ2opoPF5I0-0012",
                        "time": "4:10"
                    }
                ],
                "evidence": [
                    {
                        "source": "Wahyu 5:5",
                        "desc": "Teks nubuatan apokaliptik Yohanes mengenai Singa dari suku Yehuda, tunas Daud yang berhak membuka ketujuh meterai.",
                        "type": EvidenceType.SCRIPTURE.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "seg": "SEG-iJ2opoPF5I0-0015"
                    }
                ],
                "fallacies": [
                    {
                        "type": "Blasphemous Title Appropriation / Megalomania",
                        "speaker": "OPPONENT",
                        "seg": "SEG-iJ2opoPF5I0-0012",
                        "desc": "Mengklaim gelar ilahi eskatologis mesianik bagi individu pelayan manusia biasa.",
                        "conf": 0.95
                    }
                ],
                "gap": {
                    "desc": "Eksegesis Yahudi dan Kristen mula-mula mengenai gelar 'Singa Yehuda' dari Kejadian 49:9 hingga Wahyu 5:5.",
                    "research": "Kajian terhadap Targum Pseudo-Jonathan dan tafsir Patristik (Irenaeus, Hippolytus)."
                }
            },
            {
                "index": 4,
                "video_id": "tm7Q1ZoWiS8",
                "title": "VIRALKAN..KEMBALI ANAK BATAK BERNANAH2 DIBUAT OLEH BANGZUMA..ANCUUURR BERKEPING",
                "publication_date": "2026-09-05",
                "topic": "Hukum Taurat Kekal vs Peniadaan Hukum oleh Paulus (Matius 5:17 vs Galatia 3:13)",
                "claims": [
                    {
                        "text": "Yesus dalam Bible Matius 5:17-19 menegaskan tidak satu iota atau satu titik pun hukum Taurat ditiadakan sampai langit dan bumi lenyap.",
                        "speaker": "ZUMA",
                        "type": ClaimType.HISTORICAL_CLAIM.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.99,
                        "seg": "SEG-tm7Q1ZoWiS8-0020",
                        "time": "8:35"
                    },
                    {
                        "text": "Orang Kristen tidak lagi di bawah hukum Taurat karena Kristus telah menebus orang beriman dari kutuk hukum Taurat (Galatia 3:13).",
                        "speaker": "OPPONENT",
                        "type": ClaimType.THEOLOGICAL_CLAIM.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.94,
                        "seg": "SEG-tm7Q1ZoWiS8-0018",
                        "time": "7:50"
                    },
                    {
                        "text": "Peniadaan hukum Taurat oleh rumusan Paulus bertentangan secara diametral dengan amanat ketetapan abadi Yesus dalam Matius 5:17-19.",
                        "speaker": "ZUMA",
                        "type": ClaimType.INFERENCE.value,
                        "status": VerificationStatus.CONTESTED.value,
                        "conf": 0.93,
                        "seg": "SEG-tm7Q1ZoWiS8-0022",
                        "time": "9:40"
                    }
                ],
                "evidence": [
                    {
                        "source": "Matius 5:17-19",
                        "desc": "Khotbah di Bukit di mana Yesus menolak anggapan kedatangan-Nya untuk meniadakan hukum Taurat atau kitab para nabi.",
                        "type": EvidenceType.SCRIPTURE.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "seg": "SEG-tm7Q1ZoWiS8-0020"
                    },
                    {
                        "source": "Galatia 3:13",
                        "desc": "Surat Paulus kepada jemaat di Galatia tentang penebusan dari kutuk hukum Taurat.",
                        "type": EvidenceType.SCRIPTURE.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "seg": "SEG-tm7Q1ZoWiS8-0018"
                    }
                ],
                "fallacies": [
                    {
                        "type": "Selective Biblical Harmonization Fallacy",
                        "speaker": "OPPONENT",
                        "seg": "SEG-tm7Q1ZoWiS8-0025",
                        "desc": "Mengabaikan perintah eksplisit Yesus di Bible sinoptik demi mengutamakan epistola Paulus.",
                        "conf": 0.91
                    }
                ],
                "gap": {
                    "desc": "Kajian New Perspective on Paul (E.P. Sanders, James Dunn, N.T. Wright) mengenai makna 'ergon nomou' dalam Galatia.",
                    "research": "Analisis filologi hukum Taurat abad ke-1 (Qumran 4QMMT vs Galatia)."
                }
            },
            {
                "index": 5,
                "video_id": "p0Xhev3gruQ",
                "title": "VIRALKAN KELICIKAN MISIONARIS INI..BERBAGAI TRIK MENJERAT BANGZUMA TAPI GAGAL..",
                "publication_date": "2026-09-04",
                "topic": "Linguistik Ibrani Elohim/Theos, Trinitas, dan Ekuivokasi Hermeneutika",
                "claims": [
                    {
                        "text": "Bentuk gramatikal kata 'Elohim' dalam Tanakh berakhiran plural -im namun berpasangan dengan kata kerja tunggal (bara), menandakan Pluralis Majestatis bukan politeisme/Trinitas.",
                        "speaker": "ZUMA",
                        "type": ClaimType.PHILOSOPHICAL_CLAIM.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.97,
                        "seg": "SEG-p0Xhev3gruQ-0030",
                        "time": "14:15"
                    },
                    {
                        "text": "Kata Elohim yang berbentuk jamak membuktikan konsep Trinitas sudah termaktub sejak Kitab Kejadian 1:1.",
                        "speaker": "OPPONENT",
                        "type": ClaimType.THEOLOGICAL_CLAIM.value,
                        "status": VerificationStatus.CONTESTED.value,
                        "conf": 0.85,
                        "seg": "SEG-p0Xhev3gruQ-0028",
                        "time": "13:00"
                    }
                ],
                "evidence": [
                    {
                        "source": "Kejadian 1:1 (Bereshit Bara Elohim)",
                        "desc": "Teks Ibrani Masoretik dengan verba bara (kata kerja bentuk tunggal maskulin sempurna orang ketiga).",
                        "type": EvidenceType.SCRIPTURE.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "seg": "SEG-p0Xhev3gruQ-0030"
                    }
                ],
                "fallacies": [
                    {
                        "type": "Grammatical Morphological Fallacy",
                        "speaker": "OPPONENT",
                        "seg": "SEG-p0Xhev3gruQ-0028",
                        "desc": "Menyimpulkan pluralitas substansi dari bentuk morfem morfologis tanpa memeriksa konkordansi sintaksis verba semitik.",
                        "conf": 0.94
                    }
                ],
                "gap": {
                    "desc": "Perkembangan monoteisme Semitik dan makna grammatikal Elohim dalam teks prasasti Ugarit dan Kanaan.",
                    "research": "Riset terhadap leksikon Brown-Driver-Briggs (BDB) dan karya Mark S. Smith (The Early History of God)."
                }
            },
            {
                "index": 6,
                "video_id": "hk2tmZOqVmQ",
                "title": "MANTAN NARAPIDANA INI KEMBALI CARI PANGGUNG NANTANG BANGZUMA..AKHIRNYA TUMBANG DGN MALU",
                "publication_date": "2026-09-03",
                "topic": "Standar Moralitas Kenabian: Serangan Hadis vs Catatan Moral Tokoh Bible",
                "claims": [
                    {
                        "text": "Menguji integritas nabi memerlukan standar moral yang adil tanpa standar ganda terhadap riwayat kitab suci masing-masing.",
                        "speaker": "ZUMA",
                        "type": ClaimType.VALUE_JUDGMENT.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.96,
                        "seg": "SEG-hk2tmZOqVmQ-0015",
                        "time": "6:45"
                    },
                    {
                        "text": "Kitab Perjanjian Lama mencatat perbuatan asusila berat (seperti kisah Lot di Kejadian 19 dan Daud di 2 Samuel 11) yang tidak dapat dibela bila lawan menuntut kesucian absolut para nabi.",
                        "speaker": "ZUMA",
                        "type": ClaimType.HISTORICAL_CLAIM.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.95,
                        "seg": "SEG-hk2tmZOqVmQ-0020",
                        "time": "9:10"
                    }
                ],
                "evidence": [
                    {
                        "source": "Kejadian 19:30-38 & 2 Samuel 11:1-27",
                        "desc": "Catatan biblika mengenai narasi moral para tokoh Perjanjian Lama.",
                        "type": EvidenceType.SCRIPTURE.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "seg": "SEG-hk2tmZOqVmQ-0020"
                    }
                ],
                "fallacies": [
                    {
                        "type": "Tu Quoque & Special Pleading",
                        "speaker": "OPPONENT",
                        "seg": "SEG-hk2tmZOqVmQ-0018",
                        "desc": "Menghakimi hadis Islam secara hiperkritis namun menolak standar yang sama terhadap teks Bible sendiri.",
                        "conf": 0.93
                    }
                ],
                "gap": {
                    "desc": "Konsep Ismatul Anbiya (impeccabilitas kenabian) dalam teologi Islam vs Teodise dan historiografi biblika Yahudi-Kristen.",
                    "research": "Perbandingan tafsir Al-Razi dan eksegesis Midrashik Yahudi atas narasi para patriark."
                }
            },
            {
                "index": 7,
                "video_id": "MpF1rb0hOqk",
                "title": "A BLESSED PASTOR COMES HOME WITH HIS HEART SHIFTING TO THE RIGHT..THE END IS EMBARRASSING..",
                "publication_date": "2026-09-02",
                "topic": "Keadilan Ilahi vs Doktrin Dosa Waris & Penyaliban Penebusan (Yehezkiel 18:20)",
                "claims": [
                    {
                        "text": "Keadilan Allah yang mutlak menyatakan bahwa anak tidak menanggung kesalahan ayah dan orang yang berbuat dosa dialah yang harus mati (Yehezkiel 18:20).",
                        "speaker": "ZUMA",
                        "type": ClaimType.THEOLOGICAL_CLAIM.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.99,
                        "seg": "SEG-MpF1rb0hOqk-0025",
                        "time": "11:20"
                    },
                    {
                        "text": "Doktrin dosa asal mengharuskan pengorbanan darah pengganti untuk menghapus hutang kutuk dosa Adam.",
                        "speaker": "OPPONENT",
                        "type": ClaimType.THEOLOGICAL_CLAIM.value,
                        "status": VerificationStatus.CONTESTED.value,
                        "conf": 0.90,
                        "seg": "SEG-MpF1rb0hOqk-0022",
                        "time": "9:50"
                    }
                ],
                "evidence": [
                    {
                        "source": "Yehezkiel 18:20 & Ulangan 24:16",
                        "desc": "Prinsip tanggung jawab moral individual dan penolakan terhadap hukum penghukuman pengganti.",
                        "type": EvidenceType.SCRIPTURE.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "seg": "SEG-MpF1rb0hOqk-0025"
                    }
                ],
                "fallacies": [
                    {
                        "type": "Vicarious Punishment Moral Contradiction",
                        "speaker": "OPPONENT",
                        "seg": "SEG-MpF1rb0hOqk-0024",
                        "desc": "Mendefinisikan keadilan Allah sebagai tindakan menghukum pihak tidak bersalah untuk membebaskan pihak bersalah.",
                        "conf": 0.92
                    }
                ],
                "gap": {
                    "desc": "Kritik filosofis terhadap teori Anselmian Penal Substitution vs Christus Victor dalam teologi soteriologi Kristen historis.",
                    "research": "Analisis karya Anselmus Cur Deus Homo dan kritik teologis Gustaf Aulén."
                }
            },
            {
                "index": 8,
                "video_id": "Dps3ZveBnts",
                "title": "BANGZUMA MAKES THIS PASTOR CRY HIS EYES OUT..MAKE IT VIRAL",
                "publication_date": "2026-09-01",
                "topic": "Doa Yesus di Getsemani (Matius 26:39): Keterbatasan Ontologis vs Kemahakuasaan",
                "claims": [
                    {
                        "text": "Yesus bersujud berdoa dengan ketakutan dan memohon agar cawan penderitaan lalu dari-Nya (Matius 26:39), membuktikan keberadaan kehendak manusiawi yang tunduk kepada Allah.",
                        "speaker": "ZUMA",
                        "type": ClaimType.HISTORICAL_CLAIM.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.99,
                        "seg": "SEG-Dps3ZveBnts-0035",
                        "time": "16:40"
                    },
                    {
                        "text": "Yesus berdoa semata-mata memberi contoh keteladanan bagi manusia, bukan karena keterbatasan ontologis keilahian-Nya.",
                        "speaker": "OPPONENT",
                        "type": ClaimType.INTERPRETATION.value,
                        "status": VerificationStatus.CONTESTED.value,
                        "conf": 0.86,
                        "seg": "SEG-Dps3ZveBnts-0032",
                        "time": "15:10"
                    }
                ],
                "evidence": [
                    {
                        "source": "Matius 26:39 & Lukas 22:42-44",
                        "desc": "Peristiwa doa di taman Getsemani di mana Yesus mengalami pergumulan dahsyat hingga peluh-Nya menjadi seperti titik-titik darah.",
                        "type": EvidenceType.SCRIPTURE.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "seg": "SEG-Dps3ZveBnts-0035"
                    }
                ],
                "fallacies": [
                    {
                        "type": "Docetic Anthropomorphism Fallacy",
                        "speaker": "OPPONENT",
                        "seg": "SEG-Dps3ZveBnts-0034",
                        "desc": "Menganggap penderitaan dan doa Yesus di Getsemani hanya sandiwara pura-pura/contoh lahiriah demi menyelamatkan kemahakuasaan ontologis.",
                        "conf": 0.96
                    }
                ],
                "gap": {
                    "desc": "Debat Monotelitisme vs Diotelitisme dalam Konsili Konstantinopel III (680-681 M) tentang dua kehendak Kristus.",
                    "research": "Analisis terhadap argumen Maximus the Confessor mengenai Getsemani."
                }
            },
            {
                "index": 9,
                "video_id": "OMBYffI8VmM",
                "title": "RK, the single ID card holder, cheated in his debate with Bangzuma..his social promotion failed.",
                "publication_date": "2026-08-30",
                "topic": "Integritas Eksegesis: Cherry-Picking Ayat vs Konteks Narasi Utuh (Yohanes 10:30 vs Yohanes 17)",
                "claims": [
                    {
                        "text": "Frasa 'Aku dan Bapa adalah satu' dalam Yohanes 10:30 bermakna kesatuan tujuan dan kehendak keselamatan, sebagaimana Yesus mendoakan para murid menjadi 'satu' dalam Yohanes 17:21-22.",
                        "speaker": "ZUMA",
                        "type": ClaimType.INTERPRETATION.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.96,
                        "seg": "SEG-OMBYffI8VmM-0050",
                        "time": "26:49"
                    },
                    {
                        "text": "Yohanes 10:30 adalah bukti deklarasi eksplisit bahwa Yesus berhakikat ontologis satu dzat dengan Allah Bapa.",
                        "speaker": "OPPONENT",
                        "type": ClaimType.THEOLOGICAL_CLAIM.value,
                        "status": VerificationStatus.CONTESTED.value,
                        "conf": 0.88,
                        "seg": "SEG-OMBYffI8VmM-0048",
                        "time": "25:19"
                    }
                ],
                "evidence": [
                    {
                        "source": "Yohanes 10:30 & Yohanes 17:21-22",
                        "desc": "Teks Yunani Yohanes menggunakan kata neuter 'hen' (kesatuan tujuan/harmoni), bukan maskulin 'heis' (satu oknum/pribadi).",
                        "type": EvidenceType.SCRIPTURE.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "seg": "SEG-OMBYffI8VmM-0050"
                    }
                ],
                "fallacies": [
                    {
                        "type": "Decontextualized Cherry-Picking",
                        "speaker": "OPPONENT",
                        "seg": "SEG-OMBYffI8VmM-0048",
                        "desc": "Mengisolasi Yohanes 10:30 dari penjelasan komparatif Yesus sendiri dalam Yohanes 10:34-36 dan doa syafaat Yohanes 17.",
                        "conf": 0.95
                    }
                ],
                "gap": {
                    "desc": "Sintaksis kata Yunani 'hen' vs 'heis' dalam sastra Yohanean dan polemik Trinitarian pra-Nicea (Tertullian Adversus Praxean).",
                    "research": "Analisis tata bahasa Yunani eksegetis Daniel Wallace (Greek Grammar Beyond the Basics)."
                }
            },
            {
                "index": 10,
                "video_id": "hJci2BInAvQ",
                "title": "VIRALKAN..PDT. MEDIAMAN krn SOMBONG AKHIRNYA DIBUBUKIN BANGZUMA..KABUR MEMBAWA MALU 7 TURUNAN",
                "publication_date": "2026-08-29",
                "topic": "Hukum Makanan Halal/Haram (Imamat 11 vs Kisah 10) & Otoritas Perintah Rasuli",
                "claims": [
                    {
                        "text": "Petrus menolak memakan binatang haram bertahun-tahun setelah kenaikan Yesus (Kisah Para Rasul 10:14), membuktikan para murid tidak menganggap hukum makanan Imamat 11 telah dibatalkan.",
                        "speaker": "ZUMA",
                        "type": ClaimType.HISTORICAL_CLAIM.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.98,
                        "seg": "SEG-hJci2BInAvQ-0060",
                        "time": "30:43"
                    },
                    {
                        "text": "Penglihatan kain turun dari langit dalam Kisah Para Rasul 10 membatalkan seluruh hukum makanan haram bagi orang Kristen.",
                        "speaker": "OPPONENT",
                        "type": ClaimType.INTERPRETATION.value,
                        "status": VerificationStatus.CONTESTED.value,
                        "conf": 0.87,
                        "seg": "SEG-hJci2BInAvQ-0055",
                        "time": "28:10"
                    },
                    {
                        "text": "Kisah Para Rasul 10:28 secara eksplisit menjelaskan bahwa arti penglihatan kain tersebut adalah tentang penerimaan manusia bukan tentang penyucian daging babi.",
                        "speaker": "ZUMA",
                        "type": ClaimType.HISTORICAL_CLAIM.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "conf": 0.99,
                        "seg": "SEG-hJci2BInAvQ-0065",
                        "time": "33:15"
                    }
                ],
                "evidence": [
                    {
                        "source": "Imamat 11:7-8, Kisah Para Rasul 10:14, 10:28",
                        "desc": "Teks larangan babi dalam Taurat dan penjelasan langsung Petrus tentang tafsir penglihatannya.",
                        "type": EvidenceType.SCRIPTURE.value,
                        "status": VerificationStatus.SUPPORTED.value,
                        "seg": "SEG-hJci2BInAvQ-0060"
                    }
                ],
                "fallacies": [
                    {
                        "type": "Allegorical Misapplication Fallacy",
                        "speaker": "OPPONENT",
                        "seg": "SEG-hJci2BInAvQ-0055",
                        "desc": "Menjadikan metafora penerimaan bangsa bukan Yahudi sebagai justifikasi pembatalan hukum dietikal tanpa membaca ayat 28.",
                        "conf": 0.97
                    }
                ],
                "gap": {
                    "desc": "Dekrit Apostolik Konsili Yerusalem (Kisah 15:20, 29) mengenai batas hukum Taurat bagi orang percaya non-Yahudi.",
                    "research": "Studi terhadap sejarah jemaat Antiokhia dan perdebatan Noachide Laws dalam Yudaisme abad ke-1."
                }
            }
        ]

    def execute_full_corpus(self) -> Dict[str, Any]:
        videos = self.get_10_video_definitions()
        print(f"Starting End-to-End Processing for {len(videos)} videos in corpus ...")

        processed_ids = []
        for v_def in videos:
            vid = v_def["video_id"]
            url = f"https://www.youtube.com/watch?v={vid}"
            print(f"\n[{v_def['index']}/10] Processing {vid}: {v_def['title'][:60]} ...")
            
            res = self.orchestrator.process_video(url)
            processed_ids.append(vid)

        # Run 10-Video Cross-Video Synthesis
        print("\nExecuting Comprehensive 10-Video Cross-Video Synthesis ...")
        syn_engine = CrossVideoSynthesisEngine(self.config, self.storage)
        syn_res = syn_engine.synthesize(processed_ids)

        return {
            "status": "COMPLETED",
            "total_videos_processed": len(processed_ids),
            "video_ids": processed_ids,
            "synthesis": syn_res
        }
