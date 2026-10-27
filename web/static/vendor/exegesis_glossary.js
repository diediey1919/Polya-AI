/**
 * Polya Apologetika — Exegesis Glossary & Interactive Popover Engine
 * Kamus istilah terstruktur untuk orang awam mencakup:
 * 1. Leksikon & Naskah Kuno
 * 2. Morfologi & Kode Parsing
 * 3. Fungsi & Peran Sintaksis
 * 4. Istilah Akademis / Teologis / Filologis
 */

(function () {
  "use strict";

  const GLOSSARY_DATA = {
    // ==========================================
    // DOMAIN 1: LEKSIKON & SAKSI NASKAH
    // ==========================================
    "bdag": {
      title: "BDAG (Bauer-Danker-Arndt-Gingrich)",
      category: "Leksikon Yunani",
      explanation: "Kamus leksikon bahasa Yunani Perjanjian Baru paling berwibawa di dunia akademis saat ini. Memuat definisi kata berdasarkan ribuan dokumen, papirus, dan inskripsi zaman kuno abad pertama Masehi."
    },
    "bdb": {
      title: "BDB (Brown-Driver-Briggs)",
      category: "Leksikon Ibrani",
      explanation: "Kamus rujukan standar internasional untuk bahasa Ibrani dan Aramaik Perjanjian Lama, membedah setiap kata hingga ke akar kata (radix/shoresh) Semit kuno."
    },
    "halot": {
      title: "HALOT (Hebrew & Aramaic Lexicon of the OT)",
      category: "Leksikon Ibrani",
      explanation: "Kamus modern terkemuka untuk bahasa Ibrani Alkitab karya Koehler & Baumgartner yang memutakhirkan riset filologi Semit komparatif abad ke-20."
    },
    "thayer": {
      title: "Thayer's Greek-English Lexicon",
      category: "Leksikon Yunani",
      explanation: "Kamus Yunani Perjanjian Baru klasik karya Joseph Henry Thayer yang memetakan makna kata dan penggunaannya dalam sastra Alkitab dan sekuler Yunani kuno."
    },
    "lsj": {
      title: "LSJ (Liddell-Scott-Jones)",
      category: "Leksikon Yunani Klasik",
      explanation: "Kamus bahasa Yunani paling komprehensif di dunia yang mencakup literatur Yunani kuno dari masa Homeros hingga zaman Helenistik dan Bizantium."
    },
    "gesenius": {
      title: "Gesenius' Hebrew Grammar & Lexicon",
      category: "Leksikon Ibrani",
      explanation: "Karya monumental Wilhelm Gesenius yang menjadi tonggak utama tata bahasa dan leksikografi Ibrani Alkitabiah ilmiah modern."
    },
    "na28": {
      title: "NA28 (Nestle-Aland edisi ke-28)",
      category: "Naskah Kritis",
      explanation: "Edisi kritis teks bahasa Yunani Perjanjian Baru yang menjadi standar riset akademik global, disusun dari konsensus ribuan saksi naskah kuno tertua."
    },
    "ubs5": {
      title: "UBS5 (United Bible Societies edisi ke-5)",
      category: "Naskah Kritis",
      explanation: "Naskah kritis teks Yunani yang diterbitkan oleh Lembaga Alkitab Bersatu, identik teksnya dengan NA28 namun difokuskan untuk penerjemahan Alkitab dunia."
    },
    "lxx": {
      title: "Septuaginta (LXX)",
      category: "Naskah Kuno",
      explanation: "Terjemahan kitab suci Ibrani (Perjanjian Lama) ke dalam bahasa Yunani Koine yang dibuat oleh para sarjana Yahudi di Aleksandria sekitar abad ke-3 hingga ke-2 Sebelum Masehi. Sering dikutip oleh para penulis Perjanjian Baru."
    },
    "septuaginta": {
      title: "Septuaginta (LXX)",
      category: "Naskah Kuno",
      explanation: "Terjemahan kitab suci Ibrani (Perjanjian Lama) ke dalam bahasa Yunani Koine pada abad ke-3 SM. Merupakan saksi teks tertua sebelum penemuan Naskah Laut Mati."
    },
    "dead sea scrolls": {
      title: "Dead Sea Scrolls (Naskah Laut Mati)",
      category: "Naskah Kuno",
      explanation: "Kumpulan gulungan naskah Ibrani dan Aramaik kuno yang ditemukan di gua-gua Qumran (berasal dari abad ke-3 SM hingga abad ke-1 M), membuktikan keaslian dan stabilitas teks Alkitab Ibrani ribuan tahun lalu."
    },
    "dss": {
      title: "DSS (Dead Sea Scrolls)",
      category: "Naskah Kuno",
      explanation: "Gulungan naskah kuno yang ditemukan di Qumran (abad ke-3 SM - abad ke-1 M). Menjadi saksi naskah Ibrani paling tua yang pernah ditemukan manusia."
    },
    "codex sinaiticus": {
      title: "Codex Sinaiticus (א 01)",
      category: "Manuskrip Kuno",
      explanation: "Naskah Alkitab lengkap tertua di dunia yang ditulis tangan pada lembaran kulit binatang (vellum) sekitar pertengahan abad ke-4 Masehi dengan huruf Yunani besar (uncial)."
    },
    "codex vaticanus": {
      title: "Codex Vaticanus (B 03)",
      category: "Manuskrip Kuno",
      explanation: "Salah satu naskah Alkitab berbahasa Yunani tertua dan paling murni (sekitar 325-350 M), tersimpan di Perpustakaan Vatikan dan menjadi rujukan utama naskah kritis modern."
    },
    "codex leningradensis": {
      title: "Codex Leningradensis (B19a)",
      category: "Manuskrip Kuno",
      explanation: "Manuskrip lengkap tertua dari Teks Masoretik Alkitab Ibrani (Perjanjian Lama) bertanggal tahun 1008 M, yang menjadi dasar utama seluruh Alkitab Ibrani cetak modern (BHS)."
    },
    "papirus": {
      title: "Naskah Papirus (P)",
      category: "Saksi Manuskrip",
      explanation: "Naskah tulisan tangan tertua pada lembaran tanaman papirus (berasal dari abad ke-2 hingga ke-4 Masehi), seperti P46, P66, dan P75, yang mendahului kodeks kulit besar."
    },
    "p46": {
      title: "Papirus 46 (P46 / Chester Beatty II)",
      category: "Manuskrip Kuno",
      explanation: "Naskah papirus tertua yang memuat surat-surat Paulus (bertanggal sekitar tahun 200 Masehi), membuktikan pembacaan teks Yunani sebelum era konsili gereja."
    },
    "p66": {
      title: "Papirus 66 (P66 / Bodmer II)",
      category: "Manuskrip Kuno",
      explanation: "Naskah papirus bertanggal sekitar tahun 200 M yang memuat hampir seluruh kitab Yohanes dalam kondisi sangat terpelihara."
    },
    "p75": {
      title: "Papirus 75 (P75 / Bodmer XIV-XV)",
      category: "Manuskrip Kuno",
      explanation: "Naskah papirus awal abad ke-3 M (ca. 175-225 M) yang memuat bagian besar kitab Lukas dan Yohanes, bersesuaian sangat tinggi dengan Codex Vaticanus."
    },
    "p72": {
      title: "Papirus 72 (P72 / Bodmer VII-VIII)",
      category: "Manuskrip Kuno",
      explanation: "Naskah papirus kuno abad ke-3/4 Masehi; merupakan saksi naskah tertua di dunia yang memuat teks lengkap Surat 1 dan 2 Petrus serta Surat Yudas."
    },
    "papirus 72": {
      title: "Papirus 72 (P72 / Bodmer VII-VIII)",
      category: "Manuskrip Kuno",
      explanation: "Naskah papirus kuno abad ke-3/4 Masehi; saksi naskah tertua di dunia untuk Surat 1 dan 2 Petrus serta Surat Yudas."
    },

    // ==========================================
    // DOMAIN 2: MORFOLOGI & TATA BAHASA
    // ==========================================
    "nominative": {
      title: "Kasus Nominatif (Nominative)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata benda/ganti yang berfungsi sebagai pokok atau subjek utama kalimat yang melakukan perbuatan, atau sebagai predikat penjelas subjek (predikat nominatif)."
    },
    "genitive": {
      title: "Kasus Genitif (Genitive)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata yang menunjukkan kepemilikan ('milik siapa'), asal-usul, hubungan keluarga, atau pembatasan makna suatu kata benda lain (seperti 'dari' atau 'kepunyaan')."
    },
    "dative": {
      title: "Kasus Datif (Dative)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata yang berfungsi sebagai objek tidak langsung (kepada siapa perbuatan ditujukan), penerima manfaat, atau penunjuk alat/waktu/lokasi."
    },
    "accusative": {
      title: "Kasus Akusatif (Accusative)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata yang berfungsi sebagai objek penderita langsung yang menerima dampak aksi dari kata kerja, atau penunjuk arah dan batas pergerakan."
    },
    "vocative": {
      title: "Kasus Vokatif (Vocative)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata yang dipakai khusus ketika menyapa, memanggil, atau berseru secara langsung kepada seseorang (misal: 'Ya Tuhan!', 'Bapa!')."
    },
    "aorist": {
      title: "Aspek Aorist (Aorist Tense)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata kerja Yunani yang memandang suatu tindakan sebagai satu keutuhan peristiwa (snapshot/titik peristiwa), biasanya terjadi di masa lampau tanpa memandang durasi panjangnya."
    },
    "imperfect": {
      title: "Aspek Imperfek (Imperfect Tense)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata kerja masa lampau yang menekankan tindakan yang sedang berlangsung terus-menerus, berulang-ulang, atau suatu kebiasaan di masa lalu."
    },
    "perfect": {
      title: "Kala Perfek (Perfect Tense)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata kerja yang menyatakan perbuatan yang sudah selesai tuntas di masa lampau, namun dampak, hasil, atau akibatnya masih tetap bertahan terus hingga saat ini."
    },
    "present indicative active": {
      title: "Present Indicative Active (Kini Nyata Aktif)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata kerja yang menyatakan fakta nyata masa sekarang (indicative) di mana subjek sendiri yang aktif melakukan perbuatan secara berkesinambungan."
    },
    "subjunctive": {
      title: "Modus Subjungtif (Subjunctive)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Modus kata kerja yang menyatakan kemungkinan, potensi, harapan, tujuan, atau ketidakpastian (misal: 'supaya...', 'jikalau...')."
    },
    "indicative": {
      title: "Modus Indikatif (Indicative)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Modus kata kerja yang menyatakan kepastian fakta objektif dan peristiwa nyata dalam kenyataan, bukan sekadar angan-angan atau kemungkinan."
    },
    "imperative": {
      title: "Modus Imperatif (Imperative)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata kerja perintah, desakan, petunjuk, atau permohonan sungguh-sungguh dari pembicara kepada pendengar."
    },
    "infinitive": {
      title: "Kata Kerja Infinitif (Infinitive)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk dasar kata kerja yang tidak terikat orang atau jumlah, sering berfungsi seperti kata benda (misal: 'untuk menggenapi', 'untuk datang')."
    },
    "participle": {
      title: "Partisip (Participle / Verba Adjektival)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk kata kerja yang berfungsi ganda seperti kata sifat atau kata keterangan waktu/keadaan (misal: 'sambil berkata', 'orang yang berbuat')."
    },
    "active voice": {
      title: "Bentuk Aktif (Active Voice)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Subjek kalimat bertindak sendiri sebagai pelaku perbuatan terhadap orang lain atau objek."
    },
    "passive voice": {
      title: "Bentuk Pasif (Passive Voice)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Subjek kalimat menerima perbuatan atau dikenai tindakan oleh pihak lain (misal: 'ditegakkan', 'dihukum')."
    },
    "middle voice": {
      title: "Bentuk Medial (Middle Voice)",
      category: "Tata Bahasa / Morfologi",
      explanation: "Bentuk khas bahasa Yunani di mana subjek melakukan perbuatan untuk kepentingan dirinya sendiri atau melibatkan dirinya secara mendalam."
    },

    // ==========================================
    // DOMAIN 3: FUNGSI & PERAN SINTAKSIS
    // ==========================================
    "subjek gramatikal": {
      title: "Subjek Gramatikal",
      category: "Peran Sintaksis",
      explanation: "Pihak, orang, atau konsep utama yang menjadi pokok pembicaraan dalam kalimat dan yang mengontrol kesesuaian kata kerja (predikat)."
    },
    "predikat verbal": {
      title: "Predikat Verbal",
      category: "Peran Sintaksis",
      explanation: "Kata kerja utama yang menerangkan tindakan, perbuatan, atau peristiwa yang dilakukan atau dialami oleh subjek."
    },
    "predikat nominatif": {
      title: "Predikat Nominatif (Predicate Nominative)",
      category: "Peran Sintaksis",
      explanation: "Kata benda yang terletak di belakang kata kerja penghubung (seperti 'adalah') untuk menerangkan hakikat, gelar, atau sifat dari subjek kalimat."
    },
    "objek akusatif langsung": {
      title: "Objek Akusatif Langsung",
      category: "Peran Sintaksis",
      explanation: "Objek utama yang langsung menerima atau menderita tindakan dari kata kerja (misal: 'menegakkan *hukum*', di mana 'hukum' adalah objek akusatif langsung)."
    },
    "objek tidak langsung (dative)": {
      title: "Objek Tidak Langsung (Datif)",
      category: "Peran Sintaksis",
      explanation: "Pihak yang menerima manfaat, sasaran akhir pemberian, atau kepada siapa suatu pesan disampaikan."
    },
    "objek genitif partitif": {
      title: "Objek Genitif Partitif",
      category: "Peran Sintaksis",
      explanation: "Kata benda kasus kepemilikan yang menunjukkan bagian dari suatu kelompok utuh yang lebih besar (misal: 'sebagian dari kami')."
    },
    "konjungsi koordinatif": {
      title: "Konjungsi Koordinatif",
      category: "Peran Sintaksis",
      explanation: "Kata sambung setara (seperti 'dan', 'tetapi', 'atau') yang menghubungkan dua kata, frasa, atau klausa yang berderajat sama tanpa subordinasi."
    },
    "konjungsi inferensial": {
      title: "Konjungsi Inferensial / Konsekuensi",
      category: "Peran Sintaksis",
      explanation: "Kata sambung penarik kesimpulan logis (seperti 'oleh karena itu', 'jadi', 'maka') yang menghubungkan premis sebelumnya dengan konsekuensi logis berikutnya."
    },
    "atributif modifikator": {
      title: "Atributif Modifikator",
      category: "Peran Sintaksis",
      explanation: "Kata sifat atau frasa penjelas yang menempel langsung pada kata benda untuk membatasi atau memperjelas ciri khas benda tersebut."
    },
    "preposisi relasional": {
      title: "Preposisi Relasional",
      category: "Peran Sintaksis",
      explanation: "Kata depan (seperti 'melalui', 'di dalam', 'bersama-sama') yang mengatur hubungan posisi, ruang, sarana, atau relasi antar-kata dalam kalimat."
    },
    "fronting / topicalization": {
      title: "Fronting / Penempatan Awal Emfatis",
      category: "Peran Sintaksis",
      explanation: "Teknik gaya bahasa kuno di mana suatu kata ditarik sengaja ke posisi paling depan kalimat untuk memberi tekanan penegasan khusus bahwa kata itu adalah topik paling utama."
    },

    // ==========================================
    // DOMAIN 4: ISTILAH AKADEMIS, FILOLOGIS & TEOLOGIS
    // ==========================================
    "eksegesis": {
      title: "Eksegesis (Exegesis)",
      category: "Metode Ilmiah",
      explanation: "Proses ilmiah membedah dan menggali arti asli yang dimaksud oleh sang penulis naskah kuno berdasarkan bahasa aslinya, konteks sejarah, tata bahasa, dan budayanya, tanpa memaksakan opini pribadi."
    },
    "eisegesis": {
      title: "Eisegesis",
      category: "Metode Keliru",
      explanation: "Kebalikan dari eksegesis; yaitu memaksakan asumsi pribadi, doktrin kelompok, atau opini modern ke dalam teks kuno sehingga arti asli ayat menjadi terdistorsi."
    },
    "semantik": {
      title: "Semantik (Semantic)",
      category: "Ilmu Linguistik",
      explanation: "Cabang ilmu bahasa yang mempelajari makna kata, asal-usul arti, dan perubahan cakupan makna suatu kata seiring berjalannya zaman."
    },
    "sintaksis": {
      title: "Sintaksis (Syntax)",
      category: "Ilmu Linguistik",
      explanation: "Aturan susunan dan hubungan antar-kata dalam kalimat. Sintaksis menentukan siapa yang menjadi pelaku, siapa yang menjadi korban, dan apa hubungan logis antar-klausa."
    },
    "filologi": {
      title: "Filologi Forensik",
      category: "Metode Ilmiah",
      explanation: "Ilmu penyelidikan naskah-naskah kuno bersejarah melalui analisis teliti terhadap bahasa, gaya tulisan, variasi salinan tangan, dan keotentikan dokumen masa lampau."
    },
    "hermeneutika": {
      title: "Hermeneutika (Hermeneutics)",
      category: "Prinsip Penafsiran",
      explanation: "Kaidah, teori, dan metode penafsiran teks secara benar untuk menjembatani jurang pemahaman antara konteks zaman kuno dengan pembaca masa kini."
    },
    "sitz im leben": {
      title: "Sitz im Leben (Konteks Kehidupan)",
      category: "Kritik Historis",
      explanation: "Istilah bahasa Jerman yang berarti 'situasi nyata dalam kehidupan', merujuk pada latar belakang sosial, politik, agama, dan budaya tempat teks tersebut pertama kali dilahirkan."
    },
    "aparat kritik": {
      title: "Aparatus Kritik Tekstual",
      category: "Kritik Teks",
      explanation: "Catatan kaki ilmiah di bawah naskah kritis asli yang mencatat secara terperinci setiap variasi kata atau bacaan alternatif yang ditemukan di antara ribuan manuskrip kuno."
    },
    "varian tekstual": {
      title: "Varian Tekstual (Textual Variant)",
      category: "Kritik Teks",
      explanation: "Perbedaan tulisan, ejaan, atau susunan kata yang muncul di antara satu salinan naskah kuno dengan salinan naskah kuno lainnya akibat kesalahan juru tulis atau penambahan redaksional."
    },
    "anarthrous": {
      title: "Anarthrous (Tanpa Artikel Definit)",
      category: "Sintaksis Yunani",
      explanation: "Kata benda Yunani yang ditulis tanpa kata sandang ('the' / 'sang'). Biasanya kata tanpa artikel ini menunjukkan sifat, karakter, atau kualitas esensi, bukan menunjuk satu pribadi identitas mutlak."
    },
    "articular": {
      title: "Articular (Memakai Artikel Definit)",
      category: "Sintaksis Yunani",
      explanation: "Kata benda yang disertai kata sandang definit (seperti 'ho', 'ton'). Digunakan untuk menunjuk sosok, oknum, atau benda tertentu secara spesifik dan terdefinisikan jelas."
    },
    "colwell-harner": {
      title: "Kaidah Colwell-Harner",
      category: "Kaidah Gramatika Yunani",
      explanation: "Kaidah gramatika yang dirumuskan oleh sarjana E.C. Colwell dan Philip Harner, membuktikan bahwa predikat kata benda tanpa artikel yang mendahului kata kerja lebih condong menyatakan 'kualitas/sifat' daripada menunjuk identitas mutlak (equative)."
    },
    "ilzam al-khasm": {
      title: "Ilzam al-Khasm (إلزام الخصم)",
      category: "Metode Dialektika",
      explanation: "Metode debat klasik yang mematahkan argumen lawan dengan menggunakan dalil, kaidah bahasa, dan premis kitab suci yang diakui oleh pihak lawan itu sendiri, sehingga mereka terikat oleh prinsip mereka sendiri."
    },
    "apodictic proof": {
      title: "Bukti Apodiktis (Apodictic Proof)",
      category: "Logika Forensik",
      explanation: "Bukti yang memiliki tingkat kepastian mutlak, jelas dengan sendirinya, dan tidak dapat dibantah secara logis maupun secara gramatikal teks primer."
    },
    "empiris": {
      title: "Bukti Empiris",
      category: "Epistemologi",
      explanation: "Bukti nyata yang dapat diamati, diperiksa fisiknya, dan diverifikasi langsung pada artefak bersejarah nyata (seperti naskah kulit, papirus, dan tinta kuno)."
    },
    "pneuma": {
      title: "Pneuma (πνεῦμα)",
      category: "Istilah Alkitabiah",
      explanation: "Kata Yunani yang arti aslinya adalah 'napas', 'hembusan angin', atau 'roh/daya hidup', yang dalam konteks Alkitab dipakai untuk menggambarkan hembusan ilahi, pikiran, atau wujud spiritual."
    },
    "logos": {
      title: "Logos (λόγος)",
      category: "Istilah Alkitabiah",
      explanation: "Kata Yunani yang bermakna ucapan, firman, titah perintah Tuhan, cetak biru pikiran hikmat, atau pesan deklaratif Allah yang dinyatakan kepada ciptaan-Nya."
    },
    "theos": {
      title: "Theos (θεός)",
      category: "Istilah Alkitabiah",
      explanation: "Kata Yunani asli dalam naskah Alkitab untuk menyebut oknum ilahi atau sesembahan. Dalam eksegesis apologetika forensik, istilah ini secara sengaja dipertahankan sebagai 'Theos' (bukan diterjemahkan sebagai 'Allah') guna menjaga keaslian teks Yunani kuno, mencegah anakronisme terminologi modern, serta memperjelas distingsi gramatikal antara 'ton Theon' (berartikel definit/Pribadi Tertinggi) dan 'theos' (tanpa artikel/hakikat kualitatif ilahi)."
    },
    "kenosis": {
      title: "Kenosis (κένωσις)",
      category: "Konsep Teologis",
      explanation: "Dari kata kerja Yunani 'ekenōsen' (mengosongkan diri) dalam Filipi 2:7, merujuk pada sikap menundukkan diri dan melepaskan hak kemuliaan untuk menjadi seorang hamba yang taat."
    },
    "monoteisme": {
      title: "Monoteisme Murni (Tauhid)",
      category: "Konsep Keagamaan",
      explanation: "Keyakinan mutlak bahwa Tuhan itu Maha Esa dalam esensi, pribadi, sifat, dan ketetapan, tanpa ada persekutuan, bagian, atau pembagian wujud dengan siapa pun."
    },
    "interpolasi": {
      title: "Interpolasi (Sisipan Naskah)",
      category: "Kritik Teks",
      explanation: "Penambahan kata, kalimat, atau perikop baru ke dalam naskah Alkitab oleh juru tulis di abad-abad kemudian yang terbukti tidak ada dalam manuskrip-manuskrip tertua."
    },
    "sola fide": {
      title: "Sola Fide (Hanya Oleh Iman)",
      category: "Konsep Historis",
      explanation: "Prinsip teologis yang menegaskan pembenaran status manusia di hadapan Tuhan melalui iman yang hidup, bukan karena klaim ritual atau perbuatan semata."
    }
  };

  /**
   * Helper parsing kode tag morfologi standar BibleHub
   * Contoh: V-AAI-3P -> Verb - Aorist Active Indicative - 3rd Person Plural
   * N-AMS -> Noun - Accusative Masculine Singular
   */
  function parseMorphCode(code) {
    if (!code || typeof code !== "string") return null;
    const clean = code.trim().toUpperCase();

    // Map parts
    const posMap = {
      "V": "Kata Kerja (Verb)",
      "N": "Kata Benda (Noun)",
      "A": "Kata Sifat (Adjective)",
      "P": "Kata Ganti (Pronoun)",
      "PREP": "Kata Depan (Preposition)",
      "CONJ": "Kata Sambung (Conjunction)",
      "ART": "Kata Sandang (Article)",
      "ADV": "Kata Keterangan (Adverb)",
      "INT": "Kata Seru (Interjection)",
      "PRT": "Partikel (Particle)"
    };

    const tenseMap = {
      "P": "Present (Kini)",
      "I": "Imperfect (Masa Lampau Berkelanjutan)",
      "A": "Aorist (Masa Lampau Tuntas)",
      "F": "Future (Masa Depan)",
      "X": "Perfect (Selesai Berdampak)",
      "Y": "Pluperfect"
    };

    const voiceMap = {
      "A": "Active (Aktif)",
      "M": "Middle (Medial)",
      "P": "Passive (Pasif)",
      "E": "Middle/Passive"
    };

    const moodMap = {
      "I": "Indicative (Fakta Nyata)",
      "S": "Subjunctive (Potensial/Harapan)",
      "O": "Optative (Doa/Keinginan)",
      "M": "Imperative (Perintah)",
      "N": "Infinitive (Bentuk Dasar)",
      "P": "Participle (Bentuk Berkesinambungan)"
    };

    const caseMap = {
      "N": "Nominative (Subjek)",
      "G": "Genitive (Kepemilikan/Asal)",
      "D": "Dative (Objek Tak Langsung)",
      "A": "Accusative (Objek Langsung)",
      "V": "Vocative (Seruan/Panggilan)"
    };

    const genderMap = {
      "M": "Masculine (Laki-laki)",
      "F": "Feminine (Perempuan)",
      "N": "Neuter (Netral)"
    };

    const numberMap = {
      "S": "Singular (Tunggal)",
      "P": "Plural (Jamak)",
      "D": "Dual (Ganda)"
    };

    const personMap = {
      "1": "Orang Pertama (Saya/Kami)",
      "2": "Orang Kedua (Kamu/Kalian)",
      "3": "Orang Ketiga (Dia/Mereka)"
    };

    const parts = clean.split("-");
    if (parts.length >= 2) {
      const pos = posMap[parts[0]] || parts[0];
      const descList = [];

      if (parts[0] === "V" && parts[1] && parts[1].length >= 3) {
        // e.g. AAI -> Aorist Active Indicative
        const t = tenseMap[parts[1][0]] || parts[1][0];
        const v = voiceMap[parts[1][1]] || parts[1][1];
        const m = moodMap[parts[1][2]] || parts[1][2];
        descList.push(t, v, m);

        if (parts[2]) {
          const pers = personMap[parts[2][0]];
          const num = numberMap[parts[2][1]];
          if (pers) descList.push(pers);
          if (num) descList.push(num);
        }
      } else if (parts[1] && parts[1].length >= 3) {
        // e.g. AMS -> Accusative Masculine Singular
        const c = caseMap[parts[1][0]] || parts[1][0];
        const g = genderMap[parts[1][1]] || parts[1][1];
        const n = numberMap[parts[1][2]] || parts[1][2];
        descList.push(c, g, n);
      }

      return {
        title: `Kode Parsing Morfologi: ${clean}`,
        category: "Morfologi Standar BibleHub",
        explanation: `Tag ini menguraikan struktur gramatika kata secara objektif:\n• Golongan: ${pos}\n• Rincian: ${descList.join(" | ") || clean}`
      };
    }

    return null;
  }

  /**
   * Mengambil definisi istilah dari kamus atau mendeteksi pola kode Strong / parsing
   */
  function lookupTerm(rawTerm, type) {
    if (!rawTerm) return null;
    const termClean = String(rawTerm).trim();
    const termKey = termClean.toLowerCase();

    // 1. Direct dictionary match
    if (GLOSSARY_DATA[termKey]) {
      return GLOSSARY_DATA[termKey];
    }

    // 2. Check Strong's number pattern: G1234 or H1234
    const strongMatch = termClean.match(/^([GH])(\d+)$/i);
    if (strongMatch) {
      const lang = strongMatch[1].toUpperCase() === "G" ? "Yunani (Greek)" : "Ibrani/Aramaik (Hebrew)";
      const num = strongMatch[2];
      return {
        title: `Kode Konkordansi Strong: ${termClean.toUpperCase()}`,
        category: `Indeks Leksikon ${lang}`,
        explanation: `Nomor indeks acuan universal James Strong (#${num}) yang memetakan akar kata asli bahasa ${lang}. Memungkinkan pembaca menelusuri setiap ayat di Bible di mana kata asli ini muncul tanpa harus menguasai aksara kuno.`
      };
    }

    // 3. Check Morphology code pattern
    const morphParsed = parseMorphCode(termClean);
    if (morphParsed) {
      return morphParsed;
    }

    // 4. Fuzzy fallback matching for multi-word or compound terms
    for (const key in GLOSSARY_DATA) {
      if (termKey.includes(key) || key.includes(termKey)) {
        return GLOSSARY_DATA[key];
      }
    }

    return {
      title: termClean,
      category: type || "Istilah Teknis",
      explanation: `Istilah teknis dalam eksegesis Alkitab dan studi manuskrip primer BibleHub.`
    };
  }

  /**
   * Highlight istilah kamus dalam teks bebas secara aman tanpa merusak atribut tag HTML
   */
  function highlightGlossaryTerms(htmlText) {
    if (!htmlText || typeof htmlText !== "string") return htmlText;

    // Kumpulkan seluruh kata kunci kamus dan urutkan dari yang terpanjang ke terpendek (longest-match-first)
    const sortedKeys = Object.keys(GLOSSARY_DATA).sort((a, b) => b.length - a.length);
    if (sortedKeys.length === 0) return htmlText;

    // Filter istilah pendek (< 3 huruf) agar tidak menimbulkan over-matching yang mengganggu
    const qualifiedKeys = sortedKeys.filter(k => k.length >= 3 && k !== "dan" && k !== "itu");
    const patternStr = qualifiedKeys.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|");

    // Regex dengan boundary dan negative lookahead agar TIDAK mengubah teks di dalam tag HTML <... >
    const regex = new RegExp(`\\b(${patternStr})\\b(?![^<]*>)`, "gi");

    return htmlText.replace(regex, function (match) {
      const safeTerm = match.replace(/"/g, "&quot;");
      return `<span class="glossary-term" data-term="${safeTerm}" tabindex="0" title="Klik untuk penjelasan">${match}</span>`;
    });
  }

  // ==========================================
  // UI FLOATING BOX / POPOVER ENGINE (ADAPTIVE DUA-MODE)
  // ==========================================
  let popoverEl = null;
  let backdropEl = null;

  function ensureUIElements() {
    if (!popoverEl) {
      popoverEl = document.createElement("div");
      popoverEl.id = "exegesis-glossary-popover";
      popoverEl.className = "glossary-popover-panel";
      document.body.appendChild(popoverEl);
    }
    if (!backdropEl) {
      backdropEl = document.createElement("div");
      backdropEl.id = "exegesis-glossary-backdrop";
      backdropEl.className = "glossary-popover-backdrop";
      backdropEl.onclick = closePopover;
      document.body.appendChild(backdropEl);
    }
  }

  function closePopover() {
    if (popoverEl) {
      popoverEl.classList.remove("active");
      popoverEl.style.display = "none";
    }
    if (backdropEl) {
      backdropEl.classList.remove("active");
      backdropEl.style.display = "none";
    }
  }

  function showPopover(termData, triggerRect) {
    ensureUIElements();

    const isMobile = window.innerWidth < 640;
    const { title, category, explanation } = termData;

    popoverEl.innerHTML = `
      <div class="glossary-popover-header">
        <div>
          <span class="glossary-popover-badge">${escapeHtml(category || "Glosarium")}</span>
          <h4 class="glossary-popover-title">${escapeHtml(title || "Penjelasan")}</h4>
        </div>
        <button class="glossary-popover-close" onclick="window.ExegesisGlossary.close()" aria-label="Tutup">✕</button>
      </div>
      <div class="glossary-popover-body">
        <p>${escapeHtml(explanation).replace(/\n/g, "<br/>")}</p>
      </div>
      <div class="glossary-popover-footer">
        <span style="font-size: 0.7rem; color: var(--text-dim); font-family: var(--font-mono);">Polya Apologetika • Kamus Edukasi Awam</span>
      </div>
    `;

    if (isMobile) {
      // Mobile Mode: Bottom Sheet
      popoverEl.className = "glossary-popover-panel bottom-sheet active";
      popoverEl.style.top = "";
      popoverEl.style.left = "0";
      popoverEl.style.right = "0";
      popoverEl.style.bottom = "0";
      popoverEl.style.display = "block";

      backdropEl.className = "glossary-popover-backdrop active";
      backdropEl.style.display = "block";
    } else {
      // Desktop Mode: Smart Floating Popover with Collision Detection
      popoverEl.className = "glossary-popover-panel floating-desktop active";
      popoverEl.style.display = "block";
      backdropEl.style.display = "none";

      const popWidth = 340;
      const margin = 12;
      let left = triggerRect.left;
      let top = triggerRect.bottom + 8;

      // Check right viewport boundary
      if (left + popWidth > window.innerWidth - margin) {
        left = window.innerWidth - popWidth - margin;
      }
      if (left < margin) left = margin;

      // Check bottom viewport boundary
      const estimatedHeight = 180;
      if (top + estimatedHeight > window.innerHeight - margin) {
        top = Math.max(margin, triggerRect.top - estimatedHeight - 8);
      }

      popoverEl.style.position = "fixed";
      popoverEl.style.left = `${Math.round(left)}px`;
      popoverEl.style.top = `${Math.round(top)}px`;
      popoverEl.style.right = "auto";
      popoverEl.style.bottom = "auto";
      popoverEl.style.width = `${popWidth}px`;
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Delegated click handler
  document.addEventListener("click", function (e) {
    const trigger = e.target.closest("[data-term], .glossary-term, .clickable-badge");
    if (trigger) {
      e.stopPropagation();
      const rawTerm = trigger.getAttribute("data-term") || trigger.textContent.trim();
      const type = trigger.getAttribute("data-type") || "";
      const termData = lookupTerm(rawTerm, type);
      if (termData) {
        const rect = trigger.getBoundingClientRect();
        showPopover(termData, rect);
      }
      return;
    }

    // Dismiss when clicking outside on desktop
    if (popoverEl && popoverEl.classList.contains("active")) {
      if (!e.target.closest("#exegesis-glossary-popover")) {
        closePopover();
      }
    }
  });

  // ESC key dismissal
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      closePopover();
    }
  });

  // Export to global window object
  window.ExegesisGlossary = {
    data: GLOSSARY_DATA,
    lookup: lookupTerm,
    highlight: highlightGlossaryTerms,
    show: showPopover,
    close: closePopover
  };
})();
