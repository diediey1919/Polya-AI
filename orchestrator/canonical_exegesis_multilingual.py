# -*- coding: utf-8 -*-
"""
Multilingual Canonical Exegesis Registry for Polya Exegesis Engine.
Covers all 14 canonical languages outside id/en/it:
- ar (Arabic), tr (Turkish), ur (Urdu), fa (Persian), hi (Hindi), bn (Bengali)
- zh (Chinese), ja (Japanese), ko (Korean), es (Spanish), fr (French)
- pt (Portuguese), de (German), ru (Russian)
"""

from typing import Dict, Any, List, Optional
from web.models import (
    ExegeticalContext,
    InterlinearWordToken,
    LinguisticExegesisPackage
)
from orchestrator.canonical_exegesis_en import CANONICAL_EXEGESIS_REGISTRY_EN



CANONICAL_EXEGESIS_REGISTRY_MULTILINGUAL = {
    "Roma 3:31": {
        "ar": {
            "passage_reference": "رومية 3:31",
            "literal_translation": "الناموس إذن هل نبطل بالإيمان؟ حاشا! بل الناموس نثبت.",
            "natural_translation": "أفنبطل الناموس بالإيمان؟ حاشا! بل نثبت الناموس ونؤيده.",
            "literary_genre": "مجادلة بولسية ديداتيكية / حوار تعليمي قضائي",
            "immediate_context": "خاتمة الحديث عن التبرير بالإيمان دون أعمال الناموس في رومية 3:21-30.",
            "historical_cultural_setting": "روما في القرن الأول؛ التوتر بين المؤمنين حول سلطة الشريعة (التوراة).",
            "syntactic_exegesis": {
                "poin_1": "استفهام بلاغي يفتتح بأداة الاستنتاج 'oun' وفعل الإلغاء 'katargoumen'.",
                "poin_2": "نفي قاطع بصيغة التمني 'mē genoito' يرفض تماماً إسقاط الشريعة.",
                "poin_3": "أداة استدراك قوية 'alla' مع فعل الإثبات 'histanomen'."
            },
            "exegetical_synthesis": "يؤكد التحليل الفيلولوجي لليونانية الكوينية في رومية 3:31 أن الإيمان لا يلغي الناموس بل يثبت سريانه."
        },
        "tr": {
            "passage_reference": "Romalılar 3:31",
            "literal_translation": "Yasa'yı o halde iman aracılığıyla geçersiz mi kılıyoruz? Asla! Aksine Yasa'yı pekiştiriyoruz.",
            "natural_translation": "Öyleyse iman aracılığıyla Kutsal Yasa'yı geçersiz mi kılıyoruz? Kesinlikle hayır! Tam tersine, Yasa'yı pekiştiriyoruz.",
            "literary_genre": "Pavlus'un Diyatriği / Hukuki Öğretici Söylem",
            "immediate_context": "Romalılar 3:21-30'da yasanın eylemlerinden bağımsız imanla aklanma söyleminin sonucu.",
            "historical_cultural_setting": "1. yüzyıl Roması; Tevrat'ın bağlayıcılığına ilişkin teolojik tartışma.",
            "syntactic_exegesis": {
                "poin_1": "Sonuç bildiren 'oun' ve 'katargoumen' fiiliyle açılan retorik soru.",
                "poin_2": "'mē genoito' dilek kipiyle yapılan kesin ret, yasanın lağvedildiği iddiasını çürütür.",
                "poin_3": "'alla' karşıtlık bağlacı ve 'histanomen' (ayakta tutuyoruz) etken fiili."
            },
            "exegetical_synthesis": "Romalılar 3:31'deki filolojik analiz, imanın Tevrat'ı geçersiz kılmadığını kanıtlar."
        },
        "ur": {
            "passage_reference": "رومیوں 3:31",
            "literal_translation": "شریعت کو تو کیا ہم ایمان کے وسیلے سے باطل ٹھہراتے ہیں؟ ہرگز نہیں! بلکہ شریعت کو قائم رکھتے ہیں۔",
            "natural_translation": "پس کیا ہم ایمان کے وسیلے سے شریعت کو باطل کرتے ہیں؟ ہرگز نہیں! بلکہ ہم شریعت کو قائم رکھتے ہیں۔",
            "literary_genre": "پولوسی تعلیمی مناظرہ / قانونی خطاب",
            "immediate_context": "رومیوں 3:21-30 میں ایمان کے وسیلے سے راستبازی کے بیان کا اختتام۔",
            "historical_cultural_setting": "پہلی صدی کا روم؛ تورات کی قانونی حیثیت پر مکالمہ۔",
            "syntactic_exegesis": {
                "poin_1": "استنباطی حرف 'oun' اور فعل 'katargoumen' کے ساتھ استفساری بلاغت۔",
                "poin_2": "'mē genoito' کے ذریعے قطعی انکار جو شریعت کے خاتمے کو مسترد کرتا ہے۔",
                "poin_3": "مخالف ربط 'alla' کے ساتھ متعدی فعل 'histanomen'۔"
            },
            "exegetical_synthesis": "رومیوں 3:31 کے کوئنے یونانی تجزیے سے ثابت ہے کہ ایمان شریعت کو منسوخ نہیں کرتا۔"
        },
        "fa": {
            "passage_reference": "رومیان 3:31",
            "literal_translation": "آیا پس شریعت را به واسطه ایمان باطل می‌سازیم؟ حاشا! بلکه شریعت را استوار می‌داریم.",
            "natural_translation": "آیا شریعت را با ایمان باطل می‌سازیم؟ حاشا! بلکه شریعت را استوار و برقرار می‌داریم.",
            "literary_genre": "مباحثه پولسی / گفتمان تعلیمی و حقوقی",
            "immediate_context": "نتیجه‌گیری گفتمان عادلانه‌شمردگی با ایمان در رومیان 3:21-30.",
            "historical_cultural_setting": "روم قرن اول؛ اعتبار پایدار تورات.",
            "syntactic_exegesis": {
                "poin_1": "سؤال خطابی با حرف ربط نتیجه‌گیری 'oun' و فعل متعدی 'katargoumen'.",
                "poin_2": "رد قاطع با تمنایی 'mē genoito' که هرگونه بطلان شریعت را نفی می‌کند.",
                "poin_3": "حرف عطف تقابلی محکم 'alla' همراه با فعل 'histanomen'."
            },
            "exegetical_synthesis": "تحلیل لغوی و نحوی یونانی کوئنه اثبات می‌کند که ایمان شریعت را باطل نمی‌سازد."
        },
        "hi": {
            "passage_reference": "रोमियों 3:31",
            "literal_translation": "तो क्या व्यवस्था को हम विश्वास के द्वारा व्यर्थ ठहराते हैं? कदापि नहीं! वरन व्यवस्था को स्थिर करते हैं।",
            "natural_translation": "तो क्या हम विश्वास के द्वारा व्यवस्था को व्यर्थ ठहराते हैं? कदापि नहीं! वरन हम व्यवस्था को दृढ़ और स्थिर करते हैं।",
            "literary_genre": "पौलीय उपदेशात्मक संवाद / विधिक उद्बोधन",
            "immediate_context": "रोमियों 3:21-30 में विश्वास द्वारा धर्मी ठहराए जाने के विवेचन का निष्कर्ष।",
            "historical_cultural_setting": "प्रथम शताब्दी का रोम; तोराह की विहित प्रामाणिकता पर विमर्श।",
            "syntactic_exegesis": {
                "poin_1": "निष्कर्षसूचक 'oun' और सकर्मक क्रिया 'katargoumen' से आरंभ होने वाला प्रश्न।",
                "poin_2": "'mē genoito' द्वारा दृढ़तम निषेध जो व्यवस्था के निरस्तीकरण को नकारता है।",
                "poin_3": "दृढ़ विरोधाभासी अव्यय 'alla' के साथ क्रिया 'histanomen'।"
            },
            "exegetical_synthesis": "रोमियों 3:31 का कॉइने यूनानी भाषिक विश्लेषण सिद्ध करता है कि विश्वास व्यवस्था को निरस्त नहीं करता।"
        },
        "bn": {
            "passage_reference": "রোমীয় 3:31",
            "literal_translation": "ব্যবস্থাকে তবে কি আমরা বিশ্বাসের মাধ্যমে বাতিল করি? কখনই নয়! বরং ব্যবস্থাকে প্রতিষ্ঠিত করি।",
            "natural_translation": "তবে কি আমরা বিশ্বাসের মাধ্যমে ব্যবস্থাকে বাতিল করি? কখনই নয়! বরং আমরা ব্যবস্থাকে সুদৃঢ়ভাবে প্রতিষ্ঠিত করি।",
            "literary_genre": "পোলীয় নির্দেশনামূলক বিতর্ক / বিধিসম্মত ডিসকোর্স",
            "immediate_context": "রোমীয় 3:21-30-এ বিশ্বাসের মাধ্যমে নির্দোষ গণ্য হওয়ার প্রসঙ্গের সমাপ্তি।",
            "historical_cultural_setting": "প্রথম শতাব্দীর রোম; তৌরাতের চিরন্তন কর্তৃত্ব নিয়ে ইহুদি ও অ-ইহুদিদের সংলাপ।",
            "syntactic_exegesis": {
                "poin_1": "সিদ্ধান্তসূচক 'oun' এবং 'katargoumen' ক্রিয়া যোগে অলংকারিক প্রশ্ন।",
                "poin_2": "'mē genoito' দ্বারা চরম অস্বীকৃতি যা ব্যবস্থার অবসানকে প্রত্যাখ্যান করে।",
                "poin_3": "দৃঢ় বৈপরীত্যমূলক 'alla' এবং 'histanomen' ক্রিয়াপদ।"
            },
            "exegetical_synthesis": "রোমীয় 3:31-এর ব্যাকরণিক বিশ্লেষণ প্রমাণ করে যে বিশ্বাস তৌরাতকে বাতিল করে না।"
        },
        "zh": {
            "passage_reference": "罗马书 3:31",
            "literal_translation": "这样律法我们借着信废弃了吗？断乎没有！反倒律法我们坚立。",
            "natural_translation": "这样，我们因信废了律法吗？断乎不是！更是坚固律法。",
            "literary_genre": "保罗式辩难文体 / 法庭辩证教训",
            "immediate_context": "罗马书 3:21-30 因信称义论证的高潮结论，驳斥废弃律法主义。",
            "historical_cultural_setting": "公元一世纪罗马；妥拉（律法）永恒约束力的论辩。",
            "syntactic_exegesis": {
                "poin_1": "以推论连词 'oun' 与及物动词 'katargoumen' 发起的反问修辞句式。",
                "poin_2": "使用祈愿语气 'mē genoito' 的绝对否定式，坚决否定律法废除论。",
                "poin_3": "强烈转折连词 'alla' 与使役动词 'histanomen'（我们使之坚立）。"
            },
            "exegetical_synthesis": "罗马书 3:31 文献学分析确凿表明因信称义绝未废除律法，'histanomen' 证实使徒教导坚立妥拉。"
        },
        "ja": {
            "passage_reference": "ローマ人への手紙 3:31",
            "literal_translation": "律法をそれでは私たちは信仰によって無効にするのか。決してそうではない！かえって律法を私たちは確立する。",
            "natural_translation": "それでは、私たちは信仰によって律法を無効にするのでしょうか。決してそうではありません！かえって律法を確立するのです。",
            "literary_genre": "パウロ的ディアトリベー / 法廷的教訓ディスコース",
            "immediate_context": "ローマ人への手紙 3:21-30 の信仰義認論の結論。",
            "historical_cultural_setting": "1世紀のローマ；トーラーの拘束的妥当性に関する対話。",
            "syntactic_exegesis": {
                "poin_1": "推論的接続詞 'oun' と及物動詞 'katargoumen' による修辞的疑問文。",
                "poin_2": "希求法 'mē genoito' による絶対的否定。律法の破棄を断固として拒絶する。",
                "poin_3": "強い逆接 'alla' と能動相動詞 'histanomen'（堅く立てる、有効にする）。"
            },
            "exegetical_synthesis": "ローマ人への手紙 3:31 の分析は、信仰が律法を無効にしないことを証明する。"
        },
        "ko": {
            "passage_reference": "로마서 3:31",
            "literal_translation": "율법을 그러면 우리가 믿음을 통하여 파기하느뇨? 결코 그렇지 않다! 오히려 율법을 우리가 굳게 세운다.",
            "natural_translation": "그런즉 우리가 믿음으로 말미암아 율법을 파기합니까? 결코 그렇지 않습니다! 도리어 율법을 굳게 세웁니다.",
            "literary_genre": "바울적 디아트리베 / 법정적 교훈 담화",
            "immediate_context": "로마서 3:21-30의 믿음으로 말미암는 의인론의 결론부.",
            "historical_cultural_setting": "1세기 로마; 토라(율법)의 지속적 구속력에 관한 논쟁.",
            "syntactic_exegesis": {
                "poin_1": "추론적 접속사 'oun'과 타동사 'katargoumen'으로 시작되는 수사적 의문문.",
                "poin_2": "기원법 'mē genoito'를 통한 단호한 부정으로 율법 폐기론을 거부함.",
                "poin_3": "강한 역접 'alla'와 사역동사 'histanomen'(우리가 굳게 세운다)의 결합."
            },
            "exegetical_synthesis": "로마서 3:31의 헬라어 분석은 믿음이 율법을 폐하지 않음을 입증한다."
        },
        "es": {
            "passage_reference": "Romanos 3:31",
            "literal_translation": "¿La ley entonces invalidamos mediante la fe? ¡De ninguna manera! Al contrario, la ley confirmamos.",
            "natural_translation": "¿Luego por la fe invalidamos la ley? ¡En ninguna manera! Más bien, confirmamos y sostenemos la ley.",
            "literary_genre": "Diatriba paulina / Discurso didáctico forense",
            "immediate_context": "Conclusión del discurso sobre la justificación por la fe en Romanos 3:21-30.",
            "historical_cultural_setting": "Roma del siglo I; vigencia y autoridad de la Torá.",
            "syntactic_exegesis": {
                "poin_1": "Pregunta retórica abierta con conjunción inferencial 'oun' y verbo 'katargoumen'.",
                "poin_2": "Repudio categórico con el optativo volitivo 'mē genoito', rechazando la anulación de la ley.",
                "poin_3": "Adversativa fuerte 'alla' unida al verbo transitivo 'histanomen' (confirmamos)."
            },
            "exegetical_synthesis": "El análisis filológico en Romanos 3:31 demuestra concluyentemente que la fe no anula la Torá."
        },
        "fr": {
            "passage_reference": "Romains 3:31",
            "literal_translation": "La loi donc annulons-nous par le moyen de la foi ? Loin de là ! Au contraire, la loi nous établissons.",
            "natural_translation": "Anéantissons-nous donc la loi par la foi ? Loin de là ! Au contraire, nous confirmons et établissons la loi.",
            "literary_genre": "Diatribe paulinienne / Discours didactique médico-légal",
            "immediate_context": "Conclusion de l'argumentation sur la justification par la foi en Romains 3:21-30.",
            "historical_cultural_setting": "Rome au Ier siècle ; dialogue concernant l'autorité de la Torah.",
            "syntactic_exegesis": {
                "poin_1": "Question rhétorique introduite par l'inférentiel 'oun' et le verbe 'katargoumen'.",
                "poin_2": "Rejet absolu avec l'optatif volitif 'mē genoito', réfutant l'abrogation de la loi.",
                "poin_3": "Adversatif fort 'alla' couplé au verbe factitif 'histanomen' (nous affermissons)."
            },
            "exegetical_synthesis": "L'analyse philologique en Romains 3:31 établit que la foi n'annule pas la Torah."
        },
        "pt": {
            "passage_reference": "Romanos 3:31",
            "literal_translation": "A lei, pois, anulamos por meio da fé? De modo nenhum! Pelo contrário, a lei estabelecemos.",
            "natural_translation": "Anulamos, pois, a lei pela fé? De maneira nenhuma! Pelo contrário, confirmamos e estabelecemos a lei.",
            "literary_genre": "Diatribe paulina / Discurso didático forense",
            "immediate_context": "Conclusão do discurso da justificação pela fé em Romanos 3:21-30.",
            "historical_cultural_setting": "Roma do século I; debate sobre a validade contínua da Torá.",
            "syntactic_exegesis": {
                "poin_1": "Pergunta retórica aberta pela conjunção inferencial 'oun' e o verbo 'katargoumen'.",
                "poin_2": "Repúdio categórico com o optativo volitivo 'mē genoito', rejeitando a anulação da lei.",
                "poin_3": "Adversativa enfática 'alla' associada ao verbo transitivo 'histanomen'."
            },
            "exegetical_synthesis": "A análise filológica em Romanos 3:31 demonstra que a fé ratifica a Lei."
        },
        "de": {
            "passage_reference": "Römer 3:31",
            "literal_translation": "Das Gesetz also heben wir auf durch den Glauben? Das sei ferne! Sondern das Gesetz richten wir auf.",
            "natural_translation": "Heben wir denn das Gesetz auf durch den Glauben? Das sei ferne! Im Gegenteil, wir richten das Gesetz auf und bestätigen es.",
            "literary_genre": "Paulinische Diatribe / Forensisch-didaktischer Diskurs",
            "immediate_context": "Schlussfolgerung der Rechtfertigungslehre in Römer 3:21-30.",
            "historical_cultural_setting": "Rom im 1. Jahrhundert; bindende Geltung der Tora.",
            "syntactic_exegesis": {
                "poin_1": "Rhetorische Frage eingeleitet mit der Folgerungspartikel 'oun' und 'katargoumen'.",
                "poin_2": "Kategorische Zurückweisung mit dem Optativ 'mē genoito' (Das sei ferne!).",
                "poin_3": "Starkes adversatives 'alla' verbunden mit dem faktitiven Verb 'histanomen'."
            },
            "exegetical_synthesis": "Die philologische Analyse in Römer 3:31 belegt, dass der Glaube die Tora nicht aufhebt."
        },
        "ru": {
            "passage_reference": "Римлянам 3:31",
            "literal_translation": "Закон ли итак упраздняем через веру? Да не будет! Но закон утверждаем.",
            "natural_translation": "Итак, уничтожаем ли мы закон верою? Никак! Напротив, мы утверждаем закон.",
            "literary_genre": "Павлова диатриба / Судебно-дидактический дискурс",
            "immediate_context": "Заключение рассуждения об оправдании верой в Римлянам 3:21-30.",
            "historical_cultural_setting": "Рим I века; диалог о непреходящем авторитете Торы.",
            "syntactic_exegesis": {
                "poin_1": "Риторический вопрос, открываемый союзом 'oun' и глаголом 'katargoumen'.",
                "poin_2": "Категорическое отрицание оптативом 'mē genoito', исключающее упразднение закона.",
                "poin_3": "Сильный противительный союз 'alla' в паре с глаголом 'histanomen'."
            },
            "exegetical_synthesis": "Текстологический анализ койне в Римлянам 3:31 подтверждает: вера утверждает закон."
        }
    }
}


def get_multilingual_canonical_package(ref: str, locale: str, base_data: dict, loc_map: dict) -> Optional[LinguisticExegesisPackage]:
    loc_key = (locale or "id").strip().lower()
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

    # 1. Retrieve EN base for comparisons
    en_base = CANONICAL_EXEGESIS_REGISTRY_EN.get(ref) or base_data
    base_comp = en_base.get("translation_comparison", [])

    is_ot = base_data.get("original_language", "").lower().startswith("biblical hebrew") or "ibrani" in base_data.get("original_language", "").lower()
    bench_label = loc_map.get("benchmark_label_ot") if is_ot else loc_map.get("benchmark_label_nt", "1st-Century Original Source Meaning")
    local_code = loc_map.get("local_code", "Standard Translation")
    local_crit = loc_map.get("local_critique", "Evaluation of syntactic fidelity to the original source text.")
    kjv_crit = loc_map.get("kjv_critique", "Idiomatic translation audit of the Textus Receptus tradition.")
    esv_crit = loc_map.get("esv_critique", "Modern literal accuracy audit based on reliable critical text.")

    # Explicitly enforce is_benchmark: True on item 0
    adapted_comp = [
        {
            "version": bench_label,
            "text": base_comp[0].get("text", "") if len(base_comp) > 0 else "",
            "critique": loc_map.get("benchmark_critique", ""),
            "is_benchmark": True
        },
        {
            "version": local_code,
            "text": f"{loc_map.get('local_name', local_code)}: {ref}",
            "critique": local_crit
        },
        {
            "version": "KJV",
            "text": base_comp[2].get("text", "") if len(base_comp) > 2 else "King James Version text",
            "critique": kjv_crit
        },
        {
            "version": "ESV",
            "text": base_comp[3].get("text", "") if len(base_comp) > 3 else "English Standard Version text",
            "critique": esv_crit
        }
    ]

    # Check multilingual registry
    v_data = CANONICAL_EXEGESIS_REGISTRY_MULTILINGUAL.get(ref, {}).get(loc_key)
    if not v_data:
        # Fallback to English base data but with fully adapted translation comparison
        v_data = {
            "passage_reference": en_base.get("passage_reference", ref),
            "literal_translation": en_base.get("literal_translation", ""),
            "natural_translation": en_base.get("natural_translation", ""),
            "literary_genre": en_base.get("exegetical_context").literary_genre if hasattr(en_base.get("exegetical_context"), "literary_genre") else "Exegesis",
            "immediate_context": en_base.get("exegetical_context").immediate_context if hasattr(en_base.get("exegetical_context"), "immediate_context") else "",
            "historical_cultural_setting": en_base.get("exegetical_context").historical_cultural_setting if hasattr(en_base.get("exegetical_context"), "historical_cultural_setting") else "",
            "syntactic_exegesis": en_base.get("syntactic_exegesis", {}),
            "exegetical_synthesis": en_base.get("exegetical_synthesis", "")
        }

    return LinguisticExegesisPackage(
        passage_reference=v_data["passage_reference"],
        original_language=base_data["original_language"],
        source_text_full=base_data["source_text_full"],
        literal_translation=v_data["literal_translation"],
        natural_translation=v_data["natural_translation"],
        exegetical_context=ExegeticalContext(
            literary_genre=v_data["literary_genre"],
            immediate_context=v_data["immediate_context"],
            historical_cultural_setting=v_data["historical_cultural_setting"]
        ),
        interlinear_tokens=en_base.get("interlinear_tokens", base_data.get("interlinear_tokens", [])),
        syntactic_exegesis=v_data["syntactic_exegesis"],
        manuscript_witnesses=base_data["manuscript_witnesses"],
        translation_comparison=adapted_comp,
        corpus_cross_references=en_base.get("corpus_cross_references", base_data.get("corpus_cross_references", [])),
        exegetical_synthesis=v_data["exegetical_synthesis"]
    )
