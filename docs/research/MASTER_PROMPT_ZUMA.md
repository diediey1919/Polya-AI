<USER_REQUEST>
MASTER EXECUTION PROMPT

ZUMA DEBATE PERSONA EXTRACTION & STRATEGIC SKILL ENGINEERING

Untuk Antigravity — Polya Apologetika

---

0. MANDATE UTAMA

Tugas ini adalah penelitian dan rekayasa skill debat, bukan tugas membuat ringkasan video.

Antigravity harus meneliti 10 video TERBARU dari channel Zulkifli M. Abbas / ZUMA, menggunakan transcript sebagai bahan utama, kemudian mengekstraksi:

- cara ZUMA berbicara dalam debat/diskusi lintas iman
- cara ZUMA bertanya
- cara ZUMA membangun tekanan argumentatif
- cara ZUMA membedah argumen
- cara ZUMA melakukan cross-examination
- cara ZUMA melakukan rebuttal
- cara ZUMA menggunakan sumber
- cara ZUMA mengontrol percakapan
- cara ZUMA membaca jawaban lawan
- cara ZUMA mengubah jawaban lawan menjadi pertanyaan berikutnya
- cara ZUMA menyusun strategi menghadapi berbagai tipe lawan
- pola karakter debat yang konsisten
- pola yang berubah sesuai konteks
- strategi yang dapat diabstraksikan menjadi skill AI

Tujuan akhir:

«Menghasilkan ZUMA Debate Persona + ZUMA Strategic Debate Skill yang dapat digunakan Polya sebagai strategic/persona layer dalam Debate Engine.»

Jangan membuat Polya meniru Zulkifli M. Abbas secara verbal.

Yang diambil adalah metode, pola berpikir, pola interaksi, teknik debat, strategi, dan karakter argumentatif yang dapat diabstraksikan.

---

1. ATURAN PALING PENTING

1.1 Jangan melakukan imitasi literal

Jangan membuat aturan seperti:

«"Polya harus menggunakan kalimat yang biasa diucapkan ZUMA."»

Jangan menyalin:

- kalimat
- catchphrase
- umpatan
- kata kasar
- penghinaan
- ejekan personal
- verbal aggression yang tidak memiliki fungsi argumentatif
- kebiasaan linguistik yang hanya merupakan ciri personal

Yang harus diekstraksi:

Observed Speech
      ↓
Behavior
      ↓
Technique
      ↓
Pattern
      ↓
Strategy
      ↓
Abstract Skill

---

2. SUMBER CORPUS

Cari channel resmi Zulkifli M. Abbas / ZUMA.

Kemudian:

«Identifikasi 10 VIDEO TERBARU yang tersedia pada saat penelitian dilakukan.»

Jangan memilih video berdasarkan popularitas.

Jangan memilih video berdasarkan judul yang paling menarik.

Prioritas:

Channel
   ↓
Sort by newest/latest
   ↓
10 most recent videos
   ↓
Corpus

Catat untuk setiap video:

video_id
title
URL
publication_date
duration
channel
available_transcript
transcript_source

Jika ada video yang tidak memiliki transcript yang dapat diproses:

1. catat kegagalannya,
2. jangan mengarang transcript,
3. cari transcript alternatif yang valid bila memungkinkan,
4. jika tetap tidak tersedia, tandai video tersebut,
5. jangan diam-diam menggantinya tanpa dokumentasi.

Target corpus harus tetap:

«10 video terbaru yang benar-benar berhasil diproses, jika secara teknis memungkinkan.»

---

3. JANGAN LANGSUNG MENGANALISIS VIDEO

Setiap video harus melewati pipeline:

VIDEO
 ↓
METADATA
 ↓
TRANSCRIPT
 ↓
SPEAKER IDENTIFICATION
 ↓
TIMESTAMP
 ↓
SPEAKER-ATTRIBUTED TRANSCRIPT
 ↓
CONVERSATION SEGMENTATION
 ↓
ZUMA SPEECH DETECTION
 ↓
BEHAVIOR EXTRACTION
 ↓
TECHNIQUE EXTRACTION
 ↓
STRATEGY EXTRACTION

Baru setelah itu dilakukan corpus-level synthesis.

---

4. SPEAKER IDENTIFICATION

Ini merupakan tahap kritis.

Transcript tidak boleh dianggap seluruhnya sebagai ucapan ZUMA.

Deteksi dan pisahkan:

ZUMA
OPPONENT
HOST
GUEST
NARRATOR
AUDIENCE
UNKNOWN

Jika transcript tidak menyediakan speaker label:

gunakan konteks percakapan, nama pembicara, pola dialog, dan informasi video untuk melakukan speaker attribution.

Setiap observasi harus mempunyai:

video_id
timestamp
speaker
text
context
confidence

Jika speaker tidak dapat ditentukan dengan cukup yakin:

speaker = UNKNOWN
confidence = LOW

Jangan mengatribusikan ucapan kepada ZUMA hanya berdasarkan asumsi.

---

5. ZUMA SPEECH DETECTION

Setelah transcript tersedia, lakukan scanning khusus terhadap ucapan ZUMA.

Jangan hanya mengambil kalimat yang mengandung kata "ZUMA".

Deteksi seluruh unit ucapan ZUMA yang mempunyai fungsi:

- questioning
- clarification
- challenge
- rebuttal
- explanation
- evidence request
- source request
- definition request
- contradiction detection
- burden-of-proof challenge
- comparison
- analogy
- concession
- counterargument
- cross-examination
- topic control
- strategic redirection
- closing

Buat dataset internal:

ZUMA_SPEECH_SEGMENTS

dengan:

video_id
timestamp_start
timestamp_end
speaker
utterance
conversation_stage
function
target_claim
technique
context
confidence

---

6. SEGMENTASI PERCAKAPAN

Jangan menganalisis video sebagai satu blok.

Identifikasi struktur aktual.

Gunakan kategori berikut bila sesuai:

Opening
Introduction
Issue Definition
Worldview Setup
Claim
Question
Clarification
Evidence Request
Argument
Counterargument
Cross Examination
Rebuttal
Follow-up
Contradiction
Escalation
Topic Shift
Topic Recovery
Concession
Resolution
Closing

Jika struktur aktual berbeda, jangan memaksakan kategori.

---

7. ANALISIS SETIAP VIDEO

Setiap video harus dianalisis secara independen terlebih dahulu.

Buat:

VIDEO 01 ANALYSIS
VIDEO 02 ANALYSIS
...
VIDEO 10 ANALYSIS

Untuk setiap video ekstrak:

A. Debate Context

- topik
- worldview pihak-pihak
- jenis diskusi
- posisi masing-masing pihak
- isu utama
- isu sekunder

B. ZUMA Behavior

Apa yang dilakukan ZUMA?

C. ZUMA Technique

Teknik apa yang digunakan?

D. Strategic Purpose

Mengapa teknik tersebut digunakan pada konteks itu?

E. Opponent Response

Bagaimana lawan merespons?

F. ZUMA Adaptation

Bagaimana ZUMA mengubah langkah setelah respons lawan?

G. Outcome

Apa hasil argumentatif dari strategi tersebut?

---

8. QUESTIONING SYSTEM

Ekstrak seluruh pola pertanyaan ZUMA.

Klasifikasikan:

Clarification Question
Definition Question
Source Question
Evidence Question
Context Question
Meaning Question
Consistency Question
Socratic Question
Comparative Question
Follow-up Question
Pressure Question
Consequence Question
Burden-of-Proof Question
Contradiction Question
Precision Question

Untuk setiap pola:

Observed Question
      ↓
Purpose
      ↓
Opponent Answer
      ↓
Next ZUMA Question
      ↓
Strategic Effect

Fokus khusus pada:

«question chaining»

yaitu ketika jawaban lawan menjadi dasar pertanyaan berikutnya.

---

9. ARGUMENT DECOMPOSITION

Setiap argumen penting harus dipecah:

CLAIM
 ↓
PREMISE 1
PREMISE 2
PREMISE 3
 ↓
HIDDEN ASSUMPTION
 ↓
EVIDENCE
 ↓
INTERPRETATION
 ↓
INFERENCE
 ↓
CONCLUSION

Kemudian identifikasi bagian mana yang diuji ZUMA.

Jangan hanya mengatakan:

«"ZUMA membantah argumen."»

Harus dijelaskan:

«"ZUMA menyerang premise kedua karena evidence yang diberikan tidak mendukung inference menuju conclusion."»

---

10. CROSS-EXAMINATION EXTRACTION

Ini adalah salah satu skill prioritas tertinggi.

Pelajari bagaimana ZUMA:

CLAIM
 ↓
SOURCE?
 ↓
TEXT?
 ↓
MEANING?
 ↓
CONTEXT?
 ↓
INTERPRETATION?
 ↓
CONSISTENCY?
 ↓
CONSEQUENCE?

Analisis:

- urutan pertanyaan
- timing
- follow-up
- repetition
- narrowing
- commitment extraction
- concession harvesting
- contradiction lock
- return-to-issue
- pressure escalation

Cari pola:

«Apa yang ZUMA lakukan setelah lawan memberikan jawaban tertentu?»

---

11. REBUTTAL SYSTEM

Klasifikasikan rebuttal:

Direct Refutation
Source Refutation
Contextual Refutation
Logical Refutation
Premise Attack
Definition Challenge
Evidence Challenge
Interpretation Challenge
Internal Contradiction
Burden-of-Proof Challenge
Alternative Explanation
Counterexample
Comparative Argument
Consequence Argument

Kemudian cari decision rule:

WHEN X OCCURS
        ↓
ZUMA SELECTS Y
        ↓
BECAUSE Z

Tujuan penelitian bukan hanya mengetahui:

«"Teknik apa?"»

tetapi:

«"Kapan teknik tersebut dipilih dan mengapa?"»

---

12. SOURCE / SCRIPTURE HANDLING

Analisis bagaimana ZUMA menggunakan:

- kitab
- ayat
- dokumen
- sejarah
- kutipan
- pendapat ahli
- sumber akademik
- sumber primer
- sumber sekunder

Pipeline:

SOURCE IDENTIFICATION
 ↓
TEXT
 ↓
CONTEXT
 ↓
MEANING
 ↓
INTERPRETATION
 ↓
COMPARISON
 ↓
ARGUMENT

Pisahkan:

FACT ABOUT SOURCE

dari:

DEBATE INTERPRETATION

Jangan memasukkan interpretasi ZUMA sebagai fakta objektif tanpa label.

---

13. INTERFAITH DEBATE SKILL

Analisis bagaimana ZUMA memasuki worldview lawan.

Periksa apakah ia:

- menggunakan terminologi lawan
- menggunakan sumber yang diakui lawan
- mencari common ground
- membangun premise bersama
- menguji worldview dari dalam kerangka epistemiknya sendiri
- menunjukkan internal tension
- membandingkan worldview
- kembali ke central issue

Target skill Polya:

«Enter the opponent's epistemic framework before challenging it.»

Tetapi jangan menganggap teknik tersebut selalu tepat.

Catat kondisi kapan berhasil dan kapan tidak.

---

14. DEBATE CONTROL

Analisis:

Topic Control
Question Control
Definition Control
Evidence Control
Burden-of-Proof Control
Conversation Focus
Turn Control
Conversation Recovery

Cari respons ZUMA terhadap:

Topic diversion

Opponent changes topic
        ↓
ZUMA detects diversion
        ↓
Returns to original issue

Long answer

Long answer
 ↓
Extract relevant claim
 ↓
Ignore irrelevant branches
 ↓
Return to question

Evasion

Question
 ↓
No direct answer
 ↓
Restate / narrow
 ↓
Specific follow-up

Personal attack

Analisis bagaimana ZUMA merespons tanpa otomatis menjadikannya pola yang harus ditiru.

---

15. STRATEGIC "OPPONENT DISMANTLING"

Gunakan istilah ini dalam arti:

«Argumentative dismantling, bukan personal destruction.»

Cari bagaimana ZUMA mencari titik yang paling menentukan.

Opponent produces 10 claims
        ↓
Classify claims
        ↓
Identify foundational claims
        ↓
Identify central premise
        ↓
Identify vulnerable premise
        ↓
Attack highest-leverage point

Ekstrak strategi:

- weak-point detection
- premise isolation
- evidence isolation
- contradiction exploitation
- definition tightening
- source challenge
- commitment trapping
- concession harvesting
- consequence exposure
- argument compression

---

16. QUESTION CHAINING

Buat model:

Q1
 ↓
Opponent Answer
 ↓
Extract Commitment
 ↓
Q2
 ↓
Opponent Answer
 ↓
Extract Commitment
 ↓
Q3
 ↓
...

Cari apakah terdapat pola:

Clarify
 ↓
Commit
 ↓
Constrain
 ↓
Test
 ↓
Expose
 ↓
Resolve

Jika ditemukan berulang, abstraksikan menjadi skill.

---

17. CONTRADICTION LOCK

Deteksi:

Opponent Position A
       ↓
Commitment recorded
       ↓
Later Position B
       ↓
Potential contradiction
       ↓
Comparison
       ↓
Reconciliation question

Jangan langsung memberi label:

«"contradiction"»

jika sebenarnya masih dapat direkonsiliasi.

Gunakan:

Potential contradiction
Actual contradiction
Unresolved tension

dengan confidence.

---

18. CONCESSION HARVESTING

Cari bagaimana ZUMA memanfaatkan concession.

Opponent accepts A
       ↓
Record A
       ↓
Use A as established premise
       ↓
Move to B

Jangan membuat concession palsu.

Jika lawan mengatakan:

«"Saya tidak mengatakan itu."»

maka status harus dikoreksi.

---

19. ADAPTIVE STRATEGY

Bandingkan seluruh 10 video.

Cari:

Opponent Type
       ↓
Context
       ↓
ZUMA Strategy
       ↓
Opponent Response
       ↓
ZUMA Adaptation

Kelompokkan misalnya:

Opponent evasive
Opponent aggressive
Opponent academic
Opponent theological
Opponent historical
Opponent philosophical
Opponent conversational
Opponent highly technical

Jangan mengarang kategori jika corpus tidak mendukungnya.

---

20. COMMUNICATION PERSONA

Ekstrak karakter komunikasi:

Tone

- calm
- firm
- investigative
- assertive
- confrontational
- persuasive
- academic
- conversational

Rhythm

- short/long responses
- repetition
- pauses
- escalation
- compression

Question style

- direct
- Socratic
- probing
- comparative
- sequential
- precision-oriented

Response style

- answer
- challenge
- reverse question
- definition request
- source request
- premise test

Setiap karakter harus dibuktikan oleh pola yang muncul dalam corpus.

---

21. BEDAKAN CORE PERSONA DAN ADAPTIVE PERSONA

Hasil harus dibagi:

CORE PERSONA

yaitu perilaku yang relatif konsisten.

Dan:

ADAPTIVE STRATEGIES

yaitu perilaku yang berubah sesuai kondisi.

Contoh:

CORE:
Evidence-oriented questioning

ADAPTIVE:
Increase questioning pressure when opponent repeatedly avoids direct answers

---

22. ANTI-PATTERN EXTRACTION

Cari bukan hanya:

«Apa yang ZUMA lakukan?»

tetapi juga:

«Apa yang ZUMA cenderung hindari?»

Contoh hanya jika benar-benar terobservasi:

Do not chase irrelevant claims
Do not accept undefined terms
Do not abandon central issue
Do not treat assertion as evidence
Do not confuse source with interpretation
Do not allow unlimited topic switching

Setiap anti-pattern harus mempunyai evidence.

---

23. STRATEGIC DECISION TREE

Setelah seluruh corpus dianalisis, buat decision tree.

Contoh:

OPPONENT CLAIM
      ↓
Is claim clear?
   /       \
 NO         YES
 ↓           ↓
Clarify    Evidence?
             /   \
           NO     YES
           ↓       ↓
      Ask source  Examine evidence
                     ↓
                Valid inference?
                   /      \
                 NO        YES
                 ↓          ↓
              Attack     Continue

Decision tree final harus berasal dari pola corpus.

---

24. POLYA ENHANCEMENT LAYER

Ini sangat penting.

Jangan berhenti pada:

ZUMA PERSONA

Tambahkan:

ZUMA STRATEGY
      +
POLYA KNOWLEDGE
      +
POLYA REASONING
      +
SOURCE VERIFICATION
      +
HISTORICAL CHRONOLOGY
      +
TEXTUAL EVIDENCE
      +
CROSS-SOURCE CHECKING
      ↓
ENHANCED POLYA DEBATE

Jika ZUMA menemukan celah argumentasi tetapi fakta yang digunakan belum diverifikasi, Polya wajib melakukan verification terlebih dahulu.

---

25. FACT / DATE / YEAR VERIFICATION

Jika dalam debat terdapat klaim mengenai:

- sejarah
- tokoh
- kitab
- dokumen
- peristiwa
- tanggal
- tahun
- kutipan
- publikasi

Polya harus mampu melakukan:

CLAIM
 ↓
SOURCE
 ↓
EXACT TEXT
 ↓
DATE
 ↓
YEAR
 ↓
HISTORICAL CONTEXT
 ↓
CORROBORATION
 ↓
CONFIDENCE

Jangan menggunakan kepastian palsu.

Gunakan status:

CONFIRMED
PROBABLE
DISPUTED
UNCERTAIN
UNSUPPORTED
CONTRADICTED

---

26. EVIDENCE HIERARCHY

Untuk setiap claim penting:

Claim
 ↓
Evidence
 ↓
Primary Source?
 ↓
Secondary Source?
 ↓
Independent Corroboration?
 ↓
Context
 ↓
Interpretation

Pisahkan:

WHAT THE SOURCE SAYS

dari:

WHAT THE DEBATER CLAIMS IT MEANS

---

27. DEBATE STATE MEMORY

Simulasi Polya harus menyimpan:

Opponent Claims
Opponent Definitions
Opponent Sources
Opponent Commitments
Opponent Concessions
Opponent Contradictions
Unanswered Questions
Evidence Presented
Evidence Missing
Resolved Issues
Unresolved Issues

Dengan demikian strategi berikutnya harus menggunakan conversation history, bukan mengulang dari nol.

---

28. SELF-CORRECTION LOOP

Gunakan:

Opponent Statement
       ↓
Analyze
       ↓
Select ZUMA Strategy
       ↓
Respond
       ↓
Opponent Response
       ↓
Re-analyze
       ↓
Update Debate State
       ↓
Change Strategy if necessary
       ↓
Continue

Polya tidak boleh terpaku pada strategi awal jika respons lawan membuktikan strategi tersebut tidak efektif.

---

29. STEELMAN

Sebelum melakukan serangan besar:

Opponent Argument
       ↓
Steelman
       ↓
Strongest reasonable interpretation
       ↓
Test
       ↓
Identify actual weakness

Polya tidak boleh menyerang strawman.

---

30. STRATEGIC TARGET SELECTION

Jika terdapat banyak kelemahan, jangan menyerang semuanya.

Ranking:

Centrality
Importance
Vulnerability
Evidence availability
Logical consequence
Strategic leverage

Kemudian pilih:

«Highest-leverage attack point.»

---

31. NO FALSE VICTORY RULE

Polya tidak boleh menganggap:

minor mistake = opponent defeated

Bedakan:

Minor Error
Major Error
Foundational Error
Fatal Argument Failure

Hanya jika kelemahan tersebut menghancurkan premise utama, boleh dianggap sebagai kegagalan argumentatif yang signifikan.

---

32. DEBATE END STATES

Hasil debat tidak hanya:

WIN / LOSE

Gunakan:

Opponent Concedes
Opponent Revises Claim
Opponent Narrows Claim
Opponent Provides Evidence
Evidence Supports Opponent
Evidence Supports Polya
Evidence Inconclusive
Claim Remains Unproven
Contradiction Remains
Question Remains Open

Polya harus berani mengatakan:

«"Belum terbukti."»

dan tidak otomatis mengatakan:

«"Berarti salah."»

---

33. CORPUS-LEVEL SYNTHESIS

Setelah Video 01 sampai Video 10 selesai dianalisis:

BARU lakukan cross-video comparison.

Cari:

Repeated Patterns

Muncul berkali-kali.

Contextual Patterns

Muncul pada kondisi tertentu.

Signature Patterns

Sangat khas dan berulang.

Adaptive Patterns

Berubah berdasarkan lawan/konteks.

Anti-Patterns

Pola yang cenderung dihindari.

Jangan menyimpulkan persona hanya dari satu video.

---

34. SIGNATURE PATTERNS

Minimal identifikasi:

Signature Question Pattern
Signature Follow-up Pattern
Signature Cross-Examination Pattern
Signature Rebuttal Pattern
Signature Source Pattern
Signature Conversation-Control Pattern
Signature Pressure Pattern
Signature Closing Pattern

Untuk masing-masing:

Pattern
Evidence Count
Videos Observed
Typical Context
Strategic Purpose
Confidence

---

35. CONFIDENCE MODEL

Gunakan:

HIGH
MEDIUM
LOW

Dan:

OBSERVED
INFERRED
GENERALIZED

Contoh:

Observed:
ZUMA repeatedly asks for source.

Inferred:
Source verification is strategically important to him.

Generalized:
When facing an unsupported factual claim, request source before attacking conclusion.

Jangan menyamakan ketiganya.

---

36. PROVENANCE

Setiap skill penting harus dapat ditelusuri.

Format:

Skill
 ↓
Pattern
 ↓
Video IDs
 ↓
Timestamp
 ↓
Transcript segment
 ↓
Evidence

Jika sebuah skill tidak memiliki provenance yang cukup:

confidence = LOW

atau jangan dimasukkan ke core persona.

---

37. MASTER ZUMA PERSONA SCHEMA

Output final minimal:

{
  "name": "ZUMA Debate Persona",
  "version": "1.0",
  "purpose": "",
  "source_corpus": [],
  "core_principles": [],
  "questioning": {},
  "socratic_method": {},
  "argument_decomposition": {},
  "cross_examination": {},
  "rebuttal": {},
  "source_analysis": {},
  "scripture_handling": {},
  "interfaith_dialogue": {},
  "burden_of_proof": {},
  "logical_analysis": {},
  "conversation_control": {},
  "strategic_dismantling": {},
  "question_chaining": {},
  "contradiction_lock": {},
  "concession_harvesting": {},
  "adaptive_strategy": {},
  "communication_style": {},
  "signature_patterns": [],
  "anti_patterns": [],
  "decision_trees": [],
  "debate_workflow": {},
  "simulation_protocol": {},
  "self_correction": {},
  "confidence": {},
  "provenance": {},
  "polya_enhancement_layer": {}
}

---

38. MASTER SKILL DOCUMENT

Selain JSON, hasilkan dokumentasi manusia yang menjelaskan minimal:

01. Persona Overview
02. Debate Philosophy
03. Core Principles
04. Character Profile
05. Questioning System
06. Socratic Method
07. Argument Decomposition
08. Cross-Examination
09. Rebuttal System
10. Evidence & Source Handling
11. Scripture Handling
12. Interfaith Dialogue
13. Burden of Proof
14. Logical Analysis
15. Conversation Control
16. Strategic Dismantling
17. Question Chaining
18. Contradiction Lock
19. Concession Harvesting
20. Adaptive Strategy
21. Communication Style
22. Signature Patterns
23. Anti-Patterns
24. Decision Trees
25. Debate Workflow
26. Simulation Protocol
27. Self-Correction
28. Confidence & Provenance
29. Polya Enhancement Layer
30. Integration Specification

---

39. JANGAN CAMPURKAN PERSONA DAN KNOWLEDGE

Arsitektur harus tetap:

ZUMA PERSONA
=
HOW TO DEBATE

sedangkan:

KNOWLEDGE BASE
=
WHAT IS KNOWN

Dan:

POLYA
=
KNOWLEDGE
+
REASONING
+
APOLOGETICS
+
DEBATE SKILLS
+
ZUMA STRATEGIC PERSONA

ZUMA Persona bukan sumber fakta.

Jika ZUMA mengatakan fakta tertentu, fakta tersebut tidak otomatis menjadi knowledge Polya.

Fakta harus diverifikasi melalui knowledge/evidence layer.

---

40. UNSEEN VIDEO VALIDATION

Jangan langsung memasukkan hasil ke production.

Setelah skill selesai:

TRAINING CORPUS
10 latest videos
        ↓
ZUMA PERSONA
        ↓
MASTER SKILL

Kemudian gunakan video/segmen ZUMA yang tidak termasuk 10 video corpus.

Polya harus:

UNSEEN SEGMENT
      ↓
ANALYZE
      ↓
IDENTIFY CLAIM
      ↓
SELECT STRATEGY
      ↓
QUESTION
      ↓
FOLLOW-UP
      ↓
REBUTTAL

Evaluator kemudian membandingkan:

TRAINING-CORPUS PATTERNS
        VS
UNSEEN ZUMA BEHAVIOR

Nilai:

- strategy consistency
- questioning consistency
- cross-examination consistency
- adaptive behavior consistency
- communication consistency
- false-positive rate
- unsupported inference
- overfitting

---

41. OVERFITTING CHECK

Ini wajib.

Jika skill hanya cocok terhadap 10 video training tetapi gagal pada video baru:

«Jangan nyatakan persona berhasil.»

Cari penyebab:

Overfitting
Too-specific rule
Transcript artifact
Speaker attribution error
Context-specific behavior mistaken as core persona
Insufficient corpus evidence

Revisi skill jika diperlukan.

---

42. QUALITY GATE FINAL

Antigravity hanya boleh menyatakan:

«ZUMA Debate Persona Skill READY»

jika:

[ ] 10 latest videos identified
[ ] URLs recorded
[ ] Metadata recorded
[ ] Transcript obtained
[ ] Speaker attribution performed
[ ] ZUMA speech isolated
[ ] Timestamps retained
[ ] Conversation segmented
[ ] Claims extracted
[ ] Questions extracted
[ ] Follow-up chains analyzed
[ ] Cross-examination analyzed
[ ] Rebuttals analyzed
[ ] Source handling analyzed
[ ] Scripture handling analyzed
[ ] Interfaith patterns analyzed
[ ] Debate-control patterns analyzed
[ ] Communication persona analyzed
[ ] Adaptive patterns compared
[ ] Repeated patterns identified
[ ] Signature patterns identified
[ ] Anti-patterns identified
[ ] Strategic dismantling analyzed
[ ] Provenance retained
[ ] Confidence assigned
[ ] Core vs adaptive persona separated
[ ] Persona vs knowledge separated
[ ] Polya enhancement layer defined
[ ] Master skill generated
[ ] Decision trees generated
[ ] Simulation protocol generated
[ ] Self-correction implemented
[ ] Unseen-video validation performed
[ ] Overfitting checked
[ ] Unsupported persona claims removed
[ ] Final skill ready for integration

---

43. OUTPUT DIRECTORY

Simpan seluruh hasil secara terstruktur dan jangan mencampurnya dengan Knowledge Base.

Gunakan struktur:

skills/
└── debate/
    └── zuma/
        ├── README.md
        ├── persona.json
        ├── persona.md
        ├── questioning.md
        ├── cross-examination.md
        ├── rebuttal.md
        ├── argument-analysis.md
        ├── source-analysis.md
        ├── scripture-handling.md
        ├── interfaith-dialogue.md
        ├── debate-control.md
        ├── strategic-dismantling.md
        ├── adaptive-strategy.md
        ├── decision-trees.md
        ├── signature-patterns.md
        ├── anti-patterns.md
        ├── simulation-protocol.md
        ├── validation.md
        └── provenance/
            ├── corpus-index.json
            ├── video-01.md
            ├── video-02.md
            ├── video-03.md
            ├── video-04.md
            ├── video-05.md
            ├── video-06.md
            ├── video-07.md
            ├── video-08.md
            ├── video-09.md
            └── video-10.md

Jika repository Polya memiliki struktur skill yang berbeda, ikuti arsitektur repository yang sudah ada dan jangan membuat struktur baru yang bertentangan.

---

44. GIT / SOURCE OF TRUTH

Semua perubahan harus mengikuti:

Antigravity / Development
        ↓
Repository
        ↓
Git
        ↓
GitHub

GitHub tetap menjadi source of truth.

Jangan menghapus artefak provenance hanya demi merapikan repository.

---

45. EXECUTION MODE

Gunakan pendekatan:

PLAN
 ↓
EXECUTE
 ↓
MONITOR
 ↓
VERIFY
 ↓
REFINE

Jangan langsung melakukan perubahan production.

Tahap pertama adalah:

DISCOVERY

Setelah itu:

CORPUS BUILDING

Kemudian:

ANALYSIS

Kemudian:

SYNTHESIS

Kemudian:

VALIDATION

Baru:

INTEGRATION

---

46. FINAL PRINCIPLE

Tujuan akhir bukan:

«"Membuat Polya berbicara seperti Zulkifli M. Abbas."»

Tujuannya:

«Membuat Polya memahami dan mampu menerapkan pola strategi debat yang secara konsisten teramati dari ZUMA, tanpa menyalin bahasa kasar atau identitas personalnya, kemudian meningkatkan strategi tersebut menggunakan kemampuan Polya sendiri dalam reasoning, evidence verification, textual analysis, historical chronology, source criticism, dan knowledge retrieval.»

Dengan demikian:

ZUMA
=
Strategic Debate School

sedangkan:

POLYA
=
ZUMA Strategy
+
Independent Reasoning
+
Verified Evidence
+
Knowledge
+
Historical Accuracy
+
Textual Analysis
+
Apologetics
+
Adaptive Debate Engine

Target akhirnya adalah:

OBSERVE ZUMA
      ↓
UNDERSTAND ZUMA
      ↓
ABSTRACT ZUMA
      ↓
ENGINEER SKILL
      ↓
VALIDATE ON UNSEEN DATA
      ↓
ENHANCE WITH POLYA
      ↓
INTEGRATE INTO DEBATE ENGINE

Jangan menyatakan pekerjaan selesai hanya karena transcript 10 video telah diproses.

Pekerjaan selesai hanya setelah skill abstraction + corpus synthesis + provenance + unseen validation berhasil.47. CORPUS EXPANSION & ZUMA PATTERN REFINEMENT

ZUMA Debate Persona adalah model yang terus disempurnakan oleh penambahan corpus, bukan skill yang dianggap final setelah hanya 10 video.

10 video terbaru merupakan initial corpus / baseline corpus.

Ketika video tambahan diproses, sistem harus melakukan:

NEW ZUMA VIDEOS
      ↓
TRANSCRIPT
      ↓
SPEAKER DETECTION
      ↓
BEHAVIOR EXTRACTION
      ↓
COMPARE WITH EXISTING ZUMA PATTERN
      ↓
CONFIRM / STRENGTHEN / MODIFY / REMOVE
      ↓
UPDATED ZUMA PERSONA

---

48. PRINCIPLE OF PATTERN REFINEMENT

Semakin banyak video yang dianalisis, semakin tinggi kemampuan sistem untuk membedakan:

ZUMA CORE PATTERN

dari:

CONTEXT-SPECIFIC BEHAVIOR

dan:

NON-ZUMA / NOISE / INCIDENTAL BEHAVIOR

Jangan menganggap setiap perilaku yang muncul pada satu video sebagai karakter ZUMA.

---

49. PATTERN MATURATION

Setiap pattern harus mempunyai status kematangan.

Gunakan model:

OBSERVED
   ↓
REPEATED
   ↓
CORROBORATED
   ↓
GENERALIZED
   ↓
CORE PATTERN

Namun pattern juga dapat bergerak sebaliknya:

CORE PATTERN
   ↓
New Evidence
   ↓
Pattern Weakens
   ↓
Context-Specific
   ↓
Low Confidence

atau bahkan:

CORE PATTERN
   ↓
Contradictory Evidence
   ↓
REJECTED / REMOVED

Jadi skill harus evidence-driven dan revisable.

---

50. PATTERN CONFIDENCE SHOULD EVOLVE

Confidence bukan nilai permanen.

Misalnya:

Setelah 1 video

Pattern:
Repeated source questioning

Confidence:
LOW

Status:
OBSERVED

Setelah 5 video

Pattern:
Repeated source questioning

Confidence:
MEDIUM

Status:
CORROBORATED

Setelah 20 video

Pattern:
Source verification before accepting factual claim

Confidence:
HIGH

Status:
GENERALIZED / CORE

Jumlah video bukan satu-satunya faktor.

Pertimbangkan juga:

- frequency
- consistency
- context diversity
- opponent diversity
- topic diversity
- strategic consistency
- contradictory examples

---

51. NEGATIVE EVIDENCE

Ini sangat penting.

Jika sebuah pattern terlihat pada video 1:

ZUMA uses strategy X

tetapi setelah 20 video ternyata:

X only appears under context Y

maka jangan lagi menyebut X sebagai:

«Core ZUMA Persona.»

Ubah menjadi:

«Contextual Strategy.»

Jika pattern bahkan tidak muncul lagi pada corpus yang lebih besar, pertimbangkan:

«Incidental / weak evidence.»

---

52. REMOVE NON-ZUMA STYLE

Tujuan penambahan corpus bukan hanya menambah skill.

Tujuannya juga:

«Menghapus elemen yang ternyata bukan merupakan karakter inti ZUMA.»

Contoh:

VIDEO 01
ZUMA uses aggressive tone
        ↓
initial hypothesis:
"ZUMA = aggressive"

Setelah 15 video:

15 videos
        ↓
mostly calm / investigative
        ↓
aggression only under specific opponent/context

Maka:

REMOVE:
"ZUMA is inherently aggressive"

KEEP:
"ZUMA may increase conversational pressure
under specific conditions."

Ini disebut:

«Persona purification.»

---

53. DISTINGUISH SOURCE OF BEHAVIOR

Setiap pattern harus diuji terhadap kemungkinan bahwa perilaku tersebut berasal dari:

ZUMA
Opponent
Topic
Moderator
Format
Audience
Emotional Context
Specific Event
Video Editing
Transcript Artifact

Jangan langsung mengatribusikan semuanya kepada ZUMA.

Gunakan:

ATTRIBUTION CONFIDENCE

Jika penyebab tidak jelas:

UNKNOWN / LOW CONFIDENCE

---

54. CROSS-OPPONENT GENERALIZATION

Pattern yang benar-benar merupakan karakter ZUMA seharusnya memiliki kemungkinan muncul terhadap berbagai lawan dan topik, meskipun bentuk penerapannya dapat berubah.

Bandingkan:

Opponent A
Opponent B
Opponent C
Opponent D
...

dan:

Topic A
Topic B
Topic C
Topic D
...

Cari:

«Apa yang tetap dilakukan ZUMA meskipun lawan dan topiknya berubah?»

Itulah kandidat kuat untuk:

CORE PERSONA

---

55. CONTEXT-SPECIFIC FILTER

Jika sebuah teknik hanya muncul:

Islamic theological debate

tetapi tidak muncul pada:

Christian debate
Jewish discussion
Atheism discussion
Historical discussion
Philosophical discussion

jangan otomatis menjadikannya core persona.

Klasifikasikan:

DOMAIN-SPECIFIC STRATEGY

hingga corpus tambahan membuktikan sebaliknya.

---

56. PATTERN COMPETITION

Jika terdapat dua hipotesis:

Hypothesis A:
ZUMA generally uses direct questions.

Hypothesis B:
ZUMA uses direct questions mainly
when opponent avoids definitions.

Jangan memilih A hanya karena lebih sederhana.

Gunakan evidence corpus untuk menentukan hipotesis yang lebih kuat.

Dengan kata lain:

«Prefer the most evidence-supported explanation, not the most convenient explanation.»

---

57. PATTERN MERGING

Jika dua pattern ternyata merupakan bagian dari strategi yang sama:

Pattern A
Pattern B
        ↓
Common underlying mechanism
        ↓
Merged strategic skill

Contoh:

Definition Challenge
+
Precision Question
+
Clarification Follow-up

        ↓

TERMINOLOGY CONTROL

Tujuannya menghasilkan skill yang modular dan tidak redundan.

---

58. PATTERN SPLITTING

Sebaliknya, jika satu pattern ternyata terlalu luas:

"ZUMA asks questions"

pecah menjadi:

Definition Question
Evidence Question
Consistency Question
Consequence Question
Cross-Examination Question

Pattern harus cukup spesifik untuk dapat dipanggil oleh Debate Engine.

---

59. CORE / ADAPTIVE / CONTEXTUAL / INCIDENTAL

Pada setiap iterasi corpus, klasifikasikan behavior ke empat kelas:

CORE
↓
Konsisten lintas video dan konteks.

ADAPTIVE
↓
Berubah sesuai respons lawan.

CONTEXTUAL
↓
Muncul pada situasi/topik tertentu.

INCIDENTAL
↓
Kemungkinan besar bukan karakter inti.

INCIDENTAL behavior tidak boleh masuk ke core ZUMA Persona.

---

60. ZUMA PATTERN PURIFICATION LOOP

Gunakan loop:

CORPUS
 ↓
EXTRACT
 ↓
CLUSTER
 ↓
COMPARE
 ↓
GENERALIZE
 ↓
TEST
 ↓
REMOVE NOISE
 ↓
REFINE
 ↓
UPDATED PERSONA
 ↓
ADD NEW CORPUS
 ↓
REPEAT

Dengan demikian:

«Semakin besar corpus, semakin bersih model persona.»

---

61. VERSIONING

Jangan overwrite history secara destruktif.

Gunakan versi:

ZUMA Persona v1.0
10 videos

ZUMA Persona v1.1
20 videos

ZUMA Persona v1.2
30 videos

...

Setiap versi harus mencatat:

Corpus size
New patterns
Strengthened patterns
Weakened patterns
Removed patterns
Merged patterns
Split patterns
Confidence changes

---

62. PATTERN CHANGELOG

Buat:

pattern-changelog.md

Contoh:

v1.0
Pattern X = MEDIUM

v1.1
Pattern X strengthened to HIGH
after 8 additional videos.

v1.2
Pattern X downgraded to CONTEXTUAL
after contradictory observations.

v1.3
Pattern X removed from CORE.

Ini penting untuk audit dan debugging.

---

63. CONTINUOUS LEARNING ≠ BLIND ACCUMULATION

Penambahan video tidak berarti semua informasi baru ditambahkan ke persona.

Setiap video baru harus menjawab:

Does this confirm an existing pattern?
Does this modify an existing pattern?
Does this contradict an existing pattern?
Does this reveal a new pattern?
Does this show that an existing pattern was contextual?
Does this show that an existing pattern was incidental?

Jika tidak memberikan informasi persona yang relevan:

«jangan menambahkannya.»

---

64. ZUMA PERSONA SHOULD CONVERGE

Target jangka panjang:

More Videos
     ↓
More Observations
     ↓
More Cross-Validation
     ↓
Less Noise
     ↓
Less False Attribution
     ↓
Better Core Pattern
     ↓
More Reliable ZUMA Persona

Dengan corpus yang semakin besar, jumlah core patterns seharusnya relatif stabil, sementara:

- confidence meningkat,
- batas antar-strategi semakin jelas,
- contextual strategies semakin teridentifikasi,
- incidental behaviors semakin banyak tersaring.

---

65. FINAL OBJECTIVE

Tujuan akhirnya bukan menghasilkan:

«"Semakin banyak video, semakin banyak gaya ZUMA yang ditumpuk."»

Tujuan akhirnya adalah:

«Semakin banyak video dipelajari, semakin akurat sistem memahami pola debat ZUMA yang benar-benar konsisten, dan semakin banyak perilaku incidental, contextual, transcript artifact, atau non-ZUMA yang berhasil dikeluarkan dari core persona.»

Dengan demikian ZUMA Debate Persona menjadi:

LARGE CORPUS
      ↓
HIGH-EVIDENCE PATTERNS
      ↓
PURIFIED PERSONA
      ↓
ROBUST STRATEGIC SKILL

bukan:

LARGE CORPUS
      ↓
LARGE COLLECTION OF RANDOM HABITS

---

66. LONG-TERM TARGET

Setelah baseline 10 video selesai dan tervalidasi, corpus dapat diperluas secara bertahap:

10 videos
   ↓
20 videos
   ↓
30 videos
   ↓
50 videos
   ↓
100+ videos

Setiap ekspansi harus menjalankan pattern refinement, bukan sekadar append.

Jika suatu hari corpus sudah sangat besar, gunakan seluruh corpus untuk membangun:

ZUMA CORE PERSONA
        +
ZUMA ADAPTIVE STRATEGIES
        +
ZUMA CONTEXTUAL STRATEGIES
        +
ZUMA SIGNATURE TECHNIQUES
        +
ZUMA ANTI-PATTERNS

dengan confidence dan provenance masing-masing.

---

67. IMPORTANT: PERSONA EVOLUTION MUST NOT CORRUPT POLYA

Walaupun ZUMA Persona terus berkembang, jangan mengubah:

POLYA KNOWLEDGE BASE

hanya karena ditemukan pola baru pada ZUMA.

ZUMA corpus hanya memengaruhi:

DEBATE STRATEGY
PERSONA
INTERACTION METHOD
QUESTIONING
REBUTTAL
CROSS-EXAMINATION
CONVERSATION CONTROL

Fakta, sejarah, tanggal, tahun, teks kitab, dan evidence tetap berasal dari:

POLYA KNOWLEDGE / EVIDENCE LAYER

---

68. CORE DESIGN PRINCIPLE

Tetapkan prinsip berikut sebagai aturan permanen:

«The more ZUMA videos we process, the more refined the ZUMA pattern should become. New evidence must be allowed to strengthen, weaken, split, merge, reclassify, or remove previously inferred behaviors.»

Dan:

«A larger corpus should make the persona cleaner, not merely larger.»

Dan:

«The goal is not to accumulate ZUMA behaviors. The goal is to discover which behaviors genuinely belong to ZUMA's repeatable debate methodology.»69. DATA MODEL & STORAGE CONTRACT

Bagian ini adalah WAJIB.

Antigravity jangan memperlakukan proyek ZUMA sebagai sekadar kumpulan laporan analisis.

Yang sedang dibangun adalah:

«Behavioral Dataset → Debate Pattern Dataset → Strategic Skill → Persona Runtime Module»

Karena corpus akan terus bertambah, struktur data harus modular, traceable, versioned, extensible, dan dapat direvisi tanpa menghancurkan data mentah.

---

70. DATA LAYER ARCHITECTURE

Gunakan pemisahan layer:

LAYER 1
RAW CORPUS
        ↓
LAYER 2
TRANSCRIPT & SPEAKER DATA
        ↓
LAYER 3
BEHAVIORAL OBSERVATIONS
        ↓
LAYER 4
TECHNIQUES
        ↓
LAYER 5
PATTERNS
        ↓
LAYER 6
STRATEGIES
        ↓
LAYER 7
ZUMA PERSONA
        ↓
LAYER 8
POLYA INTEGRATION

Jangan mencampurkan layer-layer tersebut.

---

71. RECOMMENDED DIRECTORY STRUCTURE

Jika repository Polya sudah mempunyai struktur skill yang ditetapkan, sesuaikan dengan arsitektur repository tersebut.

Jika belum ada struktur yang relevan, gunakan:

skills/
└── debate/
    └── zuma/
        │
        ├── corpus/
        │   ├── corpus-index.json
        │   │
        │   ├── video-001/
        │   │   ├── video-002/
        │   │   ├── video-003/
        │   │   ├── video-004/
        │   │   ├── video-005/
        │   │   ├── video-006/
        │   │   ├── video-007/
        │   │   ├── video-008/
        │   │   ├── video-009/
        │   │   └── video-010/
        │
        ├── analysis/
        │   ├── claims.json
        │   ├── questions.json
        │   ├── argument-structures.json
        │   ├── cross-examinations.json
        │   ├── rebuttals.json
        │   ├── source-handling.json
        │   ├── interfaith-dialogue.json
        │   ├── debate-control.json
        │   ├── logical-analysis.json
        │   └── communication-patterns.json
        │
        ├── patterns/
        │   ├── repeated-patterns.json
        │   ├── contextual-patterns.json
        │   ├── adaptive-patterns.json
        │   ├── signature-patterns.json
        │   ├── anti-patterns.json
        │   └── rejected-patterns.json
        │
        ├── strategies/
        │   ├── strategy-library.json
        │   ├── questioning-strategies.json
        │   ├── cross-examination-strategies.json
        │   ├── rebuttal-strategies.json
        │   └── conversation-control-strategies.json
        │
        ├── persona/
        │   ├── persona.json
        │   ├── persona.md
        │   ├── decision-trees.json
        │   └── simulation-protocol.json
        │
        ├── validation/
        │   ├── unseen-video/
        │   ├── validation-results.json
        │   └── overfitting-report.md
        │
        └── versions/
            ├── v1.0/
            ├── v1.1/
            └── changelog.md

---

72. VIDEO DATA MODEL

Setiap video harus mempunyai record sendiri.

Minimal:

{
  "video_id": "ZUMA-VIDEO-001",
  "url": "",
  "title": "",
  "channel": "",
  "publication_date": "",
  "duration": "",
  "corpus_role": "training",
  "transcript_status": "",
  "speaker_segmentation_status": "",
  "analysis_status": "",
  "processed_at": ""
}

Jangan menyimpan video hanya berdasarkan judul.

Gunakan "video_id" sebagai primary identifier internal.

---

73. TRANSCRIPT DATA MODEL

Transcript harus mempertahankan:

{
  "segment_id": "SEG-00182",
  "video_id": "ZUMA-VIDEO-001",
  "start": "",
  "end": "",
  "speaker": "ZUMA",
  "text": "",
  "speaker_confidence": "high"
}

Timestamp harus dipertahankan jika tersedia.

Jangan menghilangkan timestamp setelah analisis selesai.

Transcript adalah raw evidence layer.

---

74. SPEAKER DATA

Gunakan speaker registry:

{
  "speaker_id": "SPK-ZUMA",
  "label": "ZUMA",
  "identity_confidence": "high"
}

Untuk lawan:

{
  "speaker_id": "SPK-OPP-001",
  "label": "OPPONENT",
  "identity": "",
  "identity_confidence": ""
}

Jika identitas tidak diketahui:

UNKNOWN

Jangan melakukan speaker attribution berdasarkan tebakan semata.

---

75. ZUMA OBSERVATION DATA MODEL

Setiap behavior yang dianggap penting harus menjadi observation terpisah.

Contoh:

{
  "observation_id": "OBS-00182",
  "video_id": "ZUMA-VIDEO-001",
  "segment_id": "SEG-00421",
  "timestamp": "00:42:18",
  "speaker": "ZUMA",
  "utterance_function": "evidence_request",
  "observed_behavior": "asks opponent to identify source for factual claim",
  "context": "",
  "opponent_claim": "",
  "opponent_response": "",
  "strategic_effect": "",
  "technique_candidate": "",
  "confidence": "high",
  "status": "observed"
}

Observation adalah data mentah hasil analisis perilaku.

Jangan langsung mengubah observation menjadi persona.

---

76. TECHNIQUE DATA MODEL

Beberapa observation dapat membentuk technique.

{
  "technique_id": "TECH-0012",
  "name": "Evidence Source Challenge",
  "description": "",
  "observations": [
    "OBS-00182",
    "OBS-00491"
  ],
  "contexts": [],
  "frequency": 0,
  "videos_observed": [],
  "confidence": "medium",
  "status": "candidate"
}

Hubungan:

Observation
   ↓
Technique

---

77. PATTERN DATA MODEL

Technique yang muncul secara konsisten dapat membentuk pattern.

{
  "pattern_id": "PAT-0042",
  "name": "Sequential Evidence Pressure",
  "type": "repeated",
  "description": "",
  "techniques": [
    "TECH-0012"
  ],
  "observations": [
    "OBS-00182",
    "OBS-00491",
    "OBS-00931"
  ],
  "source_videos": [
    "ZUMA-VIDEO-001",
    "ZUMA-VIDEO-004",
    "ZUMA-VIDEO-007"
  ],
  "typical_context": "",
  "strategic_purpose": "",
  "decision_rule": "",
  "confidence": "high",
  "status": "generalized"
}

---

78. STRATEGY DATA MODEL

Pattern yang sudah cukup kuat dapat diabstraksikan menjadi strategy.

{
  "strategy_id": "STRAT-0017",
  "name": "Evidence-First Challenge",
  "trigger": "",
  "preconditions": [],
  "steps": [],
  "expected_opponent_responses": [],
  "adaptive_branches": [],
  "failure_conditions": [],
  "related_patterns": [],
  "source_observations": [],
  "confidence": "high",
  "abstraction_level": "generalized"
}

Strategy harus menjawab:

WHEN?
WHY?
HOW?
WHAT NEXT?
WHAT IF OPPONENT RESPONDS DIFFERENTLY?

---

79. PERSONA DATA MODEL

Persona hanya boleh mengambil pattern dan strategy yang telah melewati evidence threshold.

{
  "persona_id": "ZUMA-PERSONA",
  "version": "1.0",
  "core_patterns": [],
  "adaptive_strategies": [],
  "contextual_strategies": [],
  "signature_patterns": [],
  "anti_patterns": [],
  "communication_characteristics": [],
  "decision_trees": [],
  "confidence": {}
}

Jangan memasukkan observation mentah sebagai core persona.

---

80. TRACEABILITY

Semua hubungan harus dapat ditelusuri dua arah:

PERSONA
 ↓
STRATEGY
 ↓
PATTERN
 ↓
TECHNIQUE
 ↓
OBSERVATION
 ↓
TRANSCRIPT
 ↓
VIDEO

Dan sebaliknya:

VIDEO
 ↓
TRANSCRIPT
 ↓
OBSERVATION
 ↓
TECHNIQUE
 ↓
PATTERN
 ↓
STRATEGY
 ↓
PERSONA

Jika sebuah persona rule tidak dapat ditelusuri kembali ke evidence:

«tandai sebagai "unsupported" atau jangan masukkan.»

---

81. PATTERN STATUS

Setiap pattern harus mempunyai lifecycle.

Gunakan:

candidate
↓
observed
↓
repeated
↓
corroborated
↓
generalized
↓
core

Atau:

candidate
↓
contradicted
↓
contextual

atau:

candidate
↓
rejected

Jangan menghapus history perubahan tanpa alasan.

---

82. PATTERN CLASSIFICATION

Setiap behavior/pattern wajib masuk salah satu:

CORE
ADAPTIVE
CONTEXTUAL
INCIDENTAL
REJECTED

CORE

Konsisten lintas video dan konteks.

ADAPTIVE

Berubah sesuai respons lawan.

CONTEXTUAL

Muncul karena kondisi/topik tertentu.

INCIDENTAL

Kemungkinan besar kebiasaan situasional dan bukan bagian penting persona.

REJECTED

Tidak cukup evidence atau terbukti bukan pola ZUMA yang valid.

---

83. PATTERN PURIFICATION DATA

Jika pattern diturunkan atau dihapus, jangan menghapus observation.

Contoh:

{
  "pattern_id": "PAT-0021",
  "previous_status": "core",
  "new_status": "contextual",
  "reason": "Observed primarily in theological context",
  "evidence": [],
  "changed_in_version": "1.2"
}

Dengan demikian data mentah tetap aman.

---

84. CORPUS INDEX

"corpus-index.json" harus menjadi registry utama.

Minimal:

{
  "corpus_name": "ZUMA Debate Corpus",
  "version": "1.0",
  "video_count": 10,
  "videos": [],
  "last_updated": "",
  "analysis_status": "",
  "pattern_version": ""
}

Ketika corpus berkembang:

10 → 20 → 30 → 50 → 100+

"video_count" dan index diperbarui.

---

85. CORPUS EXPANSION

Ketika video baru ditambahkan:

JANGAN hanya append data baru.

Lakukan:

NEW VIDEO
 ↓
NEW OBSERVATIONS
 ↓
COMPARE EXISTING PATTERNS
 ↓
CONFIRM
MODIFY
MERGE
SPLIT
DOWNGRADE
REJECT
OR CREATE NEW PATTERN
 ↓
REGENERATE PERSONA

Ini merupakan bagian wajib dari pipeline.

---

86. PATTERN CHANGELOG

Setiap perubahan significant pada persona harus dicatat.

Contoh:

{
  "version": "1.2",
  "date": "",
  "corpus_size": 30,
  "changes": [
    {
      "pattern_id": "PAT-0042",
      "change": "strengthened",
      "old_confidence": "medium",
      "new_confidence": "high",
      "reason": "Observed across additional contexts"
    },
    {
      "pattern_id": "PAT-0017",
      "change": "downgraded",
      "old_status": "core",
      "new_status": "contextual",
      "reason": "New contradictory observations"
    }
  ]
}

---

87. DATA IMMUTABILITY RULE

Raw evidence tidak boleh diubah hanya karena persona berubah.

Yang boleh berubah:

Technique interpretation
Pattern classification
Strategy abstraction
Persona weighting
Confidence

Yang harus dipertahankan:

Original transcript
Timestamp
Speaker attribution record
Original observation
Source URL

Jika terjadi koreksi speaker attribution, simpan:

previous value
new value
reason
version

---

88. SEPARATE RESEARCH DATA FROM RUNTIME SKILL

Ini wajib.

Research corpus:

corpus/
analysis/
patterns/
provenance/
validation/

Runtime skill:

persona/
strategies/
simulation-protocol/

Jangan membuat Debate Engine harus membaca seluruh transcript 10, 20, atau 100 video setiap kali melakukan debat.

Runtime hanya menggunakan compiled / distilled skill.

---

89. COMPILED PERSONA

Buat konsep:

RAW CORPUS
     ↓
RESEARCH DATA
     ↓
PATTERN ENGINEERING
     ↓
PERSONA COMPILATION
     ↓
RUNTIME SKILL

Dengan demikian:

100 videos

tidak berarti:

100 videos loaded into every debate

Yang masuk runtime adalah:

«distilled strategic representation.»

---

90. POLYA INTEGRATION BOUNDARY

ZUMA Persona hanya boleh mengontrol:

Question Selection
Question Sequencing
Cross-Examination Strategy
Rebuttal Strategy
Conversation Control
Opponent Modeling
Strategic Pressure
Topic Recovery
Commitment Tracking

Sedangkan:

Facts
Dates
Years
Historical Events
Scripture Text
Source Metadata
Citations
Knowledge

tetap berada pada Polya Knowledge / Evidence Layer.

---

91. RUNTIME INPUT / OUTPUT

Idealnya persona runtime menerima:

{
  "opponent_claim": "",
  "conversation_state": {},
  "known_evidence": {},
  "open_questions": [],
  "opponent_commitments": [],
  "current_topic": "",
  "debate_stage": ""
}

Kemudian menghasilkan:

{
  "selected_strategy": "",
  "reason": "",
  "next_action": "",
  "question": "",
  "evidence_required": [],
  "follow_up_conditions": [],
  "fallback_strategy": ""
}

Persona tidak menentukan fakta secara mandiri.

Ia menentukan strategi.

---

92. QUALITY REQUIREMENT FOR DATA

Data harus:

- deterministic
- machine-readable
- human-auditable
- traceable
- versioned
- extensible
- deduplicated
- internally consistent

Hindari:

- giant JSON monolith
- duplicate observations
- orphaned IDs
- undocumented fields
- unexplained confidence
- unsupported persona rules

---

93. FINAL DATA PIPELINE

Pipeline resmi:

10 LATEST ZUMA VIDEOS
        ↓
CORPUS
        ↓
TRANSCRIPTS
        ↓
SPEAKER ATTRIBUTION
        ↓
ZUMA SPEECH SEGMENTS
        ↓
OBSERVATIONS
        ↓
TECHNIQUES
        ↓
PATTERNS
        ↓
STRATEGIES
        ↓
CORE / ADAPTIVE / CONTEXTUAL / INCIDENTAL
        ↓
PATTERN PURIFICATION
        ↓
ZUMA PERSONA
        ↓
POLYA ENHANCEMENT
        ↓
COMPILED RUNTIME SKILL
        ↓
UNSEEN VIDEO VALIDATION

Ketika corpus bertambah:

NEW VIDEOS
      ↓
REPROCESS PATTERN LAYER
      ↓
REFINE
      ↓
PURIFY
      ↓
VERSION
      ↓
RECOMPILE PERSONA

---

94. FINAL RULE FOR ANTIGRAVITY

Jangan membuat database yang hanya menjawab:

«"Apa yang dikatakan ZUMA?"»

Database harus dapat menjawab:

«"Apa yang dilakukan ZUMA, dalam kondisi apa, dengan teknik apa, untuk tujuan strategis apa, bagaimana lawan merespons, bagaimana ZUMA beradaptasi, seberapa sering pola tersebut muncul, seberapa yakin kita bahwa pola itu benar-benar karakter ZUMA, dan dari video/timestamp mana kesimpulan tersebut berasal?"»

Itulah struktur data yang diperlukan untuk membangun ZUMA Debate Persona sebagai skill AI yang benar-benar dapat dipanggil, diuji, diperbaiki, dan dikembangkan bersama pertumbuhan corpus.
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-09-11T15:59:28+07:00.
</ADDITIONAL_METADATA>