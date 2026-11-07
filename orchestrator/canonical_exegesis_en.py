"""
English Localized Canonical Exegesis Packages for Polya Exegesis Engine.
Covers the 9 canonical Scripture references:
- Roma 3:31
- Yehezkiel 18:20
- Yohanes 1:1
- Ulangan 6:4
- Matius 5:17
- Lukas 22:42
- 2 Petrus 1:21
- 1 Yohanes 5:7-8
- Yesaya 9:5
"""

from typing import Dict, Any, List
from web.models import (
    ExegeticalContext,
    InterlinearWordToken,
    LinguisticExegesisPackage
)

CANONICAL_EXEGESIS_REGISTRY_EN: Dict[str, Dict[str, Any]] = {
    "Roma 3:31": {
        "passage_reference": "Roma 3:31",
        "original_language": "Koine Greek",
        "source_text_full": "νόμον οὖν καταργοῦμεν διὰ τῆς πίστεως; μὴ γένοιτο· ἀλλὰ νόμον ἱστάνομεν.",
        "literal_translation": "Law then do we nullify through faith? May it never be! On the contrary, law we establish.",
        "natural_translation": "Do we then nullify the Law through faith? Absolutely not! On the contrary, we uphold and confirm the Law.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Pauline Diatribe / Forensic Didactic Discourse",
            immediate_context="Conclusion of the discourse on justification by faith apart from legal works in Romans 3:21-30. Paul refutes potential antinomian misunderstandings.",
            historical_cultural_setting="First-century Rome; dialogue between Jewish and Gentile believers concerning the ongoing validity and authority of the Torah."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "law / Torah", "syntactic_role": "Direct Object (Pre-verbal Topical Emphatic)", "exegetical_note": "Fronted placement of 'nomon' emphasizes the divine Law as the focal point."},
            {"index": 2, "literal_gloss": "then / therefore", "syntactic_role": "Inferential Conjunction", "exegetical_note": "Draws deductive inference from the preceding justification discourse."},
            {"index": 3, "literal_gloss": "do we nullify / abolish", "syntactic_role": "Finite Verb / Predicate", "exegetical_note": "Present indicative active 1st person plural: to render inoperative."},
            {"index": 4, "literal_gloss": "through / by means of", "syntactic_role": "Instrumental Preposition", "exegetical_note": "Specifies faith as the instrumental means."},
            {"index": 5, "literal_gloss": "the", "syntactic_role": "Definite Article Genitive", "exegetical_note": "Refers back to the previously defined faith in Jesus."},
            {"index": 6, "literal_gloss": "faith", "syntactic_role": "Genitive Noun Object of Preposition", "exegetical_note": "Pistis denoting covenantal faithfulness and trust."},
            {"index": 7, "literal_gloss": "not", "syntactic_role": "Negative Particle", "exegetical_note": "Strong subjective negative preceding volitive optative."},
            {"index": 8, "literal_gloss": "may it be / come to pass", "syntactic_role": "Aorist Middle Optative", "exegetical_note": "Paul's strongest rhetorical repudiation: 'God forbid / by no means!'"},
            {"index": 9, "literal_gloss": "but / on the contrary", "syntactic_role": "Strong Adversative Conjunction", "exegetical_note": "Sharp antithesis introducing the affirmative doctrinal truth."},
            {"index": 10, "literal_gloss": "law / Torah", "syntactic_role": "Repeated Direct Object", "exegetical_note": "Reasserts the Torah as what is upheld."},
            {"index": 11, "literal_gloss": "we establish / uphold", "syntactic_role": "Factitive Present Indicative Verb", "exegetical_note": "Present indicative: to cause to stand firm, ratify, uphold."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Rhetorical question opened with inferential postpositive 'oun' and transitive verb 'katargoumen'.",
            "poin_2": "Categorical repudiation using the volitive optative 'mē genoito', rejecting any antinomian conclusion.",
            "poin_3": "Strong adversative 'alla' paired with transitive verb 'histanomen' (we cause to stand, confirm)."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Sinaiticus (א 01, 4th c.)", "reading": "νόμον οὖν καταργοῦμεν... νόμον ἱστάνομεν", "status": "Primary Alexandrian Witness"},
            {"witness": "Codex Vaticanus (B 03, 4th c.)", "reading": "νόμον οὖν καταργοῦμεν... νόμον ἱστάνομεν", "status": "Early Uncial Witness"},
            {"witness": "Papyrus Chester Beatty II (P46, c. 200 AD)", "reading": "νόμον οὖν καταργοῦμεν... νόμον ἱστάνομεν", "status": "Earliest Extant Papyrus"},
            {"witness": "Codex Alexandrinus (A 02, 5th c.)", "reading": "νόμον οὖν καταργοῦμεν... νόμον ἱστάνομεν", "status": "Byzantine / Alexandrian Consensus"}
        ],
        "translation_comparison": [
            {"version": "1st-Century Koine Greek Meaning", "text": "Do we then render the Torah void through faith? Absolute refusal (mē genoito)! On the contrary, we uphold and establish the Torah.", "critique": "Primary benchmark of 1st-century manuscript accuracy."},
            {"version": "NIV", "text": "Do we, then, nullify the law by this faith? Not at all! Rather, we uphold the law.", "critique": "Accurate rendering preserving Paul's emphatic denial."},
            {"version": "KJV", "text": "Do we then make void the law through faith? God forbid: yea, we establish the law.", "critique": "Traditional rendering using 'God forbid' for the Greek optative."},
            {"version": "ESV", "text": "Do we then overthrow the law by this faith? By no means! On the contrary, we uphold the law.", "critique": "Literal translation capturing the adversative force."}
        ],
        "corpus_cross_references": [
            {"reference": "Matius 5:17", "connection": "Jesus confirms that he did not come to abolish the Torah or Prophets, harmonizing with Paul's affirmation in Romans 3:31."},
            {"reference": "Roma 7:12", "connection": "Paul affirms that the Law is holy, and the commandment holy, righteous, and good."},
            {"reference": "Galatia 3:21", "connection": "Is the Law contrary to God's promises? Paul uses the identical repudiation 'mē genoito'."}
        ],
        "exegetical_synthesis": "Philological analysis of Romans 3:31 in Koine Greek proves that Paul categorically repudiates any notion that faith renders the Mosaic Torah void. The verb histanomen ('we uphold / make stand') confirms the ongoing validity of God's moral and covenantal standards."
    },
    "Yehezkiel 18:20": {
        "passage_reference": "Yehezkiel 18:20",
        "original_language": "Biblical Hebrew",
        "source_text_full": "הַנֶּפֶשׁ הַחֹטֵאת הִיא תָמוּת בֵּן לֹא־יִשָּׂא בַּעֲוֺן הָאָב וְאָב לֹא יִשָּׂא בַּעֲוֺן הַבֵּן צִדְקַת הַצַּדִּיק עָלָיו תִּהְיֶה וְרִשְׁעַת הָרָשָׁע עָלָיו תִּהְיֶה׃",
        "literal_translation": "The soul that sins, it shall die. A son shall not bear the guilt of the father, and a father shall not bear the guilt of the son. The righteousness of the righteous shall be upon himself, and the wickedness of the wicked shall be upon himself.",
        "natural_translation": "The soul who sins is the one who will die. A son will not bear the guilt of his father, nor will a father bear the guilt of his son. The righteousness of the righteous will remain upon himself, and the wickedness of the wicked will remain upon himself.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Prophetic Forensic Legal Discourse (Riv)",
            immediate_context="Rebuttal of the fatalistic proverb 'the fathers have eaten sour grapes, and the children's teeth are set on edge' in Ezekiel 18:1-19.",
            historical_cultural_setting="Babylonian Exile (6th c. BC); theological struggle over individual moral agency versus generational guilt."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "the soul / the person", "syntactic_role": "Topicalized Subject Noun with Article", "exegetical_note": "Nefesh denoting the entire living individual person."},
            {"index": 2, "literal_gloss": "the sinning one", "syntactic_role": "Attributive Participle", "exegetical_note": "Active participle indicating ongoing responsibility for moral actions."},
            {"index": 3, "literal_gloss": "it / she (that very one)", "syntactic_role": "Emphatic Resumptive Pronoun", "exegetical_note": "Emphasizes absolute exclusivity of individual responsibility."},
            {"index": 4, "literal_gloss": "shall die", "syntactic_role": "Qal Imperfect Finite Verb", "exegetical_note": "Legal sentence of moral retribution."},
            {"index": 5, "literal_gloss": "son", "syntactic_role": "Subject Noun", "exegetical_note": "Next generational descendant."},
            {"index": 6, "literal_gloss": "shall not bear", "syntactic_role": "Negative Particle + Qal Imperfect", "exegetical_note": "Legal prohibition against generational transference of guilt."},
            {"index": 7, "literal_gloss": "in the iniquity of the father", "syntactic_role": "Prepositional Iniquity Complement", "exegetical_note": "'Avon denotes moral guilt and punishment."},
            {"index": 8, "literal_gloss": "righteousness of the righteous", "syntactic_role": "Construct State Subject", "exegetical_note": "Tzidqat ha-tzaddik: personal moral righteousness cannot be imputed vicariously."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Topicalization of 'ha-nefesh ha-chote't' followed by emphatic resumptive pronoun 'hi' isolates liability strictly to the perpetrator.",
            "poin_2": "Parallel legal prohibition using negative particle 'lo' + imperfect 'yissa' denies transference of 'avon' across generations.",
            "poin_3": "Chiasmic closure establishes that moral status ('tzidqat ha-tzaddik' vs 'rish'at ha-rasha') adheres non-transferably upon each individual."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Leningradensis (B19a, 1008 AD)", "reading": "הַנֶּפֶשׁ הַחֹטֵאת הִיא תָמוּת...", "status": "Standard Masoretic Text"},
            {"witness": "Dead Sea Scrolls (4QEzek, 1st c. BC)", "reading": "Identical consonantal text for individual accountability", "status": "Earliest Qumran Witness"},
            {"witness": "Septuagint (LXX, 3rd c. BC)", "reading": "ψυχὴ ἡ ἁμαρτάνουσα, αὕτη ἀποθανεῖται...", "status": "Pre-Christian Greek Translation"}
        ],
        "translation_comparison": [
            {"version": "1st-Century Ancient Hebrew Meaning", "text": "The soul who commits the sin, that very person alone shall die; a son shall never bear the guilt of his father.", "critique": "Primary benchmark of 1st-century manuscript accuracy."},
            {"version": "NIV", "text": "The one who sins is the one who will die. The child will not share the guilt of the parent.", "critique": "Accurate contemporary English expression of individual culpability."},
            {"version": "KJV", "text": "The soul that sinneth, it shall die. The son shall not bear the iniquity of the father.", "critique": "Direct literal translation from the Masoretic Text."},
            {"version": "ESV", "text": "The soul who sins shall die. The son shall not suffer for the iniquity of the father.", "critique": "Clear modern standard translation preserving the legal syntax."}
        ],
        "corpus_cross_references": [
            {"reference": "Ulangan 24:16", "connection": "Fathers shall not be put to death for their children, nor children for fathers; each shall die for his own sin."},
            {"reference": "Yeremia 31:29-30", "connection": "Rejection of the sour grapes proverb: every person will die for his own iniquity."},
            {"reference": "2 Tawarikh 25:4", "connection": "King Amaziah spared the sons of assassins in accordance with the Mosaic Law."}
        ],
        "exegetical_synthesis": "Ezekiel 18:20 definitively establishes the biblical doctrine of personal moral responsibility. The syntax categorically forbids generational transfer or vicarious imputation of sin, establishing that divine justice evaluates every individual directly."
    },
    "Yohanes 1:1": {
        "passage_reference": "Yohanes 1:1",
        "original_language": "Koine Greek",
        "source_text_full": "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος.",
        "literal_translation": "In the beginning was the Logos, and the Logos was with/toward Theos, and qualitative divine/god was the Logos.",
        "natural_translation": "In the beginning existed the Word (Logos), and the Word was in fellowship with Theos, and the Word had divine essence (theos).",
        "exegetical_context": ExegeticalContext(
            literary_genre="Johannine Prologue / Theological Hymn",
            immediate_context="Opening declaration of John 1:1-18 concerning the pre-existent Logos and his role in creation and revelation.",
            historical_cultural_setting="Ephesus, late 1st c. AD; addressing Jewish wisdom traditions (Memra/Dabar) and Hellenistic conceptual frameworks."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "in", "syntactic_role": "Locative Preposition", "exegetical_note": "Evokes Genesis 1:1 primordial temporal setting."},
            {"index": 2, "literal_gloss": "beginning", "syntactic_role": "Dative Noun", "exegetical_note": "Arche: primordial temporal commencement."},
            {"index": 3, "literal_gloss": "was / existed", "syntactic_role": "Imperfect Indicative Copula", "exegetical_note": "Duration without point of origin (continuous existence)."},
            {"index": 4, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Specific identity marker."},
            {"index": 5, "literal_gloss": "Logos / Word", "syntactic_role": "Subject Noun", "exegetical_note": "The divine Word and wisdom."},
            {"index": 6, "literal_gloss": "and", "syntactic_role": "Coordinating Conjunction", "exegetical_note": "Kai linking progressive declarations."},
            {"index": 7, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Reiterates the subject."},
            {"index": 8, "literal_gloss": "Logos / Word", "syntactic_role": "Subject Noun", "exegetical_note": "The focal subject."},
            {"index": 9, "literal_gloss": "was", "syntactic_role": "Imperfect Copula", "exegetical_note": "Continuous relational existence."},
            {"index": 10, "literal_gloss": "toward / with", "syntactic_role": "Relational Preposition", "exegetical_note": "Pros + accusative: dynamic face-to-face communion, distinguishing persons."},
            {"index": 11, "literal_gloss": "the", "syntactic_role": "Definite Article Accusative", "exegetical_note": "Articular Theos designating the Father."},
            {"index": 12, "literal_gloss": "Theos", "syntactic_role": "Accusative Object of Preposition", "exegetical_note": "Ton Theon: God the Father."},
            {"index": 13, "literal_gloss": "and", "syntactic_role": "Coordinating Conjunction", "exegetical_note": "Kai introducing third clause."},
            {"index": 14, "literal_gloss": "divine / god (qualitative)", "syntactic_role": "Anarthrous Predicate Nominative", "exegetical_note": "Anarthrous 'theos' in pre-verbal position emphasizes divine nature/quality (Colwell's Rule analysis)."},
            {"index": 15, "literal_gloss": "was", "syntactic_role": "Imperfect Copula", "exegetical_note": "Finite verb."},
            {"index": 16, "literal_gloss": "the", "syntactic_role": "Definite Article Nominative", "exegetical_note": "Marks 'ho logos' as grammatical subject."},
            {"index": 17, "literal_gloss": "Logos / Word", "syntactic_role": "Subject Nominative", "exegetical_note": "The subject of the third clause."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Clause 2: 'pros ton theon' with articular accusative establishes personal distinction and communion with the Father.",
            "poin_2": "Clause 3: 'theos en ho logos' features pre-verbal anarthrous 'theos' functioning as a qualitative predicate nominative.",
            "poin_3": "The deliberate absence of the definite article before 'theos' prevents sabellian modalism while asserting divine character."
        },
        "manuscript_witnesses": [
            {"witness": "Papyrus Bodmer II (P66, c. 200 AD)", "reading": "ἐν ἀρχῇ ἦν ὁ λόγος... καὶ θεὸς ἦν ὁ λόγος", "status": "Earliest Johannine Papyrus"},
            {"witness": "Papyrus Bodmer XIV-XV (P75, early 3rd c.)", "reading": "ἐν ἀρχῇ ἦν ὁ λόγος... καὶ θεὸς ἦν ὁ λόγος", "status": "Early Alexandrian Papyrus"},
            {"witness": "Codex Sinaiticus (א 01, 4th c.)", "reading": "Articular ton theon in clause 2; anarthrous theos in clause 3", "status": "Primary Uncial Witness"},
            {"witness": "Codex Vaticanus (B 03, 4th c.)", "reading": "Consistent with critical text NA28", "status": "Primary Critical Text"}
        ],
        "translation_comparison": [
            {"version": "1st-Century Koine Greek Meaning", "text": "In the beginning was the Logos, and the Logos was in intimate communion with Theos (the Father), and the Logos shared the divine nature.", "critique": "Primary benchmark of 1st-century manuscript accuracy."},
            {"version": "NIV", "text": "In the beginning was the Word, and the Word was with God, and the Word was God.", "critique": "Traditional rendering; does not distinguish anarthrous predicate theos from articular ton theon."},
            {"version": "KJV", "text": "In the beginning was the Word, and the Word was with God, and the Word was God.", "critique": "Historic translation reflecting traditional orthodoxy."},
            {"version": "ESV", "text": "In the beginning was the Word, and the Word was with God, and the Word was God.", "critique": "Standard literal English rendering."}
        ],
        "corpus_cross_references": [
            {"reference": "Kejadian 1:1", "connection": "Linguistic echo 'In the beginning' connecting the creative decree with the pre-existent Logos."},
            {"reference": "Yohanes 17:3", "connection": "Jesus addresses the Father as 'the only true God' (ton monon alēthinon theon)."},
            {"reference": "1 Yohanes 1:1-2", "connection": "The Word of life who was with the Father (pros ton patera) and was made manifest."}
        ],
        "exegetical_synthesis": "John 1:1 employs precise Koine Greek grammatical syntax: the Logos is distinct in person from the Father ('pros ton theon') while possessing divine nature ('theos en ho logos'). It refutes both polytheistic division and modalistic identification."
    },
    "Ulangan 6:4": {
        "passage_reference": "Ulangan 6:4",
        "original_language": "Biblical Hebrew",
        "source_text_full": "שְׁמַע יִשְׂרָאֵל יְהוָה אֱלֹהֵינוּ יְהוָה אֶחָד",
        "literal_translation": "Hear, O Israel: YHWH our God, YHWH is One.",
        "natural_translation": "Hear, O Israel: YHWH is our God, YHWH alone is One.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Covenantal Creed / Liturgical Confession",
            immediate_context="The Shema Yisrael introducing the core commandments of the Sinai Covenant in Deuteronomy 6:1-9.",
            historical_cultural_setting="Plains of Moab; Moses charging Israel prior to entering Canaan to maintain absolute monotheism amid polytheistic nations."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "hear / listen heedfully", "syntactic_role": "Qal Imperative Verb", "exegetical_note": "Shema: covenantal summons to hear and obey."},
            {"index": 2, "literal_gloss": "Israel", "syntactic_role": "Vocative Proper Noun", "exegetical_note": "The covenant community addressed."},
            {"index": 3, "literal_gloss": "YHWH", "syntactic_role": "Proper Covenant Divine Name", "exegetical_note": "The personal Tetragrammaton of the Creator."},
            {"index": 4, "literal_gloss": "our God", "syntactic_role": "Construct Noun with 1st Plural Suffix", "exegetical_note": "Eloheinu: our covenantal Sovereign."},
            {"index": 5, "literal_gloss": "YHWH", "syntactic_role": "Repeated Proper Name", "exegetical_note": "Reiterates the sole identity of the Lord."},
            {"index": 6, "literal_gloss": "One / Unique / Alone", "syntactic_role": "Predicate Adjective / Cardinal Numeral", "exegetical_note": "Echad: absolute singularity, indivisibility, and uniqueness."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Nominal verbless clause asserting identity and essential oneness: 'YHWH Eloheinu YHWH Echad'.",
            "poin_2": "Cardinal adjective 'echad' functions as predicate indicating solitary uniqueness: YHWH alone is God.",
            "poin_3": "The imperative 'Shema' establishes a binding monotheistic creed forbidding any pluralization of the Godhead."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Leningradensis (B19a, 1008 AD)", "reading": "שְׁמַע יִשְׂרָאֵל יְהוָה אֱלֹהֵינוּ יְהוָה אֶחָד (with enlarged Ayin and Dalet forming 'ED' = Witness)", "status": "Standard Masoretic Text"},
            {"witness": "Nash Papyrus (2nd c. BC)", "reading": "Pre-Christian Hebrew witness confirming the exact text of the Shema", "status": "Oldest Pre-Masoretic Witness"},
            {"witness": "Septuagint (LXX, 3rd c. BC)", "reading": "ἄκουε, Ἰσραήλ· κύριος ὁ θεὸς ἡμῶν κύριος εἷς ἐστιν", "status": "Ancient Greek Translation"}
        ],
        "translation_comparison": [
            {"version": "1st-Century Ancient Hebrew Meaning", "text": "Hear, O Israel: YHWH is our God, YHWH is One and Solitary (indivisible absolute monotheism).", "critique": "Primary benchmark of 1st-century manuscript accuracy."},
            {"version": "NIV", "text": "Hear, O Israel: The LORD our God, the LORD is one.", "critique": "Standard English translation preserving the singular predicate."},
            {"version": "KJV", "text": "Hear, O Israel: The LORD our God is one LORD.", "critique": "Classic literal English translation."},
            {"version": "ESV", "text": "Hear, O Israel: The LORD our God, the LORD is one.", "critique": "Faithful modern rendering capturing covenantal monotheism."}
        ],
        "corpus_cross_references": [
            {"reference": "Markus 12:29", "connection": "Jesus cites Deuteronomy 6:4 verbatim as the primary and greatest commandment."},
            {"reference": "Zakharia 14:9", "connection": "On that day YHWH will be one and His name one (YHWH echad ushemo echad)."},
            {"reference": "Yesaya 45:5", "connection": "I am YHWH and there is no other; besides Me there is no God."}
        ],
        "exegetical_synthesis": "Deuteronomy 6:4 (Shema Yisrael) constitutes the immovable pillar of biblical monotheism. The Hebrew term 'echad' affirms the absolute singularity and indivisibility of YHWH, directly affirmed by Jesus in Mark 12:29."
    },
    "Matius 5:17": {
        "passage_reference": "Matius 5:17",
        "original_language": "Koine Greek",
        "source_text_full": "Μὴ νομίσητε ὅτι ἦλθον καταλῦσαι τὸν νόμον ἢ τοὺς προφήτας· οὐκ ἦλθον καταλῦσαι ἀλλὰ πληρῶσαι.",
        "literal_translation": "Do not think that I came to abolish the Law or the Prophets; I did not come to abolish but to fulfill.",
        "natural_translation": "Do not suppose that I came to abolish the Law or the Prophets; I did not come to abolish them, but to fulfill and bring them to full expression.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Sermon on the Mount / Halakhic Teaching",
            immediate_context="Matthew 5:17-20 establishing Jesus' authoritative relationship to the Torah and the continuing validity of every letter.",
            historical_cultural_setting="1st-century Galilee; addressing Jewish concerns regarding Jesus' interpretation of the Torah."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "not", "syntactic_role": "Negative Particle", "exegetical_note": "Prohibitive negative with subjunctive."},
            {"index": 2, "literal_gloss": "suppose / think", "syntactic_role": "Aorist Active Subjunctive Verb", "exegetical_note": "Prohibits drawing an erroneous halakhic conclusion."},
            {"index": 3, "literal_gloss": "that", "syntactic_role": "Conjunction", "exegetical_note": "Hoti introducing indirect content."},
            {"index": 4, "literal_gloss": "I came", "syntactic_role": "Aorist Active Indicative Verb", "exegetical_note": "Refers to Jesus' messianic mission."},
            {"index": 5, "literal_gloss": "to abolish / tear down", "syntactic_role": "Aorist Active Infinitive", "exegetical_note": "Katalysai: to demolish, annul, destroy."},
            {"index": 6, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Determines the Law."},
            {"index": 7, "literal_gloss": "law / Torah", "syntactic_role": "Direct Object Noun", "exegetical_note": "The Mosaic Torah."},
            {"index": 8, "literal_gloss": "or", "syntactic_role": "Disjunctive Particle", "exegetical_note": "Extends scope to the Prophets."},
            {"index": 9, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Determines the Prophets."},
            {"index": 10, "literal_gloss": "prophets", "syntactic_role": "Direct Object Noun", "exegetical_note": "The prophetic canon."},
            {"index": 11, "literal_gloss": "not", "syntactic_role": "Objective Negative Particle", "exegetical_note": "Ouk: absolute factual denial."},
            {"index": 12, "literal_gloss": "I came", "syntactic_role": "Aorist Indicative Verb", "exegetical_note": "Restates mission."},
            {"index": 13, "literal_gloss": "to abolish", "syntactic_role": "Aorist Infinitive", "exegetical_note": "Reiterates repudiation of destruction."},
            {"index": 14, "literal_gloss": "but / on the contrary", "syntactic_role": "Strong Adversative Conjunction", "exegetical_note": "Alla: contrasts destruction with fulfillment."},
            {"index": 15, "literal_gloss": "to fulfill / establish fully", "syntactic_role": "Aorist Active Infinitive", "exegetical_note": "Plērōsai: to fill to the full, uphold, realize in practice."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Prohibitive subjunctive 'mē nomisēte' directly prevents disciples from assuming Jesus abolishes the Torah.",
            "poin_2": "Antithetical parallel: 'ouk ēlthon katalysai' balanced by 'alla plērōsai'.",
            "poin_3": "Fulfillment ('plērōsai') stands in sharp contrast to abolition ('katalysai'), confirming the continuity of divine law."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Sinaiticus (א 01, 4th c.)", "reading": "Μὴ νομίσητε ὅτι ἦλθον καταλῦσαι...", "status": "Alexandrian Primary Witness"},
            {"witness": "Codex Vaticanus (B 03, 4th c.)", "reading": "Consistent with critical text NA28", "status": "Alexandrian Uncial"},
            {"witness": "Codex Bezae (D 05, 5th c.)", "reading": "Attests stable textual transmission of the prohibition", "status": "Western Text Witness"}
        ],
        "translation_comparison": [
            {"version": "1st-Century Koine Greek Meaning", "text": "Do not presume that I came to annul the Torah or the Prophets; I did not come to tear them down, but to bring them to full expression and obedience.", "critique": "Primary benchmark of 1st-century manuscript accuracy."},
            {"version": "NIV", "text": "Do not think that I have come to abolish the Law or the Prophets; I have not come to abolish them but to fulfill them.", "critique": "Clear rendering preserving the antithesis."},
            {"version": "KJV", "text": "Think not that I am come to destroy the law, or the prophets: I am not come to destroy, but to fulfil.", "critique": "Classic translation of katalysai as 'destroy'."},
            {"version": "ESV", "text": "Do not think that I have come to abolish the Law or the Prophets; I have not come to abolish them but to fulfill them.", "critique": "Standard literal translation."}
        ],
        "corpus_cross_references": [
            {"reference": "Matius 5:18-19", "connection": "Until heaven and earth pass away, not an iota, not a dot, will pass from the Law until all is accomplished."},
            {"reference": "Lukas 16:17", "connection": "It is easier for heaven and earth to pass away than for one dot of the Law to become void."},
            {"reference": "Roma 3:31", "connection": "Paul reinforces Jesus' statement: 'we uphold the law'."}
        ],
        "exegetical_synthesis": "Matthew 5:17 proves that Jesus explicitly forbade interpreting his ministry as an abrogation of the Torah. The verb 'plērōsai' signifies upholding and embodying the Law in full righteous obedience, directly condemning antinomian claims."
    },
    "Lukas 22:42": {
        "passage_reference": "Lukas 22:42",
        "original_language": "Koine Greek",
        "source_text_full": "λέγων· Πάτερ, εἰ βούλει παρένεγκε τοῦτο τὸ ποτήριον ἀπ' ἐμοῦ· πλὴν μὴ τὸ θέλημά μου ἀλλὰ τὸ σὸν γινέσθω.",
        "literal_translation": "saying: Father, if you are willing, remove this cup from me; yet not my will but yours be done.",
        "natural_translation": "saying: Father, if you are willing, take this cup away from me; nevertheless, not my will, but yours, be done.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Gospel Narrative / Agony in Gethsemane",
            immediate_context="Jesus' fervent prayer on the Mount of Olives prior to his arrest in Luke 22:39-46.",
            historical_cultural_setting="Jerusalem, Passsover season (c. 30 AD); human crisis and submission of Jesus before God."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "saying", "syntactic_role": "Present Participle", "exegetical_note": "Introduces verbatim direct speech prayer."},
            {"index": 2, "literal_gloss": "Father", "syntactic_role": "Vocative Noun", "exegetical_note": "Pater: addressing God the Father as distinct person."},
            {"index": 3, "literal_gloss": "if", "syntactic_role": "Conditional Particle", "exegetical_note": "Subordinates petition to divine sovereignty."},
            {"index": 4, "literal_gloss": "you are willing", "syntactic_role": "Present Indicative Verb", "exegetical_note": "Boulei: the Father's sovereign choice."},
            {"index": 5, "literal_gloss": "remove", "syntactic_role": "Aorist Active Imperative", "exegetical_note": "Petition for deliverance."},
            {"index": 6, "literal_gloss": "this", "syntactic_role": "Demonstrative Pronoun", "exegetical_note": "Points to impending ordeal."},
            {"index": 7, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Determines the cup."},
            {"index": 8, "literal_gloss": "cup", "syntactic_role": "Accusative Direct Object", "exegetical_note": "Metaphor for suffering and trial."},
            {"index": 9, "literal_gloss": "from", "syntactic_role": "Preposition", "exegetical_note": "Apo indicating separation."},
            {"index": 10, "literal_gloss": "me", "syntactic_role": "Genitive Pronoun", "exegetical_note": "Emou: Jesus' distinct person."},
            {"index": 11, "literal_gloss": "nevertheless / yet", "syntactic_role": "Adversative Particle", "exegetical_note": "Plēn: decisive boundary of submission."},
            {"index": 12, "literal_gloss": "not", "syntactic_role": "Negative Particle", "exegetical_note": "Mē negating Jesus' personal preference."},
            {"index": 13, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Marks subject."},
            {"index": 14, "literal_gloss": "will", "syntactic_role": "Subject Nominative Noun", "exegetical_note": "Thelēma: faculty of volition."},
            {"index": 15, "literal_gloss": "of me / my", "syntactic_role": "Possessive Genitive Pronoun", "exegetical_note": "Mou: distinctly belonging to Jesus."},
            {"index": 16, "literal_gloss": "but", "syntactic_role": "Strong Adversative Conjunction", "exegetical_note": "Alla contrasting two distinct wills."},
            {"index": 17, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Determines the Father's will."},
            {"index": 18, "literal_gloss": "yours", "syntactic_role": "Possessive Pronominal Adjective", "exegetical_note": "To son: the Father's distinct will."},
            {"index": 19, "literal_gloss": "let it happen / be done", "syntactic_role": "Present Middle Imperative Verb", "exegetical_note": "Ginesthō: absolute submission to the Father's will."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Direct linguistic contrast between 'to thelēma mou' (my will) and 'to son' (yours) proves two distinct wills.",
            "poin_2": "Adversative conjunctions 'plēn' and 'alla' separate Jesus' human desire from the Father's sovereign decree.",
            "poin_3": "The imperative 'ginesthō' expresses complete subordinate submission of the Son to God the Father."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Sinaiticus (א 01, 4th c.)", "reading": "πλὴν μὴ τὸ θέλημά μου ἀλλὰ τὸ σὸν γινέσθω", "status": "Alexandrian Primary Witness"},
            {"witness": "Codex Vaticanus (B 03, 4th c.)", "reading": "Consistent with critical text NA28", "status": "Alexandrian Uncial"},
            {"witness": "Papyrus Bodmer XIV-XV (P75, early 3rd c.)", "reading": "Earliest papyrus witness attesting distinct wills", "status": "Earliest Extant Papyrus"}
        ],
        "translation_comparison": [
            {"version": "1st-Century Koine Greek Meaning", "text": "Father, if you choose, take this cup from me; yet not my will, but your will alone be accomplished.", "critique": "Primary benchmark of 1st-century manuscript accuracy."},
            {"version": "NIV", "text": "Father, if you are willing, take this cup from me; yet not my will, but yours be done.", "critique": "Faithful rendering highlighting the contrast of wills."},
            {"version": "KJV", "text": "Father, if thou be willing, remove this cup from me: nevertheless not my will, but thine, be done.", "critique": "Classic English translation preserving the distinct pronouns."},
            {"version": "ESV", "text": "Father, if you are willing, remove this cup from me. Nevertheless, not my will, but yours, be done.", "critique": "Accurate modern literal standard."}
        ],
        "corpus_cross_references": [
            {"reference": "Yohanes 5:30", "connection": "I seek not my own will but the will of Him who sent me."},
            {"reference": "Yohanes 6:38", "connection": "For I have come down from heaven, not to do my own will but the will of Him who sent me."},
            {"reference": "Matius 26:39", "connection": "Parallel Gethsemane account: 'not as I will, but as you will'."}
        ],
        "exegetical_synthesis": "Luke 22:42 explicitly differentiates between the will of Jesus and the sovereign will of God the Father. The Greek syntax ('to thelēma mou alla to son') demonstrates that Jesus possesses a distinct personal will subordinate to the Father, refuting ontological equality."
    },
    "2 Petrus 1:21": {
        "passage_reference": "2 Petrus 1:21",
        "original_language": "Koine Greek",
        "source_text_full": "οὐ γὰρ θελήματι ἀνθρώπου ἠνέχθη προφητεία ποτέ, ἀλλὰ ὑπὸ πνεύματος ἁγίου φερόμενοι ἐλάλησαν ἀπὸ θεοῦ ἄνθρωποι.",
        "literal_translation": "for not by the will of man was prophecy ever brought, but being borne along by the Holy Spirit men spoke from God.",
        "natural_translation": "For no prophecy ever came by the will of man, but men moved by the Holy Spirit spoke from God.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Epistolary Apologetics / Epistemological Discourse",
            immediate_context="2 Peter 1:16-21 defending the divine reliability of prophetic scripture against skepticism and private interpretation.",
            historical_cultural_setting="Late apostolic period (c. 65-68 AD); Peter addressing false teachers undermining prophetic authority."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "not", "syntactic_role": "Negative Particle", "exegetical_note": "Absolute denial of human origin."},
            {"index": 2, "literal_gloss": "for", "syntactic_role": "Explanatory Conjunction", "exegetical_note": "Gar: explains previous verse regarding scriptural interpretation."},
            {"index": 3, "literal_gloss": "by will", "syntactic_role": "Instrumental Dative Noun", "exegetical_note": "Denies human initiative as the source."},
            {"index": 4, "literal_gloss": "of man", "syntactic_role": "Genitive Noun", "exegetical_note": "Human agency excluded as primary origin."},
            {"index": 5, "literal_gloss": "was brought / produced", "syntactic_role": "Aorist Passive Indicative Verb", "exegetical_note": "Passive: prophecy is conveyed by an external agent."},
            {"index": 6, "literal_gloss": "prophecy", "syntactic_role": "Subject Nominative Noun", "exegetical_note": "Scriptural prophetic revelation."},
            {"index": 7, "literal_gloss": "ever", "syntactic_role": "Temporal Adverb", "exegetical_note": "Pote: universal negative scope across all biblical history."},
            {"index": 8, "literal_gloss": "but / on the contrary", "syntactic_role": "Strong Adversative Conjunction", "exegetical_note": "Alla: contrasts human initiative with divine drive."},
            {"index": 9, "literal_gloss": "by / under", "syntactic_role": "Agency Preposition", "exegetical_note": "Hypo + genitive: direct divine agent."},
            {"index": 10, "literal_gloss": "Spirit", "syntactic_role": "Genitive Noun", "exegetical_note": "Pneumatos: God's Holy Spirit."},
            {"index": 11, "literal_gloss": "Holy", "syntactic_role": "Attributive Adjective", "exegetical_note": "Sanctified divine power."},
            {"index": 12, "literal_gloss": "being borne along / moved", "syntactic_role": "Present Passive Participle", "exegetical_note": "Pheromenoi: nautical imagery of a ship driven by the wind."},
            {"index": 13, "literal_gloss": "spoke", "syntactic_role": "Aorist Active Indicative Verb", "exegetical_note": "Human prophets as instruments."},
            {"index": 14, "literal_gloss": "from", "syntactic_role": "Preposition of Source", "exegetical_note": "Apo indicating ultimate source."},
            {"index": 15, "literal_gloss": "Theos", "syntactic_role": "Genitive Noun", "exegetical_note": "God as the sole author of revelation."},
            {"index": 16, "literal_gloss": "men", "syntactic_role": "Subject Nominative Noun", "exegetical_note": "Anthrōpoi: human messengers."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Universal negative 'ou pote' combined with dative 'thelēmati anthrōpou' eliminates human volition as the source of revelation.",
            "poin_2": "Participle 'pheromenoi' (passive) describes human prophets moved and guided by the Holy Spirit like a ship driven by wind.",
            "poin_3": "Prepositional phrase 'apo theou' establishes God as the sovereign ultimate source of prophetic utterance."
        },
        "manuscript_witnesses": [
            {"witness": "Papyrus Bodmer VIII (P72, 3rd-4th c.)", "reading": "ἀπὸ θεοῦ ἄνθρωποι (men from God)", "status": "Earliest Extant Witness for 2 Peter"},
            {"witness": "Codex Vaticanus (B 03, 4th c.)", "reading": "Consistent with NA28: ἐλάλησαν ἀπὸ θεοῦ ἄνθρωποι", "status": "Primary Alexandrian Uncial"},
            {"witness": "Codex Sinaiticus (א 01, 4th c.)", "reading": "Confirms divine origin of prophecy", "status": "Alexandrian Witness"}
        ],
        "translation_comparison": [
            {"version": "1st-Century Koine Greek Meaning", "text": "For never was prophecy brought about by human will, but men spoke from God as they were carried along by the Holy Spirit.", "critique": "Primary benchmark of 1st-century manuscript accuracy."},
            {"version": "NIV", "text": "For prophecy never had its origin in the human will, but prophets, though human, spoke from God as they were carried along by the Holy Spirit.", "critique": "Dynamic equivalent capturing the nautical metaphor."},
            {"version": "KJV", "text": "For the prophecy came not in old time by the will of man: but holy men of God spake as they were moved by the Holy Ghost.", "critique": "Traditional rendering following late Byzantine manuscripts."},
            {"version": "ESV", "text": "For no prophecy was ever produced by the will of man, but men spoke from God as they were carried along by the Holy Spirit.", "critique": "Accurate literal translation reflecting early critical text."}
        ],
        "corpus_cross_references": [
            {"reference": "2 Timotius 3:16", "connection": "All scripture is God-breathed (theopneustos) and profitable for teaching."},
            {"reference": "Kisah Para Rasul 1:16", "connection": "The Holy Spirit spoke beforehand by the mouth of David."},
            {"reference": "Yeremia 1:9", "connection": "YHWH touched Jeremiah's mouth: 'Behold, I have put My words in your mouth'."}
        ],
        "exegetical_synthesis": "2 Peter 1:21 establishes the absolute divine source of biblical prophecy. Human volition is excluded ('ou thelēmati anthrōpou'), while the Holy Spirit is the active driving power ('pheromenoi') delivering messages from God."
    },
    "1 Yohanes 5:7-8": {
        "passage_reference": "1 Yohanes 5:7-8",
        "original_language": "Koine Greek",
        "source_text_full": "ὅτι τρεῖς εἰσιν οἱ μαρτυροῦντες, τὸ πνεῦμα καὶ τὸ ὕδωρ καὶ τὸ αἷμα, καὶ οἱ τρεῖς εἰς τὸ ἕν εἰσιν.",
        "literal_translation": "For three are those who testify: the Spirit and the water and the blood; and the three agree as one.",
        "natural_translation": "For there are three that testify: the Spirit, the water, and the blood; and these three are in agreement.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Epistolary Textual Criticism / Canonical Polemic",
            immediate_context="1 John 5:6-9 setting forth the three earthly witnesses to the historical testimony of Jesus Christ.",
            historical_cultural_setting="Late 1st c. AD; subsequent Latin manuscript interpolation (Comma Johanneum) originating in 4th-c. Spain (Priscillian) and absent from all ancient Greek codices."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "for / because", "syntactic_role": "Causal Conjunction", "exegetical_note": "Hoti introducing the evidentiary testimony."},
            {"index": 2, "literal_gloss": "three", "syntactic_role": "Cardinal Numeral Nominative", "exegetical_note": "Treis: three witnesses according to biblical legal standard."},
            {"index": 3, "literal_gloss": "are", "syntactic_role": "Present Indicative Verb", "exegetical_note": "Eisin: present continuous witness."},
            {"index": 4, "literal_gloss": "those who", "syntactic_role": "Articular Masculine Participle", "exegetical_note": "Hoi martyrountes: masculine agreement with grammatical witnesses."},
            {"index": 5, "literal_gloss": "testify", "syntactic_role": "Active Participle", "exegetical_note": "Providing legal corroboration."},
            {"index": 6, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Determines first witness."},
            {"index": 7, "literal_gloss": "Spirit", "syntactic_role": "Neuter Noun", "exegetical_note": "To pneuma: the divine Spirit of truth."},
            {"index": 8, "literal_gloss": "and", "syntactic_role": "Coordinating Conjunction", "exegetical_note": "Kai linking witnesses."},
            {"index": 9, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Determines second witness."},
            {"index": 10, "literal_gloss": "water", "syntactic_role": "Neuter Noun", "exegetical_note": "To hydōr: Jesus' baptism."},
            {"index": 11, "literal_gloss": "and", "syntactic_role": "Coordinating Conjunction", "exegetical_note": "Kai linking third witness."},
            {"index": 12, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Determines third witness."},
            {"index": 13, "literal_gloss": "blood", "syntactic_role": "Neuter Noun", "exegetical_note": "To haima: Jesus' sacrificial death."},
            {"index": 14, "literal_gloss": "and", "syntactic_role": "Coordinating Conjunction", "exegetical_note": "Kai concluding clause."},
            {"index": 15, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "Hoi treis."},
            {"index": 16, "literal_gloss": "three", "syntactic_role": "Subject Numeral", "exegetical_note": "The triad of witnesses."},
            {"index": 17, "literal_gloss": "unto", "syntactic_role": "Preposition", "exegetical_note": "Eis expressing purpose and agreement."},
            {"index": 18, "literal_gloss": "the", "syntactic_role": "Definite Article", "exegetical_note": "To hen."},
            {"index": 19, "literal_gloss": "one (agreement)", "syntactic_role": "Neuter Numeral Object", "exegetical_note": "Eis to hen: unanimous harmony of testimony."},
            {"index": 20, "literal_gloss": "are", "syntactic_role": "Finite Verb Copula", "exegetical_note": "Eisin: are united in testimony."}
        ],
        "syntactic_exegesis": {
            "poin_1": "The authentic Greek text contains exclusively the three earthly witnesses: 'to pneuma, to hydōr, kai to haima'.",
            "poin_2": "The phrase 'eis to hen eisin' denotes agreement in testimony, not ontological trinitarian consubstantiality.",
            "poin_3": "The heavenly witness clause ('in heaven, the Father, the Word, and the Holy Spirit') is completely absent from all ancient Greek manuscripts before the 14th-16th century."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Sinaiticus (א 01, 4th c.)", "reading": "Omit heavenly witnesses (Comma Johanneum completely absent)", "status": "Primary Uncial Witness"},
            {"witness": "Codex Vaticanus (B 03, 4th c.)", "reading": "Omit heavenly witnesses (authentic Greek reading)", "status": "Primary Alexandrian Witness"},
            {"witness": "Codex Alexandrinus (A 02, 5th c.)", "reading": "Omit heavenly witnesses", "status": "Early Uncial Witness"},
            {"witness": "Codex Ephraemi Rescriptus (C 04, 5th c.)", "reading": "Omit heavenly witnesses", "status": "Early Uncial Witness"}
        ],
        "translation_comparison": [
            {"version": "1st-Century Koine Greek Meaning", "text": "For there are three that testify: the Spirit, the water, and the blood; and these three are in unanimous agreement.", "critique": "Primary benchmark of 1st-century manuscript accuracy without spurious interpolations."},
            {"version": "NIV", "text": "For there are three that testify: the Spirit, the water and the blood; and the three are in agreement.", "critique": "Accurate critical edition excluding the spurious Latin Comma."},
            {"version": "KJV", "text": "For there are three that bear record in heaven, the Father, the Word, and the Holy Ghost: and these three are one. And there are three that bear witness in earth...", "critique": "Contains the spurious Comma Johanneum translated from late Latin manuscripts."},
            {"version": "ESV", "text": "For there are three that testify: the Spirit and the water and the blood; and these three agree.", "critique": "Follows the authentic critical Greek text without the interpolated clause."}
        ],
        "corpus_cross_references": [
            {"reference": "Yohanes 19:34", "connection": "Water and blood flowing from Jesus' side, establishing the historical physical witnesses."},
            {"reference": "Ulangan 19:15", "connection": "By the mouth of two or three witnesses a matter shall be established."},
            {"reference": "Yohanes 8:17-18", "connection": "The testimony of two men is true; Jesus aligns with legal witness requirements."}
        ],
        "exegetical_synthesis": "Textual criticism conclusively proves that the trinitarian clause 'in heaven: the Father, the Word, and the Holy Spirit' (Comma Johanneum) is an uninspired medieval Latin gloss absent from all ancient Greek manuscripts (Codex Sinaiticus, Vaticanus, Alexandrinus). The authentic original text speaks only of the Spirit, water, and blood agreeing as one."
    },
    "Yesaya 9:5": {
        "passage_reference": "Yesaya 9:5",
        "original_language": "Biblical Hebrew",
        "source_text_full": "כִּי־יֶ֣לֶד יֻלַּד־לָ֗נוּ בֵּ֚ן נִתַּן־לָ֔נוּ וַתְּהִ֥י הַמִּשְׂרָ֖ה עַל־שִׁכְמ֑וֹ וַיִּקְרָ֨א שְׁמ֜וֹ פֶּ֠לֶא יוֹעֵץ֙ אֵ֣ל גִּבּ֔וֹר אֲבִיעַ֖ד שַׂר־שָׁלֽוֹם׃",
        "literal_translation": "For a child is born to us, a son is given to us, and the government shall be upon his shoulder; and his name shall be called Wonderful Counselor, Mighty Hero/Ruler, Father of Eternity, Prince of Peace.",
        "natural_translation": "For a child has been born for us, a son has been given to us; and the government will rest upon his shoulder. And his name will be called: Wonderful Counselor, Mighty Hero, Father of the Age to Come, Prince of Peace.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Royal Prophetic Oracle / Davidic Messianic Song",
            immediate_context="Isaiah 9:1-7 celebrating the deliverance from Assyrian darkness and the enthronement of a righteous Davidic ruler.",
            historical_cultural_setting="Judah, late 8th c. BC (Syro-Ephraimite crisis); coronation of a righteous Davidic prince (Hezekiah typology foreshadowing Messiah)."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "for / because", "syntactic_role": "Causal Particle", "exegetical_note": "Ki introducing the reason for rejoicing."},
            {"index": 2, "literal_gloss": "a child", "syntactic_role": "Subject Noun", "exegetical_note": "Yeled: mortal human male infant."},
            {"index": 3, "literal_gloss": "has been born", "syntactic_role": "Pual Perfect Verb", "exegetical_note": "Yullad: passive, born of human mother."},
            {"index": 4, "literal_gloss": "to us", "syntactic_role": "Prepositional Suffix", "exegetical_note": "Lanu: for the benefit of God's covenant people."},
            {"index": 5, "literal_gloss": "a son", "syntactic_role": "Subject Noun", "exegetical_note": "Ben: royal heir of David's line."},
            {"index": 6, "literal_gloss": "has been given", "syntactic_role": "Niphal Perfect Verb", "exegetical_note": "Nittan: given as God's gift."},
            {"index": 7, "literal_gloss": "Mighty God / Hero", "syntactic_role": "Royal Title", "exegetical_note": "'El Gibbor: in ancient Hebrew Semitic idiom, denotes a mighty hero or divine champion (cf. Ezekiel 32:21 'ele gibborim')."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Pual and Niphal passive verbs ('yullad lanu, ben nittan lanu') emphasize human birth and creaturely status of the child.",
            "poin_2": "The Hebrew title 'El Gibbor' uses 'el' in its classic Semitic sense of mighty judge or ruler (cf. Ex 15:15, Ps 82:1, Ezek 32:21).",
            "poin_3": "The pre-Christian Septuagint (LXX) translates the entire title as 'Megales boules angelos' (Messenger of Great Counsel), proving ancient Jewish readers did not read it as an incarnation of Almighty God."
        },
        "manuscript_witnesses": [
            {"witness": "Great Isaiah Scroll (1QIsa a, 2nd c. BC)", "reading": "Consonantal text identical to Masoretic Text (אל גבור)", "status": "Oldest Extant Dead Sea Scrolls Witness"},
            {"witness": "Codex Leningradensis (B19a, 1008 AD)", "reading": "פֶּ֠לֶא יוֹעֵץ֙ אֵ֣ל גִּבּ֔וֹר", "status": "Standard Masoretic Text"},
            {"witness": "Septuagint (LXX, 3rd c. BC)", "reading": "Μεγάλης βουλῆς ἄγγελος (Messenger of Great Counsel)", "status": "Pre-Christian Jewish Greek Translation"}
        ],
        "translation_comparison": [
            {"version": "1st-Century Ancient Hebrew Meaning", "text": "For a child is born to us, a son is given to us; and his name shall be proclaimed: Wonder-Counselor, Mighty Hero, Father of the Everlasting Age, Prince of Peace.", "critique": "Primary benchmark of 1st-century manuscript accuracy."},
            {"version": "NIV", "text": "For to us a child is born, to us a son is given... And he will be called Wonderful Counselor, Mighty God, Everlasting Father, Prince of Peace.", "critique": "Translates El Gibbor as 'Mighty God' reflecting traditional Christian reading."},
            {"version": "KJV", "text": "For unto us a child is born, unto us a son is given... and his name shall be called Wonderful, Counsellor, The mighty God, The everlasting Father, The Prince of Peace.", "critique": "Inserts comma between Wonderful and Counsellor."},
            {"version": "ESV", "text": "For to us a child is born, to us a son is given... and his name shall be called Wonderful Counselor, Mighty God, Everlasting Father, Prince of Peace.", "critique": "Literal translation following standard English convention."}
        ],
        "corpus_cross_references": [
            {"reference": "Yehezkiel 32:21", "connection": "The strong among the mighty ('ele gibborim') shall speak from Sheol, demonstrating the plural usage of 'el' for human warriors."},
            {"reference": "Keluaran 15:15", "connection": "The mighty men of Moab ('ele moav') trembling, confirming 'el' as a title of human rulers."},
            {"reference": "Lukas 1:32-33", "connection": "The angel Gabriel proclaims that Jesus will be great and will be called the Son of the Most High, receiving the throne of his father David."}
        ],
        "exegetical_synthesis": "In Isaiah 9:5 (MT 9:6), the royal title 'El Gibbor' in ancient Semitic Hebrew denotes a mighty warrior or God's appointed champion ruler, directly parallel to 'ele gibborim' in Ezekiel 32:21. The pre-Christian Septuagint translated it as 'Megales boules angelos' (Messenger of Great Counsel), proving that the passage prophesies a mortal Davidic deliverer, not the incarnation of the Creator."
    }
}
