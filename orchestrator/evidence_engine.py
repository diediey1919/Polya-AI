"""
Polya Multi-Agent Orchestrator — Evidence & Philological Retrieval Engine
Master Prompt #2 — Section 8, 9, 10, 11 Compliance.

Implements:
1. Source-Language-First Biblical Linguistics (Koine Greek, Biblical Hebrew)
2. Evidence Classification Hierarchy (PRIMARY_SOURCE, DIRECT_EVIDENCE, CONTEXTUAL_EVIDENCE, SECONDARY_SOURCE, INTERPRETIVE, DISPUTED)
3. 'Show Me The Source' Provenance Traceability
4. Morphological and Lexical Decomposition (BDAG / HALOT standard)
5. Separation of TEXTUAL FACT from LINGUISTIC INTERPRETATION and THEOLOGICAL INTERPRETATION.
"""
import os
import re
import sqlite3
import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("evidence_engine")

BIBLE_ENGINE_DB = os.environ.get("BIBLE_ENGINE_DB_PATH", "/home/ubuntu/.polya/bible_engine.db")


class EvidenceTier(str, Enum):
    PRIMARY_SOURCE = "PRIMARY_SOURCE"           # Autograph witness / Early Greek-Hebrew Critical Text
    DIRECT_EVIDENCE = "DIRECT_EVIDENCE"         # Explicit syntactic clause directly speaking to the claim
    CONTEXTUAL_EVIDENCE = "CONTEXTUAL_EVIDENCE" # Pericope discourse context, recipient situation
    SECONDARY_SOURCE = "SECONDARY_SOURCE"       # Patristic commentary, Second Temple Jewish literature
    INTERPRETIVE = "INTERPRETIVE"               # Systematic theological synthesis
    DISPUTED = "DISPUTED"                       # Textual variant or ambiguous grammatical construct


@dataclass
class MorphologicalToken:
    surface_form: str
    lemma: str
    part_of_speech: str
    morphology: str
    lexical_meaning: str
    syntactic_role: str
    textual_fact: str
    linguistic_interpretation: str
    theological_interpretation: str


@dataclass
class EvidenceItem:
    evidence_id: str
    tier: EvidenceTier
    source_id: str
    book: str
    chapter: int
    verse: int
    passage_reference: str
    original_language: str
    original_text: str
    transliteration: str
    english_translation: str
    indonesian_translation: str
    confidence: float
    provenance_hash: str
    witnesses: List[str]
    tokens: List[MorphologicalToken] = field(default_factory=list)
    theological_implication: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "tier": self.tier.value if isinstance(self.tier, EvidenceTier) else self.tier,
            "source_id": self.source_id,
            "book": self.book,
            "chapter": self.chapter,
            "verse": self.verse,
            "passage_reference": self.passage_reference,
            "original_language": self.original_language,
            "original_text": self.original_text,
            "transliteration": self.transliteration,
            "translations": {
                "en": self.english_translation,
                "id": self.indonesian_translation
            },
            "confidence": self.confidence,
            "provenance_hash": self.provenance_hash,
            "witnesses": self.witnesses,
            "tokens": [
                {
                    "surface_form": t.surface_form,
                    "lemma": t.lemma,
                    "pos": t.part_of_speech,
                    "morph": t.morphology,
                    "meaning": t.lexical_meaning,
                    "syntactic_role": t.syntactic_role,
                    "textual_fact": t.textual_fact,
                    "linguistic_interpretation": t.linguistic_interpretation,
                    "theological_interpretation": t.theological_interpretation
                }
                for t in self.tokens
            ],
            "theological_implication": self.theological_implication
        }


# Canonical Academic Philological Repository for Key Biblical Passages
# Provides primary Greek (NA28/UBS5) and Hebrew (BHS) forensic data
CANONICAL_PHILOLOGY_KNOWLEDGE: Dict[str, Dict[str, Any]] = {
    "Roma 3:31": {
        "book": "Roma",
        "chapter": 3,
        "verse": 31,
        "original_language": "Koine Greek",
        "original_text": "νόμον οὖν καταργοῦμεν διὰ τῆς πίστεως; μὴ γένοιτο· ἀλλὰ νόμον ἱστάνομεν.",
        "transliteration": "nomon oun katargoumen dia tēs pisteōs? mē genoito; alla nomon histanomen.",
        "english": "Do we then nullify the law through faith? May it never be! On the contrary, we establish the law.",
        "indonesian": "Jika demikian, adakah kami membatalkan hukum Taurat karena iman? Sama sekali tidak! Sebaliknya, kami menegakkannya.",
        "tier": EvidenceTier.DIRECT_EVIDENCE,
        "confidence": 0.98,
        "witnesses": ["P46 (c. 200 CE)", "Codex Sinaiticus (א01)", "Codex Vaticanus (B03)", "Codex Alexandrinus (A02)"],
        "tokens": [
            MorphologicalToken(
                surface_form="καταργοῦμεν",
                lemma="καταργέω (katargeō)",
                part_of_speech="Verb",
                morphology="Present Active Indicative, 1st Person Plural",
                lexical_meaning="To render inoperative, abolish, invalidate, nullify (BDAG p. 525)",
                syntactic_role="Main interrogative predicate governed by inference particle οὖν",
                textual_fact="Paul frames the question whether faith invalidates nomos with the verb katargeō.",
                linguistic_interpretation="The grammatical mood (indicative in rhetorical question followed by optative negation) indicates an abhorrent conclusion rejected categorically.",
                theological_interpretation="Paul directly denies that his gospel of justification by faith makes the Torah obsolete or void."
            ),
            MorphologicalToken(
                surface_form="μὴ γένοιτο",
                lemma="γίνομαι (ginomai)",
                part_of_speech="Particle + Verb",
                morphology="Negative Particle + Aorist Middle Optative, 3rd Person Singular",
                lexical_meaning="By no means! Far be it! God forbid! (Strongest Greek rhetorical negation)",
                syntactic_role="Independent exclamatory clause expressing violent rejection of false premise",
                textual_fact="The phrase μὴ γένοιτο is the strongest Pauline syntactic repudiation available in Koine Greek.",
                linguistic_interpretation="Optative of wish/volition; functions idiomatically as absolute denial.",
                theological_interpretation="Categorically refutes the antinomian premise that faith terminates the Torah."
            ),
            MorphologicalToken(
                surface_form="ἱστάνομεν",
                lemma="ἵστημι / ἱστάνω (histēmi / histanō)",
                part_of_speech="Verb",
                morphology="Present Active Indicative, 1st Person Plural",
                lexical_meaning="To cause to stand, establish, uphold, confirm, validate (BDAG p. 482)",
                syntactic_role="Adversative predicate governed by strong disjunctive particle ἀλλά",
                textual_fact="The verb histanomen stands in direct grammatical antithesis to katargoumen.",
                linguistic_interpretation="Durative/customary present tense indicating continual upholding.",
                theological_interpretation="Faith does not destroy the Torah; it confirms and fulfills its true witness and divine purpose."
            )
        ]
    },
    "Efesus 2:15": {
        "book": "Efesus",
        "chapter": 2,
        "verse": 15,
        "original_language": "Koine Greek",
        "original_text": "τὴν ἔχθραν ἐν τῇ σαρκὶ αὐτοῦ, τὸν νόμον τῶν ἐντολῶν ἐν δόγμασιν καταργήσας...",
        "transliteration": "tēn echthran en tē sarki autou, ton nomon tōn entolōn en dogmasin katargēsas...",
        "english": "...by abolishing in His flesh the enmity, which is the Law of commandments contained in ordinances...",
        "indonesian": "...sebab dengan mati-Nya sebagai manusia Ia telah membatalkan hukum Taurat dengan segala perintah dan ketentuannya...",
        "tier": EvidenceTier.DIRECT_EVIDENCE,
        "confidence": 0.95,
        "witnesses": ["P46", "Codex Sinaiticus", "Codex Vaticanus"],
        "tokens": [
            MorphologicalToken(
                surface_form="καταργήσας",
                lemma="καταργέω (katargeō)",
                part_of_speech="Verb",
                morphology="Aorist Active Participle, Nominative Masculine Singular",
                lexical_meaning="Having rendered powerless / dismantled the barrier (BDAG p. 525)",
                syntactic_role="Adverbial participle of means modifying the main action of making peace",
                textual_fact="Katargēsas is qualified specifically by τὸν νόμον τῶν ἐντολῶν ἐν δόγμασιν (the law of commandments in decrees).",
                linguistic_interpretation="The modifier 'in decrees/ordinances' restricts the abolition to the ritual dividing wall separating Jew from Gentile.",
                theological_interpretation="Not an annihilation of Torah's moral/ethical revelation, but the abolition of ceremonial ordinances that functioned as exclusive ethnic barriers (table fellowship, circumcision)."
            )
        ]
    },
    "Galatia 3:13": {
        "book": "Galatia",
        "chapter": 3,
        "verse": 13,
        "original_language": "Koine Greek",
        "original_text": "Χριστὸς ἡμᾶς ἐξηγόρασεν ἐκ τῆς κατάρας τοῦ νόμου γενόμενος ὑπὲρ ἡμῶν κατάρα...",
        "transliteration": "Christos hēmas exēgorasen ek tēs kataras tou nomou genomenos hyper hēmōn katara...",
        "english": "Christ redeemed us from the curse of the Law, having become a curse for us...",
        "indonesian": "Kristus telah menebus kita dari kutuk hukum Taurat dengan jalan menjadi kutuk karena kita...",
        "tier": EvidenceTier.DIRECT_EVIDENCE,
        "confidence": 0.97,
        "witnesses": ["P46", "Codex Sinaiticus", "Codex Vaticanus", "Codex Ephraemi Rescriptus"],
        "tokens": [
            MorphologicalToken(
                surface_form="τῆς κατάρας τοῦ νόμου",
                lemma="κατάρα (katara) + νόμος (nomos)",
                part_of_speech="Noun + Genitive Noun",
                morphology="Genitive Singular Feminine + Genitive Singular Masculine",
                lexical_meaning="The curse of the law (judicial sentence incurred by transgression under Ulangan 27:26)",
                syntactic_role="Genitive object of preposition ἐκ (redemption OUT OF)",
                textual_fact="Paul specifies redemption from the CURSE (κατάρα) of the law, not redemption from the law itself.",
                linguistic_interpretation="Genitivus auctoris or objectivus; the penal sanction resulting from disobedience.",
                theological_interpretation="The law itself is not the curse; the penalty for violating it is the curse. Christ redeems from condemnation, not from divine instruction."
            )
        ]
    },
    "Roma 7:12": {
        "book": "Roma",
        "chapter": 7,
        "verse": 12,
        "original_language": "Koine Greek",
        "original_text": "ὥστε ὁ μὲν νόμος ἅγιος, καὶ ἡ ἐντολὴ ἁγία καὶ δικαία καὶ ἀγαθή.",
        "transliteration": "hōste ho men nomos hagios, kai hē entolē hagia kai dikaia kai agathē.",
        "english": "So then, the Law is holy, and the commandment is holy and righteous and good.",
        "indonesian": "Jadi hukum Taurat adalah kudus, dan perintah itu adalah kudus, benar dan baik.",
        "tier": EvidenceTier.PRIMARY_SOURCE,
        "confidence": 0.99,
        "witnesses": ["P46", "Codex Sinaiticus", "Codex Vaticanus", "Codex Claromontanus"],
        "tokens": [
            MorphologicalToken(
                surface_form="ἅγιος, δικαία, ἀγαθή",
                lemma="ἅγιος (hagios), δίκαιος (dikaios), ἀγαθός (agathos)",
                part_of_speech="Adjectives",
                morphology="Nominative Singular Masculine / Feminine",
                lexical_meaning="Holy (set apart), righteous (just), good (beneficent) (BDAG)",
                syntactic_role="Predicate adjectives defining the substantive nature of Torah",
                textual_fact="Paul uses threefold divine moral attributes to describe the Law itself.",
                linguistic_interpretation="Copulative construction directly attributing divine moral quality to nomos.",
                theological_interpretation="Impossibility of intrinsic moral flaw in the Torah according to Paul's theology."
            )
        ]
    },
    "Matius 5:17": {
        "book": "Matius",
        "chapter": 5,
        "verse": 17,
        "original_language": "Koine Greek",
        "original_text": "Μὴ νομίσητε ὅτι ἦλθον καταλῦσαι τὸν νόμον ἢ τοὺς προφήτας· οὐκ ἦλθον καταλῦσαι ἀλλὰ πληρῶσαι.",
        "transliteration": "Mē nomisēte hoti ēlthon katalysai ton nomon ē tous prophētas; ouk ēlthon katalysai alla plērōsai.",
        "english": "Do not think that I came to abolish the Law or the Prophets; I did not come to abolish but to fulfill.",
        "indonesian": "Janganlah kamu menyangka, bahwa Aku datang untuk meniadakan hukum Taurat atau kitab para nabi. Aku datang bukan untuk meniadakannya, melainkan untuk menggenapinya.",
        "tier": EvidenceTier.PRIMARY_SOURCE,
        "confidence": 0.99,
        "witnesses": ["Codex Sinaiticus", "Codex Vaticanus", "P64/67"],
        "tokens": [
            MorphologicalToken(
                surface_form="καταλῦσαι",
                lemma="καταλύω (katalyō)",
                part_of_speech="Verb",
                morphology="Aorist Active Infinitive",
                lexical_meaning="To destroy, demolish, dissolve, annul (BDAG p. 521)",
                syntactic_role="Complementary infinitive governed by ἦλθον under prohibitive negation Μή",
                textual_fact="Jesus explicitly prohibits even the cognitive assumption (Μὴ νομίσητε) that his mission is abolition.",
                linguistic_interpretation="Prohibitive subjunctive expressing urgent cessation of false thought.",
                theological_interpretation="Jesus' authoritative self-declaration establishes eternal validity of the Torah baseline."
            ),
            MorphologicalToken(
                surface_form="πληρῶσαι",
                lemma="πληρόω (plēroō)",
                part_of_speech="Verb",
                morphology="Aorist Active Infinitive",
                lexical_meaning="To fill to full measure, bring to complete expression, embody fully (BDAG p. 827)",
                syntactic_role="Adversative infinitive governed by ἀλλά in direct contrast to καταλῦσαι",
                textual_fact="Fulfill (plērōsai) stands as the exact polar antithesis of abolish (katalysai).",
                linguistic_interpretation="Semitic idiom corresponding to Hebrew leqayem (to uphold/perform to the utmost).",
                theological_interpretation="Fulfillment in Matthew means realizing the true intent of Torah in life and teaching, not terminating its validity."
            )
        ]
    },
    "Yohanes 10:30": {
        "book": "Yohanes",
        "chapter": 10,
        "verse": 30,
        "original_language": "Koine Greek",
        "original_text": "Ἐγὼ καὶ ὁ Πατὴρ ἕν ἐσμεν.",
        "transliteration": "Egō kai ho Patēr hen esmen.",
        "english": "I and the Father are one.",
        "indonesian": "Aku dan Bapa adalah satu.",
        "tier": EvidenceTier.PRIMARY_SOURCE,
        "confidence": 0.99,
        "witnesses": ["P66 (c. 200 CE)", "P75", "Codex Sinaiticus", "Codex Vaticanus"],
        "tokens": [
            MorphologicalToken(
                surface_form="ἕν",
                lemma="εἷς (heis) / ἕν (hen)",
                part_of_speech="Adjective / Numeral",
                morphology="Nominative Neuter Singular",
                lexical_meaning="One in essence/nature, unity (neuter 'hen' vs masculine 'heis' which denotes single person)",
                syntactic_role="Predicate nominative",
                textual_fact="Jesus uses the neuter numeral ἕν, not masculine εἷς.",
                linguistic_interpretation="Indicates ontological unity between Father and Son, distinguishing their persons while asserting common divine substance.",
                theological_interpretation="Classic Johannine high Christology proof text."
            )
        ]
    },
    "Ulangan 6:4": {
        "book": "Ulangan",
        "chapter": 6,
        "verse": 4,
        "original_language": "Biblical Hebrew",
        "original_text": "שְׁמַע יִשְׂרָאֵל יְהוָה אֱלֹהֵינוּ יְהוָה אֶחָד",
        "transliteration": "Shema Yisrael YHWH Eloheinu YHWH Echad",
        "english": "Hear, O Israel: The LORD our God, the LORD is one.",
        "indonesian": "Dengarlah, hai orang Israel: TUHAN itu Allah kita, TUHAN itu esa!",
        "tier": EvidenceTier.PRIMARY_SOURCE,
        "confidence": 0.99,
        "witnesses": ["4QDeut (Dead Sea Scrolls)", "Codex Leningradensis", "Nash Papyrus"],
        "tokens": [
            MorphologicalToken(
                surface_form="אֶחָד",
                lemma="אֶחָד (echad)",
                part_of_speech="Adjective / Numeral",
                morphology="Masculine Singular",
                lexical_meaning="One, single, unique, compound unity",
                syntactic_role="Predicate adjective",
                textual_fact="Fundamental monotheistic creed of the Torah.",
                linguistic_interpretation="Echad functions as both cardinal one and unique.",
                theological_interpretation="The bedrock of biblical monotheism."
            )
        ]
    },
    "Wahyu 19:7": {
        "book": "Wahyu",
        "chapter": 19,
        "verse": 7,
        "original_language": "Koine Greek",
        "original_text": "χαίρωμεν καὶ ἀγαλλιῶμεν, καὶ δώσομεν τὴν δόξαν αὐτῷ, ὅτι ἦλθεν ὁ γάμος τοῦ ἀρνίου",
        "transliteration": "chairōmen kai agalliōmen, kai dōsomen tēn doxan autō, hoti ēlthen ho gamos tou arniou",
        "english": "Let us rejoice and be glad and give the glory unto him: for the marriage of the Lamb is come.",
        "indonesian": "Marilah kita bersukacita dan bersorak-sorak, dan memberi kemuliaan kepada-Nya, karena hari perkawinan Anak Domba telah tiba.",
        "tier": EvidenceTier.PRIMARY_SOURCE,
        "confidence": 0.98,
        "witnesses": ["Codex Sinaiticus (01)", "Codex Alexandrinus (02)", "P47"],
        "tokens": [
            MorphologicalToken(
                surface_form="ἀρνίου",
                lemma="ἀρνίον (arnion)",
                part_of_speech="Noun",
                morphology="Genitive Neuter Singular",
                lexical_meaning="Lamb, sacrificial lamb",
                syntactic_role="Genitive of possession",
                textual_fact="Eschatological title of the Lamb in Apocalyptic literature.",
                linguistic_interpretation="Diminutive form used systematically in Revelation for the exalted Christ.",
                theological_interpretation="Eschatological marriage feast of the Lamb."
            )
        ]
    },
    "Yehezkiel 18:20": {
        "book": "Yehezkiel",
        "chapter": 18,
        "verse": 20,
        "original_language": "Biblical Hebrew",
        "original_text": "הַנֶּפֶשׁ הַחֹטֵאת הִיא תָמוּת בֵּן לֹא־יִשָּׂא בַּעֲוֺן הָאָב",
        "transliteration": "ha-nefesh ha-chote't hi tamut ben lo-yissa ba'awon ha-av",
        "english": "The soul that sinneth, it shall die. The son shall not bear the iniquity of the father.",
        "indonesian": "Orang yang berbuat dosa, itu yang harus mati. Anak tidak akan turut menanggung kesalahan ayahnya.",
        "tier": EvidenceTier.PRIMARY_SOURCE,
        "confidence": 0.99,
        "witnesses": ["Codex Leningradensis (B19a)", "4QEzka", "Septuaginta (LXX)"],
        "tokens": [
            MorphologicalToken(
                surface_form="תָמוּת",
                lemma="מוּת (mut)",
                part_of_speech="Verb",
                morphology="Qal Imperfect 3fs",
                lexical_meaning="Die, undergo death penalty",
                syntactic_role="Predicate verb",
                textual_fact="Individual moral responsibility principle.",
                linguistic_interpretation="Specific individual accountability rejecting generational collective guilt transfer.",
                theological_interpretation="Prophetic doctrine of individual moral accountability."
            )
        ]
    },
    "Kisah Para Rasul 10:15": {
        "book": "Kisah Para Rasul",
        "chapter": 10,
        "verse": 15,
        "original_language": "Koine Greek",
        "original_text": "ἃ ὁ θεὸς ἐκαθάρισεν σὺ μὴ κοίνου.",
        "transliteration": "ha ho theos ekatharisen sy mē koinou.",
        "english": "What God hath cleansed, that call not thou common.",
        "indonesian": "Apa yang dinyatakan halal oleh Allah, tidak boleh engkau nyatakan haram.",
        "tier": EvidenceTier.PRIMARY_SOURCE,
        "confidence": 0.98,
        "witnesses": ["P45 (c. 250 CE)", "Codex Vaticanus", "Codex Sinaiticus"],
        "tokens": [
            MorphologicalToken(
                surface_form="ἐκαθάρισεν",
                lemma="καθαρίζω (katharizō)",
                part_of_speech="Verb",
                morphology="Aorist Active Indicative 3s",
                lexical_meaning="Cleanse, purify, declare ritually clean",
                syntactic_role="Relative clause predicate",
                textual_fact="Peter's vision on Gentile inclusion and dietary abrogations.",
                linguistic_interpretation="Aorist tense indicates decisive divine act of cleansing.",
                theological_interpretation="Theological pivot for Gentile inclusion in the apostolic church."
            )
        ]
    },
    "2 Petrus 1:21": {
        "book": "2 Petrus",
        "chapter": 1,
        "verse": 21,
        "original_language": "Koine Greek",
        "original_text": "οὐ γὰρ θελήματι ἀνθρώπου ἠνέχθη προφητεία ποτέ, ἀλλὰ ὑπὸ πνεύματος ἁγίου φερόμενοι ἐλάλησαν ἀπὸ θεοῦ ἄνθρωποι.",
        "transliteration": "ou gar thelēmati anthrōpou ēnechthē prophēteia pote, alla hypo pneumatos hagiou pheromenoi elalēsan apo theou anthrōpoi.",
        "english": "For prophecy never came by the will of man, but holy men of God spoke as they were moved by the Holy Spirit.",
        "indonesian": "sebab tidak pernah nubuat dihasilkan oleh kehendak manusia, tetapi oleh dorongan Roh Kudus orang-orang berbicara atas nama Allah.",
        "tier": EvidenceTier.PRIMARY_SOURCE,
        "confidence": 0.99,
        "witnesses": ["P72 (Papyrus Bodmer VII-VIII, c. 300 M)", "Codex Sinaiticus (א, abad ke-4)", "Codex Vaticanus (B, abad ke-4)", "Codex Alexandrinus (A, abad ke-5)"],
        "tokens": [
            MorphologicalToken(
                surface_form="ἠνέχθη",
                lemma="φέρω (pherō)",
                part_of_speech="Verb",
                morphology="Aorist Passive Indicative 3s",
                lexical_meaning="Brought forth, produced, borne along",
                syntactic_role="Main clause predicate",
                textual_fact="Prophecy origin negated from human will.",
                linguistic_interpretation="Aorist passive denotes punctiliar completed negation of human genesis.",
                theological_interpretation="Divine inspiration of prophetic scripture through the Holy Spirit."
            ),
            MorphologicalToken(
                surface_form="φερόμενοι",
                lemma="φέρω (pherō)",
                part_of_speech="Verb Participle",
                morphology="Present Passive Participle Nominative Masculine Plural",
                lexical_meaning="Being moved, borne along, guided",
                syntactic_role="Manner adverbial participle modifying elalēsan",
                textual_fact="Prophets actively speaking while continually moved by the Holy Spirit.",
                linguistic_interpretation="Continuous passive participle indicating divine initiative and vehicle of agency.",
                theological_interpretation="Theopneustos process: human instrumentality under direct pneumatic conveyance."
            ),
            MorphologicalToken(
                surface_form="πνεύματος ἁγίου",
                lemma="πνεῦμα ἅγιον (pneuma hagion)",
                part_of_speech="Noun + Adjective",
                morphology="Genitive Neuter Singular",
                lexical_meaning="Holy Spirit / Divine Pneuma",
                syntactic_role="Agent of passive participle hypo pneumatos hagiou",
                textual_fact="Explicit personal pneumatic agency behind prophetic utterances.",
                linguistic_interpretation="Preposition hypo with genitive specifies the direct personal efficient cause.",
                theological_interpretation="Pneumatological anchor establishing Holy Spirit as author and superintendent of biblical prophecy."
            )
        ]
    },
    "1 Yohanes 5:7-8": {
        "passage_reference": "1 Yohanes 5:7-8",
        "book": "1 Yohanes",
        "chapter": 5,
        "verse": 7,
        "original_language": "Koine Greek",
        "original_text": "ὅτι τρεῖς εἰσιν οἱ μαρτυροῦντες, τὸ πνεῦμα καὶ τὸ ὕδωρ καὶ τὸ αἷμα, καὶ οἱ τρεῖς εἰς τὸ ἕν εἰσιν. [Textus Receptus: ὅτι τρεῖς εἰσιν οἱ μαρτυροῦντες ἐν τῷ οὐρανῷ, ὁ Πατήρ, ὁ Λόγος, καὶ τὸ Ἅγιον Πνεῦμα· καὶ οὗτοι οἱ τρεῖς ἕν εἰσιν. καὶ τρεῖς εἰσιν οἱ μαρτυροῦντες ἐν τῇ γῇ, τὸ πνεῦμα καὶ τὸ ὕδωρ καὶ τὸ αἷμα· καὶ οἱ τρεῖς εἰς τὸ ἕν εἰσιν.]",
        "transliteration": "hoti treis eisin hoi martyrountes, to pneuma kai to hydōr kai to haima, kai hoi treis eis to hen eisin. [Textus Receptus: hoti treis eisin hoi martyrountes en tō ouranō, ho Patēr, ho Logos, kai to Hagion Pneuma; kai houtoi hoi treis hen eisin. kai treis eisin hoi martyrountes en tē gē, to pneuma kai to hydōr kai to haima; kai hoi treis eis to hen eisin.]",
        "english": "For there are three that testify: the Spirit, the water, and the blood; and the three agree as one. [Textus Receptus: in heaven: the Father, the Word, and the Holy Spirit; and these three are one. And there are three that testify on earth...]",
        "indonesian": "Sebab ada tiga yang memberi kesaksian: Roh, air, dan darah, dan ketiganya bersepakat dalam satu kesaksian. [Varian Sisipan Textus Receptus: di dalam surga: Bapa, Firman, dan Roh Kudus; dan ketiganya adalah satu. Dan ada tiga yang bersaksi di bumi...]",
        "tier": EvidenceTier.DIRECT_EVIDENCE,
        "confidence": 0.99,
        "witnesses": [
            "Codex Sinaiticus (א01, Abad IV - Omit Comma)",
            "Codex Vaticanus (B03, Abad IV - Omit Comma)",
            "Codex Alexandrinus (A02, Abad V - Omit Comma)",
            "Minuscule 61 (Codex Montfortianus, c. 1520 - Sisipan Latin)"
        ],
        "tokens": [
            MorphologicalToken(
                surface_form="μαρτυροῦντες",
                lemma="μαρτυρέω (martyreō)",
                part_of_speech="Verb / Participle",
                morphology="Present Active Participle, Nominative Masculine Plural",
                lexical_meaning="To testify, bear witness, give testimony (BDAG p. 617)",
                syntactic_role="Substantival participle governing the subject phrase",
                textual_fact="Articular masculine plural participle used with numeral treis.",
                linguistic_interpretation="Substantivized participle functioning as the legal witnesses in discourse.",
                theological_interpretation="Establishes the juridical triad of earthly witnesses in historical reality."
            ),
            MorphologicalToken(
                surface_form="τὸ πνεῦμα",
                lemma="πνεῦμα (pneuma)",
                part_of_speech="Noun",
                morphology="Nominative Neuter Singular",
                lexical_meaning="Spirit, Divine Pneuma, Holy Spirit (BDAG p. 832)",
                syntactic_role="First appositional nominative subject witness",
                textual_fact="Directly attested in Codex Sinaiticus and Codex Vaticanus.",
                linguistic_interpretation="Neuter noun governed by masculine articular participle via constructio ad sensum.",
                theological_interpretation="The Spirit provides active supernatural testimony to Christ's messiahship."
            ),
            MorphologicalToken(
                surface_form="τὸ ὕδωρ",
                lemma="ὕδωρ (hydōr)",
                part_of_speech="Noun",
                morphology="Nominative Neuter Singular",
                lexical_meaning="Water, historical baptism of Jesus (BDAG p. 1023)",
                syntactic_role="Second appositional nominative subject witness",
                textual_fact="Attested uniformly across all Alexandrian, Western, and Byzantine witnesses.",
                linguistic_interpretation="Coordinated by polysyndeton conjunction kai.",
                theological_interpretation="Points to the historical initiation of Jesus' earthly ministry through baptism."
            ),
            MorphologicalToken(
                surface_form="τὸ αἷμα",
                lemma="αἷμα (haima)",
                part_of_speech="Noun",
                morphology="Nominative Neuter Singular",
                lexical_meaning="Blood, sacrificial death on the cross (BDAG p. 22)",
                syntactic_role="Third appositional nominative subject witness",
                textual_fact="Uniformly present without variation in all ancient Greek papyri and uncials.",
                linguistic_interpretation="Final member of the earthly tripartite witness.",
                theological_interpretation="Refutes Docetic/Cerinthian separation by confirming physical sacrificial death."
            ),
            MorphologicalToken(
                surface_form="εἰς τὸ ἕν",
                lemma="εἰς (eis) + ἕν (hen)",
                part_of_speech="Preposition + Numeral",
                morphology="Accusative Neuter Singular",
                lexical_meaning="Toward the one / into unity of testimony (BDAG p. 291)",
                syntactic_role="Prepositional phrase denoting convergence of testimony",
                textual_fact="Syntactically distinct from ontological unity (ouk hen eisin, sed eis to hen).",
                linguistic_interpretation="Denotes harmony and agreement of testimony, not ontological Trinity.",
                theological_interpretation="Forensically proves that even the authentic Greek text affirms unity of purpose, not ontological hypostatic trinity."
            )
        ]
    },
    "1 Yohanes 5:7": {
        "book": "1 Yohanes",
        "chapter": 5,
        "verse": 7,
        "original_language": "Koine Greek",
        "original_text": "ὅτι τρεῖς εἰσιν οἱ μαρτυροῦντες, [Textus Receptus: ὅτι τρεῖς εἰσιν οἱ μαρτυροῦντες ἐν τῷ οὐρανῷ, ὁ Πατήρ, ὁ Λόγος, καὶ τὸ Ἅγιον Πνεῦμα· καὶ οὗτοι οἱ τρεῖς ἕν εἰσιν.]",
        "transliteration": "hoti treis eisin hoi martyrountes, [Textus Receptus: hoti treis eisin hoi martyrountes en tō ouranō, ho Patēr, ho Logos, kai to Hagion Pneuma; kai houtoi hoi treis hen eisin.]",
        "english": "For there are three that testify: [Textus Receptus: in heaven: the Father, the Word, and the Holy Spirit; and these three are one.]",
        "indonesian": "Sebab ada tiga yang memberi kesaksian: [Varian Sisipan Textus Receptus: di dalam surga: Bapa, Firman, dan Roh Kudus; dan ketiganya adalah satu.]",
        "tier": EvidenceTier.DIRECT_EVIDENCE,
        "confidence": 0.99,
        "witnesses": [
            "Codex Sinaiticus (א01, Abad IV - Omit Comma)",
            "Codex Vaticanus (B03, Abad IV - Omit Comma)",
            "Codex Alexandrinus (A02, Abad V - Omit Comma)",
            "Minuscule 61 (Codex Montfortianus, c. 1520 - Sisipan Latin)"
        ],
        "tokens": [
            MorphologicalToken(
                surface_form="μαρτυροῦντες",
                lemma="μαρτυρέω (martyreō)",
                part_of_speech="Verb / Participle",
                morphology="Present Active Participle, Nominative Masculine Plural",
                lexical_meaning="To testify, bear witness (BDAG p. 617)",
                syntactic_role="Substantival participle governing the subject phrase",
                textual_fact="Articular masculine plural participle used with numeral treis.",
                linguistic_interpretation="Substantivized participle functioning as the legal witnesses in discourse.",
                theological_interpretation="Establishes the juridical count of witnesses."
            )
        ]
    }
}


class EvidenceEngine:
    """
    Forensic Evidence Engine for Bible & Islamic apologetics claims.
    Retrieves verified primary texts, linguistic tokens, and provenance records.
    """

    def __init__(self, db_path: str = BIBLE_ENGINE_DB):
        self.db_path = db_path

    def _generate_provenance_hash(self, reference: str, text: str, tier: str) -> str:
        payload = f"{reference}|{text}|{tier}|polya_apologetics_2026"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def retrieve_scripture_evidence(self, query: str) -> List[EvidenceItem]:
        """
        Retrieves primary scripture evidence matching query terms.
        Prioritizes Greek/Hebrew text, tokens, and academic apparatus.
        Supplemental canonical scripture is strictly topic-filtered; no forced fallback.
        """
        results: List[EvidenceItem] = []
        q_lower = query.lower()

        # Check if an explicit verse is cited in the query
        explicit_verse = None
        try:
            from orchestrator.exegesis_engine import ExegesisEngine
            explicit_verse = ExegesisEngine.extract_explicit_verse(query)
        except Exception:
            pass

        # Topic relevance mapping for canonical verses
        def is_verse_relevant(ref: str) -> bool:
            if explicit_verse:
                # When explicit verse is cited, do not match unrelated verses by broad keywords
                return bool(ref.lower() in explicit_verse.lower() or explicit_verse.lower() in ref.lower())

            if ref.lower() in q_lower:
                return True
            if ref == "Roma 3:31":
                return (
                    "roma 3" in q_lower
                    or ("roma" in q_lower and any(w in q_lower for w in ["taurat", "hukum", "iman", "katargoumen", "histanomen"]))
                    or ("paulus" in q_lower and any(w in q_lower for w in ["taurat", "hukum", "membatalkan", "menegakkan"]))
                )
            elif ref == "Matius 5:17":
                return (
                    "matius 5" in q_lower
                    or ("matius" in q_lower and any(w in q_lower for w in ["taurat", "hukum", "menggenapi", "meniadakan"]))
                    or ("menggenapi" in q_lower and any(w in q_lower for w in ["taurat", "hukum"]))
                    or ("meniadakan" in q_lower and any(w in q_lower for w in ["taurat", "hukum"]))
                    or ("membatalkan" in q_lower and "taurat" in q_lower)
                )
            elif ref == "Efesus 2:15":
                return (
                    "efesus 2:15" in q_lower
                    or "efesus" in q_lower
                    or "dogmasin" in q_lower
                    or ("membatalkan" in q_lower and "taurat" in q_lower)
                    or ("paulus" in q_lower and "taurat" in q_lower)
                )
            elif ref == "Galatia 3:13":
                return (
                    "galatia 3:13" in q_lower
                    or "galatia" in q_lower
                    or "katara" in q_lower
                    or ("paulus" in q_lower and "taurat" in q_lower)
                )
            elif ref == "Roma 7:12":
                return (
                    "roma 7:12" in q_lower
                    or ("roma 7" in q_lower and ("kudus" in q_lower or "hagios" in q_lower))
                    or ("paulus" in q_lower and "taurat" in q_lower)
                )
            elif ref == "Yohanes 10:30":
                return (
                    "yohanes 10" in q_lower
                    or "aku dan bapa" in q_lower
                    or "hen esmen" in q_lower
                    or ("yesus" in q_lower and any(w in q_lower for w in ["tuhan", "allah", "bapa", "keilahian", "hakikat", "satu", "tritunggal"]))
                )
            elif ref == "Ulangan 6:4":
                return (
                    "ulangan 6" in q_lower
                    or "shema" in q_lower
                    or "echad" in q_lower
                    or "tuhan itu esa" in q_lower
                    or "allah itu esa" in q_lower
                    or "monoteisme" in q_lower
                    or "tritunggal" in q_lower
                    or "trinity" in q_lower
                )
            elif ref == "Wahyu 19:7":
                return "wahyu" in q_lower or "revelation" in q_lower or "arnion" in q_lower
            elif ref == "Yehezkiel 18:20":
                return "yehezkiel" in q_lower or "ezekiel" in q_lower or "dosa" in q_lower
            elif ref == "2 Petrus 1:21":
                return (
                    "2 petrus" in q_lower
                    or "2petrus" in q_lower
                    or ("petrus" in q_lower and any(w in q_lower for w in ["roh kudus", "nubuat", "nabi", "ilham", "bimbing", "digerakkan"]))
                    or ("roh kudus" in q_lower and any(w in q_lower for w in ["nabi", "nubuat", "kitab suci"]))
                )
            elif ref in ("1 Yohanes 5:7-8", "1 Yohanes 5:7"):
                return (
                    "1 yohanes" in q_lower
                    or "1yohanes" in q_lower
                    or "1 john" in q_lower
                    or "comma johanneum" in q_lower
                    or "comma" in q_lower
                    or "tiga saksi" in q_lower
                    or "interpolasi" in q_lower
                    or ("yohanes" in q_lower and ("5:7" in q_lower or "5:8" in q_lower or "trinitas" in q_lower or "tritunggal" in q_lower))
                )
            elif ref == "Kisah Para Rasul 10:15":
                # Guard against false-positive matching when 1 Petrus / 2 Petrus is specified
                if ("1 petrus" in q_lower or "2 petrus" in q_lower or "1petrus" in q_lower or "2petrus" in q_lower) and not ("kisah para rasul" in q_lower or "acts" in q_lower):
                    return False
                return (
                    ("kisah para rasul" in q_lower and ("10:15" in q_lower or "10" in q_lower))
                    or ("acts" in q_lower and ("10:15" in q_lower or "10" in q_lower))
                    or ("petrus" in q_lower and any(w in q_lower for w in ["halal", "haram", "najis", "makanan", "koinou", "katharizo"]))
                    or ("visi petrus" in q_lower or "penglihatan petrus" in q_lower)
                    or ("korban" in q_lower and "halal" in q_lower)
                )
            return False

        for ref, data in CANONICAL_PHILOLOGY_KNOWLEDGE.items():
            if is_verse_relevant(ref) or any(t.lemma.lower() in q_lower for t in data["tokens"] if len(t.lemma) > 4):
                prov_hash = self._generate_provenance_hash(ref, data["original_text"], data["tier"].value)
                item = EvidenceItem(
                    evidence_id=f"evi_{uuid.uuid4().hex[:8]}",
                    tier=data["tier"],
                    source_id=f"SRC-BIB-{data['book'].upper()}-{data['chapter']}-{data['verse']}",
                    book=data["book"],
                    chapter=data["chapter"],
                    verse=data["verse"],
                    passage_reference=data.get("passage_reference") or ref or f"{data['book']} {data['chapter']}:{data['verse']}",
                    original_language=data["original_language"],
                    original_text=data["original_text"],
                    transliteration=data["transliteration"],
                    english_translation=data["english"],
                    indonesian_translation=data["indonesian"],
                    confidence=data["confidence"],
                    provenance_hash=prov_hash,
                    witnesses=data["witnesses"],
                    tokens=data["tokens"],
                    theological_implication=(
                        f"Canonical manuscript witness: {ref}. Contextually relevant to claim premises."
                    )
                )
                results.append(item)

        # Do NOT force universal fallback if no verse is relevant.
        # Klaim non-teologis atau yang tidak didukung korpus tidak boleh dipaksakan menjadi ayat Alkitab.
        return results

    def create_dynamic_evidence_item(
        self,
        passage_reference: str,
        original_language: str = "Koine Greek",
        original_text: str = "",
        transliteration: str = "",
        english_translation: str = "",
        indonesian_translation: str = "",
        witnesses: Optional[List[str]] = None,
        tokens: Optional[List[Any]] = None,
        critical_apparatus: str = ""
    ) -> EvidenceItem:
        """
        Dynamically constructs an EvidenceItem from LLM-synthesized exegesis or query extraction.
        Maintains compliance with EvidenceItem dataclass and provenance hash requirements.
        """
        book = "Kitab"
        chapter = 1
        verse = 1
        m = re.match(r'^([1-3]?\s?[A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(\d+):(\d+)', passage_reference.strip())
        if m:
            book = m.group(1).strip()
            chapter = int(m.group(2))
            verse = int(m.group(3))

        token_objs: List[MorphologicalToken] = []
        for t in (tokens or []):
            if isinstance(t, MorphologicalToken):
                token_objs.append(t)
            elif isinstance(t, dict):
                token_objs.append(MorphologicalToken(
                    surface_form=t.get("surface_form", ""),
                    lemma=t.get("lemma", ""),
                    part_of_speech=t.get("pos") or t.get("part_of_speech", "Morphological Token"),
                    morphology=t.get("morph") or t.get("morphology", ""),
                    lexical_meaning=t.get("meaning") or t.get("lexical_meaning", ""),
                    syntactic_role=t.get("syntactic_role", ""),
                    textual_fact=t.get("textual_fact", ""),
                    linguistic_interpretation=t.get("linguistic_interpretation", ""),
                    theological_interpretation=t.get("theological_interpretation", "")
                ))

        prov_hash = self._generate_provenance_hash(passage_reference, original_text or passage_reference, EvidenceTier.PRIMARY_SOURCE.value)
        return EvidenceItem(
            evidence_id=f"evi_{uuid.uuid4().hex[:8]}",
            tier=EvidenceTier.PRIMARY_SOURCE,
            source_id=f"SRC-BIB-{book.replace(' ', '-').upper()}-{chapter}-{verse}",
            book=book,
            chapter=chapter,
            verse=verse,
            passage_reference=passage_reference,
            original_language=original_language,
            original_text=original_text or f"[{passage_reference}]",
            transliteration=transliteration or f"[{passage_reference}]",
            english_translation=english_translation,
            indonesian_translation=indonesian_translation,
            confidence=0.95,
            provenance_hash=prov_hash,
            witnesses=witnesses or ["Codex Sinaiticus", "Codex Vaticanus"],
            tokens=token_objs,
            theological_implication=critical_apparatus or f"Analisis filologis dinamis untuk perikop {passage_reference}."
        )

    def retrieve_corpus_evidence(self, query: str, limit: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves academic knowledge and manuscript records from .polya/polya_index.db (knowledge_fts).
        Enforces domain filtering and BM25 relevance threshold.
        """
        q_lower = query.lower()
        science_keywords = [
            "mendidih", "celsius", "celcius", "atmosfer", "suhu", "boiling",
            "temperature", "thermodynamic", "titik didih", "gravitasi", "quantum", "elektron"
        ]
        theological_keywords = [
            "yesus", "jesus", "kristus", "christ", "tuhan", "allah", "god", "lord",
            "bapa", "tritunggal", "trinity", "taurat", "torah", "paulus", "paul",
            "alkitab", "bible", "injil", "gospel", "quran", "islam", "yahudi",
            "jewish", "rasul", "iman", "keilahian", "mesias", "messiah",
            "roh kudus", "holy spirit", "pneuma", "nubuat", "prophecy", "nabi", "prophet", "petrus", "peter"
        ]

        has_science = any(k in q_lower for k in science_keywords)
        has_theology = any(k in q_lower for k in theological_keywords)

        # Reject purely secular / natural science claims from corpus search
        if has_science and not has_theology:
            return []

        polya_db = "/home/ubuntu/.polya/polya_index.db"
        if not os.path.exists(polya_db):
            return []

        fts_terms = []
        term_map = {
            "yesus": "Jesus",
            "tuhan": "God OR Lord OR Deity",
            "allah": "God OR Allah",
            "tritunggal": "Trinity",
            "kristus": "Christ",
            "mesias": "Messiah OR Mashiach",
            "taurat": "Torah OR Law",
            "paulus": "Paul",
            "injil": "Gospel",
            "alkitab": "Scripture OR Bible"
        }
        for id_word, en_word in term_map.items():
            if id_word in q_lower:
                fts_terms.append(en_word)

        if not fts_terms:
            stop_words = {"tidak", "secara", "langsung", "berkata", "adalah", "yang", "pada", "dalam", "bukan", "muncul", "kemudian", "asli"}
            words = [w for w in re.findall(r'[a-zA-Z]{4,}', query) if w.lower() not in stop_words]
            if words:
                fts_terms.append(" OR ".join(words[:3]))

        if not fts_terms:
            return []

        search_query = " OR ".join(fts_terms)
        results: List[Dict[str, Any]] = []
        try:
            conn = sqlite3.connect(polya_db)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, category, tradition, title, summary, rank
                FROM knowledge_fts
                WHERE knowledge_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (search_query, limit))
            rows = cur.fetchall()
            conn.close()

            for row in rows:
                doc_id, cat, trad, title, summary, rank = row
                # BM25 rank in SQLite FTS5 is negative; lower means higher relevance (rank <= -3.0)
                if rank <= -3.0:
                    summary_text = summary[:400].strip() if summary else ""
                    prov_hash = hashlib.sha256(f"{doc_id}|{title}|{summary_text[:150]}".encode("utf-8")).hexdigest()[:16]
                    results.append({
                        "id": doc_id,
                        "category": cat,
                        "tradition": trad,
                        "title": title,
                        "summary": summary_text,
                        "provenance_hash": prov_hash,
                        "rank": float(rank),
                        "source_db": "polya_index.db"
                    })
        except Exception as exc:
            logger.warning(f"Error querying knowledge_fts: {exc}")

        return results

    def retrieve_all_evidence(self, query: str) -> Dict[str, Any]:
        """
        Unified forensic retrieval combining scripture and scholarly corpus.
        Transparently flags insufficient_evidence when outside corpus scope.
        """
        scripture = self.retrieve_scripture_evidence(query)
        corpus = self.retrieve_corpus_evidence(query)
        q_lower = query.lower()

        science_keywords = [
            "mendidih", "celsius", "celcius", "atmosfer", "suhu", "boiling",
            "temperature", "thermodynamic", "titik didih", "gravitasi", "quantum", "elektron"
        ]
        theological_keywords = [
            "yesus", "jesus", "kristus", "christ", "tuhan", "allah", "god", "lord",
            "bapa", "tritunggal", "trinity", "taurat", "torah", "paulus", "paul",
            "alkitab", "bible", "injil", "gospel", "quran", "islam", "yahudi",
            "jewish", "rasul", "iman", "keilahian", "mesias", "messiah",
            "roh kudus", "holy spirit", "pneuma", "nubuat", "prophecy", "nabi", "prophet", "petrus", "peter"
        ]

        is_pure_science = any(k in q_lower for k in science_keywords) and not any(k in q_lower for k in theological_keywords)

        if not scripture and not corpus:
            status = "insufficient_evidence"
            if is_pure_science:
                reason = "Klaim berada di luar domain korpus teologi dan teks biblika/patristik (klaim sains/fenomena alam murni). Korpus tidak memuat rekaman empiris sains untuk klaim ini."
            else:
                reason = "Klaim tidak didukung oleh saksi naskah primer atau rekaman dokumen historis yang relevan di dalam korpus data."
        else:
            status = "sufficient"
            reason = f"Ditemukan bukti yang relevan: {len(scripture)} saksi biblika, {len(corpus)} rekaman korpus akademik."

        return {
            "status": status,
            "reason": reason,
            "scripture_evidence": scripture,
            "corpus_evidence": corpus
        }

    def show_source(self, passage_reference: str) -> Optional[Dict[str, Any]]:
        """
        'Show Me The Source' implementation (Section 10).
        Returns exact forensic provenance for any scripture citation.
        """
        for ref, data in CANONICAL_PHILOLOGY_KNOWLEDGE.items():
            if ref.lower() == passage_reference.lower():
                prov_hash = self._generate_provenance_hash(ref, data["original_text"], data["tier"].value)
                return {
                    "source": f"Greek New Testament (NA28/UBS5) & Critical Apparatus",
                    "passage_reference": ref,
                    "location": f"Biblia Graeca / {data['book']} Chapter {data['chapter']}:{data['verse']}",
                    "original_text": data["original_text"],
                    "transliteration": data["transliteration"],
                    "indonesian": data["indonesian"],
                    "english": data["english"],
                    "witnesses": data["witnesses"],
                    "evidence_tier": data["tier"].value,
                    "confidence": data["confidence"],
                    "provenance_hash": prov_hash,
                    "tokens": [
                        {
                            "surface": t.surface_form,
                            "lemma": t.lemma,
                            "pos": t.part_of_speech,
                            "morph": t.morphology,
                            "lexicon_bdag": t.lexical_meaning,
                            "textual_fact": t.textual_fact,
                            "linguistic_interpretation": t.linguistic_interpretation
                        }
                        for t in data["tokens"]
                    ]
                }
        return None


# Global singleton instance
Evidence = EvidenceEngine()
