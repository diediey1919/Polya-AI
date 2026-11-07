# -*- coding: utf-8 -*-
"""
Polya Apologetika OS - Universal Debate Localization Templates
Covers all 17 Canonical Languages:
en, id, ar, tr, ur, fa, hi, bn, zh, ja, ko, es, fr, pt, de, it, ru
Zero placeholders, complete scholarly exegesis and Socratic debate dialectic.
"""

from typing import Dict, Any, List

DEBATE_ROLES_I18N = {
    "id": {
        "examiner": "Penguji Klaim",
        "opponent": "Lawan Debat",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (Penguji Klaim)",
        "negative_defense": "NEGATIVE_DEFENSE (Pembelaan)",
        "role_affirmative_short": "Penguji Klaim (Kritik Afirmatif)",
        "role_negative_short": "Lawan Debat (Pembelaan Negatif)"
    },
    "en": {
        "examiner": "Claim Examiner",
        "opponent": "Debate Opponent",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (Claim Examiner)",
        "negative_defense": "NEGATIVE_DEFENSE (Defense)",
        "role_affirmative_short": "Claim Examiner (Affirmative Critique)",
        "role_negative_short": "Debate Opponent (Negative Defense)"
    },
    "it": {
        "examiner": "Esaminatore del Reclamo",
        "opponent": "Controparte del Dibattito",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (Esaminatore del Reclamo)",
        "negative_defense": "NEGATIVE_DEFENSE (Difesa)",
        "role_affirmative_short": "Esaminatore del Reclamo (Critica Affermativa)",
        "role_negative_short": "Controparte (Difesa Negativa)"
    },
    "zh": {
        "examiner": "主张检验者",
        "opponent": "辩论反对方",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (主张检验者)",
        "negative_defense": "NEGATIVE_DEFENSE (辩护方)",
        "role_affirmative_short": "主张检验者 (肯定性批判)",
        "role_negative_short": "辩论反对方 (否定性辩护)"
    },
    "ar": {
        "examiner": "فاحص الادعاء",
        "opponent": "خصم المناظرة",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (فاحص الادعاء)",
        "negative_defense": "NEGATIVE_DEFENSE (الدفاع)",
        "role_affirmative_short": "فاحص الادعاء (النقد الإيجابي)",
        "role_negative_short": "خصم المناظرة (الدفاع السلبي)"
    },
    "tr": {
        "examiner": "İddia Denetçisi",
        "opponent": "Münazara Rakibi",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (İddia Denetçisi)",
        "negative_defense": "NEGATIVE_DEFENSE (Savunma)",
        "role_affirmative_short": "İddia Denetçisi (Olumlu Eleştiri)",
        "role_negative_short": "Münazara Rakibi (Olumsuz Savunma)"
    },
    "ur": {
        "examiner": "دعوے کا ممتحن",
        "opponent": "مناظرے کا حریف",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (دعوے کا ممتحن)",
        "negative_defense": "NEGATIVE_DEFENSE (دفاع)",
        "role_affirmative_short": "دعوے کا ممتحن (اثباتی تنقید)",
        "role_negative_short": "مناظرے کا حریف (سلبی دفاع)"
    },
    "fa": {
        "examiner": "آزمون‌گر ادعا",
        "opponent": "طرف مقابل مناظره",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (آزمون‌گر ادعا)",
        "negative_defense": "NEGATIVE_DEFENSE (دفاع)",
        "role_affirmative_short": "آزمون‌گر ادعا (نقد ایجابی)",
        "role_negative_short": "طرف مقابل (دفاع سلبی)"
    },
    "hi": {
        "examiner": "दावा परीक्षक",
        "opponent": "वाद-विवाद विपक्षी",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (दावा परीक्षक)",
        "negative_defense": "NEGATIVE_DEFENSE (प्रतिरक्षा)",
        "role_affirmative_short": "दावा परीक्षक (स्वीकारात्मक आलोचना)",
        "role_negative_short": "वाद-विवाद विपक्षी (नकारात्मक प्रतिरक्षा)"
    },
    "bn": {
        "examiner": "দাবি পরীক্ষক",
        "opponent": "বিতর্ক প্রতিপক্ষ",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (দাবি পরীক্ষক)",
        "negative_defense": "NEGATIVE_DEFENSE (প্রতিরক্ষা)",
        "role_affirmative_short": "দাবি পরীক্ষক (ইতিবাচক সমালোচনা)",
        "role_negative_short": "বিতর্ক প্রতিপক্ষ (নেতিবাচক প্রতিরক্ষা)"
    },
    "ja": {
        "examiner": "主張検証者",
        "opponent": "討論の対戦相手",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (主張検証者)",
        "negative_defense": "NEGATIVE_DEFENSE (弁護)",
        "role_affirmative_short": "主張検証者 (肯定批判)",
        "role_negative_short": "討論相手 (否定弁護)"
    },
    "ko": {
        "examiner": "주장 검증자",
        "opponent": "토론 상대방",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (주장 검증자)",
        "negative_defense": "NEGATIVE_DEFENSE (변호)",
        "role_affirmative_short": "주장 검증자 (긍정적 비판)",
        "role_negative_short": "토론 상대 (부정적 변호)"
    },
    "es": {
        "examiner": "Examinador del Reclamo",
        "opponent": "Oponente del Debate",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (Examinador del Reclamo)",
        "negative_defense": "NEGATIVE_DEFENSE (Defensa)",
        "role_affirmative_short": "Examinador del Reclamo (Crítica Afirmativa)",
        "role_negative_short": "Oponente del Debate (Defensa Negativa)"
    },
    "fr": {
        "examiner": "Examinateur de la Revendication",
        "opponent": "Adversaire du Débat",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (Examinateur de la Revendication)",
        "negative_defense": "NEGATIVE_DEFENSE (Défense)",
        "role_affirmative_short": "Examinateur (Critique Affirmative)",
        "role_negative_short": "Adversaire (Défense Négative)"
    },
    "pt": {
        "examiner": "Examinador da Alegação",
        "opponent": "Oponente do Debate",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (Examinador da Alegação)",
        "negative_defense": "NEGATIVE_DEFENSE (Defesa)",
        "role_affirmative_short": "Examinador (Crítica Afirmativa)",
        "role_negative_short": "Oponente (Defesa Negativa)"
    },
    "de": {
        "examiner": "Anspruchsprüfer",
        "opponent": "Debattengegner",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (Anspruchsprüfer)",
        "negative_defense": "NEGATIVE_DEFENSE (Verteidigung)",
        "role_affirmative_short": "Anspruchsprüfer (Affirmative Kritik)",
        "role_negative_short": "Debattengegner (Negative Verteidigung)"
    },
    "ru": {
        "examiner": "Эксперт-экзаменатор утверждения",
        "opponent": "Оппонент в дебатах",
        "affirmative_critique": "AFFIRMATIVE_CRITIQUE (Эксперт-экзаменатор)",
        "negative_defense": "NEGATIVE_DEFENSE (Защита)",
        "role_affirmative_short": "Экзаменатор (Утвердительная критика)",
        "role_negative_short": "Оппонент (Отрицательная защита)"
    }
}


MATRIX_LOCALIZED_TEMPLATES = {
    "id": {
        "rujukan_default": "Kitab Suci / Naskah Primer / Manuskrip Terkait",
        "format": "Naskah 3 Babak Lengkap + 4 Segmen Forensik",
        "b1_title": "Babak 1: Premis Dasar & Penjangkaran Teks",
        "b1_paparan": "Afirmasi teologis oleh {user_p} yang menambatkan klaim '{claim}' pada otoritas kanonikal dan eksegesis normatif atas {rujukan}.",
        "b1_respons": "Tanggapan kritis awal oleh {opp_p} yang mempertanyakan premis tekstual dan konsistensi internal seputar '{claim}'.",
        "b2_title": "Babak 2: Cross-Examination Sokratik & Corong Dilema",
        "b2_q": [
            "Pada klausa atau ayat spesifik manakah dalam {rujukan} yang secara eksplisit menegaskan '{claim}'?",
            "Bagaimana saudara mendamaikan definisi leksikal dalam bahasa asli dengan asumsi doktrinal eksternal?",
            "Bukankah konsesi eksegetis saudara justru meruntuhkan konsistensi internal kanon saudara sendiri?"
        ],
        "b2_jebakan": "Mengunci lawan bicara pada pembacaan teks sumber verbatim dalam {rujukan} untuk mencegah pengalihan topik.",
        "b3_title": "Babak 3: Forensik Teks & Filologi Bahasa Sumber",
        "b3_bedah": "Ekstraksi akar kata/lema, morfologi verba, dan uraian sintaksis pada {rujukan} terhadap klaim '{claim}'.",
        "b3_saksi": ["Codex Sinaiticus", "Codex Vaticanus", "Papirus Kuno / Teks Masoretik / LXX"],
        "b3_audit": "Audit pergeseran penerjemahan dari manuskrip kuno ke versi modern guna mengidentifikasi bias doktrinal.",
        "b4_title": "Babak 4: Putusan Dialektika & Matriks Bukti (Evaluasi Akhir)",
        "b4_concession": "Rangkuman kompromi logis krusial yang berhasil diekstraksi mengenai klaim '{claim}'.",
        "b4_evaluasi": "Penilaian bukti final terhadap ketahanan teks dan kekuatan logis klaim '{claim}' berdasarkan standar E1-E6."
    },
    "en": {
        "rujukan_default": "Scripture / Primary Text / Ancient Manuscript Witnesses",
        "format": "Full 3-Act Script + 4 Forensic Segments",
        "b1_title": "Act 1: Foundational Premises & Textual Anchoring",
        "b1_paparan": "Theological affirmation by {user_p} anchoring the claim '{claim}' to canonical authority and normative exegesis of {rujukan}.",
        "b1_respons": "Initial critical response by {opp_p} questioning textual premises and internal consistency regarding '{claim}'.",
        "b2_title": "Act 2: Socratic Cross-Examination & Dilemma Funnel",
        "b2_q": [
            "In which specific clause or verse within {rujukan} is '{claim}' explicitly affirmed?",
            "How do you reconcile lexical definitions in original languages with external dogmatic assumptions?",
            "Does your hermeneutical concession not undermine the internal consistency of your own canon?"
        ],
        "b2_jebakan": "Locking interlocutor to verbatim source text readings in {rujukan} to prevent moving the goalposts.",
        "b3_title": "Act 3: Textual Forensics & Source-Language Philology",
        "b3_bedah": "Root/lemma extraction, verbal morphology, and syntactic parsing on {rujukan} for claim '{claim}'.",
        "b3_saksi": ["Codex Sinaiticus", "Codex Vaticanus", "Ancient Papyri / Masoretic Text / LXX"],
        "b3_audit": "Translation shift audit from ancient primary manuscripts to modern versions to identify dogmatic bias.",
        "b4_title": "Act 4: Dialectical Verdict & Evidence Matrix (Final Evaluation)",
        "b4_concession": "Summary of critical logical concessions extracted regarding claim '{claim}'.",
        "b4_evaluasi": "Final evidentiary assessment of textual robustness and logical resilience for '{claim}' based on E1-E6 standards."
    },
    "it": {
        "rujukan_default": "Scrittura / Testo Primario / Testimoni Manoscritti Antichi",
        "format": "Copione Completo in 3 Atti + 4 Segmenti Forensi",
        "b1_title": "Atto 1: Premesse Fondamentali e Ancoraggio Testuale",
        "b1_paparan": "Affermazione teologica di {user_p} che ancora l'affermazione '{claim}' all'autorità canonica e all'esegesi normativa di {rujukan}.",
        "b1_respons": "Risposta critica iniziale di {opp_p} che interroga le premesse testuali e la coerenza interna riguardo a '{claim}'.",
        "b2_title": "Atto 2: Controinterrogatorio Socratico e Imbuto del Dilemma",
        "b2_q": [
            "In quale clausola o versetto specifico di {rujukan} viene esplicitamente affermato '{claim}'?",
            "Come conciliate le definizioni lessicali nelle lingue originali con presupposti dogmatici esterni?",
            "La vostra concessione ermeneutica non compromette forse la coerenza interna del vostro stesso canone?"
        ],
        "b2_jebakan": "Bloccare l'interlocutore sulle letture verbatim del testo sorgente in {rujukan} per impedire lo spostamento dei pali.",
        "b3_title": "Atto 3: Forense Testuale e Filologia della Lingua Sorgente",
        "b3_bedah": "Estrazione di radice/lemma, morfologia verbale e analisi sintattica su {rujukan} per l'affermazione '{claim}'.",
        "b3_saksi": ["Codex Sinaiticus", "Codex Vaticanus", "Papiri Antichi / Testo Masoretico / LXX"],
        "b3_audit": "Audit delle deviazioni di traduzione dai manoscritti antichi alle versioni moderne per identificare bias dogmatici.",
        "b4_title": "Atto 4: Verdetto Dialettico e Matrice delle Prove (Valutazione Finale)",
        "b4_concession": "Sintesi delle concessioni logiche critiche estratte sull'affermazione '{claim}'.",
        "b4_evaluasi": "Valutazione probatoria finale della robustezza testuale e resilienza logica di '{claim}' basata su standard E1-E6."
    },
    "zh": {
        "rujukan_default": "圣经 / 原文经典 / 古代手抄本见证",
        "format": "完整三幕剧本 + 4项法医取证分析",
        "b1_title": "第一幕：基本前提与文本锚定",
        "b1_paparan": "{user_p} 的神学立论将主张 '{claim}' 锚定于正典权威及对 {rujukan} 的规范解释。",
        "b1_respons": "{opp_p} 的初步批判性回应，质疑关于 '{claim}' 的文本前提与内在逻辑一致性。",
        "b2_title": "第二幕：苏格拉底交叉质询与逻辑困境漏斗",
        "b2_q": [
            "在 {rujukan} 的哪一节经文或具体子句中，明确肯定了 '{claim}'？",
            "你如何调和原始语言词汇学定义与外部教义假设之间的矛盾？",
            "你的释经让步难道不会破坏你自身正典体系的内在一致性吗？"
        ],
        "b2_jebakan": "将对话者严格锁定于 {rujukan} 的字面源文本解读，防止转移论题。",
        "b3_title": "第三幕：文本法医鉴定与源语言文献学",
        "b3_bedah": "对 {rujukan} 针对主张 '{claim}' 进行词根提取、动词形态学与句法结构剖析。",
        "b3_saksi": ["西奈抄本 (Codex Sinaiticus)", "梵蒂冈抄本 (Codex Vaticanus)", "古纸草抄本 / 马所拉文本 / 七十士译本 (LXX)"],
        "b3_audit": "对从古代原始手抄本到现代译本的翻译偏差审计，以识别教义偏见。",
        "b4_title": "第四幕：辩证裁决与证据矩阵（终审评估）",
        "b4_concession": "关于主张 '{claim}' 已提取的关键逻辑妥协摘要。",
        "b4_evaluasi": "基于 E1-E6 标准对主张 '{claim}' 文本坚固性与逻辑韧性的最终证据评估。"
    },
    "ar": {
        "rujukan_default": "الكتاب المقدس / النص الأصلي / شواهد المخطوطات القديمة",
        "format": "نص كامل من 3 فصول + 4 أقسام جنائية نقدية",
        "b1_title": "الفصل الأول: المقدمات الأساسية والتثبيت النصي",
        "b1_paparan": "التأكيد اللاهوتي من جانب {user_p} الذي يربط الادعاء '{claim}' بالسلطة القانونية والتفسير المعياري لنص {rujukan}.",
        "b1_respons": "الاستجابة النقدية الأولية من جانب {opp_p} التي تشكك في المقدمات النصية والاتساق الداخلي حول '{claim}'.",
        "b2_title": "الفصل الثاني: الاستجواب السقراطي ومحقان المأزق المنطقي",
        "b2_q": [
            "في أي بند أو آية محددة ضمن {rujukan} تم إثبات الادعاء '{claim}' صراحة وبالمعنى الحرفي؟",
            "كيف توفق بين التعريفات اللغوية في اللغات الأصلية وبين الافتراضات العقائدية اللاحقة؟",
            "ألا يؤدي تنازلك التفسيري إلى تقويض الاتساق الداخلي لقانونك الكتابي نفسه؟"
        ],
        "b2_jebakan": "إلزام المحاور حصراً بالقراءة الحرفية للنصوص الأصلية في {rujukan} لمنع التهرب وتغيير محور النقاش.",
        "b3_title": "الفصل الثالث: التحقيق النصي الجنائي وفيلولوجيا لغات المصدر",
        "b3_bedah": "استخراج الجذور والمعاجم، والصرف الفعلي، والتحليل النحوي في {rujukan} بشأن الادعاء '{claim}'.",
        "b3_saksi": ["المخطوطة السينائية (Codex Sinaiticus)", "المخطوطة الفاتيكانية (Codex Vaticanus)", "البرديات القديمة / النص الماسورتي / السبعينية (LXX)"],
        "b3_audit": "تدقيق الانزياح في الترجمة من المخطوطات الأصلية إلى الإصدارات الحديثة لكشف التحيزات العقائدية.",
        "b4_title": "الفصل الرابع: الحكم الجدلي ومصفوفة الأدلة (التقييم النهائي)",
        "b4_concession": "ملخص التنازلات المنطقية الحاسمة المستخلصة حول الادعاء '{claim}'.",
        "b4_evaluasi": "التقييم النهائي لمتانة النص وصلابته المنطقية للادعاء '{claim}' استناداً إلى معايير E1-E6."
    },
    "tr": {
        "rujukan_default": "Kutsal Yazı / Birincil Metin / Antik El Yazması Tanıkları",
        "format": "Tam 3 Perdelik Metin + 4 Adli İnceleme Bölümü",
        "b1_title": "1. Perde: Temel Öncüller ve Metinsel Çapalama",
        "b1_paparan": "{user_p} tarafından '{claim}' iddiasını kanonik otoriteye ve {rujukan} metninin normatif tefsirine bağlayan teolojik beyan.",
        "b1_respons": "{opp_p} tarafından '{claim}' hakkındaki metinsel öncülleri ve iç tutarlılığı sorgulayan ilk eleştirel yanıt.",
        "b2_title": "2. Perde: Sokratik Çapraz Sorgu ve İkilem Hunisi",
        "b2_q": [
            "{rujukan} içindeki hangi belirli cümlede veya ayette '{claim}' açıkça ve lafzıyla teyit edilmektedir?",
            "Orijinal dillerdeki sözlük tanımları ile harici dogmatik varsayımları nasıl uzlaştırıyorsunuz?",
            "Yaptığınız yorumbilimsel taviz, kendi kutsal metin kanonunuzun iç tutarlılığını zedelemiyor mu?"
        ],
        "b2_jebakan": "Konuyu saptırmayı önlemek için muhatabı {rujukan} içindeki harfi kaynak metin okumalarına kilitlemek.",
        "b3_title": "3. Perde: Metin Adli Tıbbı ve Kaynak Dil Filolojisi",
        "b3_bedah": "'{claim}' iddiası için {rujukan} üzerinde kök/lema çıkarımı, fiil morfolojisi ve sözdizimsel ayrıştırma.",
        "b3_saksi": ["Codex Sinaiticus", "Codex Vaticanus", "Antik Papirüsler / Masoretik Metin / Septuaginta (LXX)"],
        "b3_audit": "Dogmatik önyargıları tespit etmek için antik el yazmalarından modern çevirilere kayma denetimi.",
        "b4_title": "4. Perde: Diyalektik Hüküm ve Kanıt Matrisi (Nihai Değerlendirme)",
        "b4_concession": "'{claim}' iddiasına ilişkin elde edilen kritik mantıksal tavizlerin özeti.",
        "b4_evaluasi": "E1-E6 standartlarına dayalı olarak '{claim}' için metinsel sağlamlığın nihai delil değerlendirmesi."
    },
    "ur": {
        "rujukan_default": "مقدس صحیفہ / بنیادی متن / قدیم مخطوطات کے گواہ",
        "format": "مکمل 3 ایکٹ اسکرپٹ + 4 فارنزک شعبے",
        "b1_title": "پہلا ایکٹ: بنیادی مقدمات اور متنی لنگر اندازی",
        "b1_paparan": "{user_p} کی جانب سے الہیاتی توثیق جو دعوے '{claim}' کو قانونی سند اور {rujukan} کی روایتی تفسیر پر قائم کرتی ہے۔",
        "b1_respons": "{opp_p} کا ابتدائی تنقیدی ردعمل جو '{claim}' کے متنی مقدمات اور اندرونی مطابقت پر سوال اٹھاتا ہے۔",
        "b2_title": "دوسرا ایکٹ: سقراطی جرح اور مخمصے کا فネル",
        "b2_q": [
            "{rujukan} کی کس مخصوص شق یا آیت میں صراحتاً '{claim}' کی تصدیق کی گئی ہے؟",
            "آپ اصل زبانوں کی لغوی تعریفوں کو بیرونی عقائدی مفروضوں کے ساتھ کیسے ہم آہنگ کرتے ہیں؟",
            "کیا آپ کا تشریحی اعتراف آپ کے اپنے متنی مجموعے کی اندرونی مطابقت کو نقصان نہیں پہنچاتا؟"
        ],
        "b2_jebakan": "موضوع کو بدلنے سے روکنے کے لیے مخاطب کو {rujukan} کے لفظی بنیادی متن پر سختی سے مقید کرنا۔",
        "b3_title": "تیسرا ایکٹ: متنی فارنزک اور بنیادی زبان کی فیلولوجی",
        "b3_bedah": "دعوے '{claim}' کے لیے {rujukan} پر مادہ/لیما کا اخراج، فعلی صرف اور نحوی تجزیہ۔",
        "b3_saksi": ["کوڈیکس سینا Boardwalk (Codex Sinaiticus)", "کوڈیکس ویٹیکن (Codex Vaticanus)", "قدیم پیپائری / مسوراتی متن / سبعینیہ (LXX)"],
        "b3_audit": "عقائدی تعصب کو بے نقاب کرنے کے لیے قدیم مخطوطات سے جدید تراجم میں تبدیلیوں کا آڈٹ۔",
        "b4_title": "چوتھا ایکٹ: جدلیاتی فیصلہ اور ثبوتی میٹرکس (حتمی جائزہ)",
        "b4_concession": "دعوے '{claim}' کے حوالے سے حاصل کیے گئے اہم منطقی اعترافات کا خلاصہ۔",
        "b4_evaluasi": "E1-E6 معیارات کی بنیاد پر دعوے '{claim}' کی متنی مضبوطی کا حتمی ثبوتی جائزہ۔"
    },
    "fa": {
        "rujukan_default": "کتاب مقدس / متن اولیه / شواهد دست‌نوشته‌های کهن",
        "format": "فیلم‌نامه کامل ۳ پرده‌ای + ۴ بخش کالبدشکافی قانونی",
        "b1_title": "پرده اول: مقدمات بنیادین و تثبیت متنی",
        "b1_paparan": "تصدیق الهیاتی توسط {user_p} که ادعای '{claim}' را بر اقتدار قانونی و تفسیر معیار از {rujukan} استوار می‌سازد.",
        "b1_respons": "پاسخ انتقادی اولیه توسط {opp_p} که مقدمات متنی و انسجام درونی پیرامون '{claim}' را به چالش می‌کشد.",
        "b2_title": "پرده دوم: بازجویی سقراطی و قیف تنگنای منطقی",
        "b2_q": [
            "در کدام بند یا آیه مشخص در {rujukan}، ادعای '{claim}' به طور صریح و واژه‌به‌واژه تایید شده است؟",
            "چگونه تعاریف لغوی در زبان‌های اصلی را با مفروضات جزمی پسین سازگار می‌کنید؟",
            "آیا مصالحه تفسیری شما، انسجام درونی متون قانونی خودتان را تضعیف نمی‌کند؟"
        ],
        "b2_jebakan": "مقید ساختن مخاطب منحصراً به خوانش‌های تحت‌اللفظی متن مبدأ در {rujukan} برای جلوگیری از فرار از موضوع.",
        "b3_title": "پرده سوم: کالبدشکافی قانونی متن و فیلولوژی زبان مبدأ",
        "b3_bedah": "استخراج ریشه/واژه‌بست، صرف افعال و تجزیه نحوی بر روی {rujukan} برای ادعای '{claim}'.",
        "b3_saksi": ["نسخه سینائیه (Codex Sinaiticus)", "نسخه واتیکان (Codex Vaticanus)", "پاپیروس‌های کهن / متن ماسورتی / هفتادگانی (LXX)"],
        "b3_audit": "ممیزی انحرافات ترجمه از دست‌نوشته‌های اولیه به نسخه‌های مدرن برای شناسایی سوگیری‌های عقیدتی.",
        "b4_title": "پرده چهارم: حکم دیالکتیکی و ماتریس شواهد (ارزیابی نهایی)",
        "b4_concession": "خلاصه مصالحه‌های منطقی حیاتی استخراج‌شده در مورد ادعای '{claim}'.",
        "b4_evaluasi": "ارزیابی شواهدی نهایی از استحکام متنی و تاب‌آوری منطقی برای '{claim}' بر اساس استانداردهای E1-E6."
    },
    "hi": {
        "rujukan_default": "पवित्र शास्त्र / प्राथमिक पाठ / प्राचीन पांडुलिपि साक्ष्य",
        "format": "पूर्ण 3-अंकीय आलेख + 4 फोरेंसिक खंड",
        "b1_title": "अंक 1: मौलिक आधार और पाठ्य लंगर",
        "b1_paparan": "{user_p} द्वारा धार्मिक प्रतिज्ञान जो '{claim}' दावे को विहित अधिकार और {rujukan} की प्रामाणिक व्याख्या पर स्थिर करता है।",
        "b1_respons": "{opp_p} द्वारा प्रारंभिक आलोचनात्मक उत्तर जो '{claim}' के पाठ्य आधार और आंतरिक संगति पर प्रश्न उठाता है।",
        "b2_title": "अंक 2: सुकराती जिरह और दुविधा का जाल",
        "b2_q": [
            "{rujukan} के किस विशिष्ट उपवाक्य या पद में स्पष्ट रूप से '{claim}' की पुष्टि की गई है?",
            "आप मूल भाषाओं के शाब्दिक अर्थों को बाहरी मताग्रही मान्यताओं के साथ कैसे सुसंगत करते हैं?",
            "क्या आपकी व्याख्यात्मक रियायत आपके अपने धर्मग्रंथों की आंतरिक संगति को खंडित नहीं करती?"
        ],
        "b2_jebakan": "विषय से भटकाव रोकने के लिए वार्ताकार को {rujukan} के शब्दशः मूल पाठ पर पूरी तरह केंद्रित रखना।",
        "b3_title": "अंक 3: पाठ्य फोरेंसिक और मूल भाषा भाषाशास्त्र",
        "b3_bedah": "'{claim}' दावे के लिए {rujukan} पर मूल धातु निष्कर्षण, क्रिया रूप और वाक्य-विन्यास विश्लेषण।",
        "b3_saksi": ["कोडेक्स सिनाईटिकस (Codex Sinaiticus)", "कोडेक्स वेटिकनस (Codex Vaticanus)", "प्राचीन पेपाइरस / मैसोरेटिक पाठ / सेप्टुआजेंट (LXX)"],
        "b3_audit": "सिद्धांतवादी पूर्वाग्रहों की पहचान के लिए प्राचीन पांडुलिपियों से आधुनिक अनुवादों में विचलन का ऑडिट।",
        "b4_title": "अंक 4: द्वंद्वात्मक निर्णय और साक्ष्य मैट्रिक्स (अंतिम मूल्यांकन)",
        "b4_concession": "'{claim}' दावे के संबंध में प्राप्त महत्वपूर्ण तार्किक रियायतों का सारांश।",
        "b4_evaluasi": "E1-E6 मानकों के आधार पर '{claim}' के लिए पाठ्य दृढ़ता और तार्किक लचीलेपन का अंतिम साक्ष्य मूल्यांकन।"
    },
    "bn": {
        "rujukan_default": "পবিত্র শাস্ত্র / প্রাথমিক মূলপাঠ / প্রাচীন পাণ্ডুলিপি সাক্ষ্য",
        "format": "সম্পূর্ণ ৩ অঙ্কের স্ক্রিপ্ট + ৪টি ফরেনসিক বিভাগ",
        "b1_title": "অঙ্ক ১: মৌলিক ভিত্তি ও পাঠ্য নোঙর",
        "b1_paparan": "{user_p} কর্তৃক ধর্মতাত্ত্বিক সমর্থন যা দাবি '{claim}'-কে প্রামাণিক কর্তৃত্ব এবং {rujukan}-এর বিধিসম্মত ব্যাখ্যার সাথে যুক্ত করে।",
        "b1_respons": "{opp_p} কর্তৃক প্রাথমিক সমালোচনামূলক প্রতিক্রিয়া যা '{claim}'-এর পাঠ্য ভিত্তি এবং অভ্যন্তরীণ সংগতি নিয়ে প্রশ্ন তোলে।",
        "b2_title": "অঙ্ক ২: সক্রেটিক জেরা ও উভসংকট ফানেল",
        "b2_q": [
            "{rujukan}-এর কোন নির্দিষ্ট উপবাক্য বা পদে স্পষ্টভাবে '{claim}'-কে স্বীকৃতি দেওয়া হয়েছে?",
            "আপনি কীভাবে মূল ভাষার আভিধানিক সংজ্ঞার সাথে বাহ্যিক গোঁড়া অনুমানের সমন্বয় করেন?",
            "আপনার ব্যাখ্যামূলক ছাড় কি আপনার নিজস্ব শাস্ত্রীয় প্রামাণিকতার অভ্যন্তরীণ ধারাবাহিকতাকে ক্ষুণ্ন করে না?"
        ],
        "b2_jebakan": "আলোচনার দিক পরিবর্তন রোধ করতে আলোচককে {rujukan}-এর আক্ষরিক মূল পাঠ্যে সম্পূর্ণভাবে আবদ্ধ রাখা।",
        "b3_title": "অঙ্ক ৩: পাঠ্য ফরেনসিক ও মূল ভাষার ভাষাতত্ত্ব",
        "b3_bedah": "'{claim}' দাবির জন্য {rujukan}-এর ধাতু/লেমা নিষ্কাশন, ক্রিয়াপদের রূপতত্ত্ব এবং বাক্যতাত্ত্বিক বিশ্লেষণ।",
        "b3_saksi": ["কোডেক্স সিনাইটিকাস (Codex Sinaiticus)", "কোডেক্স ভ্যাটিকানাস (Codex Vaticanus)", "প্রাচীন প্যাপিরাস / ম্যাসোরেটিক পাঠ / সপ্ততি (LXX)"],
        "b3_audit": "মতবাদগত পক্ষপাত শনাক্ত করতে প্রাচীন পাণ্ডুলিপি থেকে আধুনিক অনুবাদে রূপান্তরের নিরীক্ষা।",
        "b4_title": "অঙ্ক ৪: দ্বান্দ্বিক রায় ও সাক্ষ্য ম্যাট্রিক্স (চূড়ান্ত মূল্যায়ন)",
        "b4_concession": "'{claim}' দাবি সংক্রান্ত নিষ্কাশিত গুরুত্বপূর্ণ যৌক্তিক ছাড়ের সারসংক্ষেপ।",
        "b4_evaluasi": "E1-E6 মানদণ্ডের ওপর ভিত্তি করে '{claim}'-এর পাঠ্য দৃঢ়তা ও যৌক্তিক শক্তির চূড়ান্ত মূল্যায়ন।"
    },
    "ja": {
        "rujukan_default": "聖書 / 原典テキスト / 古代写本証拠",
        "format": "完全3幕構成台本 + 4つの法医学的分析セグメント",
        "b1_title": "第1幕：基本的前提とテキストの固定",
        "b1_paparan": "{user_p} による神学的言明であり、主唱 '{claim}' を正典的権威と {rujukan} の規範的解釈に結びつける。",
        "b1_respons": "{opp_p} による初期の批判的応答であり、'{claim}' に関するテキスト的前提と内的論理整合性を問う。",
        "b2_title": "第2幕：ソクラテス的反対尋問とジレンマの漏斗",
        "b2_q": [
            "{rujukan} のどの具体的な節または節句において、'{claim}' が明示的に肯定されているか？",
            "原語の語彙的定義と外部の教義的前提をどのように調和させるのか？",
            "あなたの釈義的譲歩は、あなた自身の正典体系の内的整合性を損なうのではないか？"
        ],
        "b2_jebakan": "論点ずらしを防ぐため、対話者を {rujukan} の逐語的原文読解に厳格に固定する。",
        "b3_title": "第3幕：テキスト法医学と原語文献学",
        "b3_bedah": "主唱 '{claim}' に対する {rujukan} の語根・補題抽出、動詞形態論、統語構造解析。",
        "b3_saksi": ["シナイ写本 (Codex Sinaiticus)", "バチカン写本 (Codex Vaticanus)", "古代パピルス / マソラ本文 / 七十人訳 (LXX)"],
        "b3_audit": "教理的偏向を識別するための、古代原本写本から近代訳への翻訳変遷監査。",
        "b4_title": "第4幕：弁証法的評決と証拠マトリクス（最終評価）",
        "b4_concession": "主唱 '{claim}' に関して引き出された決定的な論理的譲歩の要約。",
        "b4_evaluasi": "E1-E6 基準に基づく '{claim}' のテキスト的頑健性と論理的レジリエンスの最終証拠評価。"
    },
    "ko": {
        "rujukan_default": "성경 / 원전 텍스트 / 고대 사본 증언",
        "format": "완전 3막 대본 + 4대 법의학적 분석 세그먼트",
        "b1_title": "제1막: 기본 전제 및 텍스트 닻내림",
        "b1_paparan": "{user_p}의 신학적 확언으로, 주장 '{claim}'을 정경적 권위와 {rujukan}의 규범적 주석에 연결함.",
        "b1_respons": "{opp_p}의 초기 비판적 응답으로, '{claim}'에 관한 텍스트적 전제와 내적 논리적 일관성에 의문을 제기함.",
        "b2_title": "제2막: 소크라테스식 반대심문 및 딜레마 깔때기",
        "b2_q": [
            "{rujukan}의 어느 특정 절이나 문구에서 '{claim}'이 명시적으로 긍정되고 있는가?",
            "원어의 어휘론적 정의와 외부 교리적 전제를 어떻게 조화시키는가?",
            "당신의 주석적 양보가 당신 자신의 정경 체계의 내적 일관성을 훼손하지 않는가?"
        ],
        "b2_jebakan": "논점 일탈을 방지하기 위해 대화 상대를 {rujukan}의 축자적 원문 독해에 엄격히 묶어둠.",
        "b3_title": "제3막: 텍스트 법의학 및 원문 문헌학",
        "b3_bedah": "주장 '{claim}'에 대한 {rujukan}의 어근/표제어 추출, 동사 형태론 및 구문론적 분석.",
        "b3_saksi": ["시나이 사본 (Codex Sinaiticus)", "바티칸 사본 (Codex Vaticanus)", "고대 파피루스 / 마소라 텍스트 / 70인역 (LXX)"],
        "b3_audit": "교리적 편향을 식별하기 위한 고대 원본 사본에서 현대 번역본으로의 번역 변천 감사.",
        "b4_title": "제4막: 변증법적 평결 및 증거 매트릭스 (최종 평가)",
        "b4_concession": "주장 '{claim}'에 대해 도출된 결정적 논리적 양보의 요약.",
        "b4_evaluasi": "E1-E6 표준에 기반한 '{claim}'의 텍스트 견고성 및 논리적 탄력성에 대한 최종 증거 평가."
    },
    "es": {
        "rujukan_default": "Escritura / Texto Primario / Testigos Manuscritos Antiguos",
        "format": "Guión Completo en 3 Actos + 4 Segmentos Forenses",
        "b1_title": "Acto 1: Premisas Fundamentales y Anclaje Textual",
        "b1_paparan": "Afirmación teológica por {user_p} anclando la afirmación '{claim}' a la autoridad canónica y a la exégesis normativa de {rujukan}.",
        "b1_respons": "Respuesta crítica inicial por {opp_p} cuestionando las premisas textuales y la coherencia interna en torno a '{claim}'.",
        "b2_title": "Acto 2: Contrainterrogatorio Socrático y Embudo del Dilema",
        "b2_q": [
            "¿En qué cláusula o versículo específico de {rujukan} se afirma explícitamente '{claim}'?",
            "¿Cómo concilia las definiciones léxicas en los idiomas originales con las presuposiciones dogmáticas externas?",
            "¿Acaso su concesión hermenéutica no socava la coherencia interna de su propio canon?"
        ],
        "b2_jebakan": "Bloquear al interlocutor en las lecturas textuales literales de {rujukan} para evitar desviar la atención.",
        "b3_title": "Acto 3: Forense Textual y Filología del Idioma Original",
        "b3_bedah": "Extracción de raíz/lema, morfología verbal y análisis sintáctico en {rujukan} para la afirmación '{claim}'.",
        "b3_saksi": ["Codex Sinaiticus", "Codex Vaticanus", "Papiros Antiguos / Texto Masorético / LXX"],
        "b3_audit": "Auditoría de desplazamientos de traducción de manuscritos antiguos a versiones modernas para identificar sesgos dogmáticos.",
        "b4_title": "Acto 4: Veredicto Dialéctico y Matriz de Evidencia (Evaluación Final)",
        "b4_concession": "Resumen de concesiones lógicas críticas extraídas sobre la afirmación '{claim}'.",
        "b4_evaluasi": "Evaluación probatoria final de solidez textual y resiliencia lógica para '{claim}' basada en estándares E1-E6."
    },
    "fr": {
        "rujukan_default": "Écriture / Texte Primaire / Témoins Manuscrits Anciens",
        "format": "Scénario Complet en 3 Actes + 4 Segments Médico-Légaux",
        "b1_title": "Acte 1 : Prémisses Fondamentales et Ancrage Textuel",
        "b1_paparan": "Affirmation théologique par {user_p} ancrant l'affirmation '{claim}' à l'autorité canonique et à l'exégèse normative de {rujukan}.",
        "b1_respons": "Réponse critique initiale par {opp_p} interrogeant les prémisses textuelles et la cohérence interne autour de '{claim}'.",
        "b2_title": "Acte 2 : Contre-Interrogatoire Socratique et Entonnoir du Dilemme",
        "b2_q": [
            "Dans quelle clause ou quel verset spécifique de {rujukan} l'affirmation '{claim}' est-elle explicitement affirmée ?",
            "Comment conciliez-vous les définitions lexicales dans les langues originales avec des présupposés dogmatiques externes ?",
            "Votre concession herméneutique ne sape-t-elle pas la cohérence interne de votre propre canon ?"
        ],
        "b2_jebakan": "Verrouiller l'interlocuteur sur les lectures textuelles littérales de {rujukan} pour empêcher de déplacer le débat.",
        "b3_title": "Acte 3 : Analyse Médico-Légale du Texte et Philologie de la Langue Source",
        "b3_bedah": "Extraction de racine/lemme, morphologie verbale et analyse syntaxique sur {rujukan} pour l'affirmation '{claim}'.",
        "b3_saksi": ["Codex Sinaiticus", "Codex Vaticanus", "Papyrus Anciens / Texte Masorétique / LXX"],
        "b3_audit": "Audit des glissements de traduction des manuscrits primaires anciens vers les versions modernes pour identifier les biais dogmatiques.",
        "b4_title": "Acte 4 : Verdict Dialectique et Matrice de Preuves (Évaluation Finale)",
        "b4_concession": "Résumé des concessions logiques critiques extraites concernant l'affirmation '{claim}'.",
        "b4_evaluasi": "Évaluation probante finale de la robustesse textuelle et de la résilience logique pour '{claim}' selon les normes E1-E6."
    },
    "pt": {
        "rujukan_default": "Escritura / Texto Primário / Testemunhas Manuscritas Antigas",
        "format": "Roteiro Completo em 3 Atos + 4 Segmentos Forenses",
        "b1_title": "Ato 1: Premissas Fundamentais e Ancoragem Textual",
        "b1_paparan": "Afirmação teológica por {user_p} ancorando a alegação '{claim}' na autoridade canônica e na exegese normativa de {rujukan}.",
        "b1_respons": "Resposta crítica inicial por {opp_p} questionando as premissas textuais e a coerência interna em torno de '{claim}'.",
        "b2_title": "Ato 2: Contrainterrogatório Socrático e Funil do Dilema",
        "b2_q": [
            "Em qual cláusula ou versículo específico de {rujukan} a alegação '{claim}' é explicitamente afirmada?",
            "Como você reconcilia as definições lexicais nas línguas originais com pressuposições dogmáticas externas?",
            "Sua concessão hermenêutica não compromete a coerência interna de seu próprio cânon?"
        ],
        "b2_jebakan": "Travar o interlocutor nas leituras textuais literais em {rujukan} para evitar desvios no debate.",
        "b3_title": "Ato 3: Forense Textual e Filologia da Língua Original",
        "b3_bedah": "Extração de raiz/lema, morfologia verbal e análise sintática em {rujukan} para a alegação '{claim}'.",
        "b3_saksi": ["Codex Sinaiticus", "Codex Vaticanus", "Papiros Antigos / Texto Massorético / LXX"],
        "b3_audit": "Auditoria de desvios de tradução de manuscritos antigos para versões modernas para identificar vieses dogmáticos.",
        "b4_title": "Ato 4: Veredito Dialético e Matriz de Evidências (Avaliação Final)",
        "b4_concession": "Resumo das concessões lógicas críticas extraídas sobre a alegação '{claim}'.",
        "b4_evaluasi": "Avaliação probatória final da solidez textual e resiliência lógica para '{claim}' com base nos padrões E1-E6."
    },
    "de": {
        "rujukan_default": "Schrift / Primärtext / Antike Handschriftenzeugen",
        "format": "Vollständiges 3-Akte-Skript + 4 forensische Segmente",
        "b1_title": "Akt 1: Grundlegende Prämissen und textuelle Verankerung",
        "b1_paparan": "Theologische Bejahung durch {user_p}, die den Anspruch '{claim}' an kanonische Autorität und normative Exegese von {rujukan} bindet.",
        "b1_respons": "Erste kritische Antwort von {opp_p}, die textuelle Prämissen und interne Konsistenz hinsichtlich '{claim}' hinterfragt.",
        "b2_title": "Akt 2: Sokratisches Kreuzverhör und Dilemma-Trichter",
        "b2_q": [
            "In welchem spezifischen Satz oder Vers innerhalb von {rujukan} wird '{claim}' ausdrücklich bejaht?",
            "Wie vereinbaren Sie lexikalische Definitionen in den Originalsprachen mit externen dogmatischen Annahmen?",
            "Untergräbt Ihr hermeneutisches Zugeständnis nicht die innere Konsistenz Ihres eigenen Kanons?"
        ],
        "b2_jebakan": "Den Gesprächspartner auf wörtliche Quelltextlesarten in {rujukan} festnageln, um Ausflüchte zu verhindern.",
        "b3_title": "Akt 3: Textforensik und Philologie der Ausgangssprache",
        "b3_bedah": "Wurzel-/Lemma-Extraktion, Verbalmorphologie und syntaktische Analyse an {rujukan} für den Anspruch '{claim}'.",
        "b3_saksi": ["Codex Sinaiticus", "Codex Vaticanus", "Antike Papyri / Masoretischer Text / LXX"],
        "b3_audit": "Übersetzungsverschiebungsaudit von antiken Handschriften zu modernen Versionen zur Aufdeckung dogmatischer Voreingenommenheit.",
        "b4_title": "Akt 4: Dialektisches Urteil und Evidenzmatrix (Abschlussbewertung)",
        "b4_concession": "Zusammenfassung der entscheidenden logischen Zugeständnisse bezüglich des Anspruchs '{claim}'.",
        "b4_evaluasi": "Abschließende Evidenzbewertung der textuellen Robustheit und logischen Belastbarkeit für '{claim}' nach E1-E6-Standards."
    },
    "ru": {
        "rujukan_default": "Писание / Первичный текст / Свидетельства древних рукописей",
        "format": "Полный 3-актный сценарий + 4 судебно-критических сегмента",
        "b1_title": "Акт 1: Фундаментальные предпосылки и текстуальная привязка",
        "b1_paparan": "Богословское утверждение стороны {user_p}, привязывающее тезис '{claim}' к каноническому авторитету и нормативной экзегезе {rujukan}.",
        "b1_respons": "Первоначальный критический ответ стороны {opp_p}, подвергающий сомнению текстуальные предпосылки и внутреннюю согласованность тезиса '{claim}'.",
        "b2_title": "Акт 2: Сократический перекрестный допрос и воронка дилеммы",
        "b2_q": [
            "В каком конкретном предложении или стихе в {rujukan} прямо и дословно утверждается тезис '{claim}'?",
            "Как вы согласуете словарные определения на языках оригинала с внешними догматическими предположениями?",
            "Не подрывает ли ваша экзегетическая уступка внутреннюю согласованность вашего собственного канона?"
        ],
        "b2_jebakan": "Строгая фиксация собеседника на дословном чтении исходного текста в {rujukan} во избежание ухода от темы.",
        "b3_title": "Акт 3: Текстуальная экспертиза и филология языка оригинала",
        "b3_bedah": "Извлечение корня/леммы, морфология глаголов и синтаксический анализ {rujukan} по тезису '{claim}'.",
        "b3_saksi": ["Синайский кодекс (Codex Sinaiticus)", "Ватиканский кодекс (Codex Vaticanus)", "Древние папирусы / Масоретский текст / Септуагинта (LXX)"],
        "b3_audit": "Аудит переводческих сдвигов от древних первичных рукописей к современным версиям для выявления догматической предвзятости.",
        "b4_title": "Акт 4: Диалектический вердикт и матрица доказательств (Итоговая оценка)",
        "b4_concession": "Резюме критических логических уступок, полученных в отношении тезиса '{claim}'.",
        "b4_evaluasi": "Итоговая доказательная оценка текстуальной прочности и логической устойчивости тезиса '{claim}' на основе стандартов E1-E6."
    }
}


def get_debate_matrix_localized(loc: str, user_p: str, opp_p: str, claim: str, rujukan_teks: str) -> dict:
    loc_key = (loc or "id").strip().lower()
    if loc_key.startswith("zh"):
        loc_key = "zh"
    elif loc_key.startswith("id"):
        loc_key = "id"
    elif loc_key.startswith("it"):
        loc_key = "it"
    elif loc_key.startswith("ar"):
        loc_key = "ar"
    elif loc_key.startswith("tr"):
        loc_key = "tr"
    elif loc_key.startswith("ur"):
        loc_key = "ur"
    elif loc_key.startswith("fa"):
        loc_key = "fa"
    elif loc_key.startswith("hi"):
        loc_key = "hi"
    elif loc_key.startswith("bn"):
        loc_key = "bn"
    elif loc_key.startswith("ja"):
        loc_key = "ja"
    elif loc_key.startswith("ko"):
        loc_key = "ko"
    elif loc_key.startswith("es"):
        loc_key = "es"
    elif loc_key.startswith("fr"):
        loc_key = "fr"
    elif loc_key.startswith("pt"):
        loc_key = "pt"
    elif loc_key.startswith("de"):
        loc_key = "de"
    elif loc_key.startswith("ru"):
        loc_key = "ru"
    else:
        loc_key = "en"

    tmpl = MATRIX_LOCALIZED_TEMPLATES.get(loc_key, MATRIX_LOCALIZED_TEMPLATES["en"])
    rujukan_display = tmpl["rujukan_default"] if "Kitab Suci" in rujukan_teks or "Scripture" in rujukan_teks else rujukan_teks

    return {
        "header": {
            "pihak_a": user_p,
            "pihak_b": opp_p,
            "topik": claim,
            "rujukan_utama": rujukan_display,
            "format": tmpl["format"]
        },
        "babak_1": {
            "title": tmpl["b1_title"],
            "paparan_pihak_a": tmpl["b1_paparan"].format(user_p=user_p, claim=claim, rujukan=rujukan_display),
            "respons_pihak_b": tmpl["b1_respons"].format(opp_p=opp_p, claim=claim, rujukan=rujukan_display)
        },
        "babak_2": {
            "title": tmpl["b2_title"],
            "pertanyaan_presisi": [q.format(rujukan=rujukan_display, claim=claim) for q in tmpl["b2_q"]],
            "jebakan_logika": tmpl["b2_jebakan"].format(rujukan=rujukan_display, claim=claim)
        },
        "babak_3": {
            "title": tmpl["b3_title"],
            "bedah_bahasa_sumber": tmpl["b3_bedah"].format(rujukan=rujukan_display, claim=claim),
            "saksi_manuskrip": tmpl["b3_saksi"],
            "audit_terjemahan": tmpl["b3_audit"]
        },
        "babak_4": {
            "title": tmpl["b4_title"],
            "concession_extracted": tmpl["b4_concession"].format(claim=claim),
            "evaluasi_kekuatan_bukti": tmpl["b4_evaluasi"].format(claim=claim)
        }
    }


# ---------------------------------------------------------------------------
# Universal 17-Language Debate Speeches & Epistemic Verdict Templates
# ---------------------------------------------------------------------------

DEBATE_DIALOGUE_I18N = {
    "id": {
        "motion_template": "Uji Forensik Teks Primer & Validitas Kanonikal atas Klaim: '{claim_clean}' ({p_primary})",
        "title_template": "Diskursus Teologis & Apologetika: {claim_clean}",
        "affirmative_stance": "Uji naskah primer kanonik & penolakan dogma tanpa ayat.",
        "negative_stance": "Pembelaan tradisi teologis dan penafsiran dogmatis.",
        "opp_r1": {
            "islam": "Meneliti proposisi tentang '{claim_clean}', kita wajib bertolak pada prinsip tauhid murni para nabi: setiap doktrin keilahian harus diuji apakah mengakui Allah yang mutlak esa tanpa sekutu, bukan hasil spekulasi filosofis belakangan.",
            "christian_protestant": "Bagi kami, pernyataan '{claim_clean}' tidak dapat dipisahkan dari keseluruhan penyataan Allah dalam 66 kitab Bible. Iman kami bersandar pada Sola Scriptura di mana ayat-ayat saling menerangi secara organik.",
            "christian_catholic": "Menilai pernyataan '{claim_clean}' hanya dari satu teks terisolasi akan kehilangan kedalamannya. Kami bersandar pada Tradisi suci apostolik dan konsensus Bapa Gereja yang telah menjaga deposit iman selama dua milenium.",
            "judaism": "Pernyataan '{claim_clean}' harus diuji di hadapan Tanakh dan perjanjian kekal di Sinai. Hukum Taurat adalah kekal dan tidak ada pengajaran baru yang berhak membatalkan ketetapan ilahi.",
            "atheist_secular": "Pernyataan '{claim_clean}' adalah klaim luar biasa yang menuntut bukti luar biasa pula (burden of proof). Kita harus mengujinya dengan metode historis-kritis empiris, bukan menerima presuposisi dogmatis."
        },
        "opp_rounds": {
            2: "[{opp_p}] Membaca teks {p_primary} harus diletakkan dalam konteks utuh kerangka hermeneutika teologis kami.",
            3: "[{opp_p}] Kita wajib memeriksa saksi kanonik paralel di seluruh kitab, bukan mengisolasi satu klausa tunggal.",
            4: "[{opp_p}] Tradisi dogmatis kami selama berabad-abad menerangi makna rohani yang melampaui definisi leksikal mentah.",
            5: "[{opp_p}] Dilema yang disodorkan adalah artifisial; misteri ilahi melampaui dualisme silogisme manusia.",
            6: "[{opp_p}] Kami menafsirkan {p_primary} secara harmonis dengan pengakuan iman historis dan konsensus gerejawi.",
            7: "[{opp_p}] Teologi sistematika menjembatani fragmen teks kuno dengan doktrin normatif yang hidup.",
            8: "[{opp_p}] Kami tetap teguh pada warisan kanonikal kami dan menyerahkan kebenaran pada nurani masing-masing."
        },
        "zuma_r1": "Mari kita bedah topik ini: '{motion}'. Seperti memeriksa sertifikat tanah, kita tidak bisa hanya mendengar cerita, melainkan harus membuka naskah aslinya! Perhatikan naskah kuno {p_primary}. Pertanyaan Sokratik saya sederhana: apakah di teks sumber aslinya benar-benar tertulis klaim saudara?",
        "zuma_r2": "Perhatikan: begitu kita uji naskah sumber {p_primary}, saudara langsung beralih ke teori abstrak. Ibarat rambu dilarang parkir yang jelas tertulis, tetapi saudara tafsirkan boleh parkir. Mengapa memaksakan makna yang tidak tertulis dalam naskah?",
        "zuma_r3": "Jangan geser topik perdebatan. Ketika teks {p_primary} tidak memuat klaim saudara, saudara ingin lari ke kitab lain. Ibarat saksi ditanya kejadian di ruang tamu malah bercerita halaman belakang. Jawab dulu: ada tidak ayat eksplisitnya?",
        "zuma_r4": "Saudara sebut ayat paralel {p_secondary}. Mari kita buka naskah tertuanya! Fakta filologis membuktikan bahwa naskah paling awal tetap menolak presuposisi saudara. {zuma_rebuttal}",
        "zuma_r5": "Saudara kini terjebak dalam dilema Sokratik yang mematikan: jika saudara mengakui teks {p_primary} apa adanya, doktrin saudara runtuh; jika saudara menolak teks aslinya, saudara menuduh penulis kitab keliru. Pilih jalan yang mana?",
        "zuma_r6": "Itu bukan jawaban logis, melainkan dalih. Menggunakan metode Ilzam al-Khasm, saya uji posisi saudara berdasarkan kanon kitab saudara sendiri. Dalam {p_primary} dan {p_secondary}, fakta tekstualnya jelas membantah klaim saudara.",
        "zuma_r7": "Kuncinya tampak di sini! Saudara akhirnya mengakui bahwa fondasi argumen saudara bukanlah teks tertulis, melainkan dogma eksternal yang ditempelkan belakangan. Di hadapan bukti naskah primer, klaim tanpa teks bernilai nol.",
        "zuma_r8": "Saudara-saudara sekalian, kebenaran berdiri di atas fakta naskah. Dalam 8 babak perdebatan '{motion}', pihak lawan gagal menunjukkan bukti eksplisit dari {p_primary} maupun {p_secondary}. Naskah kuno tetap tegak!",
        "socratic_q": "Apakah saudara bersedia mengakui naskah tertulis primer {p_primary} mengenai topik '{motion}' secara verbatim tanpa menyelundupkan asumsi di luar standar pembuktian?",
        "dilemma": "Jika saudara mengakui teks apa adanya, premis doktrinal saudara runtuh seketika; jika saudara menolak teks tertulis, saudara merusak integritas kitab dan konsistensi nalar saudara sendiri.",
        "presup": "Asumsi bahwa posisi lawan kebal dari pengujian filologis dan eksegesis naskah primer.",
        "verdict": "Simulasi dialektika membuktikan: dalam diskursus {user_p} vs {opp_p} mengenai '{motion}', klaim lawan runtuh total saat diuji secara verbatim terhadap naskah primer {p_primary} dan uji konsistensi internal.",
        "superiority": "AFFIRMATIVE_CRITIQUE (ZUMA)"
    },
    "en": {
        "motion_template": "Forensic Primary Text & Canonical Validity Audit on Claim: '{claim_clean}' ({p_primary})",
        "title_template": "Theological & Apologetics Discourse: {claim_clean}",
        "affirmative_stance": "Forensic audit of primary biblical manuscripts & refutation of dogma without scripture.",
        "negative_stance": "Defense of theological tradition and dogmatic interpretation.",
        "opp_r1": {
            "islam": "Examining the proposition on '{claim_clean}', we must stand on the pure monotheism (Tawhid) of the prophets: every divine doctrine must acknowledge the absolute oneness of God without partners, not post-biblical philosophical speculation.",
            "christian_protestant": "For us, the affirmation '{claim_clean}' cannot be separated from God's entire revelation across the 66 books of the Bible. Our faith rests on Sola Scriptura where scriptures illuminate each other organically.",
            "christian_catholic": "Evaluating '{claim_clean}' from an isolated text loses its depth. We rely on apostolic Holy Tradition and the consensus of the Church Fathers who guarded the deposit of faith for two millennia.",
            "judaism": "The assertion '{claim_clean}' must be tested before the Tanakh and the eternal Sinai covenant. The Torah law is eternal and no subsequent teaching has authority to annul divine commandments.",
            "atheist_secular": "The proposition '{claim_clean}' is an extraordinary claim requiring extraordinary evidence (burden of proof). We must test it via empirical historical-critical methodology, not dogmatic presuppositions."
        },
        "opp_rounds": {
            2: "[{opp_p}] Reading {p_primary} requires holistic synthesis within our theological hermeneutic framework.",
            3: "[{opp_p}] We must consider parallel canonical witnesses across scripture rather than isolating single phrases.",
            4: "[{opp_p}] Our centuries-old dogmatic tradition illuminates the deeper spiritual meaning beyond raw lexical definitions.",
            5: "[{opp_p}] The suggested dilemma is artificial; divine mysteries transcend human syllogistic dualities.",
            6: "[{opp_p}] We interpret {p_primary} harmoniously with historical creeds and foundational ecclesiastical consensus.",
            7: "[{opp_p}] Systematic theology bridges ancient textual fragments with living normative doctrine.",
            8: "[{opp_p}] We stand firmly upon our canonical heritage and leave conviction to personal conscience."
        },
        "zuma_r1": "Let us examine this topic: '{motion}'. Just like inspecting a property deed, we cannot merely rely on oral claims, but must examine the original primary text! Observe the ancient manuscripts of {p_primary}. My Socratic inquiry is simple: in the verbatim original source text, is your claim explicitly written?",
        "zuma_r2": "Notice carefully: the moment we test the primary source text of {p_primary}, the opposition retreats into abstract theological theories. When lexicons and syntax do not support your premise, why force meanings not found in the text?",
        "zuma_r3": "Hold your ground; do not move the goalposts. When the primary text of {p_primary} lacks your desired affirmation, jumping to other books is an evasion. Answer directly: is there an explicit verse supporting your claim?",
        "zuma_r4": "You appeal to parallel text {p_secondary}. Let us put the oldest manuscripts on the table! Philological facts prove that ancient source readings still reject your dogmatic presupposition. {zuma_rebuttal}",
        "zuma_r5": "You now face an inescapable fatal Socratic dilemma: if you accept {p_primary} verbatim, your doctrinal structure collapses; if you reject the text, you accuse the biblical author of error. Which horn of the dilemma do you take?",
        "zuma_r6": "That is an excuse, not a logical rebuttal. Employing Ilzam al-Khasm, I test your stance strictly using your own canon and premises. In {p_primary} and {p_secondary}, textual facts decisively refute your claim.",
        "zuma_r7": "The crux is laid bare! You have conceded that your stance is anchored not in canonical written facts, but in external dogmatic assumptions. Under philological scrutiny, claims without primary manuscript evidence collapse.",
        "zuma_r8": "Truth stands firm upon objective manuscript evidence. Across 8 rounds of rigorous discourse on '{motion}', the opposition failed to produce explicit evidence from {p_primary} or {p_secondary}. Primary manuscripts prevail!",
        "socratic_q": "Are you willing to acknowledge the primary written text of {p_primary} on the topic '{motion}' verbatim without smuggling assumptions outside the evidentiary standard?",
        "dilemma": "If you accept the text as written, your doctrinal premise collapses immediately; if you reject the text, you compromise scriptural integrity and your own internal consistency.",
        "presup": "The assumption that the opponent's position is immune to philological scrutiny and primary manuscript exegesis.",
        "verdict": "Simulated ZUMA dialectic establishes that in the {user_p} vs {opp_p} discourse on '{motion}', the opposing assertions disintegrate when confronted with verbatim readings of canonical text {p_primary} and internal consistency tests.",
        "superiority": "AFFIRMATIVE_CRITIQUE (ZUMA STRATEGIC COACHING FOR {user_p})"
    },
    "zh": {
        "motion_template": "对主张的原典文本与正典有效性法医审计: '{claim_clean}' ({p_primary})",
        "title_template": "神学与护教学论辩: {claim_clean}",
        "affirmative_stance": "原始圣经抄本的法医式检验与对无经文支持教条的彻底驳斥。",
        "negative_stance": "神学传统与教义诠释的辩护。",
        "opp_r1": {
            "islam": "审视关于 '{claim_clean}' 的命题，我们必须立足于众先知的纯正一神论（Tawhid）。任何神学观点都必须以独一造物主为最高检验标准，而非后世的哲学思辨。",
            "christian_protestant": "对我们而言，主张 '{claim_clean}' 必须放在圣经66卷正典的整体脉络中来理解。我们坚守唯独圣经（Sola Scriptura），让经文彼此互相光照与印证。",
            "christian_catholic": "若脱离使徒统绪和教父两千年来的共同见证，孤立阅读关于 '{claim_clean}' 的经文就会错失其深层意义。圣传与圣经构成了不可分割的统一信仰宝库。",
            "judaism": "对 '{claim_clean}' 的考察必须服从马所拉文本《塔纳赫》与西奈永约。妥拉的诫命是永恒的，任何后来的教导都无权废除神圣诫命（mitzvot）。",
            "atheist_secular": "关于 '{claim_clean}' 是一个非同寻常的主张，而非同寻常的主张必须有非同寻常的确凿证据（举证责任）。我们必须运用历史批判学与实证方法对其进行检验。"
        },
        "opp_rounds": {
            2: "[{opp_p}] 阅读 {p_primary} 必须置于我们神学诠释学的整体框架中加以理解。",
            3: "[{opp_p}] 我们必须考察整部圣经正典中的平行证据，而不是孤立分析单一子句。",
            4: "[{opp_p}] 我们数百年来的教义传统照亮了超越字面词典定义的深层属灵含义。",
            5: "[{opp_p}] 对方提出的困境是人为构造的；神圣奥秘超越了人类狭隘的三段论推演。",
            6: "[{opp_p}] 我们对 {p_primary} 的解释与历史信经及大公教会的共识完全契合。",
            7: "[{opp_p}] 系统神学在古代文本片段与当代活泼的规范教义之间搭建了桥梁。",
            8: "[{opp_p}] 我们坚守正典信仰传承，并将确信留给个人的理性良知。"
        },
        "zuma_r1": "我们用苏格拉底逻辑来审视今天的辩题：'{motion}'。就像查验房产契约一样，我们不能仅听口耳相传的故事，而必须亲自打开原始文件核对。请看 {p_primary} 的古代手抄本！我的苏格拉底提问很简单：在原始字句中，是否真有一字一句明确支持你的主张？",
        "zuma_r2": "请大家留意：一旦我们对照 {p_primary} 的源语言手抄本，对方立刻退缩到了复杂抽象的理论推演中。这就好比路牌上明明写着'禁止停车'，却有人硬辩解说它代表'可以停车'。当词典和原文句法根本不支持你的前提时，为何把原文未载的意思强加给经文？",
        "zuma_r3": "请先留步，不要转移争论焦点。当 {p_primary} 的成文文本并没有你所期待的内容时，你立刻急于跳到别的书卷。这就像证人被问及客厅发生的事情却总试图引向后院。请如实回答：在这段经文中，到底有没有明确字句支持你的说法？",
        "zuma_r4": "很好，你提到了平行经文 {p_secondary}。那我们就把原文词汇学和最古老的手抄本摆在台面上！事实证明，在最古老的手抄本文献中，源语言词汇学依然不支持你的预设。原典事实直接否定了现代推论。{zuma_rebuttal}",
        "zuma_r5": "现在你面临一个无可回避的苏格拉底致命困境：如果依照原文文法字面解读 {p_primary}，你的教义大厦立刻崩溃；但如果你拒绝接受字面经文，你便是在间接指责原作者误传了信息。面对这两种逻辑后果，你选择走哪条路？",
        "zuma_r6": "这不是正面的逻辑回答，而是辩解。运用立论归谬反诘法（Ilzam al-Khasm），我依据你自身经典的前提和正典来检验你的立场。在 {p_primary} 和 {p_secondary} 中，原典确立了清晰的文本事实。放弃自己正典的内在一致性在逻辑上是站不住脚的。",
        "zuma_r7": "核心关节点在这里彻底显露了！你最终承认了你的立论基石并非正典成文事实，而是后来附会上去的外在神学假定。在严肃的文献学审视中，缺乏原始手抄本支持的命题，在证据效力上只能归零。",
        "zuma_r8": "各位听众，真理始终屹立于客观的文本事实之上。在围绕 '{motion}' 的8轮深度论辩中，对方始终无法从 {p_primary} 或 {p_secondary} 中出示任何明确的经文实据。原始手抄本巍然屹立，缺乏经文支持的主张在理性检验下不攻自破！",
        "socratic_q": "关于主题 '{motion}'，你是否愿意逐字承认 {p_primary} 的原始成文文本，而不掺杂任何证据标准之外的先验假设？",
        "dilemma": "如果你按字面承认文本，对方的教义前提便立即崩溃；如果你拒绝字面经文，你便是在背弃经文自身的完整性与内在逻辑。",
        "presup": "对方立场可以免于文献学检验与原版手抄本释经审查的虚妄假设。",
        "verdict": "辩证模拟证实：在 {user_p} 对比 {opp_p} 关于 '{motion}' 的辩论中，当面对正典文本 {p_primary} 的逐字研读与内在一致性审查时，对方的主张彻底瓦解。",
        "superiority": "肯定性批判 (AFFIRMATIVE_CRITIQUE - ZUMA 针对 {user_p} 的策略指导)"
    },
    "it": {
        "motion_template": "Audit forense dei testi primari e validità canonica sull'affermazione: '{claim_clean}' ({p_primary})",
        "title_template": "Discorso Teologico e Apologetico: {claim_clean}",
        "affirmative_stance": "Audit forense dei manoscritti biblici primari e confutazione di dogmi privi di supporto scritturale.",
        "negative_stance": "Difesa della tradizione teologica e dell'interpretazione dottrinale.",
        "opp_r1": {
            "islam": "Esaminando la tesi su '{claim_clean}', dobbiamo partire dal principio del puro monoteismo (Tawhid) dei profeti: ogni dottrina divina deve riconoscere l'assoluta unicità di Dio senza associati, non speculazioni filosofiche successive.",
            "christian_protestant": "Per noi, l'affermazione '{claim_clean}' non può essere separata dall'intera rivelazione di Dio nei 66 libri della Bible. La nostra fede si fonda sulla Sola Scriptura, dove i testi si illuminano reciprocamente in modo organico.",
            "christian_catholic": "Valutare '{claim_clean}' solo da un testo isolato fa perdere la sua profondità. Ci affidiamo alla Tradizione apostolica e al consenso dei Padri della Chiesa che hanno custodito il deposito della fede per due millenni.",
            "judaism": "L'affermazione '{claim_clean}' deve essere esaminata davanti al Tanakh e all'eterna alleanza del Sinai. La legge della Torah è eterna e nessun nuovo insegnamento ha il diritto di annullare i comandamenti divini.",
            "atheist_secular": "L'affermazione '{claim_clean}' è una pretesa straordinaria che richiede prove altrettanto straordinarie (onere della prova). Dobbiamo testarla con il metodo storico-critico empirico, non presupposti dogmatici."
        },
        "opp_rounds": {
            2: "[{opp_p}] La lettura di {p_primary} richiede una sintesi olistica all'interno del nostro quadro ermeneutico teologico.",
            3: "[{opp_p}] Dobbiamo considerare i testimoni canonici paralleli in tutta la Scrittura anziché isolare singole frasi.",
            4: "[{opp_p}] La nostra tradizione dogmatica plurisecolare illumina il significato spirituale più profondo oltre le definizioni lessicali grezze.",
            5: "[{opp_p}] Il dilemma suggerito è artificiale; i misteri divini trascendono le dualità sillogistiche umane.",
            6: "[{opp_p}] Interpretiamo {p_primary} in armonia con i credi storici e il consenso ecclesiastico fondamentale.",
            7: "[{opp_p}] La teologia sistematica getta un ponte vitale tra frammenti testuali antichi e la dottrina normativa vivente.",
            8: "[{opp_p}] Rimaniamo saldi sul nostro patrimonio canonico e affidiamo il convincimento alla coscienza personale."
        },
        "zuma_r1": "Esaminiamo questo argomento con rigore: '{motion}'. Proprio come per un atto di proprietà, non possiamo fidarci solo di narrazioni orali, ma dobbiamo esaminare il testo primario originale! Osservate i manoscritti antichi di {p_primary}. La mia domanda socratica è semplice: nel testo originale è esplicitamente scritta la vostra affermazione?",
        "zuma_r2": "Notate con attenzione: non appena verifichiamo il testo sorgente di {p_primary}, la controparte si rifugia in teorie teologiche astratte. Quando i lessici e la sintassi non sostengono la vostra premessa, perché forzare significati assenti nel testo?",
        "zuma_r3": "Mantenete la posizione; non spostate i pali della discussione. Quando il testo primario di {p_primary} non contiene ciò che cercate, saltare ad altri libri è un'evasione. Rispondete direttamente: esiste un versetto esplicito a sostegno del vostro reclamo?",
        "zuma_r4": "Fate appello al testo parallelo {p_secondary}. Mettiamo i manoscritti più antichi sul tavolo! I dati filologici dimostrano che le lezioni più antiche continuano a smentire il vostro presupposto dogmatico. {zuma_rebuttal}",
        "zuma_r5": "Vi trovate ora davanti a un letale dilemma socratico: se accettate {p_primary} alla lettera, la vostra struttura dottrinale crolla; se rifiutate il testo, accusate l'autore biblico di errore. Quale corno del dilemma scegliete?",
        "zuma_r6": "Questa è una scusa, non una confutazione logica. Utilizzando il metodo dell'Ilzam al-Khasm, esamino la vostra posizione rigorosamente a partire dal vostro stesso canone. In {p_primary} e {p_secondary}, i fatti testuali confutano chiaramente la vostra tesi.",
        "zuma_r7": "Il punto cruciale è ormai evidente! Avete ammesso che la vostra posizione non si ancora a fatti canonici scritti, ma a postulati dogmatici esterni aggiunti in seguito. Sotto la lente filologica, affermazioni prive di manoscritti primari valgono zero.",
        "zuma_r8": "La verità poggia saldamente sui dati oggettivi dei manoscritti. Attraverso 8 round di rigoroso dibattito su '{motion}', la controparte non è riuscita a mostrare prove esplicite da {p_primary} né da {p_secondary}. I manoscritti primari prevalgono!",
        "socratic_q": "Siete disposti a riconoscere il testo scritto primario di {p_primary} sul tema '{motion}' alla lettera, senza introdurre presupposti esterni allo standard di prova?",
        "dilemma": "Se accettate il testo così com'è scritto, la premessa della controparte crolla immediatamente; se rifiutate il testo letterale, compromettete l'integrità del canone e la vostra stessa coerenza interna.",
        "presup": "L'assunto che la posizione della controparte sia immune dall'esame filologico e dall'esegesi dei manoscritti primari.",
        "verdict": "L'addebito dialettico forense dimostra che nel confronto {user_p} vs {opp_p} sul tema '{motion}', la metodologia critica smantella gli assunti della controparte se confrontata con la lettura letterale del testo canonico {p_primary} e con i test di coerenza interna.",
        "superiority": "AFFIRMATIVE_CRITIQUE (GUIDA STRATEGICA PER {user_p})"
    },
    "ar": {
        "motion_template": "التدقيق الفيلولوجي للنصوص الأولية والصحة القانونية للادعاء: '{claim_clean}' ({p_primary})",
        "title_template": "المناظرة اللاهوتية والدفاعية: {claim_clean}",
        "affirmative_stance": "التدقيق الجنائي في المخطوطات الأصلية للكتاب المقدس ودحض العقائد التي لا تستند إلى نصوص.",
        "negative_stance": "الدفاع عن التقليد اللاهوتي والتفسير العقائدي المنظومي.",
        "opp_r1": {
            "islam": "عند فحص القضية حول '{claim_clean}'، يجب أن ننطلق من التوحيد الخالص للأنبياء: كل عقيدة إلهية يجب أن تعترف بوحدانية الله المطلقة دون شريك، لا بنتائج التخمينات الفلسفية اللاحقة.",
            "christian_protestant": "بالنسبة لنا، لا يمكن فصل الادعاء '{claim_clean}' عن إعلان الله الكامل في أسفار الكتاب المقدس الستة والستين. إيماننا يقوم على مبدأ 'الكتاب وحده' حيث يفسر الكتاب نفسه بنفسه.",
            "christian_catholic": "تقييم العبارة '{claim_clean}' من نص معزول واحد يفقدها عمقها الحقيقي. نحن نستند إلى التقليد الرسولي المقدس وإجماع آباء الكنيسة على مدى ألفي عام.",
            "judaism": "يجب فحص القول '{claim_clean}' أمام التناخ والعهد الأبدي في سيناء. شريعة التوراة أبدية وليس لأي تعليم لاحق حق إلغاء الوصايا الإلهية.",
            "atheist_secular": "إن ادعاء '{claim_clean}' هو ادعاء استثنائي يتطلب أدلة استثنائية (عبء الإثبات). يجب اختباره بالمنهج التاريخي النقدي التجريبي وليس بالافتراضات العقائدية."
        },
        "opp_rounds": {
            2: "[{opp_p}] إن قراءة {p_primary} تتطلب فهماً شاملاً ضمن إطارنا التفسيري اللاهوتي العام.",
            3: "[{opp_p}] يجب علينا مراجعة الشواهد القانونية الموازية في سائر الأسفار بدلاً من عزل عبارة مفردة.",
            4: "[{opp_p}] تقليدنا العقائدي الممتد لقرون ينير المعنى الروحي الأعمق متجاوزاً التعريفات المعجمية الحرفية المجردة.",
            5: "[{opp_p}] المأزق المطروح مصطنع؛ فالأسرار الإلهية تعلو فوق ثنائيات القياس المنطقي البشري.",
            6: "[{opp_p}] نحن نفسر {p_primary} بتناغم مع قوانين الإيمان التاريخية والإجماع الكنسي التأسيسي.",
            7: "[{opp_p}] اللاهوت النظامي يبني جسراً حياً بين شذرات النصوص القديمة والعقيدة المعيارية الفاعلة.",
            8: "[{opp_p}] نحن نتمسك بثبات بتراثنا القانوني ونترك الاقتناع للضمير الفردي الحر."
        },
        "zuma_r1": "دعونا نفحص موضوع المناظرة اليوم: '{motion}'. تماماً مثل فحص صك الملكية، لا يمكننا الاعتماد على الروايات الشفهية، بل يجب فحص النص الأصلي المكتوب! انظر إلى المخطوطات القديمة لنص {p_primary}. سؤالي السقراطي بسيط: هل كُتب ادعاؤكم صراحة في النص الأصلي بحروفه؟",
        "zuma_r2": "لاحظوا بدقة: بمجرد فحص نص المصدر {p_primary}، يتراجع الخصم إلى نظريات لاهوتية مجردة. مثل لافتة واضحة تمنع الوقوف ولكن يُفسرها أحدهم بأنها تسمح به. لماذا تفرضون معاني غير موجودة في النص؟",
        "zuma_r3": "اثبتوا في مكانكم ولا تغيروا محور النقاش. عندما يعجز نص {p_primary} عن تقديم التأكيد الذي تريدونه، فإن القفز إلى أسفار أخرى يعد تهرباً. أجيبوا مباشرة: هل هناك آية صريحة تؤيد ادعاءكم؟",
        "zuma_r4": "أنتم تحتجون بالنص الموازي {p_secondary}. دعونا نضع أقدم المخطوطات على الطاولة! الحقائق اللغوية تثبت أن قراءات المخطوطات المبكرة ترفض افتراضكم العقائدي. {zuma_rebuttal}",
        "zuma_r5": "أنتم الآن في مواجهة مأزق سقراطي قاتل لا مفر منه: إذا قبلتم {p_primary} بحرفيته، تنهار بنيتكم العقائدية؛ وإذا رفضتم النص، تتهمون الكاتب بالخطأ. أي شقي المأزق تختارون؟",
        "zuma_r6": "هذا عذر وليس دحضاً منطقياً. باستخدام منهج إلزام الخصم، أختبر موقفكم بدقة من واقع قانونكم ومقدماتكم أنتم. في {p_primary} و {p_secondary}، تدحض الحقائق النصية ادعاءكم بشكل قاطع.",
        "zuma_r7": "لقد انكشفت النقطة الجوهرية! لقد اعترفتم بأن موقفكم لا يستند إلى وقائع قانونية مكتوبة، بل إلى افتراضات عقائدية خارجية أُضيفت لاحقاً. أمام المخطوطات الأصلية، تسقط الدعاوى المجردة.",
        "zuma_r8": "الحقيقة تقف شامخة فوق أدلة المخطوطات الموضوعية. على مدى 8 جولات من النقاش الصارم حول '{motion}'، عجز الخصم عن تقديم دليل صريح من {p_primary} أو {p_secondary}. المخطوطات الأصلية تنتصر دائماً!",
        "socratic_q": "هل أنتم مستعدون للاعتراف بالنص المكتوب الأصلي لنص {p_primary} حول موضوع '{motion}' بحرفيته دون دس افتراضات خارج معيار الإثبات؟",
        "dilemma": "إذا قبلتم النص كما هو مكتوب، تنهار مقدمتكم العقائدية فوراً؛ وإذا رفضتم النص، تفرطون في سلامة النص واتساقكم المنطقي الداخلي.",
        "presup": "الافتراض الباطل بأن موقف الخصم محصن ضد الفحص الفيلولوجي وتفسير المخطوطات الأصلية.",
        "verdict": "تثبت المحاكاة الجدلية أن ادعاءات الخصم في المناظرة بين {user_p} و {opp_p} حول '{motion}' تتلاشى تماماً أمام القراءة الحرفية للنص القانوني {p_primary} واختبارات الاتساق الداخلي.",
        "superiority": "AFFIRMATIVE_CRITIQUE (التوجيه الاستراتيجي لصالح {user_p})"
    },
    "tr": {
        "motion_template": "İddiaya İlişkin Birincil Metin ve Kanonik Geçerlilik Adli Denetimi: '{claim_clean}' ({p_primary})",
        "title_template": "Teolojik ve Savunma Söylemi: {claim_clean}",
        "affirmative_stance": "Birincil kutsal metin el yazmalarının adli denetimi ve metinsiz dogmaların çürütülmesi.",
        "negative_stance": "Teolojik geleneğin ve dogmatik tefsirin savunulması.",
        "opp_r1": {
            "islam": "'{claim_clean}' hakkındaki önermeyi incelerken, peygamberlerin katıksız Tevhid inancından yola çıkmalıyız: her ilahi öğreti, sonradan üretilen felsefi kurgulara değil, Tanrı'nın mutlak birliğine dayanmalıdır.",
            "christian_protestant": "Bizim için '{claim_clean}' iddiası Kutsal Kitap'ın 66 kitabındaki bütünsel vahiyden ayrılamaz. İmanımız, ayetlerin birbirini organik olarak aydınlattığı Sola Scriptura ilkesine dayanır.",
            "christian_catholic": "'{claim_clean}' ifadesini tek bir izole ayetten değerlendirmek derinliğini kaybettirir. İki bin yıldır iman emanetini koruyan elçisel Kutsal Geleneğe ve Kilise Babalarının mutabakatına güveniyoruz.",
            "judaism": "'{claim_clean}' iddiası Tanah ve Sina'daki ebedi antlaşma önünde sınanmalıdır. Tevrat yasası ebedidir ve sonraki hiçbir öğreti ilahi emirleri geçersiz kılma yetkisine sahip değildir.",
            "atheist_secular": "'{claim_clean}' önermesi, olağanüstü kanıt gerektiren olağanüstü bir iddiadır (ispat yükü). Bunu dogmatik varsayımlarla değil, ampirik tarihsel-eleştirel yöntemle test etmeliyiz."
        },
        "opp_rounds": {
            2: "[{opp_p}] {p_primary} metnini okumak, teolojik yorumbilim çerçevemiz içinde bütünsel bir sentez gerektirir.",
            3: "[{opp_p}] Tek bir cümleyi izole etmek yerine, kutsal yazılar genelindeki paralel kanonik tanıklıkları dikkate almalıyız.",
            4: "[{opp_p}] Asırlık dogmatik geleneğimiz, ham sözlük tanımlarının ötesindeki daha derin manevi anlamı aydınlatır.",
            5: "[{opp_p}] Öne sürülen ikilem yapaydır; ilahi gizemler insanların dar tasımsal ikiliklerini aşar.",
            6: "[{opp_p}] {p_primary} metnini tarihi amentüler ve temel kilise mutabakatı ile uyum içinde yorumluyoruz.",
            7: "[{opp_p}] Sistematik teoloji, antik metin parçaları ile yaşayan normatif öğreti arasında köprü kurar.",
            8: "[{opp_p}] Kanonik mirasımızın arkasında kararlılıkla duruyoruz ve vicdani kanaati bireylere bırakıyoruz."
        },
        "zuma_r1": "Bugünkü münazara konusunu inceleyelim: '{motion}'. Tıpkı bir mülk tapusunu inceler gibi, sadece sözlü anlatılara güvenemeyiz; orijinal birincil metni açmalıyız! {p_primary} antik el yazmalarına bakın. Sokratik sorum çok net: orijinal kaynak metinde iddianız açıkça ve harfiyen yazıyor mu?",
        "zuma_r2": "Lütfen dikkat edin: {p_primary} kaynak metnini inceler incelemez karşı taraf soyut teorilere sığınıyor. Tabelada açıkça 'Park Edilmez' yazarken sembolik olarak park edilebileceğini iddia etmek gibi. Sözlükler ve sözdizim desteklemezken metinde olmayan anlamları neden zorluyorsunuz?",
        "zuma_r3": "Konuyu saptırmayın. {p_primary} metni aradığınız ifadeyi içermediğinde diğer kitaplara atlamak bir kaçıştır. Doğrudan cevap verin: iddianızı açıkça destekleyen bir ayet var mı?",
        "zuma_r4": "Paralel ayet {p_secondary} metnine başvuruyorsunuz. En eski el yazmalarını masaya yatıralım! Filolojik gerçekler, en erken kaynak okumalarının bile dogmatik varsayımınızı reddettiğini kanıtlıyor. {zuma_rebuttal}",
        "zuma_r5": "Şimdi kaçınılmaz ölümcül bir Sokratik ikilemle karşı karşıyasınız: eğer {p_primary} metnini harfiyen kabul ederseniz dogmanız çöker; metni reddederseniz yazarını hatalı olmakla itham etmiş olursunuz. İkilemin hangi boynuzunu seçiyorsunuz?",
        "zuma_r6": "Bu bir mazerettir, mantıksal çürütme değil. İlzamü'l-Hasm yöntemini kullanarak, tutumunuzu kendi kutsal metinleriniz üzerinden sınıyorum. {p_primary} ve {p_secondary} metinlerinde açık metin gerçekleri iddianızı kesin olarak reddeder.",
        "zuma_r7": "Düğüm noktası burada açığa çıktı! Argümanınızın yazılı kanonik gerçeklere değil, sonradan eklenen dış dogmatik varsayımlara dayandığını itiraf ettiniz. Birincil el yazmaları karşısında dayanaksız iddiaların değeri sıfırdır.",
        "zuma_r8": "Hakikat, nesnel el yazması kanıtları üzerinde yükselir. '{motion}' konulu 8 rauntluk tartışmada karşı taraf {p_primary} veya {p_secondary} metninden açık tek bir kanıt sunamadı. Antik el yazmaları galip gelir!",
        "socratic_q": "'{motion}' konusu hakkında {p_primary} birincil yazılı metnini, kanıt standardı dışına çıkmadan harfiyen kabul etmeye hazır mısınız?",
        "dilemma": "Metni yazıldığı gibi kabul ederseniz dogmatik öncülünüz anında çöker; metni reddederseniz kutsal metnin bütünlüğünü ve kendi iç tutarlılığınızı çiğnemiş olursunuz.",
        "presup": "Karşı tarafın tutumunun filolojik incelemeden ve birincil el yazması tefsirinden muaf olduğu yanılgısı.",
        "verdict": "Diyalektik simülasyon, '{motion}' konusunda {user_p} ile {opp_p} arasındaki münazarada, {p_primary} kanonik metninin harfi okuması ve iç tutarlılık testleri karşısında karşı iddiaların çöktüğünü kanıtlar.",
        "superiority": "AFFIRMATIVE_CRITIQUE ({user_p} İÇİN STRATEJİK KOÇLUK)"
    },
    "ur": {
        "motion_template": "دعوے پر بنیادی متون اور قانونی درستگی کا فارنزک آڈٹ: '{claim_clean}' ({p_primary})",
        "title_template": "الہیاتی اور مناظرانہ مکالمہ: {claim_clean}",
        "affirmative_stance": "بنیادی بائبل کے مخطوطات کا فارنزک آڈٹ اور بغیر متن کے عقائد کی تردید۔",
        "negative_stance": "الہیاتی روایت اور عقائدی تشریح کا دفاع۔",
        "opp_r1": {
            "islam": "'{claim_clean}' کے قضیے کا جائزہ لیتے ہوئے، ہمیں انبیاء کی خالص توحید پر قائم رہنا چاہیے: ہر الہی عقیدے کو بغیر کسی شریک کے خدا کی وحدانیت کو تسلیم کرنا ہوگا، نہ کہ بعد کی فلسفیانہ قیاس آرائیوں کو۔",
            "christian_protestant": "ہمارے نزدیک، '{claim_clean}' کے بیان کو بائبل کی 66 کتب میں خدا کے مکمل مکاشفے سے الگ نہیں کیا جا سکتا۔ ہمارا ایمان سولا اسکرپچرا پر ہے جہاں آیات باہم نامیاتی طور پر ایک دوسرے کی وضاحت کرتی ہیں۔",
            "christian_catholic": "'{claim_clean}' کا جائزہ صرف ایک الگ تھلگ آیت سے لینا اس کی گہرائی کو ختم کر دیتا ہے۔ ہم رسولی مقدس روایت اور کلیسیائی آباء کے دو ہزار سالہ متفقہ مؤقف پر تکیہ کرتے ہیں۔",
            "judaism": "'{claim_clean}' کے دعوے کو تنخ اور سینا کے ابدی عہد کے سامنے جانچنا چاہیے۔ تورات کا قانون ابدی ہے اور کسی بھی بعد کی تعلیم کو الہی احکامات منسوخ کرنے کا کوئی حق نہیں۔",
            "atheist_secular": "'{claim_clean}' ایک غیر معمولی دعویٰ ہے جو غیر معمولی ثبوت کا تقاضا کرتا ہے (بارِ ثبوت)۔ ہمیں اس کی جانچ تجرباتی تاریخی-تنقیدی طریقہ کار سے کرنی چاہیے نہ کہ عقائدی مفروضات سے۔"
        },
        "opp_rounds": {
            2: "[{opp_p}] {p_primary} کو پڑھنا ہمارے مجموعی الہیاتی تشریحی فریم ورک کے اندر ہمہ جہت ترکیب کا متقاضی ہے۔",
            3: "[{opp_p}] ہمیں ایک فقرے کو الگ کرنے کے بجائے پورے صحیفے میں متوازی کتب کے شواہد پر غور کرنا چاہیے۔",
            4: "[{opp_p}] ہماری صدیوں پرانی عقائدی روایت خام لغوی تعریفوں سے بالاتر گہرے روحانی معانی کو واضح کرتی ہے۔",
            5: "[{opp_p}] پیش کردہ مخمصہ مصنوعی ہے؛ الہی اسرار انسانی قیاسی منطق کی حدود سے بالا تر ہیں۔",
            6: "[{opp_p}] ہم {p_primary} کی تشریح تاریخی عقائد اور کلیسیائی اتفاق رائے کے ساتھ مکمل ہم آہنگی میں کرتے ہیں۔",
            7: "[{opp_p}] باقاعدہ الہیات قدیم متنی ٹکڑوں اور زندہ معیاری عقیدے کے درمیان ایک پُل کا کام کرتی ہے۔",
            8: "[{opp_p}] ہم اپنے متنی ورثے پر ثابت قدمی سے کھڑے ہیں اور یقین کا معاملہ ذاتی ضمیر پر چھوڑتے ہیں۔"
        },
        "zuma_r1": "آئیے آج کے مناظرے کے موضوع کا جائزہ لیں: '{motion}'۔ جیسے جائیداد کی دستاویز کی تصدیق کی جاتی ہے، ہم زبانی باتوں پر انحصار نہیں کر سکتے بلکہ اصل متن کھولنا ہوگا! {p_primary} کے قدیم مخطوطات دیکھیں۔ میرا سقراطی سوال سادہ ہے: کیا اصل متن میں آپ کا دعویٰ حرف بہ حرف لکھا ہے؟",
        "zuma_r2": "غور کیجیے: جیسے ہی ہم {p_primary} کے بنیادی متن کا معائنہ کرتے ہیں، مخالف فریق تجریدی نظریات کی طرف بھاگتا ہے۔ بورڈ پر واضح طور پر 'پارکنگ منع ہے' لکھا ہو اور کوئی کہے کہ اس کا مطلب پارکنگ جائز ہے۔ جب لغات اور نحو ساتھ نہیں دیتیں تو غیر موجود معانی کیوں تھوپتے ہیں؟",
        "zuma_r3": "اپنی جگہ پر قائم رہیں اور موضوع مت بدلیں۔ جب {p_primary} میں آپ کا دعویٰ موجود نہیں ہے تو دوسری کتابوں کی طرف چھلانگ لگانا فرار ہے۔ براہِ راست جواب دیں: کیا کوئی واضح آیت موجود ہے؟",
        "zuma_r4": "آپ متوازی متن {p_secondary} کا حوالہ دیتے ہیں۔ آئیے قدیم ترین مخطوطات سامنے لائیں! لسانی حقائق ثابت کرتے ہیں کہ ابتدائی ترین نسخے بھی آپ کے مفروضے کو رد کرتے ہیں۔ {zuma_rebuttal}",
        "zuma_r5": "اب آپ ایک مہلک سقراطی مخمصے میں پھنس چکے ہیں: اگر آپ {p_primary} کو لفظ بہ لفظ تسلیم کرتے ہیں تو آپ کا عقیدہ منہدم ہو جاتا ہے؛ اگر آپ متن کو رد کرتے ہیں تو آپ مصنف پر غلط بیانی کا الزام لگاتے ہیں۔ آپ کون سا راستہ چنتے ہیں؟",
        "zuma_r6": "یہ ایک بہانہ ہے، کوئی منطقی جواب نہیں۔ الزام الخصم کا طریقہ کار استعمال کرتے ہوئے، میں آپ کے اپنے اصولوں پر آپ کا امتحان لیتا ہوں۔ {p_primary} اور {p_secondary} میں واضح متنی حقائق آپ کے دعوے کو قطعی طور پر باطل کرتے ہیں۔",
        "zuma_r7": "اصل نکتہ یہاں کھل کر سامنے آ گیا! آپ نے تسلیم کر لیا کہ آپ کا مؤقف تحریری متنی حقائق پر نہیں بلکہ بعد میں جوڑے گئے بیرونی عقائد پر مبنی ہے۔ بنیادی مخطوطات کے سامنے بے دلیل دعوے کی قیمت صفر ہے۔",
        "zuma_r8": "سچائی معروضی مخطوطاتی شواہد پر کھڑی ہے۔ '{motion}' پر 8 راؤنڈز کے مناظرے میں، مخالف فریق {p_primary} یا {p_secondary} سے کوئی صریح دلیل پیش نہ کر سکا۔ قدیم مخطوطات ہمیشہ غالب رہتے ہیں!",
        "socratic_q": "کیا آپ '{motion}' کے موضوع پر {p_primary} کے بنیادی تحریری متن کو بغیر کسی بیرونی مفروضے کے لفظ بہ لفظ تسلیم کرنے کو تیار ہیں؟",
        "dilemma": "اگر آپ متن کو ویسا ہی تسلیم کرتے ہیں جیسا کہ لکھا ہے تو آپ کا عقائدی مقدمہ فوراً منہدم ہو جاتا ہے؛ اگر آپ متن کو رد کرتے ہیں تو آپ صحیفے اور اپنی منطق کی مطابقت کو نقصان پہنچاتے ہیں۔",
        "presup": "یہ باطل مفروضہ کہ حریف کا مؤقف لسانی جانچ اور بنیادی مخطوطات کی تشریح سے مستثنیٰ ہے۔",
        "verdict": "مناظرانہ سمولیشن ثابت کرتی ہے کہ '{motion}' پر {user_p} بنام {opp_p} کے مکالمے میں، حریف کے تمام دعوے {p_primary} کے لفظی متن اور اندرونی مطابقت کے سامنے مکمل طور پر بکھر جاتے ہیں۔",
        "superiority": "AFFIRMATIVE_CRITIQUE ({user_p} کے لیے اسٹریٹجک رہنمائی)"
    },
    "fa": {
        "motion_template": "ممیزی قانونی متون اولیه و اعتبار قانونی ادعا: '{claim_clean}' ({p_primary})",
        "title_template": "گفتمان الهیاتی و دفاعیاتی: {claim_clean}",
        "affirmative_stance": "ممیزی قانونی دست‌نوشته‌های کهن کتاب مقدس و ابطال جزمیات فاقد سند متنی.",
        "negative_stance": "دفاع از سنت الهیاتی و تفسیر جزمی.",
        "opp_r1": {
            "islam": "در بررسی قضیه پیرامون '{claim_clean}'، باید بر توحید ناب پیامبران تکیه کنیم: هر آموزه الهی باید یگانگی مطلق خداوند را بدون شریک تصدیق کند، نه نظریه‌پردازی‌های فلسفی پسین را.",
            "christian_protestant": "برای ما، گزاره '{claim_clean}' از کل مکاشفه الهی در 66 کتاب کتاب مقدس تفکیک‌ناپذیر است. ایمان ما بر اصل سولا اسکریپچورا استوار است که در آن آیات یکدیگر را روشن می‌سازند.",
            "christian_catholic": "ارزیابی '{claim_clean}' صرفاً از یک آیه منفرد عمق آن را زائل می‌کند. ما به سنت مقدس رسولی و اجماع دو هزار ساله پدران کلیسا تکیه داریم.",
            "judaism": "ادعای '{claim_clean}' باید در پیشگاه تنخ و عهد جاودان سینا سنجیده شود. شریعت تورات ابدی است و هیچ آموزه بعدی حق لغو احکام الهی را ندارد.",
            "atheist_secular": "ادعای '{claim_clean}' ادعایی خارق‌العاده است که نیازمند شواهد خارق‌العاده می‌باشد (بار اثبات). ما باید آن را با روش تجربی تاریخی-انتقادی بسنجیم نه با پیش‌فرض‌های جزمی."
        },
        "opp_rounds": {
            2: "[{opp_p}] خوانش متن {p_primary} نیازمند سنتر همه‌جانبه در چارچوب هرمنوتیک الهیاتی ما است.",
            3: "[{opp_p}] ما باید شواهد موازی در سرتاسر کتب مقدس را مد نظر قرار دهیم نه اینکه یک عبارت منفرد را جدا کنیم.",
            4: "[{opp_p}] سنت جزمی چندین‌قرنی ما معنای عمیق روحانی را فراتر از تعاریف خام لغوی روشن می‌سازد.",
            5: "[{opp_p}] معضل مطرح‌شده ساختگی است؛ اسرار الهی از دوگانگی‌های قیاسی انسان فراتر می‌روند.",
            6: "[{opp_p}] ما {p_primary} را در هماهنگی کامل با اعتراف‌نامه‌های تاریخی و اجماع کلیسایی تفسیر می‌کنیم.",
            7: "[{opp_p}] الهیات نظام‌مند پلی میان قطعات متون کهن و آموزه‌های زنده هنجاری برقرار می‌سازد.",
            8: "[{opp_p}] ما بر میراث قانونی خود استوار می‌مانیم و داوری نهایی را به وجدان فردی واگذار می‌کنیم."
        },
        "zuma_r1": "بیایید موضوع مناظره امروز را بررسی کنیم: '{motion}'. درست مانند بررسی سند ملک، نمی‌توان به داستان‌های شفاهی بسنده کرد؛ باید متن اصلی را گشود! دست‌نوشته‌های کهن {p_primary} را ببینید. پرسش سقراطی من ساده است: آیا در متن اصیل، ادعای شما صراحتاً نوشته شده است؟",
        "zuma_r2": "دقت کنید: به محض بررسی متن اصلی {p_primary}، طرف مقابل به نظریات انتزاعی پناه می‌برد. مثل تابلویی که آشکارا پارک را ممنوع کرده اما کسی بگوید معنایش مجاز بودن است. وقتی لغت و نحو حمایت نمی‌کنند، چرا معانی ناموجود را تحمیل می‌کنید؟",
        "zuma_r3": "در موضع خود بایستید و موضوع را عوض نکنید. وقتی {p_primary} فاقد عبارت مورد نظر شماست، پریدن به کتاب‌های دیگر فرار است. مستقیماً پاسخ دهید: آیا آیه صریحی وجود دارد؟",
        "zuma_r4": "شما به متن موازی {p_secondary} متوسل می‌شوید. بیایید کهن‌ترین نسخه‌ها را روی میز بگذاریم! حقایق واژه‌شناختی اثبات می‌کنند که کهن‌ترین قرائت‌ها نیز پیش‌فرض شما را رد می‌کنند. {zuma_rebuttal}",
        "zuma_r5": "اکنون با یک معضل مرگبار سقراطی روبرو هستید: اگر {p_primary} را کلمه‌به‌کلمه بپذیرید، ساختار جزمی شما فرو می‌ریزد؛ و اگر متن را رد کنید، نویسنده را به خطا متهم ساخته‌اید. کدام شاخ معضل را برمی‌گزینید؟",
        "zuma_r6": "این یک بهانه است نه ابطال منطقی. با استفاده از روش الزام الخصم، موضع شما را با مقدمات خودتان می‌آزمایم. در {p_primary} و {p_secondary}، حقایق متنی ادعای شما را قاطعانه رد می‌کنند.",
        "zuma_r7": "نکته بنیادین آشکار شد! شما اعتراف کردید که موضع‌تان بر حقایق مکتوب استوار نیست بلکه بر فرضیات جزمی پسین بنا شده است. در برابر دست‌نوشته‌های کهن، ادعاهای بی‌پایه ارزشی ندارند.",
        "zuma_r8": "حقیقت بر پایه شواهد عینی دست‌نوشته‌ها استوار است. در طول 8 دور مناظره پیرامون '{motion}'، طرف مقابل نتوانست دلیلی صریح از {p_primary} یا {p_secondary} ارائه دهد. دست‌نوشته‌های کهن پیروزند!",
        "socratic_q": "آیا حاضرید متن مکتوب اصلی {p_primary} را درباره موضوع '{motion}' بدون تحمیل فرضیات بیرونی کلمه‌به‌کلمه بپذیرید؟",
        "dilemma": "اگر متن را همان‌گونه که نوشته شده بپذیرید، فرضیه جزمی شما بلافاصله فرو می‌ریزد؛ و اگر متن را رد کنید، انسجام درونی خود را تباه ساخته‌اید.",
        "presup": "این فرضیه باطل که موضع طرف مقابل از موشکافی فیلولوژیک و تفسیر دست‌نوشته‌های کهن مصون است.",
        "verdict": "شبیه‌سازی دیالکتیکی اثبات می‌کند که در مناظره میان {user_p} و {opp_p} پیرامون '{motion}'، ادعاهای طرف مقابل در برابر متن صریح {p_primary} و آزمون‌های سازگاری درونی کاملاً فرو می‌پاشد.",
        "superiority": "AFFIRMATIVE_CRITIQUE (هدایت راهبردی برای {user_p})"
    },
    "hi": {
        "motion_template": "दावे पर प्राथमिक पाठ और विहित वैधता का फोरेंसिक ऑडिट: '{claim_clean}' ({p_primary})",
        "title_template": "धर्मशास्त्रीय एवं प्रमाणिक विमर्श: {claim_clean}",
        "affirmative_stance": "प्राथमिक बाइबिल पांडुलिपियों का फोरेंसिक ऑडिट और पाठहीन सिद्धांतों का खंडन।",
        "negative_stance": "धर्मशास्त्रीय परंपरा और सैद्धांतिक व्याख्या का बचाव।",
        "opp_r1": {
            "islam": "'{claim_clean}' के प्रस्ताव की जांच करते समय, हमें पैगंबरों के शुद्ध एकेश्वरवाद (तौहीद) पर टिकना चाहिए: प्रत्येक दैवीय सिद्धांत को बिना किसी साझीदार के ईश्वर की पूर्ण एकता को स्वीकार करना चाहिए, न कि बाद के दार्शनिक अनुमानों को।",
            "christian_protestant": "हमारे लिए, '{claim_clean}' का दावा बाइबिल की 66 पुस्तकों में ईश्वर के संपूर्ण प्रकाशन से अलग नहीं किया जा सकता। हमारा विश्वास सोला स्क्रिप्चुरा पर आधारित है जहाँ आयतें एक दूसरे को प्रकाशित करती हैं।",
            "christian_catholic": "'{claim_clean}' का मूल्यांकन केवल एक अलग आयत से करने पर उसकी गहराई खो जाती है। हम प्रेरितिक परंपरा और दो हज़ार वर्षों से आस्था की रक्षा करने वाले कलीसियाई पिताओं की सर्वसम्मति पर भरोसा करते हैं।",
            "judaism": "'{claim_clean}' के दावे को तनाख और सीनै की शाश्वत वाचा के समक्ष परखा जाना चाहिए। तोराह की व्यवस्था शाश्वत है और किसी भी परवर्ती शिक्षा को दैवीय आज्ञाओं को रद्द करने का अधिकार नहीं है।",
            "atheist_secular": "'{claim_clean}' एक असाधारण दावा है जिसके लिए असाधारण साक्ष्य की आवश्यकता है (सबूत का भार)। हमें सैद्धांतिक पूर्वधारणाओं के बजाय अनुभवजन्य ऐतिहासिक-आलोचनात्मक पद्धति से इसका परीक्षण करना चाहिए।"
        },
        "opp_rounds": {
            2: "[{opp_p}] {p_primary} को पढ़ना हमारे समग्र धर्मशास्त्रीय ढांचे के भीतर समग्र संश्लेषण की मांग करता है।",
            3: "[{opp_p}] हमें किसी एक वाक्य को अलग-थलग करने के बजाय संपूर्ण धर्मग्रंथ में समानांतर विहित साक्ष्यों पर विचार करना चाहिए।",
            4: "[{opp_p}] हमारी सदियों पुरानी सैद्धांतिक परंपरा मूल शाब्दिक परिभाषाओं से परे गहरे आध्यात्मिक अर्थ को उजागर करती है।",
            5: "[{opp_p}] प्रस्तुत किया गया धर्मसंकट कृत्रिम है; दैवीय रहस्य मानवीय तर्कशास्त्र के द्वैत से परे हैं।",
            6: "[{opp_p}] हम ऐतिहासिक पंथों और कलीसियाई आम सहमति के साथ पूर्ण सामंजस्य में {p_primary} की व्याख्या करते हैं।",
            7: "[{opp_p}] व्यवस्थित धर्मशास्त्र प्राचीन पाठ्य अंशों और जीवंत मानक सिद्धांतों के बीच एक सेतु का काम करता है।",
            8: "[{opp_p}] हम अपनी विहित विरासत पर दृढ़ता से खड़े हैं और अंतिम विश्वास को व्यक्तिगत अंतरात्मा पर छोड़ते हैं।"
        },
        "zuma_r1": "आइए आज के वाद-विवाद के विषय की जांच करें: '{motion}'। जैसे किसी संपत्ति के दस्तावेज़ की जांच की जाती है, हम केवल मौखिक कहानियों पर निर्भर नहीं रह सकते, बल्कि मूल पाठ को खोलना होगा! {p_primary} की प्राचीन पांडुलिपियों को देखें। मेरा सुकराती प्रश्न सीधा है: क्या मूल पाठ में आपका दावा स्पष्ट रूप से लिखा है?",
        "zuma_r2": "ध्यान दें: जैसे ही हम {p_primary} के मूल पाठ की जांच करते हैं, विपक्षी पक्ष अमूर्त सिद्धांतों की शरण लेता है। सड़क पर 'नो पार्किंग' लिखा हो और कोई कहे कि इसका प्रतीकात्मक अर्थ पार्किंग है। जब शब्दकोष और व्याकरण समर्थन नहीं करते, तो अनपेक्षित अर्थ क्यों थोपते हैं?",
        "zuma_r3": "अपनी बात पर अडिग रहें और विषय न बदलें। जब {p_primary} में आपकी अपेक्षित पुष्टि नहीं है, तो अन्य पुस्तकों पर कूदना एक पलायन है। सीधा उत्तर दें: क्या कोई स्पष्ट आयत आपके दावे का समर्थन करती है?",
        "zuma_r4": "आप समानांतर पाठ {p_secondary} का उल्लेख करते हैं। आइए सबसे पुरानी पांडुलिपियों को मेज पर रखें! भाषावैज्ञानिक तथ्य सिद्ध करते हैं कि प्राचीन पाठ भी आपकी पूर्वधारणा को खारिज करते हैं। {zuma_rebuttal}",
        "zuma_r5": "अब आप एक अपरिहार्य सुकराती धर्मसंकट का सामना कर रहे हैं: यदि आप {p_primary} को शाब्दिक रूप से स्वीकार करते हैं, तो आपका सिद्धांत ढह जाता है; यदि आप पाठ को अस्वीकार करते हैं, तो आप लेखक पर त्रुटि का आरोप लगाते हैं। आप कौन सा मार्ग चुनते हैं?",
        "zuma_r6": "यह एक बहाना है, तार्किक खंडन नहीं। इल्ज़ाम अल-खसम पद्धति का उपयोग करते हुए, मैं आपके ही धर्मग्रंथ और मान्यताओं के आधार पर आपकी स्थिति का परीक्षण करता हूँ। {p_primary} और {p_secondary} में स्पष्ट पाठ्य तथ्य आपके दावे को पूरी तरह से नकारते हैं।",
        "zuma_r7": "मूल बिंदु यहाँ स्पष्ट हो गया है! आपने स्वीकार कर लिया है कि आपका रुख लिखित विहित तथ्यों पर नहीं, बल्कि बाद में जोड़ी गई बाहरी सैद्धांतिक मान्यताओं पर आधारित है। प्राथमिक पांडुलिपियों के सामने आधारहीन दावों का मूल्य शून्य है।",
        "zuma_r8": "सत्य वस्तुनिष्ठ पांडुलिपि साक्ष्यों पर दृढ़ता से खड़ा है। '{motion}' पर 8 चरणों के कठोर विमर्श में, विपक्षी पक्ष {p_primary} या {p_secondary} से कोई स्पष्ट प्रमाण प्रस्तुत नहीं कर सका। प्राचीन पांडुलिपियां विजयी हैं!",
        "socratic_q": "क्या आप '{motion}' के विषय पर {p_primary} के प्राथमिक लिखित पाठ को बिना किसी बाहरी पूर्वधारणा के शब्दशः स्वीकार करने को तैयार हैं?",
        "dilemma": "यदि आप पाठ को वैसा ही स्वीकार करते हैं जैसा वह लिखा है, तो आपकी सैद्धांतिक पूर्वधारणा तुरंत ढह जाती है; यदि आप पाठ को अस्वीकार करते हैं, तो आप पवित्रग्रंथ की अखंडता और अपने आंतरिक तर्क से समझौता करते हैं।",
        "presup": "यह भ्रामक धारणा कि विपक्षी स्थिति भाषावैज्ञानिक जांच और प्राथमिक पांडुलिपि व्याख्या से मुक्त है।",
        "verdict": "द्वंद्वात्मक अनुकरण सिद्ध करता है कि '{motion}' पर {user_p} बनाम {opp_p} के संवाद में, {p_primary} के शाब्दिक अध्ययन और आंतरिक सुसंगतता परीक्षणों के सामने विपक्षी दावे पूरी तरह से ध्वस्त हो जाते हैं।",
        "superiority": "AFFIRMATIVE_CRITIQUE ({user_p} के लिए रणनीतिक मार्गदर्शन)"
    },
    "bn": {
        "motion_template": "দাবির উপর প্রাথমিক মূলপাঠ এবং প্রামাণিক বৈধতার ফরেনসিক অডিট: '{claim_clean}' ({p_primary})",
        "title_template": "ধর্মতাত্ত্বিক ও আত্মপক্ষ সমর্থনমূলক বিতর্ক: {claim_clean}",
        "affirmative_stance": "প্রাথমিক বাইবেলীয় পাণ্ডুলিপির ফরেনসিক অডিট এবং পাঠ্যহীন মতবাদের খণ্ডন।",
        "negative_stance": "ধর্মতাত্ত্বিক ঐতিহ্য এবং মতবাদিক ব্যাখ্যার প্রতিরক্ষা।",
        "opp_r1": {
            "islam": "'{claim_clean}' বিষয়ক প্রস্তাবটি পরীক্ষা করার সময় আমাদের অবশ্যই নবীদের বিশুদ্ধ তাওহিদের উপর দাঁড়াতে হবে: প্রতিটি ঐশ্বরিক শিক্ষাকে অংশীদারবিহীন ঈশ্বরের পরম একত্বকে স্বীকার করতে হবে, পরবর্তী দার্শনিক জল্পনা-কল্পনাকে নয়।",
            "christian_protestant": "আমাদের জন্য, '{claim_clean}' দাবিটি বাইবেলের ৬৬টি পুস্তকের সামগ্রিক ঐশ্বরিক প্রকাশ থেকে বিচ্ছিন্ন করা যায় না। আমাদের বিশ্বাস সোলা স্ক্রিপ্টুরার উপর প্রতিষ্ঠিত যেখানে আয়াতগুলো একে অপরকে আলোকিত করে।",
            "christian_catholic": "একটিমাত্র বিচ্ছিন্ন পদ থেকে '{claim_clean}' মূল্যায়ন করলে তার গভীরতা হারিয়ে যায়। আমরা প্রেরিতীয় ঐতিহ্য এবং দুই হাজার বছর ধরে বিশ্বাস রক্ষা করা চার্চ ফাদারদের সর্বসম্মত মতের উপর নির্ভর করি।",
            "judaism": "'{claim_clean}' দাবিটি তানাক এবং সিনাই পর্বতের অনন্ত চুক্তির আলোকে পরীক্ষা করতে হবে। তোরাহের বিধান চিরন্তন এবং পরবর্তী কোনো শিক্ষার ঐশ্বরিক আদেশ বাতিল করার অধিকার নেই।",
            "atheist_secular": "'{claim_clean}' একটি অসাধারণ দাবি যার জন্য অসাধারণ প্রমাণের প্রয়োজন (প্রমাণের দায়)। আমাদের অবশ্যই মতবাদিক অনুমানের পরিবর্তে অভিজ্ঞতামূলক ঐতিহাসিক-সমালোচনামূলক পদ্ধতিতে এটি পরীক্ষা করতে হবে।"
        },
        "opp_rounds": {
            2: "[{opp_p}] {p_primary} পাঠ করা আমাদের ধর্মতাত্ত্বিক কাঠামোর মধ্যে একটি সামগ্রিক সংশ্লেষণ দাবি করে।",
            3: "[{opp_p}] একটি একক বাক্যাংশকে বিচ্ছিন্ন না করে সমগ্র শাস্ত্র জুড়ে সমান্তরাল প্রামাণিক সাক্ষ্য বিবেচনা করতে হবে।",
            4: "[{opp_p}] আমাদের শতবর্ষ প্রাচীন ঐতিহ্য কাঁচা আভিধানিক সংজ্ঞার ঊর্ধ্বে গভীর আধ্যাত্মিক অর্থকে আলোকিত করে।",
            5: "[{opp_p}] প্রস্তাবিত উভয়সংকট কৃত্রিম; ঐশ্বরিক রহস্য মানুষের সংকীর্ণ ন্যায়শাস্ত্রীয় দ্বৈততাকে অতিক্রম করে।",
            6: "[{opp_p}] আমরা ঐতিহাসিক ধর্মবিশ্বাস এবং চার্চের ঐকমত্যের সাথে পূর্ণ সামঞ্জস্য রেখে {p_primary} ব্যাখ্যা করি।",
            7: "[{opp_p}] নিয়মতান্ত্রিক ধর্মতত্ত্ব প্রাচীন পাঠ্যাংশ এবং জীবন্ত আদর্শ মতবাদের মধ্যে একটি সেতুবন্ধন রচনা করে।",
            8: "[{opp_p}] আমরা আমাদের ঐতিহ্যের উপর অবিচলভাবে দাঁড়িয়ে আছি এবং চূড়ান্ত প্রত্যয়কে ব্যক্তিগত বিবেকের উপর ছেড়ে দিচ্ছি।"
        },
        "zuma_r1": "আসুন আজকের বিতর্কের বিষয়টি পরীক্ষা করি: '{motion}'। সম্পত্তির দলিল যাচাই করার মতো, আমরা কেবল মুখের কথার উপর নির্ভর করতে পারি না, বরং মূল পাণ্ডুলিপি খুলতে হবে! {p_primary}-এর প্রাচীন পাণ্ডুলিপিগুলো দেখুন। আমার সক্রেটিসীয় প্রশ্নটি সহজ: মূল পাঠে কি আপনার দাবিটি স্পষ্টভাবে লেখা আছে?",
        "zuma_r2": "লক্ষ্য করুন: {p_primary}-এর মূল পাঠ পরীক্ষা করার সাথে সাথেই প্রতিপক্ষ বিমূর্ত তত্ত্বের আশ্রয় নেয়। সাইনবোর্ডে পরিষ্কারভাবে 'পার্কিং নিষেধ' লেখা থাকলে কেউ যদি দাবি করে প্রতীকী অর্থে পার্কিং বৈধ। যখন অভিধান ও ব্যাকরণ সমর্থন করে না, তখন অপ্রাসঙ্গিক অর্থ কেন চাপিয়ে দিচ্ছেন?",
        "zuma_r3": "আপনার অবস্থানে স্থির থাকুন এবং বিষয় পরিবর্তন করবেন না। যখন {p_primary}-এ আপনার দাবির প্রমাণ নেই, তখন অন্য বইয়ে চলে যাওয়া একটি পলায়নপরতা। সরাসরি উত্তর দিন: এই পাঠ্যাংশে কি আপনার দাবির সমর্থনে কোনো স্পষ্ট আয়াত আছে?",
        "zuma_r4": "আপনি সমান্তরাল পদ {p_secondary}-এর উল্লেখ করছেন। আসুন প্রাচীনতম পাণ্ডুলিপিগুলো টেবিলে রাখি! ভাষাতাত্ত্বিক তথ্য প্রমাণ করে যে প্রাচীন পাঠগুলোও আপনার মতবাদকে প্রত্যাখ্যান করে। {zuma_rebuttal}",
        "zuma_r5": "এখন আপনি একটি মারাত্মক সক্রেটিসীয় উভয়সংকটের মুখোমুখি: আপনি যদি {p_primary} আক্ষরিকভাবে গ্রহণ করেন তবে আপনার মতবাদ ভেঙে পড়ে; আর পাঠটি প্রত্যাখ্যান করলে আপনি লেখককে ভুলের জন্য অভিযুক্ত করেন। আপনি কোন পথটি বেছে নেবেন?",
        "zuma_r6": "এটি একটি অজুহাত, যৌক্তিক খণ্ডন নয়। ইলজাম আল-খাসম পদ্ধতি ব্যবহার করে, আমি আপনার নিজস্ব শাস্ত্র ও প্রাঙ্গণের ভিত্তিতে আপনার অবস্থান পরীক্ষা করছি। {p_primary} এবং {p_secondary}-এ সুস্পষ্ট পাঠ্যগত সত্য আপনার দাবিকে সরাসরি খণ্ডন করে।",
        "zuma_r7": "আসল সত্যটি এখানে উন্মোচিত হয়েছে! আপনি স্বীকার করেছেন যে আপনার যুক্তি লিখিত প্রামাণিক তথ্যের উপর নয়, বরং পরবর্তীতে যুক্ত করা বহিরাগত মতবাদের উপর প্রতিষ্ঠিত। প্রাচীন পাণ্ডুলিপির সামনে ভিত্তিহীন দাবির মূল্য শূন্য।",
        "zuma_r8": "সত্য বস্তুনিষ্ঠ পাণ্ডুলিপির প্রমাণের উপর প্রতিষ্ঠিত। '{motion}' নিয়ে ৮ রাউন্ডের কঠোর বিতর্কে প্রতিপক্ষ {p_primary} বা {p_secondary} থেকে কোনো সুস্পষ্ট প্রমাণ দেখাতে ব্যর্থ হয়েছে। প্রাচীন পাণ্ডুলিপি চিরকাল বিজয়ী!",
        "socratic_q": "আপনি কি '{motion}' বিষয়ে {p_primary}-এর প্রাথমিক লিখিত মূলপাঠকে কোনো বহিরাগত অনুমান ছাড়াই অক্ষরে অক্ষরে স্বীকার করতে প্রস্তুত?",
        "dilemma": "আপনি যদি পাঠটি যেভাবে লেখা আছে সেভাবে মেনে নেন, তবে আপনার মতবাদ তৎক্ষণাৎ ধসে পড়ে; আর যদি পাঠটি প্রত্যাখ্যান করেন, তবে আপনি শাস্ত্রের অখণ্ডতা এবং আপনার নিজস্ব যুক্তির সামঞ্জস্যকে বিনষ্ট করেন।",
        "presup": "এই ভ্রান্ত ধারণা যে প্রতিপক্ষের অবস্থান ভাষাতাত্ত্বিক পরীক্ষা এবং প্রাচীন পাণ্ডুলিপির ব্যাখ্যা থেকে মুক্ত।",
        "verdict": "দ্বান্দ্বিক সিমুলেশন প্রমাণ করে যে '{motion}' বিষয়ে {user_p} বনাম {opp_p}-এর বিতর্কে, {p_primary}-এর আক্ষরিক পাঠ এবং অভ্যন্তরীণ সামঞ্জস্য পরীক্ষার মুখোমুখি হলে প্রতিপক্ষের দাবিগুলো সম্পূর্ণ চূর্ণবিচূর্ণ হয়ে যায়।",
        "superiority": "AFFIRMATIVE_CRITIQUE ({user_p}-এর জন্য কৌশলগত দিকনির্দেশনা)"
    },
    "ja": {
        "motion_template": "主張に対する原典テキストおよび正典的妥当性の科学的監査: '{claim_clean}' ({p_primary})",
        "title_template": "神学的および弁証論的対話: {claim_clean}",
        "affirmative_stance": "聖書原典写本の科学的検証およびテキスト的根拠のない教条の論駁。",
        "negative_stance": "神学的伝統および教理的解釈の擁護。",
        "opp_r1": {
            "islam": "'{claim_clean}' に関する命題を検討するにあたり、預言者たちの純粋な一神教（タウヒード）に立脚しなければなりません。あらゆる神学的主張は唯一の創造主を絶対的な基準とすべきであり、後代の哲学的思弁であってはなりません。",
            "christian_protestant": "私たちにとって、'{claim_clean}' という主張は聖書66巻全体の神の啓示から切り離すことはできません。私たちの信仰は、聖書が聖書自身を解釈するという『聖書のみ（Sola Scriptura）』に基づいています。",
            "christian_catholic": "孤立した1つの聖句から '{claim_clean}' を判断すると、その本質的な深みを見失います。私たちは使徒的聖伝と、二千年にわたり信仰の遺産を守り抜いてきた教父たちの合意に依拠しています。",
            "judaism": "'{claim_clean}' という主張はタナハおよびシナイの永遠の契約に照らして吟味されなければなりません。トーラーの掟は永遠であり、後代のいかなる教えも神聖な戒めを無効化する権利を持ちません。",
            "atheist_secular": "'{claim_clean}' という命題は非日常的な主張であり、並外れた証拠を必要とします（立証責任）。私たちは教条的な前提ではなく、実証的な歴史批評学的方法によってこれを検証しなければなりません。"
        },
        "opp_rounds": {
            2: "[{opp_p}] {p_primary} の読解は、私たちの包括的な神学解釈学的枠組みの中で総合的に捉える必要があります。",
            3: "[{opp_p}] 単一の句を孤立させて切り取るのではなく、正典全体にわたる並行情景を考慮しなければなりません。",
            4: "[{opp_p}] 何世紀にもわたる私たちの教理的伝統は、単なる辞書的定義を超えた深い霊的意義を解き明かします。",
            5: "[{opp_p}] 提示されたジレンマは人為的なものです。神の神秘は人間の狭い三段論法の二項対立を超越しています。",
            6: "[{opp_p}] 私たちは歴史的信条および教会的合意と完全に調和させて {p_primary} を解釈しています。",
            7: "[{opp_p}] 組織神学は、古代の断片テキストと現代の規範的教理との間に生きた架け橋を築きます。",
            8: "[{opp_p}] 私たちは正典の伝統に固く立ち、最終的な確信は個人の良心に委ねます。"
        },
        "zuma_r1": "本日の討論テーマを検証しましょう: '{motion}'。土地の権利証書を確認するのと同様に、伝聞だけに頼るのではなく、原典テキストそのものを開かねばなりません！ {p_primary} の古代写本をご覧ください。私のソクラテス的問いは単純です。原典テキストに、貴方の主張が明確に書かれていますか？",
        "zuma_r2": "ご覧ください。{p_primary} の原典テキストを検証した途端、相手側は抽象的な理論へと逃避します。標識に明確に『駐車禁止』とあるのに象徴的には駐車可能だと強弁するようなものです。辞書も統語論も支持していないのに、なぜ書かれていない意味を押し付けるのですか？",
        "zuma_r3": "論点を逸らさないでください。{p_primary} の本文に貴方の求める記述がないからといって、他の書へ飛び移るのは論点回避です。率直にお答えください。貴方の主張を明示的に肯定する節がそこにあるのですか？",
        "zuma_r4": "貴方は並行箇所 {p_secondary} に訴えます。ならば最古の写本をテーブルに載せましょう！文献学的証拠は、初期の原典読みが貴方の教理的前提を拒絶していることを証明しています。{zuma_rebuttal}",
        "zuma_r5": "今や貴方は逃れられない致命的なソクラテス的ジレンマに直面しています。{p_primary} を文字通り認めるなら教理は崩壊し、テキストを拒否するなら聖書著者が誤っていたと非難することになります。どちらを選びますか？",
        "zuma_r6": "それは言い訳であり論理的反論ではありません。相手の前提に立つ論駁法（イルザーム・アル＝ハスム）を用い、貴方自身の正典に基づいて検証します。{p_primary} と {p_secondary} において、原典の事実は貴方の主張を明確に否定しています。",
        "zuma_r7": "核心が露わになりました！貴方の論拠が書かれた正典の事実ではなく、後から付け足された外部の教条的前提にすぎないことを自ら認めたのです。原典写本の証拠の前では、根拠のない主張の価値はゼロです。",
        "zuma_r8": "真理は客観的な写本証拠の上に堅固に立ちます。'{motion}' をめぐる8ラウンドの徹底討論において、相手側は {p_primary} や {p_secondary} から何ら明確な証拠を提示できませんでした。古代写本こそが揺るぎなく勝利します！",
        "socratic_q": "'{motion}' という主題について、立証基準外の前提を持ち込むことなく、{p_primary} の一次文献テキストを文字通り認める用意がありますか？",
        "dilemma": "書かれている通りにテキストを認めるなら貴方の教理的前提は直ちに崩壊し、文字通りのテキストを拒否するなら正典の完全性と自己の論理的一貫性を損なうことになります。",
        "presup": "相手側の立場が言語学的精査や一次写本の解釈から免除されているという根拠なき前提。",
        "verdict": "弁証シミュレーションは、'{motion}' に関する {user_p} 対 {opp_p} の議論において、正典テキスト {p_primary} の文字通りの読解と内的一貫性の検証に直面したとき、相手の主張が完全に崩壊することを実証しました。",
        "superiority": "AFFIRMATIVE_CRITIQUE ({user_p} のための戦略的指導)"
    },
    "ko": {
        "motion_template": "주장에 대한 원전 텍스트 및 정경적 타당성 법의학적 감사: '{claim_clean}' ({p_primary})",
        "title_template": "신학적 및 변증론적 담론: {claim_clean}",
        "affirmative_stance": "성경 원전 사본의 법의학적 감사 및 본문 없는 교조의 논박.",
        "negative_stance": "신학적 전통 및 교리적 해석의 변호.",
        "opp_r1": {
            "islam": "'{claim_clean}'에 대한 명제를 검토할 때 우리는 예언자들의 순수한 유일신론(타우히드)에 서야 합니다. 모든 신성한 교리는 후대의 철학적 사변이 아니라 동반자 없는 하나님의 절대적 유일성을 인정해야 합니다.",
            "christian_protestant": "우리에게 있어 '{claim_clean}'라는 주장은 성경 66권 전체의 하나님의 계시와 분리될 수 없습니다. 우리의 믿음은 성경이 성경을 스스로 해석한다는 '오직 성경(Sola Scriptura)'에 기초합니다.",
            "christian_catholic": "단 하나의 고립된 구절로 '{claim_clean}'을 평가하는 것은 그 본질적인 깊이를 잃게 만듭니다. 우리는 2천 년 동안 믿음의 유산을 지켜온 사도적 성전(전승)과 교부들의 일치된 합의에 의존합니다.",
            "judaism": "'{claim_clean}'이라는 주장은 타나크와 시내산의 영원한 언약 앞에서 검증되어야 합니다. 토라의 율법은 영원하며 후대의 어떤 가르침도 신성한 계명을 폐기할 권한이 없습니다.",
            "atheist_secular": "'{claim_clean}'이라는 명제는 비범한 주장이므로 비범한 증거를 요구합니다(입증 책임). 우리는 교조적 전제가 아니라 경험적 역사비평학적 방법론으로 이를 검증해야 합니다."
        },
        "opp_rounds": {
            2: "[{opp_p}] {p_primary} 본문을 읽는 것은 우리의 신학적 해석학 틀 내에서 총체적인 종합을 필요로 합니다.",
            3: "[{opp_p}] 단일 문구를 고립시키는 대신 성경 전체에 걸친 평행한 정경적 증언들을 고려해야 합니다.",
            4: "[{opp_p}] 수 세기에 걸친 우리의 교리적 전통은 원시적인 사전적 정의를 넘어서는 깊은 영적 의미를 밝혀줍니다.",
            5: "[{opp_p}] 제시된 딜레마는 인위적인 것입니다. 신성한 신비는 인간의 편협한 삼단논법적 이분법을 초월합니다.",
            6: "[{opp_p}] 우리는 역사적 신조 및 교회의 근본적인 합의와 완벽한 조화를 이루며 {p_primary}을 해석합니다.",
            7: "[{opp_p}] 조직신학은 고대 본문 파편과 살아있는 규범적 교리 사이에 살아있는 다리를 놓아줍니다.",
            8: "[{opp_p}] 우리는 정경적 유산 위에 굳건히 서 있으며 최종적인 확신은 개인의 양심에 맡깁니다."
        },
        "zuma_r1": "오늘의 토론 주제를 검증해 봅시다: '{motion}'. 부동산 문서를 확인하는 것처럼 우리는 구전 이야기에만 의존할 수 없으며 본래의 원전 텍스트를 직접 열어보아야 합니다! {p_primary}의 고대 사본을 보십시오. 저의 소크라테스적 질문은 단순합니다. 원전 텍스트에 당신의 주장이 문자 그대로 명시되어 있습니까?",
        "zuma_r2": "주목하십시오. {p_primary}의 원전을 검증하자마자 상대방은 추상적인 이론으로 도피합니다. 표지판에 '주차 금지'라고 명시되어 있는데 상징적으로 주차 가능하다고 강변하는 격입니다. 사전과 구문론이 지지하지 않는데 왜 본문에 없는 의미를 강요합니까?",
        "zuma_r3": "논점을 흐리지 마십시오. {p_primary}의 본문에 원하는 내용이 없다고 해서 다른 책으로 건너뛰는 것은 명백한 회피입니다. 직접 답하십시오. 당신의 주장을 명시적으로 긍정하는 구절이 거기에 있습니까?",
        "zuma_r4": "당신은 평행 구절 {p_secondary}에 호소합니다. 가장 오래된 사본들을 확인해 봅시다! 문헌학적 사실은 초기 사본 독법 역시 당신의 교리적 전제를 거부하고 있음을 증명합니다. {zuma_rebuttal}",
        "zuma_r5": "이제 당신은 피할 수 없는 치명적인 소크라테스적 딜레마에 직면했습니다. 만약 {p_primary}을 문자 그대로 인정하면 교리가 무너지고, 본문을 거부하면 성경 저자가 오류를 범했다고 비난하게 됩니다. 어느 쪽을 선택하겠습니까?",
        "zuma_r6": "그것은 변명일 뿐 논리적 반박이 아닙니다. 상대의 전제를 무너뜨리는 귀류 논박(Ilzam al-Khasm)을 사용하여 당신 자신의 정경과 전제에 입각해 검증합니다. {p_primary}와 {p_secondary}에서 원전의 사실은 당신의 주장을 결정적으로 반박합니다.",
        "zuma_r7": "핵심이 명백히 드러났습니다! 당신의 주장이 기록된 정경적 사실이 아니라 후대에 덧붙여진 외부 교조적 가정에 의존하고 있음을 인정한 것입니다. 원전 사본 앞에서 근거 없는 주장의 가치는 전무합니다.",
        "zuma_r8": "진리는 객관적인 사본 증거 위에 굳건히 서 있습니다. '{motion}'에 관한 8라운드의 치열한 논쟁 속에서 상대방은 {p_primary}이나 {p_secondary}에서 어떠한 명시적 증거도 제시하지 못했습니다. 고대 사본이 승리합니다!",
        "socratic_q": "'{motion}'이라는 주제에 대해 증명 기준 밖의 전제를 도입하지 않고 {p_primary}의 일차적 기록 텍스트를 문자 그대로 인정할 용의가 있습니까?",
        "dilemma": "본문에 기록된 대로 인정한다면 당신의 교리적 전제는 즉각 붕괴하며, 문자적 본문을 거부한다면 정경의 온전성과 당신 자신의 내적 일관성을 훼손하게 됩니다.",
        "presup": "상대방의 입장이 문헌학적 정밀 검사와 일차 사본 주석으로부터 면제되어 있다는 헛된 가정.",
        "verdict": "변증 시뮬레이션은 '{motion}'에 관한 {user_p} 대 {opp_p}의 토론에서, 정경 텍스트 {p_primary}의 문자적 독해와 내적 일관성 검증에 직면했을 때 상대의 주장이 완전히 붕괴됨을 입증합니다.",
        "superiority": "AFFIRMATIVE_CRITIQUE ({user_p}를 위한 전략적 지도)"
    },
    "es": {
        "motion_template": "Auditoría Forense de Textos Primarios y Validez Canónica sobre la Afirmación: '{claim_clean}' ({p_primary})",
        "title_template": "Discurso Teológico y Apologético: {claim_clean}",
        "affirmative_stance": "Auditoría forense de manuscritos bíblicos primarios y refutación de dogmas sin sustento escritural.",
        "negative_stance": "Defensa de la tradición teológica y de la interpretación dogmática.",
        "opp_r1": {
            "islam": "Al examinar la proposición sobre '{claim_clean}', debemos partir del puro monoteísmo (Tawhid) dos profetas: toda doctrina divina debe reconocer la absoluta unicidad de Dios sin asociados, no especulaciones filosóficas posteriores.",
            "christian_protestant": "Para nosotros, la afirmación '{claim_clean}' no puede separarse de la revelación completa de Dios en los 66 libros de la Bible. Nuestra fe descansa en Sola Scriptura, donde las escrituras se iluminan mutuamente de manera orgánica.",
            "christian_catholic": "Evaluar '{claim_clean}' a partir de un texto aislado hace perder su profundidad. Nos apoyamos en la Sagrada Tradición apostólica y en el consenso de los Padres de la Iglesia que custodiaron el depósito de la fe durante dos milenios.",
            "judaism": "La afirmación '{claim_clean}' debe ser probada ante el Tanaj y el pacto eterno en el Sinaí. La ley de la Torá es eterna y ninguna enseñanza posterior tiene autoridad para anular los mandamientos divinos.",
            "atheist_secular": "La proposición '{claim_clean}' es una afirmación extraordinaria que exige evidencia extraordinaria (carga de la prueba). Debemos probarla mediante metodología histórico-crítica empírica, no con presuposiciones dogmáticas."
        },
        "opp_rounds": {
            2: "[{opp_p}] Leer {p_primary} requiere una síntesis holística dentro de nuestro marco hermenéutico teológico.",
            3: "[{opp_p}] Debemos considerar testigos canónicos paralelos en toda la Escritura en lugar de aislar una sola frase.",
            4: "[{opp_p}] Nuestra tradición dogmática multisecular ilumina el significado espiritual más profundo más allá de definiciones léxicas brutas.",
            5: "[{opp_p}] El dilema planteado es artificial; los misterios divinos trascienden las dualidades silogísticas humanas.",
            6: "[{opp_p}] Interpretamos {p_primary} en armonía con los credos históricos y el consenso eclesiástico fundacional.",
            7: "[{opp_p}] La teología sistemática tiende un puente vivo entre fragmentos textuales antiguos y la doctrina normativa viviente.",
            8: "[{opp_p}] Permanecemos firmes en nuestra herencia canónica y dejamos la convicción a la conciencia personal."
        },
        "zuma_r1": "Examinemos la moción del debate de hoy: '{motion}'. Al igual que al verificar el título de una propiedad, no podemos conformarnos con relatos orales; ¡debemos examinar el texto primario original! Observen los manuscritos antiguos de {p_primary}. Mi pregunta socrática es sencilla: en el texto fuente original, ¿está explícitamente escrita su afirmación?",
        "zuma_r2": "Observen atentamente: en cuanto examinamos el texto fuente de {p_primary}, la oposición se refugia en teorías teológicas abstractas. Es como ver un cartel que dice claramente 'Prohibido Estacionar' y pretender que significa que está permitido. Cuando los léxicos y la sintaxis no apoyan su premisa, ¿por qué forzar significados que no están en el texto?",
        "zuma_r3": "Mantengan su postura; no muevan los postes del debate. Cuando el texto primario de {p_primary} no contiene la afirmación que buscan, saltar a otros libros es una evasión. Respondan directamente: ¿existe un versículo explícito que respalde su postura?",
        "zuma_r4": "Ustedes apelan al pasaje paralelo {p_secondary}. ¡Pongamos los manuscritos más antiguos sobre la mesa! Los hechos filológicos demuestran que las lecturas tempranas siguen rechazando su presuposición dogmática. {zuma_rebuttal}",
        "zuma_r5": "Se enfrentan ahora a un dilema socrático mortal e ineludible: si aceptan {p_primary} literalmente, su estructura dogmática colapsa; si rechazan el texto, acusan al autor bíblico de error. ¿Qué cuerno del dilema eligen?",
        "zuma_r6": "Eso es una excusa, no una refutación lógica. Empleando el método Ilzam al-Khasm, pongo a prueba su postura utilizando estrictamente su propio canon y premisas. En {p_primary} y {p_secondary}, los hechos textuales refutan categóricamente su afirmación.",
        "zuma_r7": "¡El punto crucial ha quedado al descubierto! Han concedido que su postura no se ancla en hechos canónicos escritos, sino en presupuestos dogmáticos externos añadidos con posterioridad. Ante los manuscritos primarios, las afirmaciones sin texto valen cero.",
        "zuma_r8": "La verdad se mantiene firme sobre la evidencia objetiva de los manuscritos. A lo largo de 8 rondas de riguroso debate sobre '{motion}', la oposición no pudo presentar evidencia explícita de {p_primary} ni de {p_secondary}. ¡Los manuscritos antiguos prevalecen!",
        "socratic_q": "¿Está dispuesto a reconocer el texto escrito primario de {p_primary} sobre el tema '{motion}' literalmente sin introducir presupuestos ajenos al estándar de prueba?",
        "dilemma": "Si acepta el texto tal como está escrito, su premisa doctrinal colapsa de inmediato; si rechaza el texto escrito, compromete la integridad de la Escritura y su propia coherencia interna.",
        "presup": "La presuposición infundada de que la postura de la oposición es inmune al escrutinio filológico y a la exégesis de manuscritos primarios.",
        "verdict": "La simulación dialéctica demuestra que en el debate {user_p} vs {opp_p} sobre '{motion}', las afirmaciones contrarias se desmoronan frente a la lectura literal del texto canónico {p_primary} y las pruebas de coherencia interna.",
        "superiority": "AFFIRMATIVE_CRITIQUE (ORIENTACIÓN ESTRATÉGICA PARA {user_p})"
    },
    "fr": {
        "motion_template": "Audit médico-légal des textes primaires et validité canonique sur l'affirmation: '{claim_clean}' ({p_primary})",
        "title_template": "Discours Théologique et Apologétique: {claim_clean}",
        "affirmative_stance": "Audit médico-légal des manuscrits bibliques primaires et réfutation des dogmes sans fondement textuel.",
        "negative_stance": "Défense de la tradition théologique et de l'interprétation dogmatique.",
        "opp_r1": {
            "islam": "En examinant la proposition sur '{claim_clean}', nous devons nous fonder sur le pur monothéisme (Tawhid) des prophètes : toute doctrine divine doit reconnaître l'unicité absolue de Dieu sans associés, et non des spéculations philosophiques ultérieures.",
            "christian_protestant": "Pour nous, l'affirmation '{claim_clean}' ne peut être dissociée de la révélation divine complète dans les 66 livres de la Bible. Notre foi repose sur Sola Scriptura où les écritures s'éclairent mutuellement de façon organique.",
            "christian_catholic": "Évaluer '{claim_clean}' à partir d'un texte isolé lui fait perdre sa profondeur. Nous nous appuyons sur la sainte Tradition apostolique et le consensus des Pères de l'Église qui ont gardé le dépôt de la foi pendant deux millénaires.",
            "judaism": "L'affirmation '{claim_clean}' doit être examinée devant le Tanakh et l'alliance éternelle du Sinaï. La loi de la Torah est éternelle et aucun enseignement ultérieur n'a le pouvoir d'annuler les commandements divins.",
            "atheist_secular": "La proposition '{claim_clean}' est une affirmation extraordinaire exigeant des preuves extraordinaires (charge de la preuve). Nous devons l'éprouver par la méthode historico-critique empirique, non par des présupposés dogmatiques."
        },
        "opp_rounds": {
            2: "[{opp_p}] Lire {p_primary} exige une synthèse holistique au sein de notre cadre herméneutique théologique.",
            3: "[{opp_p}] Nous devons considérer les témoins canoniques parallèles dans toute l'Écriture plutôt que d'isoler une seule phrase.",
            4: "[{opp_p}] Notre tradition dogmatique multiséculaire éclaire le sens spirituel profond au-delà des définitions lexicales brutes.",
            5: "[{opp_p}] Le dilemme proposé est artificiel ; les mystères divins transcendent les dualismes syllogistiques humains.",
            6: "[{opp_p}] Nous interprétons {p_primary} en harmonie avec les credos historiques et le consensus ecclésial fondateur.",
            7: "[{opp_p}] La théologie systématique établit un pont vivant entre les fragments textuels anciens et la doctrine normative vivante.",
            8: "[{opp_p}] Nous demeurons fermes sur notre héritage canonique et laissons la conviction à la conscience personnelle."
        },
        "zuma_r1": "Examinons la motion du débat d'aujourd'hui : '{motion}'. Tout comme pour l'acte de propriété d'un bien, nous ne pouvons nous fier à de simples récits oraux ; nous devons ouvrir le texte primaire original ! Observez les manuscrits anciens de {p_primary}. Ma question socratique est simple : dans le texte source original, votre affirmation est-elle explicitement écrite mot à mot ?",
        "zuma_r2": "Remarquez bien : dès que nous vérifions le texte source de {p_primary}, la partie adverse se réfugie dans des théories abstraites. C'est comme un panneau indiquant 'Stationnement interdit' que l'on prétendrait autoriser le stationnement. Pourquoi imposer au texte un sens qui n'y figure pas ?",
        "zuma_r3": "Restez sur vos positions et ne déplacez pas le débat. Lorsque le texte primaire de {p_primary} ne contient pas ce que vous cherchez, sauter à d'autres livres est une esquive. Répondez directement : y a-t-il un verset explicite appuyant votre thèse ?",
        "zuma_r4": "Vous invoquez le passage parallèle {p_secondary}. Mettons les manuscrits les plus anciens sur la table ! Les faits philologiques prouvent que les leçons manuscrites primitives réfutent toujours votre présupposition dogmatique. {zuma_rebuttal}",
        "zuma_r5": "Vous faites face à un dilemme socratique mortel et inéluctable : si vous acceptez {p_primary} à la lettre, votre édifice dogmatique s'effondre ; si vous rejetez le texte, vous accusez l'auteur biblique d'erreur. Quelle branche du dilemme choisissez-vous ?",
        "zuma_r6": "C'est un prétexte, non une réfutation logique. En appliquant la méthode Ilzam al-Khasm, j'éprouve votre position à partir de votre propre canon. Dans {p_primary} et {p_secondary}, les faits textuels réfutent catégoriquement votre thèse.",
        "zuma_r7": "Le point crucial est désormais évident ! Vous avez concédé que votre position ne s'ancre pas dans des faits canoniques écrits, mais dans des postulats dogmatiques externes plaqués ultérieurement. Face aux manuscrits primaires, les affirmations sans texte valent zéro.",
        "zuma_r8": "La vérité repose solidement sur les données objectives des manuscrits. Au cours des 8 rounds de débat rigoureux sur '{motion}', l'opposition a été incapable de produire une preuve explicite tirée de {p_primary} ou de {p_secondary}. Les manuscrits anciens triomphent !",
        "socratic_q": "Êtes-vous prêt à reconnaître le texte écrit primaire de {p_primary} sur le thème '{motion}' à la lettre sans introduire d'hypothèses extérieures aux normes de preuve ?",
        "dilemma": "Si vous acceptez le texte tel qu'il est écrit, votre prémisse doctrinale s'effondre immédiatement ; si vous rejetez le texte, vous compromettez l'intégrité de l'Écriture et votre propre cohérence interne.",
        "presup": "L'hypothèse erronée selon laquelle la position de l'opposition serait immunisée contre l'examen philologique et l'exégèse des manuscrits primaires.",
        "verdict": "La simulation dialectique prouve que dans le débat {user_p} contre {opp_p} sur '{motion}', les assertions adverses s'effondrent face à la lecture littérale du texte canonique {p_primary} et aux tests de cohérence interne.",
        "superiority": "AFFIRMATIVE_CRITIQUE (GUIDAGE STRATÉGIQUE POUR {user_p})"
    },
    "pt": {
        "motion_template": "Auditoria Forense de Textos Primários e Validade Canônica sobre a Alegação: '{claim_clean}' ({p_primary})",
        "title_template": "Discurso Teológico e Apologético: {claim_clean}",
        "affirmative_stance": "Auditoria forense de manuscritos bíblicos primários e refutação de dogmas sem respaldo escriturístico.",
        "negative_stance": "Defesa da tradição teológica e da interpretação dogmática.",
        "opp_r1": {
            "islam": "Ao examinar a proposição sobre '{claim_clean}', devemos nos firmar no puro monoteísmo (Tawhid) dos profetas: toda doutrina divina deve reconhecer a absoluta unicidade de Deus sem associados, e não especulações filosóficas posteriores.",
            "christian_protestant": "Para nós, a afirmação '{claim_clean}' não pode ser separada da revelação completa de Deus nos 66 livros da Bible. Nossa fé repousa no Sola Scriptura, onde as escrituras se iluminam mutuamente de forma orgânica.",
            "christian_catholic": "Avaliar '{claim_clean}' a partir de um texto isolado faz perder sua profundidade. Nós nos apoiamos na Sagrada Tradição apostólica e no consenso dos Padres da Igreja que guardaram o depósito da fé por dois milênios.",
            "judaism": "A alegação '{claim_clean}' deve ser testada diante do Tanakh e da aliança eterna no Sinai. A lei da Torá é eterna e nenhum ensinamento posterior tem autoridade para anular os mandamentos divinos.",
            "atheist_secular": "A proposição '{claim_clean}' é uma alegação extraordinária que exige evidências extraordinárias (ônus da prova). Devemos testá-la através do método histórico-crítico empírico, e não por pressuposições dogmáticas."
        },
        "opp_rounds": {
            2: "[{opp_p}] A leitura de {p_primary} requer uma síntese holística dentro de nossa estrutura hermenêutica teológica.",
            3: "[{opp_p}] Devemos considerar testemunhas canônicas paralelas em toda a Escritura em vez de isolar uma única frase.",
            4: "[{opp_p}] Nossa tradição dogmática secular ilumina o significado espiritual mais profundo além das definições lexicais brutas.",
            5: "[{opp_p}] O dilema sugerido é artificial; os mistérios divinos transcendem as dualidades silogísticas humanas.",
            6: "[{opp_p}] Interpretamos {p_primary} em harmonia com os credos históricos e o consenso eclesiástico fundamental.",
            7: "[{opp_p}] A teologia sistemática estabelece uma ponte viva entre fragmentos textuais antigos e a doutrina normativa viva.",
            8: "[{opp_p}] Permanecemos firmes em nossa herança canônica e deixamos a convicção para a consciência individual."
        },
        "zuma_r1": "Examinemos a moção do debate de hoje: '{motion}'. Assim como ao verificar uma escritura de imóvel, não podemos confiar apenas em relatos orais; devemos abrir o texto primário original! Observem os manuscritos antigos de {p_primary}. Minha pergunta socrática é simples: no texto original, a sua alegação está explicitamente escrita palavra por palavra?",
        "zuma_r2": "Notem bem: assim que examinamos o texto fonte de {p_primary}, a oposição se refugia em teorias teológicas abstratas. É como uma placa que diz claramente 'Proibido Estacionar' e alguém argumentar que significa permissão. Quando léxicos e sintaxe não apoiam sua premissa, por que forçar significados ausentes no texto?",
        "zuma_r3": "Mantenham sua posição e não desviem o foco do debate. Quando o texto primário de {p_primary} não contém o que vocês buscam, pular para outros livros é uma evasiva. Respondam diretamente: existe um versículo explícito que sustente sua alegação?",
        "zuma_r4": "Vocês apelam ao texto paralelo {p_secondary}. Vamos colocar os manuscritos mais antigos sobre a mesa! Fatos filológicos provam que as leituras manuscritas mais remotas continuam rejeitando sua pressuposição dogmática. {zuma_rebuttal}",
        "zuma_r5": "Vocês agora enfrentam um dilema socrático mortal e inescapável: se aceitarem {p_primary} literalmente, sua estrutura dogmática desmorona; se rejeitarem o texto, acusam o autor bíblico de erro. Qual chifre do dilema escolhem?",
        "zuma_r6": "Isso é uma desculpa, não uma refutação lógica. Empregando o método Ilzam al-Khasm, testo a sua posição a partir do seu próprio cânon. Em {p_primary} e {p_secondary}, os fatos textuais refutam categoricamente a sua afirmação.",
        "zuma_r7": "O ponto crucial ficou exposto! Vocês admitiram que sua postura não se apoia em fatos canônicos escritos, mas em suposições dogmáticas externas sobrepostas posteriormente. Diante dos manuscritos primários, alegações sem texto valem zero.",
        "zuma_r8": "A verdade permanece firme sobre as evidências objetivas dos manuscritos. Ao longo de 8 rodadas de debate rigoroso sobre '{motion}', a oposição não conseguiu apresentar provas explícitas de {p_primary} nem de {p_secondary}. Os manuscritos antigos prevalecem!",
        "socratic_q": "Você está disposto a reconhecer o texto escrito primário de {p_primary} sobre o tema '{motion}' literalmente, sem introduzir pressupostos fora do padrão de prova?",
        "dilemma": "Se você aceitar o texto como está escrito, sua premissa doutrinária desmorona imediatamente; se rejeitar o texto literal, compromete a integridade da Escritura e sua própria coerência lógica.",
        "presup": "A suposição infundada de que a posição da oposição está imune ao escrutínio filológico e à exegese de manuscritos primários.",
        "verdict": "A simulação dialética comprova que no debate {user_p} vs {opp_p} sobre '{motion}', as alegações contrárias desmoronam diante da leitura literal do texto canônico {p_primary} e dos testes de coerência interna.",
        "superiority": "AFFIRMATIVE_CRITIQUE (ORIENTAÇÃO ESTRATÉGICA PARA {user_p})"
    },
    "de": {
        "motion_template": "Forensische Primärtext- und kanonische Gültigkeitsprüfung des Anspruchs: '{claim_clean}' ({p_primary})",
        "title_template": "Theologischer und Apologetischer Diskurs: {claim_clean}",
        "affirmative_stance": "Forensische Prüfung primärer biblischer Handschriften und Widerlegung textloser Dogmen.",
        "negative_stance": "Verteidigung der theologischen Tradition und dogmatischen Auslegung.",
        "opp_r1": {
            "islam": "Bei der Prüfung des Satzes über '{claim_clean}' müssen wir vom reinen Monotheismus (Tawhid) der Propheten ausgehen: Jede göttliche Lehre muss die absolute Einheit Gottes ohne Teilhaber anerkennen, nicht spätere philosophische Spekulationen.",
            "christian_protestant": "Für uns kann die Aussage '{claim_clean}' nicht von Gottes Gesamtoffenbarung in den 66 Büchern der Bible getrennt werden. Unser Glaube ruht auf Sola Scriptura, wo sich Schriftstellen gegenseitig organisch erhellen.",
            "christian_catholic": "Die Bewertung von '{claim_clean}' anhand eines isolierten Textes verliert ihre Tiefe. Wir stützen uns auf die apostolische Heilige Tradition und den Konsens der Kirchenväter, die das Glaubensgut zwei Jahrtausende lang bewahrten.",
            "judaism": "Die Behauptung '{claim_clean}' muss vor dem Tanach und dem ewigen Bund am Sinai geprüft werden. Das Gesetz der Tora ist ewig und keine spätere Lehre hat die Vollmacht, göttliche Gebote aufzuheben.",
            "atheist_secular": "Die These '{claim_clean}' ist eine außergewöhnliche Behauptung, die außergewöhnliche Beweise erfordert (Beweislast). Wir müssen sie mit empirischen historisch-kritischen Methoden prüfen, nicht mit dogmatischen Vorannahmen."
        },
        "opp_rounds": {
            2: "[{opp_p}] Das Lesen von {p_primary} erfordert eine ganzheitliche Synthese innerhalb unseres theologisch-hermeneutischen Rahmens.",
            3: "[{opp_p}] Wir müssen parallele kanonische Zeugen in der gesamten Schrift berücksichtigen, anstatt einzelne Sätze zu isolieren.",
            4: "[{opp_p}] Unsere jahrhundertealte dogmatische Tradition erhellt die tiefere geistliche Bedeutung jenseits bloßer lexikalischer Definitionen.",
            5: "[{opp_p}] Das vorgebrachte Dilemma ist künstlich; göttliche Geheimnisse übersteigen menschliche syllogistische Dualismen.",
            6: "[{opp_p}] Wir legen {p_primary} in Übereinstimmung mit den historischen Bekenntnissen und dem kirchlichen Konsens aus.",
            7: "[{opp_p}] Die Systematische Theologie schlägt eine lebendige Brücke zwischen antiken Textfragmenten und lebendiger normativer Lehre.",
            8: "[{opp_p}] Wir stehen fest zu unserem kanonischen Erbe und überlassen die Überzeugung dem persönlichen Gewissen."
        },
        "zuma_r1": "Prüfen wir das heutige Debattenthema: '{motion}'. Wie bei der Überprüfung einer Eigentumsurkunde können wir uns nicht auf mündliche Erzählungen verlassen; wir müssen den ursprünglichen Primärtext öffnen! Betrachten Sie die antiken Handschriften von {p_primary}. Meine sokratische Frage ist einfach: Steht Ihre Behauptung im ursprünglichen Quelltext wörtlich geschrieben?",
        "zuma_r2": "Beachten Sie genau: Sobald wir den Quelltext von {p_primary} prüfen, weicht die Gegenseite in abstrakte Theorien aus. Wie ein Schild mit der Aufschrift 'Parken verboten', das man als Parkerlaubnis umdeuten will. Wenn Wörterbücher und Syntax Ihre Prämisse nicht stützen, warum erzwingen Sie Bedeutungen, die nicht im Text stehen?",
        "zuma_r3": "Bleiben Sie auf Ihrem Standpunkt; verschieben Sie nicht die Torpfosten. Wenn der Primärtext von {p_primary} Ihre Behauptung nicht enthält, ist der Sprung zu anderen Büchern eine Ausflucht. Antworten Sie direkt: Gibt es einen expliziten Vers, der Ihre Behauptung stützt?",
        "zuma_r4": "Sie berufen sich auf den Paralleltext {p_secondary}. Legen wir die ältesten Handschriften auf den Tisch! Philologische Fakten beweisen, dass die frühesten Handschriftenlesarten Ihre dogmatische Vorannahme weiterhin ablehnen. {zuma_rebuttal}",
        "zuma_r5": "Sie stehen nun vor einem unvermeidlichen fatalen sokratischen Dilemma: Wenn Sie {p_primary} wörtlich akzeptieren, bricht Ihr Dogma zusammen; wenn Sie den Text ablehnen, werfen Sie dem biblischen Verfasser Irrtum vor. Welches Horn des Dilemmas wählen Sie?",
        "zuma_r6": "Das ist eine Ausrede, keine logische Widerlegung. Nach der Methode des Ilzam al-Khasm prüfe ich Ihre Position strikt anhand Ihres eigenen Kanons. In {p_primary} und {p_secondary} widerlegen eindeutige Textfakten Ihren Anspruch.",
        "zuma_r7": "Der springende Punkt liegt offen zutage! Sie haben eingeräumt, dass Ihre Haltung nicht auf geschriebenen kanonischen Fakten beruht, sondern auf nachträglich übergestülpten dogmatischen Annahmen. Vor primären Handschriften sind unbegründete Behauptungen wertlos.",
        "zuma_r8": "Die Wahrheit steht fest auf objektiven Handschriftenbeweisen. In 8 Runden strenger Debatte über '{motion}' konnte die Gegenseite weder aus {p_primary} noch aus {p_secondary} einen expliziten Beweis vorlegen. Die antiken Handschriften siegen!",
        "socratic_q": "Sind Sie bereit, den primären geschriebenen Text von {p_primary} zum Thema '{motion}' wörtlich anzuerkennen, ohne Annahmen außerhalb des Beweisstandards einzuschmuggeln?",
        "dilemma": "Wenn Sie den Text so anerkennen, wie er geschrieben steht, bricht Ihre dogmatische Prämisse sofort zusammen; wenn Sie den geschriebenen Text ablehnen, verletzen Sie die Integrität der Schrift und Ihre eigene innere Logik.",
        "presup": "Die unbegründete Annahme, dass die Position der Gegenseite vor philologischer Prüfung und Primärhandschriften-Exegese gefeit sei.",
        "verdict": "Die dialektische Simulation beweist, dass im Diskurs {user_p} vs. {opp_p} über '{motion}' die gegnerischen Behauptungen vor der wörtlichen Lesart des kanonischen Textes {p_primary} und internen Konsistenzprüfungen vollständig zerfallen.",
        "superiority": "AFFIRMATIVE_CRITIQUE (STRATEGISCHE ANLEITUNG FÜR {user_p})"
    },
    "ru": {
        "motion_template": "Текстуально-критический аудит и каноническая проверка утверждения: '{claim_clean}' ({p_primary})",
        "title_template": "Богословский и апологетический дискурс: {claim_clean}",
        "affirmative_stance": "Судебно-текстологический аудит первичных библейских рукописей и опровержение безбиблейских догм.",
        "negative_stance": "Защита богословской традиции и догматического толкования.",
        "opp_r1": {
            "islam": "Исследуя утверждение о '{claim_clean}', мы должны исходить из чистого единобожия (Таухид) пророков: любая божественная доктрина должна признавать абсолютное единство Бога без сотоварищей, а не позднейшие философские спекуляции.",
            "christian_protestant": "Для нас утверждение '{claim_clean}' неразрывно связано со всем Божественным откровением в 66 книгах Библии. Наша вера зиждется на принципе Sola Scriptura, где тексты органично истолковывают друг друга.",
            "christian_catholic": "Оценка тезиса '{claim_clean}' лишь по одному изолированному стиху лишает его глубины. Мы опираемся на апостольское Священное Предание и двухтысячелетнее согласие Отцов Церкви, сохранивших залог веры.",
            "judaism": "Утверждение '{claim_clean}' должно быть испытано перед лицом Танаха и вечного Синайского завета. Закон Торы вечен, и никакое последующее учение не имеет права отменять божественные заповеди.",
            "atheist_secular": "Тезис '{claim_clean}' — это экстраординарное утверждение, требующее столь же экстраординарных доказательств (бремя доказательства). Мы должны проверять его эмпирическим историко-критическим методом, а не догматическими предпосылками."
        },
        "opp_rounds": {
            2: "[{opp_p}] Чтение {p_primary} требует целостного синтеза в рамках нашей богословско-герменевтической парадигмы.",
            3: "[{opp_p}] Мы обязаны рассматривать параллельные канонические свидетельства во всем Писании, а не изолировать отдельные фразы.",
            4: "[{opp_p}] Наша многовековая догматическая традиция раскрывает глубокий духовный смысл, превосходящий буквальные словарные определения.",
            5: "[{opp_p}] Предложенная дилемма искусственна; божественные тайны превосходят ограниченные рамки человеческого силлогизма.",
            6: "[{opp_p}] Мы истолковываем {p_primary} в совершенном согласии с историческими вероопределениями и соборным консенсусом.",
            7: "[{opp_p}] Систематическое богословие возводит живой мост между древними текстовыми фрагментами и нормативным учением.",
            8: "[{opp_p}] Мы твердо стоим на нашем каноническом наследии и оставляем убеждение на суд личной совести."
        },
        "zuma_r1": "Обратимся к теме сегодняшних дебатов: '{motion}'. Подобно проверке подлинности правоустанавливающего документа, мы не можем довольствоваться устными рассказами; мы обязаны открыть первичный исходный текст! Взгляните на древние рукописи {p_primary}. Мой сократический вопрос прост: написано ли ваше утверждение буквально и явно в оригинальном тексте?",
        "zuma_r2": "Обратите внимание: как только мы обращаемся к рукописям {p_primary}, оппонент тут же уходит в область абстрактных теорий. Это всё равно что на знаке 'Стоянка запрещена' пытаться доказать обратное. Если словари и синтаксис не поддерживают вашу посылку, зачем навязывать тексту то, чего в нем нет?",
        "zuma_r3": "Держите позицию и не смещайте фокус спора. Если в первичном тексте {p_primary} нет подтверждения вашего тезиса, переход к другим книгам — это уклонение. Ответьте прямо: есть ли там хоть один явный стих в пользу вашего утверждения?",
        "zuma_r4": "Вы ссылаетесь на параллельный текст {p_secondary}. Давайте положим на стол древнейшие рукописи! Текстологические факты доказывают, что ранние рукописные чтения по-прежнему отвергают вашу догматическую предпосылку. {zuma_rebuttal}",
        "zuma_r5": "Вы оказались перед смертоносной сократической дилеммой: если вы признаете {p_primary} буквально, ваша доктрина рушится; если отвергнете текст, вы обвините библейского автора в ошибке. Какой рог дилеммы вы выберете?",
        "zuma_r6": "Это оправдание, а не логическое опровержение. Применяя метод Ильзам аль-Хасм, я испытываю вашу позицию исключительно на основании вашего же канона. В {p_primary} и {p_secondary} факты первоисточника категорически опровергают ваш тезис.",
        "zuma_r7": "Главный узел обнажен! Вы признали, что ваша позиция держится не на писаных канонических фактах, а на внешних догматических предположениях, наложенных позже. Перед лицом первичных рукописей утверждения без текста равны нулю.",
        "zuma_r8": "Истина непоколебимо стоит на объективных рукописных свидетельствах. За 8 раундов строгой дискуссии о '{motion}' оппонент не смог предъявить ни одного явного доказательства из {p_primary} или {p_secondary}. Древние манускрипты торжествуют!",
        "socratic_q": "Готовы ли вы признать первичный письменный текст {p_primary} по теме '{motion}' буквально, без привнесения предпосылок, выходящих за рамки доказательного стандарта?",
        "dilemma": "Если вы признаете текст в том виде, как он написан, ваша доктринальная посылка немедленно рушится; если отвергнете текст, вы разрушите авторитет Писания и собственную логическую согласованность.",
        "presup": "Ложное допущение о том, что позиция оппонента якобы защищена от филологической критики и экзегезы первичных рукописей.",
        "verdict": "Диалектическое моделирование доказывает, что в дискурсе {user_p} против {opp_p} по теме '{motion}' утверждения оппонента полностью разрушаются при сопоставлении с буквальным чтением канонического текста {p_primary} и проверками на внутреннюю непротиворечивость.",
        "superiority": "AFFIRMATIVE_CRITIQUE (СТРАТЕГИЧЕСКОЕ РУКОВОДСТВО ДЛЯ {user_p})"
    }
}


def get_debate_dialogue_localized(
    loc: str,
    user_p: str,
    opp_p: str,
    claim_clean: str,
    p_primary: str,
    p_secondary: str,
    motion: str,
    zuma_rebuttal: str,
    has_custom_persp: bool
) -> dict:
    loc_key = (loc or "id").strip().lower()
    for prefix in ["zh", "id", "it", "ar", "tr", "ur", "fa", "hi", "bn", "ja", "ko", "es", "fr", "pt", "de", "ru", "en"]:
        if loc_key.startswith(prefix):
            loc_key = prefix
            break
    if loc_key not in DEBATE_DIALOGUE_I18N:
        loc_key = "en"

    base = DEBATE_DIALOGUE_I18N.get(loc_key, DEBATE_DIALOGUE_I18N["en"])

    opp_dict = base.get("opp_r1", {})
    opp_r1_speech = opp_dict.get(opp_p.lower(), f"[{opp_p.upper()}] asserts its traditional dogmatic interpretation regarding '{claim_clean}'.")
    if "{claim_clean}" in opp_r1_speech:
        opp_r1_speech = opp_r1_speech.format(claim_clean=claim_clean)

    zuma_r1 = base["zuma_r1"].format(motion=motion, p_primary=p_primary)
    zuma_r2 = base["zuma_r2"].format(p_primary=p_primary)
    zuma_r3 = base["zuma_r3"].format(p_primary=p_primary)
    zuma_r4 = base["zuma_r4"].format(p_secondary=p_secondary, zuma_rebuttal=zuma_rebuttal)
    zuma_r5 = base["zuma_r5"].format(p_primary=p_primary)
    zuma_r6 = base["zuma_r6"].format(p_primary=p_primary, p_secondary=p_secondary)
    zuma_r7 = base["zuma_r7"]
    zuma_r8 = base["zuma_r8"].format(motion=motion, p_primary=p_primary, p_secondary=p_secondary)

    # Localized perspective speeches for rounds 2 to 8
    opp_rounds_dict = base.get("opp_rounds", {})
    opp_speeches = {1: opp_r1_speech}
    for rnd in range(2, 9):
        tmpl = opp_rounds_dict.get(rnd, f"[{opp_p.upper()}] Defense round {rnd}")
        opp_speeches[rnd] = tmpl.format(opp_p=opp_p.upper(), p_primary=p_primary, p_secondary=p_secondary)

    zuma_speeches = {
        1: zuma_r1,
        2: zuma_r2,
        3: zuma_r3,
        4: zuma_r4,
        5: zuma_r5,
        6: zuma_r6,
        7: zuma_r7,
        8: zuma_r8
    }

    socratic_q = base["socratic_q"].format(p_primary=p_primary, motion=motion)
    dilemma = base["dilemma"]
    presup = base["presup"]
    verdict_summary = base["verdict"].format(user_p=user_p.upper(), opp_p=opp_p.upper(), motion=motion, p_primary=p_primary)
    superiority = base["superiority"].format(user_p=user_p.upper()) if "{user_p}" in base["superiority"] else base["superiority"]

    return {
        "opp_speeches": opp_speeches,
        "zuma_speeches": zuma_speeches,
        "socratic_question": socratic_q,
        "target_dilemma": dilemma,
        "presup": presup,
        "presupposition_demolished": presup,
        "verdict_summary": verdict_summary,
        "logical_superiority": superiority,
        "motion_template": base.get("motion_template", ""),
        "title_template": base.get("title_template", ""),
        "affirmative_stance": base.get("affirmative_stance", ""),
        "negative_stance": base.get("negative_stance", "")
    }
