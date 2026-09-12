# OPERATIONAL SOURCE REGISTRY
## Polya Apologetica Knowledge Base

This registry serves as the operational source directory for the Polya Apologetica Knowledge Base. It maps trustworthy and useful external sources for future knowledge ingestion, providing structured metadata, domain classifications, specialist mappings, evidentiary roles, authority levels, usage rules, and verification statuses.

> **CRITICAL WARNING:** This registry is **NOT** a truth ranking. It is a source-discovery and source-routing system. "Authority Level A" does not mean everything the source says is true; it means the source has a direct evidentiary role appropriate to certain questions. Likewise, institutional and traditional sources represent their respective traditions but do not automatically settle whether their claims are historically or metaphysically true.

---

## 1. SOURCE REGISTRY PRINCIPLES

Every registered source must adhere to rigorous metadata standards and operational rules:
1. **Metadata Completeness:** Every source includes `SOURCE_ID`, `SOURCE_NAME`, `URL`, `SOURCE_TYPE`, `DOMAIN`, `TRADITION / SCOPE`, `PRIMARY_OR_SECONDARY`, `SPECIALISTS`, `EVIDENCE_ROLE`, `AUTHORITY_LEVEL`, `LIMITATIONS`, and `VERIFICATION_STATUS`.
2. **Metadata Integrity:** Never invent metadata. If information cannot be verified, record `UNKNOWN`. If the website cannot currently be verified via automated HTTP check, record `UNVERIFIED`.
3. **Contextual Authority:** Authority levels are contextual. A source at a lower level may be useful for discovery or orientation, whereas a source at level F must not be used as sole evidence for a major historical, textual, linguistic, or theological claim.
4. **Source Chain Compatibility:** Every source must trace its relationship through original language, manuscript, transcription, transliteration, translation, interpretation, doctrine, and apologetic argument without conflating intermediate layers with primary attestation.

---

## 2. AUTHORITY LEVELS

* **A — PRIMARY / DIRECT EVIDENCE:** Direct manuscript witness, epigraphic artifact, foundational historical primary text, or direct canonical text edition.
* **B — CRITICAL / MANUSCRIPT / SCHOLARLY DATABASE:** Critical apparatus, digital manuscript room, scholarly text collection, or digitized codex repository.
* **C — ACADEMIC / RESEARCH:** Peer-reviewed journals, academic discovery portals, scholarly monographs, and university presses.
* **D — INSTITUTIONAL / TRADITIONAL REFERENCE:** Official ecclesiastical, confessional, or canonical bodies, traditional commentary databases, and authoritative institutional repositories.
* **E — GENERAL REFERENCE:** Study Bibles, interlinear tools, linguistic corpora, encyclopedias, and general multi-tradition text archives.
* **F — POPULAR / DEBATE / DISCUSSION:** Popular apologetic websites, debate archives, discussion forums, and secondary commentary portals.

---

## 3. MASTER SOURCE TABLE

| SOURCE_ID | SOURCE_NAME | URL | TYPE | LEVEL | DOMAIN | SPECIALISTS | PRIMARY/SECONDARY | ROLE | VERIFICATION | LIMITATIONS |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SRC-BIB-001** | BibleHub | https://biblehub.com/ | REFERENCE / STUDY TOOL | E | Christian Bible Studies | 01, 03, 04 | Secondary | Translation, Exegesis, Discovery | VERIFIED | Not an independent primary manuscript authority; aggregates multiple translations and commentaries. |
| **SRC-BIB-002** | BibleHub Interlinear | https://biblehub.com/interlinear/ | REFERENCE / STUDY TOOL | E | Biblical Languages | 01, 03, 04 | Secondary | Linguistics, Translation | VERIFIED | Relies on standard critical texts (e.g., NA28/BHS) paired with glosses; not a primary manuscript witness. |
| **SRC-BIB-003** | STEP Bible | https://www.stepbible.org/ | BIBLICAL LANGUAGE / TEXT REFERENCE TOOL | E | Biblical Languages & Exegesis | 01, 03, 04 | Secondary | Linguistics, Exegesis, Translation | VERIFIED | Software/database interface; depends on underlying lexicons and editions without replacing critical text criticism. |
| **SRC-BIB-004** | Sefaria | https://www.sefaria.org/ | DIGITAL TEXT & COMMENTARY LIBRARY | B | Jewish Texts & Rabbinic Literature | 01, 04, 07, 10 | Primary / Secondary | Primary Text Access, Exegesis, Theology | VERIFIED | Crowdsourced and digitized traditional texts; translations and commentaries vary in critical scholarly consensus. |
| **SRC-BIB-005** | Scaife Viewer | https://scaife.perseus.org/ | CLASSICAL TEXT VIEWER | B | Greco-Roman & Classical Literature | 01, 07, 11 | Primary | Primary Text Access, Linguistics | VERIFIED | UI for reading historical texts; requires separate critical editions for absolute textual variants. |
| **SRC-BIB-006** | Perseus Digital Library | https://www.perseus.tufts.edu/ | DIGITAL LIBRARY | B | Classical & Near Eastern Studies | 01, 07, 10, 11 | Primary / Secondary | Primary Text Access, History, Philosophy | VERIFIED | Digitized public domain classical texts; some metadata and scans require verification against recent scholarly editions. |
| **SRC-MSS-001** | New Testament Virtual Manuscript Room | https://ntvmr.uni-muenster.de/ | MANUSCRIPT REPOSITORY | A | New Testament Textual Criticism | 01, 02, 03 | Primary | Manuscript Evidence, Textual Criticism | VERIFIED | Specialized paleographic and codicological portal; requires advanced technical knowledge to interpret manuscript folios. |
| **SRC-MSS-002** | Codex Sinaiticus | https://codexsinaiticus.org/ | MANUSCRIPT REPOSITORY | A | Early Christian Manuscripts | 01, 02, 04 | Primary | Manuscript Evidence, Textual Criticism | VERIFIED | Presents a specific 4th-century uncial codex; physical damage, lacunae, and corrector hands require scholarly apparatus to parse. |
| **SRC-MSS-003** | Dead Sea Scrolls Digital Library | https://www.deadseascrolls.org.il/ | MANUSCRIPT REPOSITORY | A | Second Temple Judaism & Biblical Scrolls | 02, 07, 08 | Primary | Manuscript Evidence, Archaeology | VERIFIED | High-resolution images of fragmentary Qumran texts; translations and identifications are subject to ongoing academic debate. |
| **SRC-QUR-001** | Quran.com | https://quran.com/ | TEXT ACCESS / RECITATION PLATFORM | D | Islamic Textual Tradition | 01, 03, 06 | Primary / Secondary | Primary Text Access, Translation | VERIFIED | Standard Uthmani text representation and multiple translations; interface does not replace specialized critical text editions. |
| **SRC-QUR-002** | Quranic Arabic Corpus | https://corpus.quran.com/ | LINGUISTIC / ANNOTATION RESOURCE | E | Quranic Arabic Linguistics | 01, 03 | Secondary | Linguistics, Grammar, Morphology | VERIFIED | Statistical and grammatical treebank annotations; ontological interpretations reflect specific grammatical schools. |
| **SRC-QUR-003** | Corpus Coranicum | https://corpuscoranicum.de/ | ACADEMIC RESEARCH / MANUSCRIPT RESOURCE | A / C | Quranic Studies & Manuscript History | 01, 02, 07 | Primary / Secondary | Manuscript Evidence, Textual Criticism | VERIFIED | Manuscript data and academic commentary; academic interpretation must remain distinct from the manuscript itself. |
| **SRC-QUR-004** | Sunnah.com | https://sunnah.com/ | HADITH REFERENCE ACCESS | D | Hadith Literature | 05, 06, 09 | Secondary | Hadith, Fiqh, Doctrinal Representation | VERIFIED | Website presentation and grading aggregates; does not replace independent hadith chain (isnad) authentication and kritika. |
| **SRC-QUR-005** | Altafsir | https://www.altafsir.com/ | TAFSIR & EXEGESIS REPOSITORY | D | Islamic Exegesis & Theology | 04, 05, 06, 09 | Secondary | Tafsir, Exegesis, Theology, Fiqh | VERIFIED | Comprehensive digital repository of classical and modern tafsir works; digitization errors or omissions require verification against critical print editions. |
| **SRC-COL-001** | Internet Archive | https://archive.org/ | DIGITAL ARCHIVE | C | General Scholarly & Historical Works | 07, 10, 11 | Primary / Secondary | Discovery Only, Historical Research | VERIFIED | Broad repository containing public domain books and scans; OCR errors, missing pages, and varying work quality require manual verification. |
| **SRC-COL-002** | Digital Bodleian | https://digital.bodleian.ox.ac.uk/ | MANUSCRIPT & RARE BOOK REPOSITORY | B | Oriental & Western Manuscripts | 02, 07 | Primary | Manuscript Evidence, Historical Research | VERIFIED | High-resolution digital facsimiles; restricted to specific cataloged collections with varying accompanying scholarly transcriptions. |
| **SRC-ACA-001** | JSTOR | https://www.jstor.org/ | ACADEMIC DISCOVERY / RESEARCH ACCESS | C | Peer-Reviewed Academic Scholarship | 01 to 12 | Secondary | Academic Research, Peer-Reviewed Studies | VERIFIED | Subscription-walled digital library; an article's academic status does not automatically make its conclusion correct or definitive. |
| **SRC-ACA-002** | Google Scholar | https://scholar.google.com/ | ACADEMIC DISCOVERY SEARCH ENGINE | C | Cross-Disciplinary Academic Research | 01 to 12 | Secondary | Discovery Only, Academic Research | VERIFIED | Algorithmic indexing aggregator; includes unrefereed preprints, predatory journals, and retracted literature alongside top-tier scholarship. |
| **SRC-ACA-003** | Directory of Open Access Journals | https://doaj.org/ | ACADEMIC DISCOVERY PORTAL | C | Open Access Peer-Reviewed Research | 01 to 12 | Secondary | Academic Research, Open Access Discovery | UNVERIFIED | Index of open-access journals; editorial quality and peer-review rigor vary significantly across indexed venues. |
| **SRC-ACA-004** | Cambridge Core | https://www.cambridge.org/core | ACADEMIC PUBLISHER PLATFORM | C | Academic Monographs & Journals | 01 to 12 | Secondary | Academic Research, Scholarly Monographs | VERIFIED | Commercial university press platform; high editorial standards but requires paid access or institutional subscription for full texts. |
| **SRC-CHR-001** | Vatican | https://www.vatican.va/ | INSTITUTIONAL / DOCTRINAL SOURCE | D | Roman Catholic Church | 06, 10, 12 | Primary (Institutional) | Doctrinal Representation, Theology | VERIFIED | Authoritative for official Roman Catholic teaching; represents Catholic doctrine, not neutral proof of Christian doctrine as a whole. |
| **SRC-CHR-002** | Orthodox Church in America | https://www.oca.org/ | INSTITUTIONAL / DOCTRINAL SOURCE | D | Eastern Orthodox Christianity | 06, 10, 12 | Primary (Institutional) | Doctrinal Representation, Theology | VERIFIED | Authoritative for Autocephalous Orthodox Church perspective; represents Eastern Orthodoxy, not all Christianity. |
| **SRC-REL-001** | Internet Sacred Text Archive | https://sacred-texts.com/ | GENERAL TEXT ARCHIVE | E | World Religions & Folklore | 10 | Primary / Secondary | Discovery Only, Comparative Religion | VERIFIED | Older digital text archive; translations are frequently outdated, lacking modern critical apparatus and philological rigor. |

---

## 4. DETAILED SOURCE ENTRIES

### SRC-BIB-001: BibleHub
* **SOURCE_NAME:** BibleHub
* **URL:** https://biblehub.com/
* **SOURCE_TYPE:** REFERENCE / STUDY TOOL
* **DOMAIN:** Christian Bible Studies
* **TRADITION / SCOPE:** Christianity / Biblical Studies
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 01_LANGUAGE, 03_TRANSLATION, 04_EXEGESIS_HERMENEUTICS
* **EVIDENCE_ROLE:** Translation, Exegesis, Discovery
* **AUTHORITY_LEVEL:** E — GENERAL REFERENCE
* **LIMITATIONS:** Aggregates multiple translations and commentaries without providing independent primary manuscript authority.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, translation analysis, exegetical comparison.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** major theological conclusion, manuscript authenticity conclusion, scholarly consensus claim.
* **SOURCE_CHAIN COMPATIBILITY:** Original Language → Translation → Interpretation. Does not establish manuscript history or doctrinal truth.

### SRC-BIB-002: BibleHub Interlinear
* **SOURCE_NAME:** BibleHub Interlinear
* **URL:** https://biblehub.com/interlinear/
* **SOURCE_TYPE:** REFERENCE / STUDY TOOL
* **DOMAIN:** Biblical Languages
* **TRADITION / SCOPE:** Biblical Hebrew, Aramaic, and Greek
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 01_LANGUAGE, 03_TRANSLATION, 04_EXEGESIS_HERMENEUTICS
* **EVIDENCE_ROLE:** Linguistics, Translation
* **AUTHORITY_LEVEL:** E — GENERAL REFERENCE
* **LIMITATIONS:** Relies on standard critical texts paired with lexically glossed word-for-word translation; not a primary manuscript witness.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, linguistic analysis, translation.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** manuscript authenticity conclusion, major theological conclusion.
* **SOURCE_CHAIN COMPATIBILITY:** Critical Text → Transliteration → Translation. Does not establish original composition or historical certainty.

### SRC-BIB-003: STEP Bible
* **SOURCE_NAME:** STEP Bible
* **URL:** https://www.stepbible.org/
* **SOURCE_TYPE:** BIBLICAL LANGUAGE / TEXT REFERENCE TOOL
* **DOMAIN:** Biblical Languages & Exegesis
* **TRADITION / SCOPE:** Biblical Studies / Multilingual Scripture
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 01_LANGUAGE, 03_TRANSLATION, 04_EXEGESIS_HERMENEUTICS
* **EVIDENCE_ROLE:** Linguistics, Exegesis, Translation
* **AUTHORITY_LEVEL:** E — GENERAL REFERENCE
* **LIMITATIONS:** Software and database interface; depends on underlying lexicons and editions without replacing critical text criticism.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, linguistic analysis, translation.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** manuscript authenticity conclusion, historical certainty.
* **SOURCE_CHAIN COMPATIBILITY:** Critical Text → Lexical Tagging → Translation. Does not establish absolute doctrinal truth.

### SRC-BIB-004: Sefaria
* **SOURCE_NAME:** Sefaria
* **URL:** https://www.sefaria.org/
* **SOURCE_TYPE:** DIGITAL TEXT & COMMENTARY LIBRARY
* **DOMAIN:** Jewish Texts & Rabbinic Literature
* **TRADITION / SCOPE:** Judaism (Tanakh, Talmud, Midrash, Halakhah)
* **PRIMARY_OR_SECONDARY:** Primary / Secondary
* **SPECIALISTS:** 01_LANGUAGE, 04_EXEGESIS_HERMENEUTICS, 07_HISTORY, 10_COMPARATIVE_RELIGION
* **EVIDENCE_ROLE:** Primary Text Access, Exegesis, Theology
* **AUTHORITY_LEVEL:** B — CRITICAL / MANUSCRIPT / SCHOLARLY DATABASE
* **LIMITATIONS:** Crowdsourced and digitized traditional texts; translations and commentaries vary in critical scholarly consensus.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary evidence, textual analysis, comparative analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** scholarly consensus claim, absolute historical certainty.
* **SOURCE_CHAIN COMPATIBILITY:** Manuscript Tradition → Transcription → Translation → Rabbinic Interpretation.

### SRC-BIB-005: Scaife Viewer
* **SOURCE_NAME:** Scaife Viewer
* **URL:** https://scaife.perseus.org/
* **SOURCE_TYPE:** CLASSICAL TEXT VIEWER
* **DOMAIN:** Greco-Roman & Classical Literature
* **TRADITION / SCOPE:** Classical Philology & Ancient History
* **PRIMARY_OR_SECONDARY:** Primary
* **SPECIALISTS:** 01_LANGUAGE, 07_HISTORY, 11_PHILOSOPHY_LOGIC
* **EVIDENCE_ROLE:** Primary Text Access, Linguistics
* **AUTHORITY_LEVEL:** B — CRITICAL / MANUSCRIPT / SCHOLARLY DATABASE
* **LIMITATIONS:** UI for reading historical texts; requires separate critical editions for absolute textual variants.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary evidence, linguistic analysis, historical analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** manuscript authenticity conclusion, historical certainty.
* **SOURCE_CHAIN COMPATIBILITY:** Ancient Text → Digital UI → Translation.

### SRC-BIB-006: Perseus Digital Library
* **SOURCE_NAME:** Perseus Digital Library
* **URL:** https://www.perseus.tufts.edu/
* **SOURCE_TYPE:** DIGITAL LIBRARY
* **DOMAIN:** Classical & Near Eastern Studies
* **TRADITION / SCOPE:** Greco-Roman Antiquity & Humanities
* **PRIMARY_OR_SECONDARY:** Primary / Secondary
* **SPECIALISTS:** 01_LANGUAGE, 07_HISTORY, 10_COMPARATIVE_RELIGION, 11_PHILOSOPHY_LOGIC
* **EVIDENCE_ROLE:** Primary Text Access, History, Philosophy
* **AUTHORITY_LEVEL:** B — CRITICAL / MANUSCRIPT / SCHOLARLY DATABASE
* **LIMITATIONS:** Digitized public domain classical texts; some metadata and scans require verification against recent scholarly editions.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary evidence, historical analysis, comparative analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** scholarly consensus claim, absolute historical certainty.
* **SOURCE_CHAIN COMPATIBILITY:** Historical Source → Digital Scans → Modern Indexing.

### SRC-MSS-001: New Testament Virtual Manuscript Room
* **SOURCE_NAME:** New Testament Virtual Manuscript Room
* **URL:** https://ntvmr.uni-muenster.de/
* **SOURCE_TYPE:** MANUSCRIPT REPOSITORY
* **DOMAIN:** New Testament Textual Criticism
* **TRADITION / SCOPE:** Early Christian Greek Manuscripts
* **PRIMARY_OR_SECONDARY:** Primary
* **SPECIALISTS:** 01_LANGUAGE, 02_MANUSCRIPT, 03_TRANSLATION
* **EVIDENCE_ROLE:** Manuscript Evidence, Textual Criticism
* **AUTHORITY_LEVEL:** A — PRIMARY / DIRECT EVIDENCE
* **LIMITATIONS:** Specialized paleographic and codicological portal; requires advanced technical knowledge to interpret manuscript folios and apparatus.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary evidence, manuscript analysis, textual analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** major theological conclusion without exegetical contextualization.
* **SOURCE_CHAIN COMPATIBILITY:** Physical Manuscript → Digital Facsimile → Paleographic Transcription → Critical Apparatus.

### SRC-MSS-002: Codex Sinaiticus
* **SOURCE_NAME:** Codex Sinaiticus
* **URL:** https://codexsinaiticus.org/
* **SOURCE_TYPE:** MANUSCRIPT REPOSITORY
* **DOMAIN:** Early Christian Manuscripts
* **TRADITION / SCOPE:** 4th-Century Christian Codex (Aleph / 01)
* **PRIMARY_OR_SECONDARY:** Primary
* **SPECIALISTS:** 01_LANGUAGE, 02_MANUSCRIPT, 04_EXEGESIS_HERMENEUTICS
* **EVIDENCE_ROLE:** Manuscript Evidence, Textual Criticism
* **AUTHORITY_LEVEL:** A — PRIMARY / DIRECT EVIDENCE
* **LIMITATIONS:** Presents a specific 4th-century uncial codex; physical damage, lacunae, and corrector hands require scholarly apparatus to parse.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary evidence, manuscript analysis, textual analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** entire textual history of the New Testament without comparison to other manuscript families.
* **SOURCE_CHAIN COMPATIBILITY:** Physical Codex → High-Res Digital Image → Paleographic Reading → Textual Apparatus.

### SRC-MSS-003: Dead Sea Scrolls Digital Library
* **SOURCE_NAME:** Dead Sea Scrolls Digital Library
* **URL:** https://www.deadseascrolls.org.il/
* **SOURCE_TYPE:** MANUSCRIPT REPOSITORY
* **DOMAIN:** Second Temple Judaism & Biblical Scrolls
* **TRADITION / SCOPE:** Qumran / Judean Desert Manuscripts
* **PRIMARY_OR_SECONDARY:** Primary
* **SPECIALISTS:** 02_MANUSCRIPT, 07_HISTORY, 08_ARCHAEOLOGY_EPIGRAPHY
* **EVIDENCE_ROLE:** Manuscript Evidence, Archaeology
* **AUTHORITY_LEVEL:** A — PRIMARY / DIRECT EVIDENCE
* **LIMITATIONS:** High-resolution images of fragmentary texts; translations and identifications are subject to ongoing academic debate.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary evidence, manuscript analysis, historical analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** definitive consensus on sectarian sectarian identity or theological unity across all Qumran texts.
* **SOURCE_CHAIN COMPATIBILITY:** Fragmentary Scroll → Multispectral Imaging → Transcription → Scholarly Reconstruction.

### SRC-QUR-001: Quran.com
* **SOURCE_NAME:** Quran.com
* **URL:** https://quran.com/
* **SOURCE_TYPE:** TEXT ACCESS / RECITATION PLATFORM
* **DOMAIN:** Islamic Textual Tradition
* **TRADITION / SCOPE:** Classical Arabic Qur'an
* **PRIMARY_OR_SECONDARY:** Primary / Secondary
* **SPECIALISTS:** 01_LANGUAGE, 03_TRANSLATION, 06_THEOLOGY_AQIDAH
* **EVIDENCE_ROLE:** Primary Text Access, Translation
* **AUTHORITY_LEVEL:** D — INSTITUTIONAL / TRADITIONAL REFERENCE
* **LIMITATIONS:** Standard Uthmani text representation and multiple translations; interface does not replace specialized critical text editions.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary text quotation, translation comparison.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** manuscript variant analysis or early variant history.
* **SOURCE_CHAIN COMPATIBILITY:** Uthmani Text → Digital Encoding → Translation.

### SRC-QUR-002: Quranic Arabic Corpus
* **SOURCE_NAME:** Quranic Arabic Corpus
* **URL:** https://corpus.quran.com/
* **SOURCE_TYPE:** LINGUISTIC / ANNOTATION RESOURCE
* **DOMAIN:** Quranic Arabic Linguistics
* **TRADITION / SCOPE:** Arabic Grammar, Morphology, Syntax
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 01_LANGUAGE, 03_TRANSLATION
* **EVIDENCE_ROLE:** Linguistics, Grammar, Morphology
* **AUTHORITY_LEVEL:** E — GENERAL REFERENCE
* **LIMITATIONS:** Statistical and grammatical treebank annotations; ontological interpretations reflect specific grammatical schools. Do not treat annotations as identical to the Qur'an itself.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, linguistic analysis, grammatical parsing.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** major theological conclusion or historical authorship claims.
* **SOURCE_CHAIN COMPATIBILITY:** Quranic Text → Linguistic Tagging → Syntactic Treebank.

### SRC-QUR-003: Corpus Coranicum
* **SOURCE_NAME:** Corpus Coranicum
* **URL:** https://corpuscoranicum.de/
* **SOURCE_TYPE:** ACADEMIC RESEARCH / MANUSCRIPT RESOURCE
* **DOMAIN:** Quranic Studies & Manuscript History
* **TRADITION / SCOPE:** Academic Qur'anic Textual History
* **PRIMARY_OR_SECONDARY:** Primary / Secondary
* **SPECIALISTS:** 01_LANGUAGE, 02_MANUSCRIPT, 07_HISTORY
* **EVIDENCE_ROLE:** Manuscript Evidence, Textual Criticism
* **AUTHORITY_LEVEL:** A / C (Primary Manuscript Data / Academic Research)
* **LIMITATIONS:** Manuscript data and academic interpretation must remain distinct. Academic historical-critical hypotheses do not automatically invalidate traditional accounts, nor vice versa.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary manuscript evidence, textual criticism, historical analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** absolute historical certainty regarding text genesis.
* **SOURCE_CHAIN COMPATIBILITY:** Early Quranic Manuscript → Academic Documentation → Historical Commentary.

### SRC-QUR-004: Sunnah.com
* **SOURCE_NAME:** Sunnah.com
* **URL:** https://sunnah.com/
* **SOURCE_TYPE:** HADITH REFERENCE ACCESS
* **DOMAIN:** Hadith Literature
* **TRADITION / SCOPE:** Sunni Hadith Collections (Kutub al-Sittah)
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 05_HADITH, 06_THEOLOGY_AQIDAH, 09_FIQH_USUL_FIQH
* **EVIDENCE_ROLE:** Hadith, Fiqh, Doctrinal Representation
* **AUTHORITY_LEVEL:** D — INSTITUTIONAL / TRADITIONAL REFERENCE
* **LIMITATIONS:** Website presentation and grading aggregates; does not treat website presentation as equivalent to independent hadith chain (isnad) authentication.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary hadith text lookup, traditional categorization.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** definitive isnad critique or historical historicity without specialist matn and isnad analysis.
* **SOURCE_CHAIN COMPATIBILITY:** Classical Print Edition → Digital Transcription → English Translation / Grading Tag.

### SRC-QUR-005: Altafsir
* **SOURCE_NAME:** Altafsir
* **URL:** https://www.altafsir.com/
* **SOURCE_TYPE:** TAFSIR & EXEGESIS REPOSITORY
* **DOMAIN:** Islamic Exegesis & Theology
* **TRADITION / SCOPE:** Classical and Modern Tafsir (Sunni, Shia, Sufi, Linguistic)
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 04_EXEGESIS_HERMENEUTICS, 05_HADITH, 06_THEOLOGY_AQIDAH, 09_FIQH_USUL_FIQH
* **EVIDENCE_ROLE:** Tafsir, Exegesis, Theology, Fiqh
* **AUTHORITY_LEVEL:** D — INSTITUTIONAL / TRADITIONAL REFERENCE
* **LIMITATIONS:** Comprehensive digital repository of classical and modern tafsir works; digitization errors or omissions require verification against critical print editions.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, exegetical analysis, doctrinal representation, comparative analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** universal scholarly consensus across all Islamic schools of thought.
* **SOURCE_CHAIN COMPATIBILITY:** Manuscript/Print Tafsir → Digital Archival → Exegetical Argument.

### SRC-COL-001: Internet Archive
* **SOURCE_NAME:** Internet Archive
* **URL:** https://archive.org/
* **SOURCE_TYPE:** DIGITAL ARCHIVE
* **DOMAIN:** General Scholarly & Historical Works
* **TRADITION / SCOPE:** Open Digital Library & Historical Repository
* **PRIMARY_OR_SECONDARY:** Primary / Secondary
* **SPECIALISTS:** 07_HISTORY, 10_COMPARATIVE_RELIGION, 11_PHILOSOPHY_LOGIC
* **EVIDENCE_ROLE:** Discovery Only, Historical Research
* **AUTHORITY_LEVEL:** C — ACADEMIC / RESEARCH (for hosted editions) / E (as general archive)
* **LIMITATIONS:** Broad repository containing public domain books and scans; OCR errors, missing pages, and varying work quality require manual verification.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, historical analysis, bibliographic access.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** scholarly consensus claim or unverified text attribution.
* **SOURCE_CHAIN COMPATIBILITY:** Historical Book → Scan → Digital Hosting.

### SRC-COL-002: Digital Bodleian
* **SOURCE_NAME:** Digital Bodleian
* **URL:** https://digital.bodleian.ox.ac.uk/
* **SOURCE_TYPE:** MANUSCRIPT & RARE BOOK REPOSITORY
* **DOMAIN:** Oriental & Western Manuscripts
* **TRADITION / SCOPE:** Bodleian Libraries Special Collections
* **PRIMARY_OR_SECONDARY:** Primary
* **SPECIALISTS:** 02_MANUSCRIPT, 07_HISTORY
* **EVIDENCE_ROLE:** Manuscript Evidence, Historical Research
* **AUTHORITY_LEVEL:** B — CRITICAL / MANUSCRIPT / SCHOLARLY DATABASE
* **LIMITATIONS:** High-resolution digital facsimiles; restricted to specific cataloged collections with varying accompanying scholarly transcriptions.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, primary evidence, manuscript analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** exhaustive manuscript collation across global libraries.
* **SOURCE_CHAIN COMPATIBILITY:** Rare Manuscript → Institutional Digitization → Online Facsimile.

### SRC-ACA-001: JSTOR
* **SOURCE_NAME:** JSTOR
* **URL:** https://www.jstor.org/
* **SOURCE_TYPE:** ACADEMIC DISCOVERY / RESEARCH ACCESS
* **DOMAIN:** Peer-Reviewed Academic Scholarship
* **TRADITION / SCOPE:** Multidisciplinary Academic Literature
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 01_LANGUAGE, 02_MANUSCRIPT, 03_TRANSLATION, 04_EXEGESIS_HERMENEUTICS, 05_HADITH, 06_THEOLOGY_AQIDAH, 07_HISTORY, 08_ARCHAEOLOGY_EPIGRAPHY, 09_FIQH_USUL_FIQH, 10_COMPARATIVE_RELIGION, 11_PHILOSOPHY_LOGIC, 12_APOLOGETICS_DEBATE
* **EVIDENCE_ROLE:** Academic Research, Peer-Reviewed Studies
* **AUTHORITY_LEVEL:** C — ACADEMIC / RESEARCH
* **LIMITATIONS:** Subscription-walled digital library; an article's academic status does not automatically make its conclusion correct or definitive.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, academic research, scholarly citation, peer-reviewed analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** absolute historical certainty or infallible scholarly consensus.
* **SOURCE_CHAIN COMPATIBILITY:** Scholarly Research → Peer Review → Academic Journal Publication.

### SRC-ACA-002: Google Scholar
* **SOURCE_NAME:** Google Scholar
* **URL:** https://scholar.google.com/
* **SOURCE_TYPE:** ACADEMIC DISCOVERY SEARCH ENGINE
* **DOMAIN:** Cross-Disciplinary Academic Research
* **TRADITION / SCOPE:** Global Scholarly Indexing
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 01 to 12 (All Specialists)
* **EVIDENCE_ROLE:** Discovery Only, Academic Research
* **AUTHORITY_LEVEL:** C — ACADEMIC / RESEARCH (for indexed peer-reviewed sources) / F (for unverified preprints)
* **LIMITATIONS:** Algorithmic indexing aggregator; includes unrefereed preprints, predatory journals, and retracted literature alongside top-tier scholarship.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, literature search, citation tracking.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** authority verification without checking underlying journal peer-review status.
* **SOURCE_CHAIN COMPATIBILITY:** Web Crawl → Algorithmic Indexing → Search Result.

### SRC-ACA-003: Directory of Open Access Journals
* **SOURCE_NAME:** Directory of Open Access Journals
* **URL:** https://doaj.org/
* **SOURCE_TYPE:** ACADEMIC DISCOVERY PORTAL
* **DOMAIN:** Open Access Peer-Reviewed Research
* **TRADITION / SCOPE:** Global Open Access Scholarly Journals
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 01 to 12 (All Specialists)
* **EVIDENCE_ROLE:** Academic Research, Open Access Discovery
* **AUTHORITY_LEVEL:** C — ACADEMIC / RESEARCH
* **LIMITATIONS:** Index of open-access journals; editorial quality and peer-review rigor vary significantly across indexed venues.
* **VERIFICATION_STATUS:** UNVERIFIED (Automated reachability limited by WAF/Cloudflare bot challenge; functionally verified scholarly portal).
* **CAN_USE_FOR:** discovery, open-access academic research.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** guaranteed peer-reviewed quality without verifying individual journal metrics.
* **SOURCE_CHAIN COMPATIBILITY:** Journal Metadata → DOAJ Indexing → Scholarly Discovery.

### SRC-ACA-004: Cambridge Core
* **SOURCE_NAME:** Cambridge Core
* **URL:** https://www.cambridge.org/core
* **SOURCE_TYPE:** ACADEMIC PUBLISHER PLATFORM
* **DOMAIN:** Academic Monographs & Journals
* **TRADITION / SCOPE:** Cambridge University Press Scholarly Publications
* **PRIMARY_OR_SECONDARY:** Secondary
* **SPECIALISTS:** 01 to 12 (All Specialists)
* **EVIDENCE_ROLE:** Academic Research, Scholarly Monographs
* **AUTHORITY_LEVEL:** C — ACADEMIC / RESEARCH
* **LIMITATIONS:** Commercial university press platform; high editorial standards but requires paid access or institutional subscription for full texts.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, academic research, peer-reviewed citation.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** absolute historical certainty.
* **SOURCE_CHAIN COMPATIBILITY:** Academic Manuscript → Editorial Review → University Press Publication.

### SRC-CHR-001: Vatican
* **SOURCE_NAME:** Vatican
* **URL:** https://www.vatican.va/
* **SOURCE_TYPE:** INSTITUTIONAL / DOCTRINAL SOURCE
* **DOMAIN:** Roman Catholic Church
* **TRADITION / SCOPE:** Roman Catholicism (Magisterium, Papal Encyclicals, Conciliar Documents)
* **PRIMARY_OR_SECONDARY:** Primary (Institutional)
* **SPECIALISTS:** 06_THEOLOGY_AQIDAH, 10_COMPARATIVE_RELIGION, 12_APOLOGETICS_DEBATE
* **EVIDENCE_ROLE:** Doctrinal Representation, Theology
* **AUTHORITY_LEVEL:** D — INSTITUTIONAL / TRADITIONAL REFERENCE
* **LIMITATIONS:** Authoritative for official Roman Catholic teaching; represents Catholic doctrine, not neutral proof of Christian doctrine as a whole.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, doctrinal representation, institutional theological analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** universal Christian consensus or historical truth claims outside Catholic dogma.
* **SOURCE_CHAIN COMPATIBILITY:** Magisterial Pronouncement → Official Vatican Archive → Institutional Publication.

### SRC-CHR-002: Orthodox Church in America
* **SOURCE_NAME:** Orthodox Church in America
* **URL:** https://www.oca.org/
* **SOURCE_TYPE:** INSTITUTIONAL / DOCTRINAL SOURCE
* **DOMAIN:** Eastern Orthodox Christianity
* **TRADITION / SCOPE:** Eastern Orthodoxy (Doctrinal, Liturgical, and Historical Teachings)
* **PRIMARY_OR_SECONDARY:** Primary (Institutional)
* **SPECIALISTS:** 06_THEOLOGY_AQIDAH, 10_COMPARATIVE_RELIGION, 12_APOLOGETICS_DEBATE
* **EVIDENCE_ROLE:** Doctrinal Representation, Theology
* **AUTHORITY_LEVEL:** D — INSTITUTIONAL / TRADITIONAL REFERENCE
* **LIMITATIONS:** Authoritative for Autocephalous Orthodox Church perspective; represents Eastern Orthodoxy, not all Christianity.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, doctrinal representation, liturgical and theological analysis.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** universal Christian consensus across Western or non-Chalcedonian traditions.
* **SOURCE_CHAIN COMPATIBILITY:** Orthodox Tradition → Synodal Teaching → Institutional Publication.

### SRC-REL-001: Internet Sacred Text Archive
* **SOURCE_NAME:** Internet Sacred Text Archive
* **URL:** https://sacred-texts.com/
* **SOURCE_TYPE:** GENERAL TEXT ARCHIVE
* **DOMAIN:** World Religions & Folklore
* **TRADITION / SCOPE:** Global Religious Texts (Public Domain)
* **PRIMARY_OR_SECONDARY:** Primary / Secondary
* **SPECIALISTS:** 10_COMPARATIVE_RELIGION
* **EVIDENCE_ROLE:** Discovery Only, Comparative Religion
* **AUTHORITY_LEVEL:** E — GENERAL REFERENCE
* **LIMITATIONS:** Older digital text archive; translations are frequently outdated, lacking modern critical apparatus and philological rigor.
* **VERIFICATION_STATUS:** VERIFIED
* **CAN_USE_FOR:** discovery, comparative religion orientation, public-domain text search.
* **CANNOT_USE_AS_SOLE_BASIS_FOR:** rigorous philological, textual, or theological argument.
* **SOURCE_CHAIN COMPATIBILITY:** Historical Public Domain Edition → Digitization → Web Archive.

---

## 5. SOURCE USAGE RULES

### CAN_USE_FOR:
* Discovery and bibliographic orientation
* Citation of institutional positions and standard text editions
* Primary text quotation (when backed by proper manuscript or critical edition attestation)
* Linguistic and grammatical analysis (via specialized lexicons and corpora)
* Manuscript and paleographic examination (via certified digital manuscript rooms)
* Doctrinal representation (specifically via institutional primary sources)
* Historical and comparative analysis (within established scholarly parameters)

### CANNOT_USE_AS_SOLE_BASIS_FOR:
* Major theological conclusions without multi-source triangulation
* Manuscript authenticity conclusions without critical apparatus support
* Historical certainty without peer-reviewed historical verification
* Divine revelation claims or theological truth verdicts
* Textual corruption or transmission claims based on single-source website presentations
* Scholarly consensus claims without direct engagement with peer-reviewed literature

---

## 6. RELIGIOUS NEUTRALITY & GOVERNANCE

This registry maintains balanced source coverage across Christianity, Islam, Judaism, and critical academic inquiry (Agnosticism/Atheism), ensuring that no single tradition monopolizes the evidential baseline. Institutional sources are strictly utilized for self-representation ("How does this tradition represent itself?") rather than as metaphysical proof of truth ("Is this tradition historically or theologically true?").

---

## 7. SOURCE DISCOVERY POLICY

When the Chief Agent or specialist modules require external evidence not currently registered:
1. Identify the required evidence type and specialist domain.
2. Search for a primary or high-quality scholarly source.
3. Verify source provenance, editorial independence, and accessibility.
4. Classify the source according to Authority Levels A–F.
5. Apply source chain compatibility rules.
6. Propose adding the verified source to the operational registry.
7. Never automatically ingest unverified or predatory websites.

---

## 8. FINAL VALIDATION & SUMMARY

* **SOURCE REGISTRY:** PASS
* **CANDIDATE SOURCES:** 23
* **VERIFIED:** 22
* **PARTIALLY VERIFIED:** 0
* **UNVERIFIED:** 1 (DOAJ - functional scholarly portal, blocked by automated HTTP handshake)
* **FILES CREATED:** `/home/ubuntu/apologetica/sources/SOURCE_REGISTRY.md` only
* **FILES MODIFIED:** NONE
* **ARCHITECTURE MODIFIED:** NO
