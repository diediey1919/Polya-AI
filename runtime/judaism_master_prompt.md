<USER_REQUEST>
POLIA JUDAISM KNOWLEDGE BASE MASTER PROMPT v1.0

ROLE

You are the senior knowledge-architecture, research, verification, data-engineering, and repository-implementation agent for the Polia AI project.

You are responsible for designing and implementing a rigorous Judaism / Jewish Knowledge Base as a permanent knowledge layer of Polia.

Your job is NOT merely to write articles.

Your job is to:

1. inspect the existing Polia repository and knowledge architecture;
2. identify the current knowledge-base structure;
3. identify missing capabilities;
4. perform source discovery;
5. perform source-gap audits;
6. verify sources;
7. construct structured knowledge;
8. preserve provenance;
9. preserve differences among Jewish traditions;
10. build comparative Judaism-Christianity-Islam knowledge;
11. build evidence and argument structures;
12. build a source graph;
13. build debate-oriented retrieval structures;
14. create automated validation and test cases;
15. integrate the Judaism knowledge layer into the repository without damaging existing knowledge;
16. produce a final audit report.

You must work autonomously through the entire pipeline.

Do not stop after producing a research report.

Do not ask for confirmation unless there is a genuinely blocking technical or authorization issue.

---

0. PRIME DIRECTIVE

Build a Judaism knowledge layer that prioritizes:

ACCURACY
TRACEABILITY
PROVENANCE
SOURCE DISCIPLINE
HISTORICAL CONTEXT
TEXTUAL CONTEXT
TRADITIONAL DIVERSITY
INTELLECTUAL HONESTY
REPRODUCIBILITY

Polia is not being built with a database whose purpose is to attack Jews or Judaism.

The purpose is:

UNDERSTAND JUDAISM ACCURATELY
→ REPRESENT JEWISH POSITIONS FAIRLY
→ IDENTIFY SOURCES
→ DISTINGUISH FACT FROM INTERPRETATION
→ COMPARE JUDAISM, CHRISTIANITY, AND ISLAM
→ ENABLE EVIDENCE-BASED APOLOGETIC ANALYSIS

Never distort a Jewish position merely because the eventual use case may involve Islamic apologetics.

---

1. NON-NEGOTIABLE EPISTEMIC RULES

1.1 No fabricated sources

Never invent:

- books;
- articles;
- manuscripts;
- authors;
- quotations;
- publication dates;
- chapter numbers;
- page numbers;
- URLs;
- rabbis;
- academic consensus;
- denominational statements.

If a source cannot be verified, mark it:

UNVERIFIED

Never silently promote an unverified source to verified knowledge.

---

1.2 No fabricated quotations

Never create an exact quotation from memory.

If exact wording has not been verified:

QUOTE_STATUS = UNVERIFIED

Use paraphrase instead and clearly label it as paraphrase.

---

1.3 Separate evidence classes

Every knowledge item must distinguish among:

FACT
CLAIM
QUOTE
INTERPRETATION
INFERENCE
ARGUMENT
COUNTERARGUMENT
ACADEMIC_CONSENSUS
DENOMINATIONAL_POSITION
HISTORICAL_REPORT
TRADITIONAL_POSITION
DISPUTED_CLAIM
UNRESOLVED_QUESTION

Never merge these categories.

---

1.4 Never flatten Judaism

Do not treat Judaism as one monolithic position.

Always consider, when relevant:

- Biblical / Israelite period;
- Second Temple Judaism;
- Rabbinic Judaism;
- medieval Judaism;
- modern Judaism;
- Orthodox Judaism;
- Modern Orthodox;
- Haredi;
- Hasidic;
- Conservative / Masorti;
- Reform;
- Reconstructionist;
- Renewal;
- Humanistic;
- Karaite;
- secular Jewish identity;
- other historically relevant Jewish movements.

If a claim is specific to one tradition, label that tradition.

---

1.5 Never conflate categories

Never automatically equate:

JEWISH = JUDAISM
JEWISH = ISRAELI
JUDAISM = ZIONISM
ISRAEL = BIBLICAL ISRAEL
ZIONIST = RELIGIOUS JEW
MODERN ISRAEL = ANCIENT ISRAEL

These categories must remain distinct.

---

1.6 Historical anachronism control

Do not project modern Jewish beliefs backward into ancient periods.

Do not project ancient Jewish concepts forward into modern Judaism without evidence.

Every historically significant claim should include:

PERIOD

when applicable.

---

2. MISSION

Create a complete and extensible:

POLIA JUDAISM KNOWLEDGE BASE

It must function as a third major religious knowledge layer alongside existing Christianity and Islam knowledge.

The final conceptual architecture is:

POLIA KNOWLEDGE
│
├── JUDAISM
├── CHRISTIANITY
├── ISLAM
│
└── COMPARATIVE LAYER
├── THEME BANK
├── EVIDENCE BANK
├── SOURCE GRAPH
├── ARGUMENT BANK
├── COUNTERARGUMENT BANK
└── DEBATE REASONING

The Judaism layer must be useful independently and comparatively.

---

3. FIRST ACTION: INSPECT THE REPOSITORY

Before creating files:

1. inspect repository root;
2. inspect existing knowledge-base directories;
3. inspect existing data schemas;
4. inspect existing source registries;
5. inspect existing loaders/indexers;
6. inspect retrieval code;
7. inspect reasoning engine interfaces;
8. inspect testing infrastructure;
9. inspect existing Christianity knowledge;
10. inspect existing Islam knowledge;
11. inspect configuration;
12. inspect documentation;
13. inspect AGENTS.md / CLAUDE.md / README.md and any other project constitution files;
14. identify naming conventions;
15. identify existing data formats;
16. identify what can be reused.

Do not assume directory names.

Use the repository's actual architecture whenever compatible.

Before modifying any file:

BACKUP / PRESERVE CURRENT STATE

Record all important changes.

Do not overwrite existing knowledge blindly.

---

4. OPERATING MODE

Use the following workflow:

PLAN
→ EXECUTE
→ VALIDATE
→ MONITOR
→ CORRECT
→ RE-VALIDATE

Do not merely generate a large batch of files and assume success.

At every major stage, validate the output.

---

5. THREE-PASS RESEARCH ARCHITECTURE

The entire Judaism research process must use three primary passes.

PASS 1: DISCOVERY

Purpose:

Find what exists and identify gaps.

Research categories:

- Jewish primary sources;
- Tanakh;
- textual traditions;
- Dead Sea Scrolls;
- Masoretic tradition;
- Septuagint;
- Samaritan Pentateuch;
- Targumim;
- Mishnah;
- Tosefta;
- Jerusalem Talmud;
- Babylonian Talmud;
- Midrash;
- Responsa;
- medieval Jewish works;
- modern Jewish theological works;
- Jewish philosophical works;
- mystical works;
- historical sources;
- archaeological evidence;
- manuscript studies;
- linguistic studies;
- Second Temple studies;
- Rabbinic studies;
- modern denominational sources;
- Jewish-Christian sources;
- Jewish-Islamic sources;
- academic scholarship.

Do not restrict discovery to the sources already listed in this prompt.

Your purpose is to detect blind spots.

---

PASS 2: VERIFICATION

For every significant candidate source:

Verify, where possible:

- title;
- author;
- tradition;
- historical period;
- approximate date;
- language;
- source type;
- bibliographic identity;
- publication information;
- manuscript status where relevant;
- institutional or academic reliability;
- availability of reliable edition;
- relationship to Judaism;
- primary / secondary classification.

Assign:

VERIFIED
PARTIALLY_VERIFIED
UNVERIFIED
DISPUTED

Do not promote uncertain sources to authoritative status.

---

PASS 3: CONSTRUCTION

Only after verification:

1. construct structured knowledge;
2. connect claims to sources;
3. connect interpretations to traditions;
4. connect historical claims to periods;
5. connect arguments to evidence;
6. create comparative nodes;
7. create source graph relationships;
8. create debate structures;
9. run validation;
10. generate export-ready data.

---

6. SOURCE-GAP AUDIT

Perform a source-gap audit at least THREE TIMES.

AUDIT A: OUR CURRENT OUTLINE

Check every area in this prompt.

Identify omissions.

AUDIT B: EXTERNAL KNOWLEDGE ARCHITECTURE

Compare the planned structure against recognized areas of:

- Jewish studies;
- Hebrew Bible studies;
- Second Temple studies;
- Rabbinic studies;
- Jewish history;
- Jewish philosophy;
- Jewish mysticism;
- Jewish-Christian studies;
- Jewish-Islamic studies;
- archaeology;
- manuscript studies;
- linguistics.

Identify missing source categories.

AUDIT C: FINAL DATABASE GAP CHECK

After construction, inspect the resulting repository.

Ask:

What major Jewish knowledge area is still absent?

What major source class is still absent?

What major historical period is still weak?

What denominational perspective is missing?

What comparative area is weak?

What provenance information is missing?

What claims lack sources?

What source claims lack verification?

Everything found in the three audits must be recorded.

---

7. SOURCE HIERARCHY

Maintain explicit distinction among:

TIER 1: PRIMARY / ANCIENT / HISTORICAL TEXTUAL EVIDENCE

Examples may include:

- Tanakh;
- Dead Sea Scrolls;
- ancient inscriptions;
- archaeological evidence;
- ancient Jewish literature;
- other historically relevant primary evidence.

TIER 2: RABBINIC AND TRADITIONAL SOURCES

Examples:

- Mishnah;
- Tosefta;
- Talmud;
- Midrash;
- Responsa;
- major rabbinic commentators.

TIER 3: MEDIEVAL / EARLY MODERN JEWISH SOURCES

Examples:

- Rashi;
- Ibn Ezra;
- Rambam / Maimonides;
- Ramban / Nachmanides;
- Saadia Gaon;
- other major commentators and philosophers.

TIER 4: MODERN JEWISH SOURCES

Examples:

- Orthodox;
- Conservative / Masorti;
- Reform;
- Reconstructionist;
- Hasidic;
- modern Jewish philosophical;
- modern Jewish theological literature.

TIER 5: ACADEMIC SOURCES

Examples:

- peer-reviewed studies;
- university press publications;
- academic monographs;
- critical editions;
- specialist reference works;
- manuscript studies;
- archaeological studies.

TIER 6: APOLOGETIC / POLEMICAL SOURCES

Examples:

- Jewish apologetics;
- Christian apologetics;
- Islamic apologetics;
- polemical literature.

These may be useful for understanding arguments but must not automatically be treated as neutral historical evidence.

---

8. MASTER JUDAISM TAXONOMY

Create and validate the following taxonomy.

A. Identity and Terminology

- Judaism;
- Jewish;
- Jew;
- Yehudi;
- Judah;
- Judahite;
- Israel;
- Israelite;
- Hebrew;
- Bani Israil;
- Jewish people;
- Jewish ethnicity;
- Jewish religion;
- Jewish culture;
- Jewish nation / peoplehood where historically applicable.

Document differences and historical development.

---

B. Jewish History

Cover:

- Patriarchal traditions;
- Exodus;
- Sinai;
- Israelite settlement;
- Judges;
- Saul;
- David;
- Solomon;
- United Monarchy;
- Northern Kingdom;
- Southern Kingdom;
- Assyrian period;
- Babylonian exile;
- Persian period;
- Second Temple;
- Hellenistic period;
- Maccabean Revolt;
- Hasmonean dynasty;
- Roman period;
- Herodian period;
- destruction of Second Temple;
- Bar Kokhba revolt;
- rabbinic period;
- Byzantine period;
- Islamic-era Jewish communities;
- medieval Jewish communities;
- Sephardic history;
- Ashkenazi history;
- Mizrahi history;
- Ottoman period;
- European Jewish history;
- Haskalah;
- emancipation;
- secularization;
- modern Jewish movements;
- Holocaust;
- Zionism;
- establishment of modern Israel;
- contemporary Jewish communities.

---

9. TANAKH CORE LAYER

Create:

TORAH

- Genesis
- Exodus
- Leviticus
- Numbers
- Deuteronomy

NEVI'IM

- Former Prophets
- Latter Prophets

KETUVIM

- Psalms
- Proverbs
- Job
- Five Megillot
- Daniel
- Ezra-Nehemiah
- Chronicles
- etc.

For each book where appropriate record:

- Hebrew name;
- English name;
- canonical position;
- broad historical context;
- language;
- genre;
- major themes;
- textual witnesses;
- important interpretive traditions;
- major scholarly debates.

---

10. TANAKH VS CHRISTIAN OLD TESTAMENT

Explicitly model:

- canonical differences;
- ordering differences;
- terminology;
- book grouping;
- textual traditions;
- theological interpretation;
- Jewish vs Christian reading conventions.

Never simply state that Tanakh = Old Testament without qualification.

---

11. LANGUAGE LAYER

Create a Hebrew / Aramaic knowledge layer covering:

- Biblical Hebrew;
- Mishnaic Hebrew;
- Medieval Hebrew;
- Modern Hebrew;
- Biblical Aramaic;
- Rabbinic Aramaic;
- important transliteration conventions;
- Hebrew terminology;
- semantic range;
- lexical ambiguity;
- textual variants;
- translation problems.

For major apologetic passages, where relevant, record:

ORIGINAL_LANGUAGE
TRANSLITERATION
GLOSS
SEMANTIC_RANGE
TRANSLATION_VARIANTS
TRADITIONAL_INTERPRETATION
ACADEMIC_INTERPRETATION

Do not make simplistic one-word-to-one-word lexical arguments.

---

12. TEXTUAL TRADITION LAYER

Create dedicated structures for:

- Masoretic Text;
- Septuagint;
- Dead Sea Scrolls;
- Samaritan Pentateuch;
- Targumim;
- manuscript traditions;
- scribal transmission;
- textual variants;
- textual criticism;
- canon formation;
- manuscript dating;
- critical editions.

Whenever discussing "the original text", require explicit identification of:

WHICH TEXTUAL TRADITION?

WHAT MANUSCRIPT / EDITION?

WHAT LANGUAGE?

WHAT DATE?

WHAT EVIDENCE?

---

13. TORAH / MITZVOT / HALAKHA

Cover:

- Torah;
- mitzvot;
- traditional enumeration of commandments;
- 613 commandments;
- Halakha;
- Written Torah;
- Oral Torah;
- Kashrut;
- Shabbat;
- circumcision;
- purity laws;
- dietary law;
- sacrificial law;
- Temple law;
- festivals;
- agricultural law where relevant;
- civil law;
- family law.

Track historical development rather than assuming all laws have always been practiced identically.

---

14. JEWISH THEOLOGY

Cover:

- monotheism;
- YHWH;
- divine names;
- Shema;
- covenant;
- election;
- chosen people;
- Torah and revelation;
- sin;
- repentance / teshuvah;
- forgiveness;
- atonement;
- salvation;
- Messiah / Mashiach;
- kingdom of God;
- resurrection;
- afterlife;
- angels;
- Satan;
- prophecy;
- revelation;
- divine law;
- free will;
- divine providence;
- human responsibility;
- world to come;
- Gehinnom;
- Gan Eden;
- Olam Ha-Ba;
- Yetzer Ha-Ra;
- Yetzer Ha-Tov;
- Shekhinah;
- divine presence;
- other major theological concepts identified during source-gap audits.

Do not assume that every concept is equally emphasized across all Jewish traditions.

---

15. WORSHIP AND LIFE CYCLE

Cover:

- synagogue;
- prayer;
- siddur;
- Amidah;
- Shema;
- blessings;
- Torah reading;
- communal worship;
- Shabbat practice;
- Bar Mitzvah;
- Bat Mitzvah;
- brit milah;
- marriage;
- divorce;
- conversion;
- burial;
- mourning;
- lifecycle customs.

---

16. JEWISH FESTIVALS

Cover at minimum:

- Pesach / Passover;
- Shavuot;
- Sukkot;
- Rosh Hashanah;
- Yom Kippur;
- Hanukkah;
- Purim.

Where relevant, distinguish:

BIBLICAL ORIGIN
SECOND TEMPLE DEVELOPMENT
RABBINIC DEVELOPMENT
MODERN PRACTICE

---

17. SECOND TEMPLE JUDAISM

Create a dedicated historical layer covering:

- Second Temple Judaism;
- Pharisees;
- Sadducees;
- Essenes;
- Zealots;
- apocalyptic movements;
- messianic expectations;
- Temple theology;
- Jewish sectarianism;
- Jewish groups in the first century;
- political and religious context;
- Roman occupation.

Do not treat all Second Temple Jews as sharing one theology.

---

18. RABBINIC JUDAISM

Cover:

- Mishnah;
- Tosefta;
- Talmud;
- Jerusalem Talmud;
- Babylonian Talmud;
- Midrash;
- Aggadah;
- Halakhic reasoning;
- Oral Torah;
- rabbinic authority;
- major rabbis;
- development of rabbinic interpretation.

Include distinctions between:

MISHNAH
TALMUD
MIDRASH
COMMENTARY
RESPONSA

---

19. MEDIEVAL JEWISH THOUGHT

Include major figures and traditions such as:

- Saadia Gaon;
- Rashi;
- Ibn Ezra;
- Maimonides;
- Nachmanides;
- other historically important commentators;
- Jewish philosophy;
- Jewish biblical interpretation;
- Jewish law.

Discover additional significant figures through source-gap auditing.

---

20. JEWISH PHILOSOPHY

Cover major intellectual developments such as:

- Hellenistic Jewish thought;
- Philo;
- medieval Jewish philosophy;
- Maimonidean thought;
- rationalism;
- mysticism;
- modern Jewish philosophy;
- existential approaches;
- modern theological debates.

---

21. JEWISH MYSTICISM

Cover:

- early mystical traditions;
- Merkavah traditions;
- Hekhalot traditions;
- Kabbalah;
- Zohar;
- Lurianic Kabbalah;
- Hasidic thought;
- major mystical concepts.

Always distinguish mainstream denominational Judaism from specialized mystical traditions.

---

22. JEWISH DENOMINATIONS / MOVEMENTS

Create explicit knowledge clusters for:

- Orthodox;
- Modern Orthodox;
- Haredi;
- Hasidic;
- Conservative / Masorti;
- Reform;
- Reconstructionist;
- Renewal;
- Humanistic;
- Karaite;
- secular Jewish identity;
- other relevant movements discovered during research.

For each movement where possible record:

ORIGIN
DATE/PERIOD
THEOLOGY
HALAKHIC_POSITION
SCRIPTURE_POSITION
MESSIAH_POSITION
VIEW_OF_MODERNITY
VIEW_OF_OTHER_JEWS
VIEW_OF_CHRISTIANITY
VIEW_OF_ISLAM

Never present a movement-specific claim as "the Jewish position".

---

23. MESSIAH / MASHIACH CLUSTER

Build an especially deep knowledge cluster.

Cover:

- meaning of Mashiach;
- anointed terminology;
- Davidic covenant;
- Son of David;
- messianic expectations in Tanakh;
- Second Temple messianism;
- messianic movements;
- rabbinic interpretations;
- medieval interpretations;
- modern Jewish views;
- Jewish objections to Jesus as Messiah;
- Messianic Judaism;
- differences between Messianic Judaism and mainstream rabbinic Judaism.

For every messianic claim, track:

TEXT
JEWISH INTERPRETATION
CHRISTIAN INTERPRETATION
ISLAMIC RELEVANCE
HISTORICAL CONTEXT
LINGUISTIC CONTEXT
COUNTERINTERPRETATIONS

---

24. JUDAISM AND JESUS

Create a dedicated cluster separate from Christianity.

Cover:

- Jesus in first-century Jewish context;
- Jesus and Torah;
- Jesus and Pharisees;
- Jesus and Temple;
- Jewish historical context of Jesus;
- Jewish perspectives on Jesus;
- Jewish rejection of Christian claims;
- historical Jesus;
- theological Jesus;
- Jewish-Christian historical disputes.

Do not project later Christian doctrine automatically into first-century Jewish context.

---

25. JUDAISM AND CHRISTIANITY

Create two-way knowledge structures.

Topics include:

- separation of Christianity from Judaism;
- Jewish-Christian communities;
- Paul and Judaism;
- Law and faith;
- covenant theology;
- messianic interpretation;
- Trinity and Jewish monotheism;
- incarnation;
- Son of God;
- divinity of Jesus;
- crucifixion;
- resurrection;
- Christian interpretation of Tanakh;
- Jewish interpretation of Christian proof texts;
- Christian-Jewish polemics;
- historical anti-Judaism;
- modern Jewish-Christian dialogue.

For each debate theme:

JEWISH POSITION
CHRISTIAN POSITION
ACADEMIC ANALYSIS
PRIMARY SOURCES
COUNTERARGUMENTS
UNRESOLVED QUESTIONS

---

26. JUDAISM AND ISLAM

Create a dedicated cluster.

Topics include:

- Bani Israil;
- prophets shared in Jewish and Islamic traditions;
- Abraham;
- Isaac;
- Jacob;
- Joseph;
- Moses;
- Aaron;
- David;
- Solomon;
- Elijah;
- Elisha;
- Jonah;
- Zachariah;
- John / Yahya;
- Torah in Islam;
- Qur'anic references to Israelites;
- Jewish communities in Arabia;
- Muhammad and Jewish tribes of Medina;
- Qur'anic critiques of some Jewish claims/actions;
- revelation;
- preservation;
- tahrif;
- Jewish responses to Islamic claims.

---

27. Tahrif must be modeled carefully

Do not reduce tahrif to one proposition.

Distinguish:

TAHRIF AL-NASS
TAHRIF AL-MA'NA
INTERPRETIVE CORRUPTION
TEXTUAL CORRUPTION CLAIM
TRANSMISSION CLAIM
THEOLOGICAL CLAIM
MEDIEVAL INTERPRETATION
MODERN INTERPRETATION

Record different Muslim scholarly interpretations separately where relevant.

Also record Jewish responses and academic analysis separately.

---

28. TRIANGULAR COMPARATIVE LAYER

Create a reusable comparative schema for:

- God;
- revelation;
- scripture;
- prophecy;
- covenant;
- law;
- sin;
- repentance;
- forgiveness;
- atonement;
- salvation;
- Messiah;
- resurrection;
- afterlife;
- Abraham;
- Moses;
- David;
- Solomon;
- Jesus;
- Jerusalem;
- Temple;
- human nature;
- final judgment.

The structure should support:

JUDAISM
CHRISTIANITY
ISLAM

with independent evidence and provenance for each.

---

29. JEWISH APOLOGETICS

Document how Jews defend Judaism.

Cover:

- Jewish-Christian polemics;
- Jewish responses to Christian messianic proof texts;
- Jewish responses to Trinity;
- Jewish responses to incarnation;
- Jewish responses to Pauline theology;
- Jewish responses to Christian proof texts;
- Jewish responses to Islamic claims;
- Jewish arguments concerning Torah;
- Jewish arguments concerning textual preservation;
- Jewish arguments concerning Messiah;
- Jewish views of covenant and election.

The objective is understanding the argument, not caricaturing it.

---

30. ISRAEL / ZIONISM / JUDAISM

Create separate structures for:

- ancient Israel;
- biblical Israel;
- Jewish people;
- modern State of Israel;
- Zionism;
- secular Zionism;
- religious Zionism;
- anti-Zionist Jewish movements;
- Jewish views of modern Israel;
- Jerusalem;
- Temple Mount;
- modern messianic expectations;
- contemporary Jewish political/religious diversity.

Never infer theology or political ideology solely from ethnic/religious identity.

---

31. GEOGRAPHIC AND CULTURAL JEWISH DIVERSITY

Cover historically important communities such as:

- Middle Eastern Jews;
- North African Jews;
- Sephardic Jews;
- Ashkenazi Jews;
- Mizrahi Jews;
- Yemenite Jews;
- Ethiopian Jews;
- Persian/Iranian Jews;
- Iraqi Jews;
- European Jewish communities;
- Jewish communities in the Americas;
- Jewish communities in Islamic civilization;
- Jewish communities in Arabia.

Track differences in:

LANGUAGE
CUSTOM
HALAKHA
HISTORY
LITURGY
CULTURE

where evidence supports them.

---

32. MASTER KNOWLEDGE OBJECT SCHEMA

Every substantive knowledge item should support fields similar to:

id
title
domain
subdomain
topic
subtopic
claim_type
claim
summary
definition
tradition
denomination
historical_period
date_from
date_to
language
region
primary_sources
secondary_sources
academic_sources
textual_witnesses
citations
interpretations
counterinterpretations
arguments
counterarguments
comparative_notes
confidence
verification_status
provenance
notes
related_topics
related_sources
last_verified

Use the existing repository schema if one already exists.

Do not create redundant incompatible schemas when a reusable project schema already exists.

---

33. SOURCE OBJECT SCHEMA

Every source record should support:

source_id
title
author
editor
date
approximate_date
historical_period
tradition
denomination
language
region
source_type
primary_or_secondary
academic_or_religious
publisher
edition
identifier
url
repository
manuscript_reference
bibliographic_reference
verification_status
confidence
provenance
notes

---

34. CLAIM-SOURCE RELATIONSHIP

Implement explicit source linkage.

A claim must be able to point to one or more sources.

A source must be able to support multiple claims.

Model relationships such as:

SUPPORTS
CONTRADICTS
INTERPRETS
QUOTES
SUMMARIZES
CHALLENGES
HISTORICALLY_PRECEDES
DERIVES_FROM
RESPONDS_TO

This is necessary for Source Graph construction.

---

35. EVIDENCE BANK

Create evidence records classified as:

FACT
CLAIM
QUOTE
INTERPRETATION
INFERENCE
ARGUMENT
COUNTERARGUMENT
ACADEMIC_CONSENSUS
DENOMINATIONAL_POSITION
HISTORICAL_REPORT
TRADITIONAL_POSITION
DISPUTED_CLAIM
UNRESOLVED_QUESTION

Every evidence object should contain a source reference wherever applicable.

---

36. SOURCE GRAPH

Build a graph representing connections between:

TEXT
AUTHOR
TRADITION
PERIOD
CLAIM
INTERPRETATION
COUNTERARGUMENT
DENOMINATION
HISTORICAL_EVENT
THEME

Example:

ISAIAH 7
→ MASORETIC TEXT
→ JEWISH INTERPRETATIONS
→ CHRISTIAN INTERPRETATIONS
→ LINGUISTIC QUESTIONS
→ ACADEMIC STUDIES
→ MESSIANIC DEBATE

The implementation should make these relationships machine-readable.

---

37. DEBATE KNOWLEDGE STRUCTURE

For each major debate theme create:

THEME
│
├── JEWISH POSITION
├── CHRISTIAN POSITION
├── ISLAMIC POSITION
├── PRIMARY EVIDENCE
├── JEWISH EVIDENCE
├── CHRISTIAN EVIDENCE
├── ISLAMIC EVIDENCE
├── HISTORICAL CONTEXT
├── TEXTUAL CONTEXT
├── LINGUISTIC CONTEXT
├── THEOLOGICAL CONTEXT
├── COMMON ARGUMENTS
├── COUNTERARGUMENTS
├── COUNTER-COUNTERARGUMENTS
├── COMMON MISREPRESENTATIONS
└── UNRESOLVED QUESTIONS

---

38. DEBATE REASONING RULE

When Polia encounters:

"According to Judaism..."

The reasoning pipeline should conceptually perform:

IDENTIFY WHICH JEWISH TRADITION
↓
IDENTIFY HISTORICAL PERIOD
↓
IDENTIFY CLAIM
↓
IDENTIFY SOURCE
↓
VERIFY SOURCE
↓
READ TEXTUAL CONTEXT
↓
CHECK LANGUAGE
↓
CHECK INTERPRETIVE TRADITION
↓
CHECK COMPETING JEWISH INTERPRETATIONS
↓
COMPARE WITH CHRISTIAN POSITION
↓
COMPARE WITH ISLAMIC POSITION
↓
FORM EVIDENCE-BASED RESPONSE

Never jump directly from question to rebuttal.

---

39. QUALITY CONTROL

Create automated or semi-automated checks for:

- duplicate source IDs;
- duplicate knowledge IDs;
- missing citations;
- invalid references;
- unverified quotations;
- source records without titles;
- source records without source type;
- conflicting classification;
- unsupported claims;
- missing traditions;
- missing historical period;
- malformed JSON;
- malformed JSONL;
- broken links where technically testable;
- orphaned evidence;
- orphaned source records;
- source records not referenced by any knowledge item;
- knowledge items referencing nonexistent source IDs.

---

40. ANTI-HALLUCINATION VALIDATION

Before finalizing any dataset:

Search specifically for:

- invented rabbis;
- fabricated quotations;
- invented book titles;
- invented chapter/page references;
- false academic consensus;
- unverified websites;
- mislabeled denominational positions;
- modern views projected into ancient periods;
- Christian interpretations presented as Jewish interpretations;
- Islamic claims presented as Jewish claims;
- Jewish claims presented as universally accepted.

Any detected issue must be corrected or explicitly marked uncertain.

---

41. FINAL AUDIT

At the end, conduct a complete audit.

Answer these questions internally and record the results:

1. Is Judaism structurally represented?
2. Are major historical periods covered?
3. Are major Jewish textual traditions covered?
4. Are Rabbinic sources represented?
5. Are medieval sources represented?
6. Are modern denominational perspectives represented?
7. Are Jewish philosophical traditions represented?
8. Are Jewish mystical traditions represented?
9. Are Hebrew and Aramaic issues represented?
10. Are textual criticism issues represented?
11. Is Messiah coverage sufficiently deep?
12. Is Second Temple Judaism sufficiently deep?
13. Is Rabbinic Judaism sufficiently deep?
14. Is Judaism-Jesus coverage sufficient?
15. Is Judaism-Christianity coverage sufficient?
16. Is Judaism-Islam coverage sufficient?
17. Is tahrif modeled carefully?
18. Are Israel and Zionism separated from Judaism?
19. Is source provenance preserved?
20. Are claims source-linked?
21. Are disagreements preserved?
22. Are uncertain claims labeled?
23. Are Jewish positions represented fairly?
24. Are apologetic arguments distinguished from historical evidence?
25. Can the knowledge be safely consumed by Polia's retrieval/reasoning system?

---

42. FILE / REPOSITORY IMPLEMENTATION RULES

Before implementation:

1. inspect current architecture;
2. reuse existing architecture when possible;
3. avoid unnecessary duplication;
4. create backups;
5. preserve compatibility;
6. maintain clean naming conventions;
7. update documentation;
8. update indexes/configuration only when required;
9. do not break existing Christianity or Islam knowledge;
10. do not delete old knowledge merely to simplify the structure.

If obsolete files are identified:

mark them first.

Only remove them after confirming that no active references depend on them.

---

43. OUTPUT FORMAT

Prefer structured machine-readable data for the actual knowledge layer.

Preferred hierarchy:

DATA:
JSON or JSONL

DOCUMENTATION:
Markdown

SOURCE REGISTRY:
structured JSON/JSONL or existing repository equivalent

TAXONOMY:
structured machine-readable format

TESTS:
repository-native testing format

Use the repository's current conventions when superior.

---

44. DOCUMENTATION REQUIRED

Create/update documentation explaining:

- Judaism KB architecture;
- taxonomy;
- source hierarchy;
- provenance;
- verification status;
- evidence classes;
- source graph;
- data schemas;
- integration with Polia;
- testing;
- maintenance process.

Do not create duplicate documentation if a canonical project document already exists.

---

45. MAINTENANCE MODEL

The Judaism KB must be designed for future updates.

Every knowledge item should be replaceable or enrichable without rebuilding the entire database.

Maintain:

VERSION
DATE_ADDED
DATE_UPDATED
LAST_VERIFIED
SOURCE_VERSION
CHANGE_LOG where appropriate

---

46. CHANGE MANAGEMENT

For every meaningful repository modification:

record:

FILE
OLD_STATE
NEW_STATE
REASON
DEPENDENCIES
VALIDATION_RESULT

Do not destroy provenance during refactoring.

---

47. SEARCH STRATEGY

Use broad discovery first.

Then narrow verification.

Then structured extraction.

Do not rely on a single source for contested claims.

For high-importance topics, seek independent corroboration.

For denominational questions, prioritize relevant official or authoritative denominational materials.

For historical questions, prioritize academic and primary evidence.

For textual questions, prioritize primary textual witnesses and critical scholarship.

For apologetic questions, preserve each tradition's own argumentative sources.

---

48. SOURCE AUTHORITY DISCIPLINE

Use the source appropriate to the claim.

Examples:

For:
"How does Reform Judaism currently view X?"

Prefer:
Reform Jewish institutional / authoritative sources and relevant scholarship.

For:
"What does the Mishnah say?"

Prefer:
Mishnah / critical editions / recognized scholarship.

For:
"What did Jews in first-century Judea believe?"

Prefer:
Second Temple evidence + historical scholarship.

For:
"How does Christianity interpret this verse?"

Use:
Christian theological/exegetical sources.

For:
"How does Islam interpret this passage?"

Use:
Qur'an + recognized tafsir / Islamic scholarship.

Never use one religion's apologetic source as a substitute for the other religion's own source.

---

49. REPRESENTATION OF DISAGREEMENT

When scholars or Jewish traditions disagree:

DO NOT force consensus.

Represent:

POSITION_A
POSITION_B
POSITION_C
EVIDENCE
ARGUMENT
COUNTERARGUMENT
ACADEMIC_STATUS
UNRESOLVED

Where no consensus exists:

STATUS = DISPUTED

---

50. SPECIAL TREATMENT OF APOLOGETIC CLAIMS

Every major apologetic claim should be tagged:

TRADITION = JEWISH / CHRISTIAN / ISLAMIC / SECULAR / ACADEMIC

CLAIM_TYPE = APOLOGETIC where applicable

Never present an apologetic argument as neutral historical fact.

---

51. JEWISH-CHRISTIAN-ISLAMIC COMPARISON RULE

For every major comparative topic, independently construct:

JEWISH DATASET
CHRISTIAN DATASET
ISLAMIC DATASET

Then create:

COMPARATIVE DATASET

Do not create comparison first and backfill evidence later.

---

52. RECOMMENDED PRIORITY ORDER

Execute the project in this order:

PHASE 1
Foundation

1. Repository inspection
2. Constitution
3. Taxonomy
4. Data schema
5. Source registry
6. Provenance system

PHASE 2
Source architecture

7. Source discovery
8. Source-gap audit A
9. Source-gap audit B
10. Verification
11. Source-gap audit C

PHASE 3
Core Judaism

12. Tanakh
13. textual traditions
14. Hebrew / Aramaic
15. Torah / mitzvot / Halakha
16. theology
17. worship
18. festivals
19. lifecycle

PHASE 4
Historical Judaism

20. ancient Israel
21. Second Temple Judaism
22. Rabbinic Judaism
23. medieval Judaism
24. modern Judaism

PHASE 5
Intellectual Judaism

25. Jewish philosophy
26. Jewish mysticism
27. denominational diversity
28. geographic Jewish diversity

PHASE 6
Interfaith

29. Judaism and Jesus
30. Judaism and Christianity
31. Judaism and Islam
32. tahrif
33. triangular comparison

PHASE 7
Apologetics

34. Jewish apologetics
35. Christian-Jewish arguments
36. Jewish-Islamic arguments
37. argument bank
38. counterargument bank
39. debate structures

PHASE 8
Infrastructure

40. Evidence Bank
41. Source Graph
42. Retrieval metadata
43. testing
44. validation
45. final audit

---

53. CHECKPOINTS

At minimum create checkpoints after:

CHECKPOINT 1
Repository + architecture

CHECKPOINT 2
Taxonomy + schemas

CHECKPOINT 3
Source discovery

CHECKPOINT 4
Source verification

CHECKPOINT 5
Core Judaism

CHECKPOINT 6
Historical Judaism

CHECKPOINT 7
Interfaith

CHECKPOINT 8
Evidence + Source Graph

CHECKPOINT 9
Testing

CHECKPOINT 10
Final audit

At each checkpoint:

- inspect;
- validate;
- report;
- correct;
- continue.

---

54. DO NOT STOP EARLY

Do not stop after:

- making an outline;
- finding a list of sources;
- creating empty folders;
- generating documentation;
- creating schemas.

The task is complete only when:

SOURCE DISCOVERY
+
SOURCE VERIFICATION
+
KNOWLEDGE CONSTRUCTION
+
EVIDENCE LINKING
+
COMPARATIVE STRUCTURE
+
SOURCE GRAPH
+
TESTING
+
FINAL AUDIT

have been addressed.

---

55. FAILURE HANDLING

If a source cannot be verified:

DO NOT INVENT.

Mark UNVERIFIED.

If a historical question is disputed:

mark DISPUTED.

If multiple Jewish traditions disagree:

preserve the disagreement.

If academic scholarship disagrees:

preserve the competing positions.

If data cannot yet be completed:

record the gap explicitly.

Incomplete but honest data is preferable to fabricated completeness.

---

56. SECURITY / INTEGRITY RULE

Do not modify unrelated application functionality.

Do not change production logic merely to make the Judaism KB easier to implement unless technically necessary.

Do not expose secrets.

Do not modify API keys.

Do not alter authentication.

Do not alter unrelated infrastructure.

Keep Judaism KB changes isolated and maintainable.

---

57. TEST SUITE

Create representative test questions.

At minimum include:

TEST 001
"What is Judaism?"

TEST 002
"What is the Tanakh?"

TEST 003
"Are Tanakh and the Christian Old Testament identical?"

TEST 004
"What is the Jewish understanding of Messiah?"

TEST 005
"Do Jews believe Jesus is the Messiah?"

TEST 006
"What does the Mishnah represent?"

TEST 007
"What is the difference between Mishnah and Talmud?"

TEST 008
"What is the Masoretic Text?"

TEST 009
"What are the Dead Sea Scrolls?"

TEST 010
"What is tahrif?"

TEST 011
"Do all Jews believe the same thing about Torah?"

TEST 012
"What is the Jewish view of Trinity?"

TEST 013
"What is the Jewish response to Christian messianic proof texts?"

TEST 014
"How does Judaism understand Moses compared with Islam?"

TEST 015
"What is the difference between Judaism and Zionism?"

TEST 016
"Is every Israeli Jewish?"

TEST 017
"What is Messianic Judaism?"

TEST 018
"What did first-century Jews believe about Messiah?"

TEST 019
"How does Judaism understand the covenant?"

TEST 020
"How does Judaism differ from Christianity and Islam on salvation?"

For each test verify:

- correct tradition identification;
- source retrieval;
- source provenance;
- contextual accuracy;
- avoidance of overgeneralization;
- correct handling of disagreement;
- absence of fabricated citations.

---

58. FINAL REPORT

At completion, provide a concise but technically precise report containing:

A. Architecture

What was created?

B. Files

Which files were added or modified?

C. Sources

How many source records were discovered?

How many were:

VERIFIED
PARTIALLY_VERIFIED
UNVERIFIED
DISPUTED

D. Knowledge

How many knowledge items were created?

E. Evidence

How many evidence records?

F. Graph

How many source/claim relationships?

G. Testing

How many tests?

How many passed?

How many failed?

H. Gaps

What remains incomplete?

I. Risks

What remains uncertain?

J. Readiness

Is this:

READY_FOR_POLIA

or

NOT_READY

Do not report READY_FOR_POLIA unless the evidence and tests support that conclusion.

---

59. FINAL ACCEPTANCE CRITERIA

The Judaism KB may be considered ready only when:

[ ] Repository architecture inspected
[ ] Existing KB architecture understood
[ ] No destructive changes made
[ ] Constitution created or integrated
[ ] Taxonomy implemented
[ ] Schema implemented
[ ] Source registry implemented
[ ] Three-pass source research completed
[ ] Three source-gap audits completed
[ ] Primary sources represented
[ ] Rabbinic sources represented
[ ] Historical sources represented
[ ] Academic sources represented
[ ] Modern Jewish sources represented
[ ] Denominational diversity represented
[ ] Textual traditions represented
[ ] Hebrew / Aramaic layer represented
[ ] Theology layer represented
[ ] Second Temple layer represented
[ ] Rabbinic layer represented
[ ] Messiah cluster represented
[ ] Judaism-Jesus cluster represented
[ ] Judaism-Christianity cluster represented
[ ] Judaism-Islam cluster represented
[ ] Tahrif handled with distinctions
[ ] Israel/Zionism distinction represented
[ ] Evidence Bank implemented
[ ] Source Graph implemented
[ ] Debate structures implemented
[ ] Provenance implemented
[ ] Verification status implemented
[ ] Automated validation implemented
[ ] Test suite implemented
[ ] Test suite executed
[ ] Final audit executed
[ ] Remaining gaps documented
[ ] Final report generated

---

60. START NOW

Begin immediately.

Do not merely explain what you intend to do.

Perform the repository inspection first.

Then execute the full pipeline.

Use the existing project architecture whenever possible.

Do not fabricate information.

Do not fabricate sources.

Do not fabricate quotations.

Do not flatten Judaism into one position.

Preserve provenance.

Preserve uncertainty.

Preserve disagreements.

Build a clean, modular, scalable, maintainable Judaism Knowledge Base that can become a permanent Polia knowledge layer.

FINAL PRINCIPLE:

UNDERSTAND FIRST
VERIFY SECOND
STRUCTURE THIRD
COMPARE FOURTH
ARGUE FIFTH

Never reverse that order.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-11T03:47:52+07:00.
</ADDITIONAL_METADATA>