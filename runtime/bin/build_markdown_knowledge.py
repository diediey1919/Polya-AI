#!/usr/bin/env python3
"""
Generate Markdown Source Records, Claims, and Forensic Analyses for Apologetica
Adheres to existing Apologetica repository schema, frontmatter, and audit protocols.
"""
import os

bases = [
    "/home/ubuntu/Polya-AI/apologetica",
    "/home/ubuntu/apologetica"
]

sources_to_write = {
    "SRC-JEW-MT-001.md": """---
SOURCE_ID: SRC-JEW-MT-001
TITLE: Codex Leningradensis (B19a) — Primary Complete Hebrew Masoretic Witness
TYPE: CANONICAL SCRIPTURE / MANUSCRIPT WITNESS
AUTHORS: Samuel ben Jacob (Scribe), Aaron ben Moses ben Asher (Masorah)
DATE: 1008 CE (1008–1009 CE)
TRADITION: JEWISH / MASORETIC TIBERIAN
LANGUAGE: Biblical Hebrew / Biblical Aramaic
REPOSITORY: National Library of Russia, St. Petersburg (MS Firkovich B 19 A)
EDITIONS: Facsimile (Eerdmans 1998); basis for BHS (Biblia Hebraica Stuttgartensia) and BHQ
STATUS: REGISTERED / TIER 1 PRIMARY WITNESS
---

# CODEX LENINGRADENSIS (B19a)

**Source ID:** SRC-JEW-MT-001  
**Full Title:** Codex Leningradensis (Firkovich B 19 A)  
**Date:** 1008 CE (Colophon dated year 4769 of Jewish creation calendar)  
**Location:** Fustat (Old Cairo), Egypt; currently St. Petersburg, Russia  

## Overview
Codex Leningradensis is the oldest complete manuscript of the Hebrew Bible (Tanakh) preserved in its entirety. Copied from corrected codices prepared by Master Masorete Aaron ben Moses ben Asher in Tiberias.

## Significance for Polia Knowledge Base
1. **Critical Text Baseline:** Serves as the diplomatic master text for academic critical editions: Rudolf Kittel's BHK (3rd ed.), K. Elliger and W. Rudolph's BHS, and the ongoing Biblia Hebraica Quinta (BHQ).
2. **Masoretic Apparatus:** Preserves complete Tiberian vocalization (nikkud), accents/cantillation (te'amim), Masorah Parva (marginal notes), and Masorah Magna (concordance notes).
3. **Textual Verification:** Benchmark for evaluating variants across Dead Sea Scrolls, Samaritan Pentateuch, and the Septuagint.
""",

    "SRC-JEW-DSS-001.md": """---
SOURCE_ID: SRC-JEW-DSS-001
TITLE: The Great Isaiah Scroll (1QIsa-a) — Complete Qumran Biblical Scroll
TYPE: DEAD SEA SCROLL / ANCIENT MANUSCRIPT
AUTHORS: Second Temple Jewish Scribes
DATE: c. 125–100 BCE
TRADITION: JEWISH / SECOND TEMPLE
LANGUAGE: Biblical Hebrew (Hasmonean Orthography)
REPOSITORY: Shrine of the Book, Israel Museum, Jerusalem
EDITIONS: DJD / Ulrich & Flint (Brill/OUP 2010)
STATUS: REGISTERED / TIER 1 PRIMARY WITNESS
---

# THE GREAT ISAIAH SCROLL (1QIsa-a)

**Source ID:** SRC-JEW-DSS-001  
**Discovered:** 1947 in Cave 1 at Qumran  
**Date:** Late 2nd Century BCE (paleographically and radiocarbon confirmed)  

## Physical Description
Consists of 17 parchment sheets sewn end-to-end measuring 7.34 meters in length, arranged in 54 columns containing the complete text of all 66 chapters of Isaiah.

## Significance for Polia Knowledge Base
1. **Textual Stability:** Demonstrates astonishing fidelity to the medieval Masoretic Text (over 95% textual agreement over a 1,100-year transmission gap).
2. **Isaiah 53 Witness:** Preserves the entire text of the fourth Servant Song (Isa 52:13–53:12), proving that the passage was not a post-Christian interpolation.
3. **Orthography:** Employs fuller phonetic (plene) spelling typical of the Second Temple scribal school.
""",

    "SRC-JEW-MISHNAH-001.md": """---
SOURCE_ID: SRC-JEW-MISHNAH-001
TITLE: The Mishnah — Foundational Code of the Oral Torah
TYPE: CANONICAL RABBINIC CODE
AUTHORS: Rabbi Yehudah Ha-Nasi (Redactor) and the Tannaim
DATE: c. 200–220 CE
TRADITION: JEWISH / RABBINIC TANNAITIC
LANGUAGE: Mishnaic Hebrew
REPOSITORY: Hungarian Academy of Sciences (MS Kaufmann A 50); Parma de Rossi 138
EDITIONS: Chanoch Albeck & Hanoch Yalon (Bialik/Dvir 1952); Herbert Danby (OUP 1933)
STATUS: REGISTERED / TIER 2 RABBINIC CANONICAL
---

# THE MISHNAH (משנה)

**Source ID:** SRC-JEW-MISHNAH-001  
**Redaction Date:** c. 200 CE  
**Redactor:** Rabbi Judah the Prince (Rabbi Yehudah Ha-Nasi)  

## Structure
Comprises Six Orders (Shishah Sidrei Mishnah - Shas):
1. **Zera'im (Seeds):** 11 tractates on agricultural laws, tithes, and blessings (Berakhot).
2. **Mo'ed (Festivals):** 12 tractates on Shabbat and the sacred calendar.
3. **Nashim (Women):** 7 tractates on marriage, divorce (Gittin), and vows.
4. **Nezikin (Damages):** 10 tractates on civil/criminal law, ethics (Pirkei Avot), and courts (Sanhedrin).
5. **Kodashim (Holy Things):** 11 tractates on sacrifices, Temple architecture (Middot), and slaughter (Chullin).
6. **Tohorot (Purities):** 12 tractates on ritual purity and impurity.

## Significance for Polia Knowledge Base
1. **Oral Law Baseline:** The primary locus of Rabbinic Judaism's Oral Torah transmission.
2. **Transition from Temple Cult:** Systematizes how Judaism continued to function legally and ethically without animal sacrifice following the 70 CE cataclysm.
""",

    "SRC-JEW-RAMBAM-MT-001.md": """---
SOURCE_ID: SRC-JEW-RAMBAM-MT-001
TITLE: Maimonides: Mishneh Torah (Yad Ha-Chazaqah) — Comprehensive Halakhic Code
TYPE: RABBINIC LEGAL CODE / THEOLOGICAL COMPENDIUM
AUTHORS: Rabbi Moshe ben Maimon (Maimonides / Rambam)
DATE: c. 1170–1180 CE
TRADITION: JEWISH / MEDIEVAL RISHONIM
LANGUAGE: Mishnaic Hebrew
REPOSITORY: Bodleian Library, Oxford (MS Huntington 80 - autograph signature)
EDITIONS: Frankel Edition (Jerusalem 1975–2001); Yosef Qafih Edition
STATUS: REGISTERED / TIER 3 MEDIEVAL CANONICAL
---

# MAIMONIDES: MISHNEH TORAH (משנה תורה)

**Source ID:** SRC-JEW-RAMBAM-MT-001  
**Author:** Moses Maimonides (Rambam, 1138–1204 CE)  
**Location:** Fustat (Old Cairo), Egypt  

## Content & Scope
A 14-book systematic codification of every aspect of biblical and rabbinic Halakha:
- **Book 1: Sefer Ha-Madda (Book of Knowledge):** The foundational theology of monotheism, negative attributes, prophecy, ethics, and repentance.
- **Book 14: Sefer Shofetim (Judges):** Sanhedrin, mourning, and Hilkhot Melakhim u-Milchamotehem (Laws of Kings and Wars), containing chapters 11–12 on King Messiah and the criteria for identifying true and false messiahs.

## Significance for Polia Knowledge Base
Authoritative benchmark for Jewish halakhic definitions of monotheism, the non-physicality of God, and objective messianic criteria.
"""
}

claims_to_write = {
    "CLAIM-JEW-MONO-001.md": """---
CLAIM_ID: CLAIM-JEW-MONO-001
CLAIM: Judaism teaches the absolute, indivisible, non-composite, and incorporeal unity of God (Yihud Ha-Shem), rejecting trinitarianism, incarnation, and polytheism.
SOURCE_ID: SRC-JEW-MT-001
SOURCE_LOCATION: Deuteronomy 6:4; Isaiah 45:5-7; Maimonides Mishneh Torah, Hilkhot Yesodei Ha-Torah 1:7
CLAIM_TYPE: THEOLOGICAL CLAIM / TRADITIONAL DOGMA
EVIDENCE: The Shema ('Shema Yisrael YHWH Eloheinu YHWH Echad' - Hear O Israel, the Lord is our God, the Lord is One) is the primary creedal declaration of Judaism. Maimonides codifies: 'This God is One. He is not two or more than two, but One, whose unity is unlike any other unity in the universe... He is not a body nor a physical force.'
TRADITION: JEWISH (PAN-DENOMINATIONAL CONSENSUS)
HISTORICAL_PERIOD: CONTINUOUS (BIBLICAL TO CONTEMPORARY)
VERIFICATION_STATUS: VERIFIED
CONFIDENCE: ESTABLISHED
---

# CLAIM: ABSOLUTE DIVINE UNITY IN JUDAISM

Judaism holds an uncompromising monotheism where God is uniquely single, indivisible, and totally devoid of physical form or internal composition. Any theology positing plural persons within the godhead (such as the Christian Trinity) or divine incarnation into human flesh is categorized in Jewish halakha as incompatible with pure monotheism (Shituf / Avodah Zarah for Jews).
""",

    "CLAIM-JEW-MASHIACH-001.md": """---
CLAIM_ID: CLAIM-JEW-MASHIACH-001
CLAIM: In Jewish theology, the Messiah (Mashiach) is an ordinary mortal human king of Davidic patrilineage who must fulfill concrete historical tasks—ingathering exiles, rebuilding the Temple, and establishing global peace—prior to his death.
SOURCE_ID: SRC-JEW-RAMBAM-MT-001
SOURCE_LOCATION: Mishneh Torah, Hilkhot Melakhim ch. 11–12; Isaiah 2:1-4, 11:1-12
CLAIM_TYPE: THEOLOGICAL CLAIM / HALAKHIC CRITERIA
EVIDENCE: Rambam states: 'If a king arises from the House of David who meditates upon the Torah... and compels all Israel to walk in its ways... and fights the battles of God, he is presumed to be the Messiah. If he succeeds, rebuilds the Temple on its site, and gathers the dispersed of Israel, he is definitely the Messiah. But if he does not succeed or is killed, it is known that he is not the one promised in the Torah.'
TRADITION: JEWISH / RABBINIC
HISTORICAL_PERIOD: SECOND TEMPLE TO CONTEMPORARY
VERIFICATION_STATUS: VERIFIED
CONFIDENCE: ESTABLISHED
---

# CLAIM: JEWISH MESSIANIC DEFINITION & CRITERIA

Judaism distinguishes between 'presumed Messiah' (Be-Chezkot Mashiach) and 'confirmed Messiah' (Mashiach Vadai). Because Jesus of Nazareth was crucified before gathering the global Jewish exiles, rebuilding the Temple, or bringing universal world peace, normative Judaism firmly rejects his claim to messiahship.
""",

    "CLAIM-JEW-TAHRIF-001.md": """---
CLAIM_ID: CLAIM-JEW-TAHRIF-001
CLAIM: Manuscript discoveries, notably the Dead Sea Scrolls, provide empirical historical proof against the severe polemical claim of Tahrif al-Nass (total textual corruption of the Hebrew Bible prior to Islam).
SOURCE_ID: SRC-JEW-DSS-001
SOURCE_LOCATION: 1QIsa-a, 4QpaleoExod-m, 4QMMT, and comparative Masoretic codices
CLAIM_TYPE: HISTORICAL CLAIM / TEXTUAL CRITICAL FACT
EVIDENCE: Complete and fragmentary biblical scrolls discovered at Qumran (dating from c. 250 BCE to 68 CE) demonstrate over 95% word-for-word textual alignment with the 10th-century Masoretic Text, completely refuting allegations that the Hebrew Bible was systematically rewritten or forged in late antiquity or post-Islamic times.
TRADITION: ACADEMIC_CRITICAL / JEWISH HISTORICAL
HISTORICAL_PERIOD: SECOND TEMPLE TO MEDIEVAL
VERIFICATION_STATUS: VERIFIED
CONFIDENCE: ESTABLISHED
---

# CLAIM: TEXTUAL PRESERVATION & REFUTATION OF TAHRIF AL-NASS

Archaeological discovery of Hebrew biblical manuscripts pre-dating the Islamic era by over 700 years conclusively establishes the antiquity and stability of the Hebrew biblical text, aligning with the nuanced stance of classical Muslim exegetes (such as Al-Tabari and Al-Razi) who favored Tahrif al-Ma'na (misinterpretation) over Tahrif al-Nass (textual falsification).
""",

    "CLAIM-JEW-ZION-001.md": """---
CLAIM_ID: CLAIM-JEW-ZION-001
CLAIM: Judaism (a religious covenant), the Jewish People (an ethno-religious collective), Israeli citizenship (a modern geopolitical nationality), and Zionism (a political movement) are distinct historical and analytical categories that must not be conflated.
SOURCE_ID: SRC-ACAD-COHEN-001
SOURCE_LOCATION: Demographic and Sociological Analysis of Modern Israel and Diaspora
CLAIM_TYPE: HISTORICAL REPORT / CATEGORY SEPARATION
EVIDENCE: Over 20% of citizens of the State of Israel are non-Jewish (Arab Muslims, Christians, Druze); hundreds of thousands of religious Orthodox Jews historically or currently express non-Zionist or anti-Zionist stances (e.g. Satmar, Neturei Karta, Edah Ha-Chareidis); millions of Jewish people live as citizens of other sovereign nations.
TRADITION: ACADEMIC / SOCIOLOGICAL
HISTORICAL_PERIOD: MODERN (1897–PRESENT)
VERIFICATION_STATUS: VERIFIED
CONFIDENCE: ESTABLISHED
---

# CLAIM: CATEGORY SEPARATION OF JUDAISM, ISRAEL, AND ZIONISM

In compliance with Polia Epistemic Rule 1.5, religious Judaism cannot be simplistically equated with modern Israeli state actions or political Zionism. Analysis of Jewish religious thought must remain independent of modern Middle Eastern geopolitical debates.
"""
}

analyses_to_write = {
    "JUDAISM-MASHIACH-CHRISTOLOGY-FORENSIC-AUDIT.md": """# JUDAISM-MASHIACH-CHRISTOLOGY-FORENSIC-AUDIT

**Audit Date:** 2026-09-11  
**Category:** INTERFAITH FORENSIC AUDIT / MESSIANIC THEOLOGY  
**Sources Referenced:** SRC-JEW-MT-001, SRC-JEW-DSS-001, SRC-JEW-RAMBAM-MT-001, SRC-JEW-RASHI-001, SRC-JEW-TROKI-001  
**Claims Referenced:** CLAIM-JEW-MONO-001, CLAIM-JEW-MASHIACH-001  

---

## 1. Executive Summary
This forensic audit analyzes the core divergence between traditional Judaism and Christian Christology concerning the identity, function, and scriptural validation of the Messiah. It examines primary Hebrew texts against Greek Patristic and New Testament interpretations, verifying linguistic glosses, literary context, and historical execution.

---

## 2. Textual & Linguistic Forensic Analysis

### A. Isaiah 7:14 — 'Almah vs. Bethulah
* **Masoretic Text (Codex Leningradensis):** `הִנֵּה הָעַלְמָה הָרָה וְיֹלֶדֶת בֵּן וְקָרָאת שְׁמוֹ עִמָּנוּ אֵל`
* **Linguistic Breakdown:** 
  - `הָעַלְמָה` (ha-almah): Definite article `ha-` + noun feminine singular `almah`. Semantic range: a young woman of childbearing age.
  - Distinct from `בְּתוּלָה` (bethulah), which specifically denotes anatomical virginity (e.g. Genesis 24:16, Deuteronomy 22:19).
* **Contextual Audit:** The historical setting is the Syro-Ephraimite War (734 BCE). King Ahaz of Judah feared King Rezin of Damascus and King Pekah of Samaria. Isaiah offered a contemporary sign: before the child learns to distinguish right from wrong, the threatening kingdoms will be laid waste (Isa 7:16). The child was born in the 8th century BCE (identified by Rashi and Ibn Ezra as Isaiah's son Maher-Shalal-Hash-Baz or King Hezekiah).
* **Finding:** Projecting this verse forward 700 years to a virgin birth in Bethlehem violates original historical and literary context.

### B. Isaiah 52:13–53:12 — The Suffering Servant
* **Exegetical Dispute:** Classical Christian apologetics reads this passage as predictive of Jesus's crucifixion.
* **Contextual Audit:** Throughout Second Isaiah, the Servant of the Lord is repeatedly identified explicitly as collective Israel:
  - Isaiah 41:8: "But you, Israel, My servant, Jacob, whom I have chosen..."
  - Isaiah 44:1: "Now hear, O Jacob My servant, and Israel whom I have chosen."
  - Isaiah 49:3: "You are My servant, Israel, in whom I will be glorified."
* **Rabbinic Consensus:** Major medieval commentators (Rashi, Ibn Ezra, Radak, Chizkuni) affirm that Chapter 53 depicts the Gentile nations and their kings speaking in awe at the redemption of Israel, acknowledging that the Jewish people suffered unjustly while bearing the brunt of international persecution.

---

## 3. Halakhic Messianic Criteria (Maimonides' Audit)
Maimonides in *Hilkhot Melakhim* (ch. 11–12) outlines the necessary and sufficient conditions for the Messiah:
1. **Patrilineal descent from David and Solomon:** Unbroken human biological lineage.
2. **Torah Fidelity:** Strict adherence to both Written and Oral Torah.
3. **Ingathering of the Exiles:** Bringing world Jewry back to the ancestral homeland.
4. **Rebuilding the Sanctuary:** Rebuilding the Temple in Jerusalem.
5. **Universal Disarmament:** Establishing global peace where nations beat swords into plowshares (Isaiah 2:4).

**Conclusion:** Because Jesus died without fulfilling the Temple reconstruction, ingathering, or world peace, he does not meet the halakhic definition of Mashiach.
""",

    "JUDAISM-ISLAM-TAHRIF-BANI-ISRAIL-FORENSIC-AUDIT.md": """# JUDAISM-ISLAM-TAHRIF-BANI-ISRAIL-FORENSIC-AUDIT

**Audit Date:** 2026-09-11  
**Category:** INTERFAITH FORENSIC AUDIT / TEXTUAL TRANSMISSION  
**Sources Referenced:** SRC-JEW-MT-001, SRC-JEW-DSS-001, SRC-ACAD-TOV-001, SRC-ISL-IBN-HAZM-001  
**Claims Referenced:** CLAIM-JEW-TAHRIF-001  

---

## 1. Executive Summary
This audit investigates the Islamic doctrine of Tahrif (scriptural corruption) regarding the Hebrew Bible, distinguishing between the historical-critical evidence of Hebrew manuscripts and early vs late Islamic theological models.

---

## 2. Distinction between Tahrif al-Ma'na and Tahrif al-Nass

### A. Classical Tafsir (Al-Tabari, Al-Razi) — Tahrif al-Ma'na
* **Position:** Early classical commentators maintained that the physical consonantal text of the Torah in Jewish hands was genuine, but that Jewish scholars misinterpreted the meanings, concealed prophecies of Muhammad, or misapplied legal decrees.
* **Fakhr al-Din al-Razi (d. 1210 CE):** Explicitly noted that coordinated textual modification across thousands of dispersed copies in Europe, Africa, and Asia without leaving trace or protest is physically impossible.

### B. Polemical Radicalization (Ibn Hazm) — Tahrif al-Nass
* **Position:** Ibn Hazm of Cordoba (d. 1064 CE) in *Al-Fasl* pioneered the view that the original Torah was completely lost during the Babylonian exile, and that Ezra fabricated the text, resulting in internal numerical and chronological contradictions.

---

## 3. Archaeological & Manuscript Evidence
* **Dead Sea Scrolls:** Discovery of over 220 biblical manuscripts at Qumran (250 BCE–68 CE) demonstrates that the text of the Hebrew Bible was fixed and widely copied in Palestine over seven centuries prior to the Prophet Muhammad.
* **1QIsa-a Alignment:** The Great Isaiah Scroll exhibits over 95% textual agreement with the 10th-century Masoretic Text, proving that no mass rewriting or corruption occurred in the intervening period.

**Conclusion:** Historical manuscript evidence firmly refutes Tahrif al-Nass while confirming that textual variants across MT, LXX, and DSS are natural scribal phenomena, not sectarian conspiracy.
"""
}

# Write files to both bases
for base in bases:
    for fn, content in sources_to_write.items():
        p = os.path.join(base, "knowledge", "sources", fn)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"Wrote {p}")

    for fn, content in claims_to_write.items():
        p = os.path.join(base, "knowledge", "claims", fn)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"Wrote {p}")

    for fn, content in analyses_to_write.items():
        p = os.path.join(base, "knowledge", "analyses", fn)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"Wrote {p}")

print("Apologetica Markdown knowledge records created and deployed successfully.")
