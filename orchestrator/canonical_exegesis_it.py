"""
Italian Localized Canonical Exegesis Packages for Polya Exegesis Engine.
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

CANONICAL_EXEGESIS_REGISTRY_IT: Dict[str, Dict[str, Any]] = {
    "Roma 3:31": {
        "passage_reference": "Roma 3:31",
        "original_language": "Koine Greek",
        "source_text_full": "νόμον οὖν καταργοῦμεν διὰ τῆς πίστεως; μὴ γένοιτο· ἀλλὰ νόμον ἱστάνομεν.",
        "literal_translation": "La Legge dunque annulliamo mediante la fede? Giammai! Al contrario, la Legge stabiliamo fermamente.",
        "natural_translation": "Annulliamo forse la Legge attraverso la fede? Assolutamente no! Al contrario, confermiamo e sosteniamo pienamente la Legge.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Diatriba paolina / Discorso didattico forense",
            immediate_context="Conclusione dell'argomentazione sulla giustificazione per grazia mediante la fede in Roma 3:21-30. Paolo anticipa l'obiezione antinomista.",
            historical_cultural_setting="Roma del I secolo; tensione dialogica tra credenti giudei e gentili riguardante l'autorità vincolante della Torah."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "legge / Torah", "syntactic_role": "Oggetto Diretto Emfatico Preverbale", "exegetical_note": "Collocazione enfatica di 'nomon' in posizione iniziale."},
            {"index": 2, "literal_gloss": "dunque / quindi", "syntactic_role": "Congiunzione Infernziale", "exegetical_note": "Collega la conclusione logica con l'argomentazione precedente."},
            {"index": 3, "literal_gloss": "annulliamo / aboliamo", "syntactic_role": "Predicato Verbale Transitivo", "exegetical_note": "Presente indicativo attivo 1P plurale."},
            {"index": 4, "literal_gloss": "mediante / per mezzo di", "syntactic_role": "Preposizione Strumentale", "exegetical_note": "Indica il mezzo della giustificazione."},
            {"index": 5, "literal_gloss": "la", "syntactic_role": "Articolo Determinativo Genitivo", "exegetical_note": "Determina specificamente la fede."},
            {"index": 6, "literal_gloss": "fede", "syntactic_role": "Complemento di Mezzo", "exegetical_note": "Pistis nel senso di fedeltà e fiducia totale."},
            {"index": 7, "literal_gloss": "non", "syntactic_role": "Particella Negativa Volitiva", "exegetical_note": "Negazione assoluta rafforzata."},
            {"index": 8, "literal_gloss": "avvenga mai / sia mai", "syntactic_role": "Ottativo Aoristo Medio", "exegetical_note": "Formula enfatica di ripudio categorico."},
            {"index": 9, "literal_gloss": "ma / al contrario", "syntactic_role": "Congiunzione Avversativa Forte", "exegetical_note": "Introduce l'affermazione antitetica definitiva."},
            {"index": 10, "literal_gloss": "legge / Torah", "syntactic_role": "Oggetto Diretto Ripetuto", "exegetical_note": "Ribadisce l'oggetto dell'azione apostolica."},
            {"index": 11, "literal_gloss": "stabiliamo / confermiamo", "syntactic_role": "Predicato Verbale Fattitivo", "exegetical_note": "Presente indicativo durativo: far stare in piedi, rendere valida e salda."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Interrogativa retorica introdotta dalla particella inferenziale 'oun' con 'katargoumen' (presente indicativo attivo 1P plurale).",
            "poin_2": "Negazione assoluta con ottativo volitivo 'mē genoito', che esprime il massimo rifiuto logico e dottrinale.",
            "poin_3": "Congiunzione avversativa forte 'alla' unita al verbo transitivo 'histanomen' (noi facciamo stare in piedi, confermiamo)."
        },
        "manuscript_witnesses": [
            {"witness": "P46 (Papiro Chester Beatty II, c. 200 d.C.)", "reading": "νόμον ἱστάνομεν (identico)", "status": "Consenso primario più antico"},
            {"witness": "Codex Sinaiticus (א 01, IV sec.)", "reading": "νόμον ἱστάνομεν (identico)", "status": "Testo alessandrino puro"},
            {"witness": "Codex Vaticanus (B 03, IV sec.)", "reading": "νόμον ἱστάνομεν (identico)", "status": "Manoscritto critico primario NA28"},
            {"witness": "Codex Alexandrinus (A 02, V sec.)", "reading": "νόμον ἱστάνομεν (identico)", "status": "Senza varianti di rilievo"}
        ],
        "translation_comparison": [
            {"version": "Significato del Greco Koine del I Secolo", "text": "Annulliamo dunque la Legge mediante la fede? Giammai! Al contrario, stabiliamo fermamente la Legge.", "critique": "Standard di accuratezza primario: preserva il verbo plurale inclusivo 'histanomen' (noi stabiliamo) e il rifiuto enfatico assoluto 'mē genoito'."},
            {"version": "CEI", "text": "Togliamo dunque ogni valore alla Legge mediante la fede? Niente affatto, anzi confermiamo la Legge.", "critique": "Rende accuratamente il rifiuto enfatico 'niente affatto' (mē genoito) e il verbo plurale inclusivo 'confermiamo'."},
            {"version": "KJV", "text": "Do we then make void the law through faith? God forbid: yea, we establish the law.", "critique": "'God forbid' è una parafrasi teologica idiomatica; il testo greco originale non contiene affatto la parola 'Theos'."},
            {"version": "ESV", "text": "Do we then overthrow the law by this faith? By no means! On the contrary, we uphold the law.", "critique": "Rende con precisione l'aspetto grammaticale durativo di histanomen attraverso 'uphold'."}
        ],
        "corpus_cross_references": [
            {"reference": "Matteo 5:17", "connection": "Gesù dichiara di non essere venuto per abolire la Legge ma per adempierla pienamente."},
            {"reference": "Giacomo 2:10-12", "connection": "Unità organica e perpetua validità normativa dei precetti statutari della Torah."},
            {"reference": "Romani 7:12", "connection": "Paolo riafferma solennemente: 'La Legge è santa, e il comandamento è santo, giusto e buono'."}
        ],
        "exegetical_synthesis": "L'analisi filologica e sintattica del greco Koine in Romani 3:31 dimostra in modo incontrovertibile che la fede non annulla né abroga la Legge (Torah). Il verbo 'histanomen' certifica che l'insegnamento apostolico fa stare salda e convalida la validità statutaria della Torah."
    },

    "Yehezkiel 18:20": {
        "passage_reference": "Yehezkiel 18:20",
        "original_language": "Biblical Hebrew",
        "source_text_full": "הַנֶּפֶשׁ הַחֹטֵאת הִיא תָמוּת בֵּן לֹא־יִשָּׂא בַּעֲוֹן הָאָב וְאָב לֹא יִשָּׂא בַּעֲוֹן הַבֵּן צִדְקַת הַצַּדִּיק עָלָיו תִּהְיֶה וְרִשְׁעַת רָשָׁע עָלָיו תִּהְיֶה׃",
        "literal_translation": "La persona che pecca, essa sola morirà. Il figlio non porterà la colpa del padre, né il padre porterà la colpa del figlio; la giustizia del giusto sarà su di lui, e la malvagità del malvagio sarà su di lui.",
        "natural_translation": "Colui che pecca è colui che morirà. Il figlio non sconterà l'iniquità del padre, e il padre non sconterà l'iniquità del figlio. La rettitudine del giusto ricadrà su di lui, così come la malvagità dell'empio ricadrà su di lui.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Oracolo profetico giuridico / Disputa forense sacerdotale",
            immediate_context="Ezechiele smantella il proverbio fatalista dei padri che mangiano uva acerba (Ezechiele 18:1-4).",
            historical_cultural_setting="Esilio babilonese (VI sec. a.C.); affermazione della responsabilità individuale davanti alla giustizia divina."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "l'anima / la persona", "syntactic_role": "Soggetto Gramaticale", "exegetical_note": "Nephesh indica l'individuo vivente responsabile."},
            {"index": 2, "literal_gloss": "che pecca", "syntactic_role": "Modificatore Attributivo", "exegetical_note": "Participio attivo: colui che compie l'atto peccaminoso."},
            {"index": 3, "literal_gloss": "essa sola / proprio essa", "syntactic_role": "Pronome Anaforico Enfatico", "exegetical_note": "Isola l'imputabilità alla singola persona."},
            {"index": 4, "literal_gloss": "morirà", "syntactic_role": "Predicato Verbale", "exegetical_note": "Imperfetto Qal con sanzione capitale giudiziaria."},
            {"index": 5, "literal_gloss": "figlio", "syntactic_role": "Soggetto Clausola Secondaria", "exegetical_note": "Esclude il discendente biologico dalla colpa."},
            {"index": 6, "literal_gloss": "non porterà", "syntactic_role": "Negazione + Verbo Qal", "exegetical_note": "Nasa denota l'atto di farsi carico della colpa forense."},
            {"index": 7, "literal_gloss": "nella colpa del padre", "syntactic_role": "Complemento Giuridico", "exegetical_note": "Iniquità (awon) non trasferibile tra generazioni."},
            {"index": 8, "literal_gloss": "e padre non porterà", "syntactic_role": "Chiasmo Speculare", "exegetical_note": "Conferma bilaterale dell'intrasferibilità della colpa."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Sintagma nominale con pronome anaforico enfatico 'hi tamut' che delimita la sanzione penale esclusivamente al trasgressore.",
            "poin_2": "Chiasmo simmetrico 'ben lo-yissa ba'awon ha'av / we'av lo-yissa ba'awon habben'.",
            "poin_3": "Verbo 'nasa' nello stato Qal con preposizione 'be-' denota l'imputabilità giuridica diretta personale."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Leningradensis (B19a, 1008 d.C.)", "reading": "Testo Masoretico con vocalizzazione completa e stabile", "status": "Testimone primario del testo ebraico"},
            {"witness": "4QEzka (Manoscritti del Mar Morto / DSS)", "reading": "Frammento di Qumran concorde con la lezione masoretica", "status": "Testimone pre-cristiano"},
            {"witness": "Septuaginta (LXX, III sec. a.C.)", "reading": "ψυχὴ ἡ ἁμαρτάνουσα, αὕτη ἀποθανεῖται", "status": "Traduzione greca antica fedele"}
        ],
        "translation_comparison": [
            {"version": "Significato dell'Ebraico Antico del I Secolo", "text": "La persona che pecca, essa sola subirà la morte. Il figlio non porterà la colpa del padre, né il padre porterà la colpa del figlio.", "critique": "Standard di accuratezza primario: stabilisce il principio di imputabilità morale individuale escludendo qualsiasi colpa ereditaria."},
            {"version": "CEI", "text": "Colui che pecca morirà; il figlio non sconterà l'iniquità del padre, né il padre l'iniquità del figlio.", "critique": "Traduce fedelmente il principio di responsabilità personale diretta."},
            {"version": "KJV", "text": "The soul that sinneth, it shall die. The son shall not bear the iniquity of the father.", "critique": "Conserva il termine arcaico 'soul' che riflette il significato letterale di nephesh."},
            {"version": "ESV", "text": "The soul who sins shall die. The son shall not suffer for the iniquity of the father.", "critique": "L'uso di 'suffer for' esprime la valenza giuridica di nasa ba'awon."}
        ],
        "corpus_cross_references": [
            {"reference": "Deuteronomio 24:16", "connection": "Legge statutaria mosaica: non si metteranno a morte i padri per i figli né i figli per i padri."},
            {"reference": "Geremia 31:29-30", "connection": "Ognuno morirà per la propria iniquità; chiunque mangi l'uva acerba avrà i propri denti allegati."},
            {"reference": "2 Re 14:6", "connection": "Applicazione storica del re Amasias che non uccise i figli dei congiurati secondo la Torah."}
        ],
        "exegetical_synthesis": "Ezechiele 18:20 sancisce il principio fondamentale della giustizia divina: la totale responsabilità morale individuale. Il testo ebraico esclude rigorosamente la trasmissione vicaria della colpa penale o il concetto di peccato originale ereditario."
    },

    "Yohanes 1:1": {
        "passage_reference": "Yohanes 1:1",
        "original_language": "Koine Greek",
        "source_text_full": "Ἐν ἀρχῇ ἦν ὁ λόγος, καὶ ὁ λόγος ἦν πρὸς τὸν θεόν, καὶ θεὸς ἦν ὁ λόγος.",
        "literal_translation": "Nel principio era il Logos, e il Logos era rivolto verso il Theos, e di natura divina / Theos qualitativo era il Logos.",
        "natural_translation": "Nel principio sussisteva la Parola (il Logos), e la Parola era presso il Theos, e la Parola era di essenza divina.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Prologo teologico poetico / Inno sapienziale giovanneo",
            immediate_context="Apertura solenne dell'Evangelo secondo Giovanni (1:1-18) sull'origine e rivelazione del Logos.",
            historical_cultural_setting="Ambiente ellenistico-giudaico del I secolo; concetto del Memra / Dabar e della Sapienza preesistente."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "in", "syntactic_role": "Preposizione Locativa", "exegetical_note": "Introduce il punto temporale iniziale."},
            {"index": 2, "literal_gloss": "principio", "syntactic_role": "Complemento di Tempo", "exegetical_note": "Allude a Bereshit di Genesi 1:1."},
            {"index": 3, "literal_gloss": "era / sussisteva", "syntactic_role": "Verbo di Esistenza Continua", "exegetical_note": "Imperfetto durativo prima della creazione."},
            {"index": 4, "literal_gloss": "il", "syntactic_role": "Articolo Determinativo", "exegetical_note": "Determina il soggetto Logos."},
            {"index": 5, "literal_gloss": "Logos / Parola", "syntactic_role": "Soggetto Gramaticale", "exegetical_note": "Memra divino incarnato."},
            {"index": 6, "literal_gloss": "e", "syntactic_role": "Congiunzione Coordinante", "exegetical_note": "Collega le proposizioni progressive."},
            {"index": 7, "literal_gloss": "il", "syntactic_role": "Articolo Determinativo", "exegetical_note": "Ripete il soggetto determinato."},
            {"index": 8, "literal_gloss": "Logos", "syntactic_role": "Soggetto", "exegetical_note": "Il medesimo Logos."},
            {"index": 9, "literal_gloss": "era", "syntactic_role": "Verbo", "exegetical_note": "Relazione continua."},
            {"index": 10, "literal_gloss": "verso / presso", "syntactic_role": "Preposizione di Relazione", "exegetical_note": "Pros con accusativo: comunione intima faccia a faccia."},
            {"index": 11, "literal_gloss": "il", "syntactic_role": "Articolo Accusativo Maschile", "exegetical_note": "Identifica l'unico Dio supremo (il Padre)."},
            {"index": 12, "literal_gloss": "Theos / Dio", "syntactic_role": "Oggetto di Relazione", "exegetical_note": "Ton theon articolato: il Padre celeste."},
            {"index": 13, "literal_gloss": "e", "syntactic_role": "Congiunzione", "exegetical_note": "Introduce la clausola climatica."},
            {"index": 14, "literal_gloss": "divino / di natura Theos", "syntactic_role": "Predicato Nominale Anartro Anteposto", "exegetical_note": "Theos senza articolo esprime qualità e natura ontologica divina, non identità di persona con Ton Theon."},
            {"index": 15, "literal_gloss": "era", "syntactic_role": "Copula", "exegetical_note": "Imperfetto continuo."},
            {"index": 16, "literal_gloss": "il", "syntactic_role": "Articolo Soggetto", "exegetical_note": "Identifica il soggetto grammaticale."},
            {"index": 17, "literal_gloss": "Logos", "syntactic_role": "Soggetto Definito", "exegetical_note": "Il Logos è il soggetto, non Theos."}
        ],
        "syntactic_exegesis": {
            "poin_1": "L'imperfetto continuo 'ēn' indica esistenza atemporale durativa prima della creazione del cosmo.",
            "poin_2": "La preposizione 'pros' con accusativo articolato 'ton theon' esprime relazione intima verso il Padre, distinguendo ontologicamente due entità.",
            "poin_3": "Nella clausola 'kai theos ēn ho logos': 'theos' è privo di articolo (anartro) e anteposto al verbo, fungendo da predicato nominale qualitativo."
        },
        "manuscript_witnesses": [
            {"witness": "P66 (Papiro Bodmer II, c. 200 d.C.)", "reading": "καὶ θεὸς ἦν ὁ λόγος", "status": "Testimone più antico del testo greco"},
            {"witness": "P75 (Papiro Bodmer XIV-XV, III sec.)", "reading": "καὶ θεὸς ἦν ὁ λόγος", "status": "Primo testimone alessandrino"},
            {"witness": "Codex Sinaiticus (א 01, IV sec.)", "reading": "καὶ θεὸς ἦν ὁ λόγος", "status": "Identico al testo critico NA28"},
            {"witness": "Codex Vaticanus (B 03, IV sec.)", "reading": "καὶ θεὸς ἦν ὁ λόγος", "status": "Identico al testo critico NA28"}
        ],
        "translation_comparison": [
            {"version": "Significato del Greco Koine del I Secolo", "text": "Nel principio esisteva il Logos, e il Logos era rivolto verso il Theos, e di natura divina / Theos qualitativo era il Logos.", "critique": "Standard di accuratezza primario: preserva la cruciale distinzione sintattica tra 'ho theos' (con articolo per il Padre) e 'theos' qualitativo anartro."},
            {"version": "CEI", "text": "In principio era il Verbo, e il Verbo era presso Dio e il Verbo era Dio.", "critique": "Traducendo entrambi come 'Dio', uniforma e confonde la netta distinzione grammaticale greca tra 'ton theon' articolato e 'theos' privo di articolo."},
            {"version": "KJV", "text": "In the beginning was the Word, and the Word was with God, and the Word was God.", "critique": "Rende indistinto l'articolo determinativo determinando una lettura modalista o trinitaria non supportata dalla sintassi greca originale."},
            {"version": "ESV", "text": "In the beginning was the Word, and the Word was with God, and the Word was God.", "critique": "Mantiene la formulazione tradizionale omettendo la specifica valenza qualitativa del predicato greco anteposto."}
        ],
        "corpus_cross_references": [
            {"reference": "Giovanni 17:3", "connection": "Gesù definisce il Padre come 'l'unico vero Dio' ('ton monon alēthinon theon')."},
            {"reference": "1 Corinzi 8:6", "connection": "Paolo distingue: 'Per noi c'è un solo Dio, il Padre... e un solo Signore, Gesù Cristo'."},
            {"reference": "Proverbi 8:22-30", "connection": "La Sapienza personificata preesistente al principio delle opere divine di YHWH."}
        ],
        "exegetical_synthesis": "In Giovanni 1:1, la precisa grammatica del greco Koine distingue chiaramente il Padre ('ho theos' con l'articolo) dal Logos ('theos' senza articolo, con valore qualitativo). Il testo non insegna l'identità ontologica assoluta tra Gesù e l'unico Dio supremo."
    },

    "Ulangan 6:4": {
        "passage_reference": "Ulangan 6:4",
        "original_language": "Biblical Hebrew",
        "source_text_full": "שְׁמַע יִשְׂרָאֵל יְהוָה אֱלֹהֵינוּ יְהוָה אֶחָד׃",
        "literal_translation": "Ascolta, Israele: YHWH nostro Dio, YHWH è Uno.",
        "natural_translation": "Ascolta, Israele: YHWH è il nostro Dio, YHWH è Uno solo.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Credo teologico / Confessione liturgica e kerygma dell'Alleanza",
            immediate_context="Il culmine del discorso di Mosè prima dell'ingresso nella terra promessa.",
            historical_cultural_setting="Monoteismo biblico assoluto in contrasto con il politeismo cananeo ed egiziano."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "Ascolta!", "syntactic_role": "Imperativo Qal 2ms", "exegetical_note": "Comando solenne di attenzione e obbedienza vitale."},
            {"index": 2, "literal_gloss": "Israele", "syntactic_role": "Vocativo", "exegetical_note": "Interpella l'intera comunità dell'Alleanza."},
            {"index": 3, "literal_gloss": "YHWH", "syntactic_role": "Soggetto / Nome Proprio Divino", "exegetical_note": "Il Tetragrammaton, l'Eterno Creatore Unico."},
            {"index": 4, "literal_gloss": "nostro Dio / Elohim", "syntactic_role": "Apposizione di Patto", "exegetical_note": "Plurale maiestatico dell'Unico Dio d'Israele."},
            {"index": 5, "literal_gloss": "YHWH", "syntactic_role": "Soggetto Ripetuto", "exegetical_note": "Ribadisce l'esclusività della persona divina."},
            {"index": 6, "literal_gloss": "Uno / Unico", "syntactic_role": "Predicato Nominale Assoluto", "exegetical_note": "Echad indica unicità numerica assoluta e indivisibilità."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Proposizione nominale pura che associa il Tetragrammaton YHWH con il numerale cardinale 'Echad' (uno solo, indivisibile).",
            "poin_2": "'Echad' denota unicità numerica assoluta (cfr. Genesi 42:13, Ecclesiaste 4:8), escludendo qualsiasi concetto di unità composita.",
            "poin_3": "La ripetizione del nome YHWH ribadisce che solo YHWH possiede la divinità suprema."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Leningradensis (B19a, 1008 d.C.)", "reading": "Lettere ingrandite Ayin (שְׁמַע) e Dalet (אֶחָד) formanti 'Ed' (Testimone)", "status": "Tradizione masoretica venerata"},
            {"witness": "4QDeutn (Manoscritti del Mar Morto / DSS)", "reading": "Testo identico al Masoretico di Qumran", "status": "Sito primario pre-cristiano"},
            {"witness": "Papyrus Nash (II sec. a.C.)", "reading": "Inclusione liturgica dello Shema prima del Decalogo", "status": "Papiro liturgico antichissimo"}
        ],
        "translation_comparison": [
            {"version": "Significato dell'Ebraico Antico del I Secolo", "text": "Ascolta, o Israele: YHWH è il nostro Elohim, YHWH è Uno (assoluto, unico ed indivisibile).", "critique": "Standard di accuratezza primario: afferma il monoteismo rigoroso ed esclusivo senza alcuna pluralità interna."},
            {"version": "CEI", "text": "Ascolta, Israele: il Signore è il nostro Dio, il Signore è uno solo.", "critique": "Rende accuratamente l'esclusività 'uno solo', sostituendo il nome YHWH con 'Signore'."},
            {"version": "KJV", "text": "Hear, O Israel: The LORD our God is one LORD.", "critique": "Rende letteralmente la proposizione nominale."},
            {"version": "ESV", "text": "Hear, O Israel: The LORD our God, the LORD is one.", "critique": "Traduzione fedele all'enunciato sintetico ebraico."}
        ],
        "corpus_cross_references": [
            {"reference": "Marco 12:29", "connection": "Gesù cita letteralmente Deuteronomio 6:4 come il 'primo di tutti i comandamenti'."},
            {"reference": "Isaia 44:6", "connection": "'Io sono il primo e io sono l'ultimo; fuori di me non c'è Dio'."},
            {"reference": "Zaccaria 14:9", "connection": "'In quel giorno YHWH sarà unico e unico sarà il suo nome'."}
        ],
        "exegetical_synthesis": "Lo Shema Yisrael (Deuteronomio 6:4) costituisce il fondamento monoteistico assoluto delle Scritture. Il termine 'Echad' sancisce l'unicità numerica e ontologica di Dio, escludendo qualsiasi suddivisione in persone distinte."
    },

    "Matius 5:17": {
        "passage_reference": "Matius 5:17",
        "original_language": "Koine Greek",
        "source_text_full": "Μὴ νομίσητε ὅτι ἦλθον καταλῦσαι τὸν νόμον ἢ τοὺς προφήτας· οὐκ ἦλθον καταλῦσαι ἀλλὰ πληρῶσαι.",
        "literal_translation": "Non pensate che io sia venuto per abrogare la Legge o i Profeti; non sono venuto per abrogare, ma per compiere / mettere in pieno vigore.",
        "natural_translation": "Non crediate che io sia venuto per abolire la Legge o i Profeti; non sono venuto per abolire, ma per dare pieno compimento.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Discorso della Montagna / Istruzione statutaria halakhica",
            immediate_context="Matteo 5:17-20 precede le antitesi etiche, stabilendo l'indissolubilità di ogni singolo iota della Legge.",
            historical_cultural_setting="Giudaismo galileo del I secolo; Gesù si difende dall'accusa farisaica di antinomismo."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "Non", "syntactic_role": "Particella Proibitiva", "exegetical_note": "Mē con congiuntivo aoristo esprime divieto categorico."},
            {"index": 2, "literal_gloss": "pensiate / supponiate", "syntactic_role": "Congiuntivo Aoristo Attivo 2P plurale", "exegetical_note": "Nomisēte: smettere di formulare quell'ipotesi."},
            {"index": 3, "literal_gloss": "che", "syntactic_role": "Congiunzione Dichiarativa", "exegetical_note": "Introduce il contenuto dell'opinione smentita."},
            {"index": 4, "literal_gloss": "venni / sono venuto", "syntactic_role": "Indicativo Aoristo Attivo 1s", "exegetical_note": "Dichiara lo scopo della missione storica di Gesù."},
            {"index": 5, "literal_gloss": "per abrogare / demolire", "syntactic_role": "Infinito Aoristo Attivo di Scopo", "exegetical_note": "Katalysai: distruggere, invalidare o dichiarare nullo."},
            {"index": 6, "literal_gloss": "la", "syntactic_role": "Articolo Accusativo", "exegetical_note": "Determina specificamente la Torah statutaria."},
            {"index": 7, "literal_gloss": "Legge / Torah", "syntactic_role": "Oggetto Diretto", "exegetical_note": "Il corpo dei precetti rivelati da Dio a Mosè."},
            {"index": 8, "literal_gloss": "o", "syntactic_role": "Congiunzione Disgiuntiva", "exegetical_note": "Estende la salvaguardia a tutto il canone profetico."},
            {"index": 9, "literal_gloss": "i", "syntactic_role": "Articolo Accusativo Plurale", "exegetical_note": "Determina i libri profetici."},
            {"index": 10, "literal_gloss": "Profeti", "syntactic_role": "Oggetto Coordinato", "exegetical_note": "I Nevi'im dell'Antico Testamento."},
            {"index": 11, "literal_gloss": "non", "syntactic_role": "Negazione Enfatica Indicativa", "exegetical_note": "Ouk: negazione oggettiva assoluta."},
            {"index": 12, "literal_gloss": "venni", "syntactic_role": "Verbo", "exegetical_note": "Ripetizione enfatica."},
            {"index": 13, "literal_gloss": "per abrogare", "syntactic_role": "Infinito di Scopo", "exegetical_note": "Ribadisce la non-abrogazione."},
            {"index": 14, "literal_gloss": "ma", "syntactic_role": "Congiunzione Avversativa Forte", "exegetical_note": "Alla introduce l'antitesi autentica."},
            {"index": 15, "literal_gloss": "per adempiere / dare pienezza", "syntactic_role": "Infinito Aoristo Attivo", "exegetical_note": "Plērōsai: confermare pienamente, mettere in vigore pratico."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Congiuntivo aoristo proibitivo 'Mē nomisēte' (smettete di pensare / non presumete minimamente).",
            "poin_2": "Antitesi esplicita tra l'infinito aoristo 'katalysai' (demolire, revocare) e 'plērōsai' (adempiere, dare piena efficacia).",
            "poin_3": "La formula 'ton nomon ē tous prophētas' designa la totalità delle Scritture canoniche vincolanti."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Sinaiticus (א 01, IV sec.)", "reading": "καταλῦσαι ἀλλὰ πληρῶσαι", "status": "Consenso alessandrino"},
            {"witness": "Codex Vaticanus (B 03, IV sec.)", "reading": "καταλῦσαι ἀλλὰ πληρῶσαι", "status": "Identico al testo critico"},
            {"witness": "Codex Bezae (D 05, V sec.)", "reading": "καταλῦσαι ἀλλὰ πληρῶσαι", "status": "Testimone occidentale concorde"}
        ],
        "translation_comparison": [
            {"version": "Significato del Greco Koine del I Secolo", "text": "Non pensate che io sia venuto per abrogare la Legge o i Profeti; non sono venuto per abrogare, ma per adempiere / mettere in pieno vigore.", "critique": "Standard di accuratezza primario: il verbo plērōsai indica l'adempimento pratico e l'insegnamento perfetto della Torah, non la sua cessazione."},
            {"version": "CEI", "text": "Non crediate che io sia venuto ad abolire la Legge o i Profeti; non sono venuto ad abolire, ma a dare pieno compimento.", "critique": "Traduce con 'dare pieno compimento', evidenziando la continuità statutaria della Legge."},
            {"version": "KJV", "text": "Think not that I am come to destroy the law, or the prophets: I am not come to destroy, but to fulfil.", "critique": "Traduzione letterale che preserva la polarità verbale originale."},
            {"version": "ESV", "text": "Do not think that I have come to abolish the Law or the Prophets; I have not come to abolish them but to fulfill them.", "critique": "Rende accuratamente l'imperativo proibitivo."}
        ],
        "corpus_cross_references": [
            {"reference": "Matteo 5:18-19", "connection": "Nemmeno uno iota o un apice passerà dalla Legge finché cielo e terra non passeranno."},
            {"reference": "Romani 3:31", "connection": "Paolo ribadisce che la fede non abroga la Legge ma la conferma saldamente."},
            {"reference": "Giacomo 2:10", "connection": "Chiunque osservi tutta la Legge ma fallisca in un solo punto è colpevole di tutti."}
        ],
        "exegetical_synthesis": "Matteo 5:17 conferma che la missione di Gesù non intendeva in alcun modo revocare o abrogare i precetti statutari della Torah. Il termine 'plērōsai' implica vivere, insegnare ed esaltare la Legge nella sua massima purezza e fedeltà."
    },

    "Lukas 22:42": {
        "passage_reference": "Lukas 22:42",
        "original_language": "Koine Greek",
        "source_text_full": "λέγων· πάτερ, εἰ βούλει παρένεγκε τοῦτο τὸ ποτήριον ἀπ' ἐμοῦ· πλὴν μὴ τὸ θέλημά μου ἀλλὰ τὸ σὸν γινέσθω.",
        "literal_translation": "Dicendo: Padre, se vuoi, allontana questo calice da me; tuttavia non la mia volontà, ma la tua si compia.",
        "natural_translation": "Dicendo: Padre, se è tua volontà, allontana da me questo calice! Tuttavia non sia fatta la mia volontà, ma la tua.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Preghiera di agonia nel Getsemani / Narrazione della Passione",
            immediate_context="Gesù si ritira sul Monte degli Ulivi a pregare prima dell'arresto.",
            historical_cultural_setting="Giudaismo del I secolo; sottomissione assoluta del servo devoto al decreto sovrano di Dio."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "dicendo", "syntactic_role": "Participio Presente Attivo", "exegetical_note": "Azione concomitante dell'orazione."},
            {"index": 2, "literal_gloss": "Padre", "syntactic_role": "Vocativo", "exegetical_note": "Invocazione filiale rispettosa a Dio."},
            {"index": 3, "literal_gloss": "se", "syntactic_role": "Particella Condizionale", "exegetical_note": "Subordina la richiesta alla volontà divina."},
            {"index": 4, "literal_gloss": "vuoi / è tua intenzione", "syntactic_role": "Indicativo Presente 2s", "exegetical_note": "Boulomai: decreto sovrano deliberato di Dio."},
            {"index": 5, "literal_gloss": "allontana / fa passare", "syntactic_role": "Imperativo Aoristo Attivo", "exegetical_note": "Supplica di allontanamento della prova imminente."},
            {"index": 6, "literal_gloss": "questo", "syntactic_role": "Pronome Dimostrativo", "exegetical_note": "Designa la coppa della sofferenza."},
            {"index": 7, "literal_gloss": "il", "syntactic_role": "Articolo Accusativo", "exegetical_note": "Determina il calice."},
            {"index": 8, "literal_gloss": "calice / coppa", "syntactic_role": "Oggetto Diretto", "exegetical_note": "Metafora biblica dell'amara prova terrena."},
            {"index": 9, "literal_gloss": "da", "syntactic_role": "Preposizione di Separazione", "exegetical_note": "Allontanamento fisico ed esistenziale."},
            {"index": 10, "literal_gloss": "me", "syntactic_role": "Pronome Personale 1s", "exegetical_note": "Riferito a Gesù come soggetto sofferente."},
            {"index": 11, "literal_gloss": "tuttavia / nondimeno", "syntactic_role": "Congiunzione Avversativa Restrittiva", "exegetical_note": "Plēn: segna il primato assoluto della volontà paterna."},
            {"index": 12, "literal_gloss": "non", "syntactic_role": "Particella Negativa", "exegetical_note": "Mē: nega il compimento della propria volontà."},
            {"index": 13, "literal_gloss": "la", "syntactic_role": "Articolo Neutro", "exegetical_note": "Sostantivizza thelēma."},
            {"index": 14, "literal_gloss": "volontà", "syntactic_role": "Soggetto Clausola Esclusa", "exegetical_note": "Thelēma: centro volitivo decisionale umano."},
            {"index": 15, "literal_gloss": "mia", "syntactic_role": "Pronome Possessivo 1s", "exegetical_note": "Mou: la distinta volontà personale di Gesù."},
            {"index": 16, "literal_gloss": "ma", "syntactic_role": "Congiunzione Avversativa", "exegetical_note": "Alla: polarità positiva."},
            {"index": 17, "literal_gloss": "la", "syntactic_role": "Articolo Neutro", "exegetical_note": "Sostantivizza son."},
            {"index": 18, "literal_gloss": "tua", "syntactic_role": "Pronome Possessivo 2s", "exegetical_note": "Son: la sovrana volontà del Padre celeste."},
            {"index": 19, "literal_gloss": "si compia / sia fatta", "syntactic_role": "Imperativo Presente Medio-Passivo 3s", "exegetical_note": "Ginesthō: sottomissione durativa continua."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Chiara demarcazione pronominale tra due soggetti distinti: 'to thelēma mou' (la mia volontà) e 'to son' (la tua).",
            "poin_2": "La congiunzione avversativa restrittiva 'plēn' stabilisce la subordinazione volontaria della volontà di Gesù alla volontà suprema del Padre.",
            "poin_3": "L'imperativo presente medio-passivo 'ginesthō' (si compia costantemente) esprime sottomissione incondizionata."
        },
        "manuscript_witnesses": [
            {"witness": "P75 (Papiro Bodmer XIV, III sec.)", "reading": "πλὴν μὴ τὸ θέλημά μου ἀλλὰ τὸ σὸν γινέσθω", "status": "Testimone primario antico"},
            {"witness": "Codex Sinaiticus (א 01, IV sec.)", "reading": "Testo identico a NA28", "status": "Consenso alessandrino"},
            {"witness": "Codex Vaticanus (B 03, IV sec.)", "reading": "Testo identico a NA28", "status": "Consenso alessandrino"}
        ],
        "translation_comparison": [
            {"version": "Significato del Greco Koine del I Secolo", "text": "Padre, se è Tua volontà, allontana questo calice da me; tuttavia non la mia volontà, ma la Tua si compia.", "critique": "Standard di accuratezza primario: dimostra la distinzione indiscutibile tra due centri di volontà ontologicamente distinti ('to thelēma mou' vs 'to son')."},
            {"version": "CEI", "text": "Padre, se vuoi, allontana da me questo calice! Tuttavia non sia fatta la mia, ma la tua volontà.", "critique": "Mantiene con limpidezza la distinzione tra la volontà sottomessa di Gesù e la volontà sovrana del Padre."},
            {"version": "KJV", "text": "Father, if thou be willing, remove this cup from me: nevertheless not my will, but thine, be done.", "critique": "Traduzione fedele dell'antitesi della subordinazione."},
            {"version": "ESV", "text": "Father, if you are willing, remove this cup from me. Nevertheless, not my will, but yours, be done.", "critique": "Preserva accuratamente la coordinazione avversativa 'plēn'."}
        ],
        "corpus_cross_references": [
            {"reference": "Giovanni 5:30", "connection": "'Non cerco la mia volontà, ma la volontà di colui che mi ha mandato'."},
            {"reference": "Giovanni 6:38", "connection": "'Sono disceso dal cielo non per fare la mia volontà, ma la volontà di colui che mi ha mandato'."},
            {"reference": "Ebrei 5:7-8", "connection": "Cristo offrì preghiere e suppliche con forti grida e lacrime a colui che poteva salvarlo dalla morte."}
        ],
        "exegetical_synthesis": "In Luca 22:42, la netta contrapposizione linguistica tra 'la mia volontà' e 'la tua' dimostra inconfutabilmente che Gesù possiede una volontà autonoma e sottomessa, distinta dalla volontà suprema di Dio. Due centri di volontà implicano due entità distinte, confutando l'unicità di sostanza ontologica post-nicena."
    },

    "2 Petrus 1:21": {
        "passage_reference": "2 Petrus 1:21",
        "original_language": "Koine Greek",
        "source_text_full": "οὐ γὰρ θελήματι ἀνθρώπου ἠνέχθη προφητεία ποτέ, ἀλλὰ ὑπὸ πνεύματος ἁγίου φερόμενοι ἐλάλησαν ἀπὸ θεοῦ ἄνθρωποι.",
        "literal_translation": "Poiché non per volontà di uomo fu mai portata una profezia, ma dallo Spirito Santo guidati parlarono da parte di Dio degli uomini.",
        "natural_translation": "Nessuna profezia infatti è mai venuta da volontà umana, ma mossi dallo Spirito Santo degli uomini hanno parlato da parte del Theos.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Epistola apostolica testamentaria",
            immediate_context="Conferma della certezza della parola profetica paragonata a lampada che splende in luogo oscuro (2 Pietro 1:19-20).",
            historical_cultural_setting="Comunità cristiane primitive esposte a false dottrine e favole artificiose."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "non", "syntactic_role": "Negazione Enfatica", "exegetical_note": "Ou nega categoricamente l'impulso soggettivo umano."},
            {"index": 2, "literal_gloss": "infatti / poiché", "syntactic_role": "Congiunzione Esplicativa", "exegetical_note": "Gar: spiega la ragione dell'ispirazione."},
            {"index": 3, "literal_gloss": "per volontà", "syntactic_role": "Dativo Strumentale", "exegetical_note": "Thelēmati: esclusione dell'origine volontaria umana."},
            {"index": 4, "literal_gloss": "di uomo", "syntactic_role": "Genitivo di Possesso", "exegetical_note": "Anthrōpou: creatura umana limitata."},
            {"index": 5, "literal_gloss": "fu portata / originata", "syntactic_role": "Indicativo Aoristo Passivo", "exegetical_note": "Ēnechthē: recata come messaggio esteriore."},
            {"index": 6, "literal_gloss": "profezia", "syntactic_role": "Soggetto Gramaticale", "exegetical_note": "Prophēteia: la parola profetica ispirata."},
            {"index": 7, "literal_gloss": "mai", "syntactic_role": "Avverbio Temporale", "exegetical_note": "Pote: in nessuna epoca storica passata."},
            {"index": 8, "literal_gloss": "ma", "syntactic_role": "Congiunzione Avversativa Forte", "exegetical_note": "Alla: introduce la causa reale trascendente."},
            {"index": 9, "literal_gloss": "da / sotto l'azione di", "syntactic_role": "Preposizione di Agente", "exegetical_note": "Hypo con genitivo: agente causale diretto."},
            {"index": 10, "literal_gloss": "Spirito", "syntactic_role": "Genitivo Singolare Neutro", "exegetical_note": "Pneumatos: lo Spirito di Dio."},
            {"index": 11, "literal_gloss": "Santo", "syntactic_role": "Aggettivo Qualificativo", "exegetical_note": "Hagiou: lo Spirito Santo di verità."},
            {"index": 12, "literal_gloss": "guidati / mossi / portati", "syntactic_role": "Participio Presente Passivo Nom. Pl.", "exegetical_note": "Pheromenoi: condotti dall'impulso sovrano dello Spirito."},
            {"index": 13, "literal_gloss": "parlarono", "syntactic_role": "Indicativo Aoristo Attivo 3P plurale", "exegetical_note": "Elalēsan: proclamarono oralmente e per iscritto."},
            {"index": 14, "literal_gloss": "da / da parte di", "syntactic_role": "Preposizione di Provenienza", "exegetical_note": "Apo: proveniente direttamente da Dio."},
            {"index": 15, "literal_gloss": "Theos / Dio", "syntactic_role": "Genitivo", "exegetical_note": "Theou: l'Origine somma del messaggio profetico."},
            {"index": 16, "literal_gloss": "uomini", "syntactic_role": "Soggetto Plurale", "exegetical_note": "Anthrōpoi: gli araldi umani scelti da Dio."}
        ],
        "syntactic_exegesis": {
            "poin_1": "La negazione 'ou gar... pote' nega categoricamente l'impulso soggettivo umano come fonte originaria della profezia.",
            "poin_2": "Il participio presente passivo 'pheromenoi' (guidati, trasportati) descrive l'azione dinamica dello Spirito Santo sui profeti.",
            "poin_3": "La preposizione 'apo theou' colloca la fonte primaria trascendente in Dio, di cui i profeti sono gli araldi parlanti ('elalēsan')."
        },
        "manuscript_witnesses": [
            {"witness": "P72 (Papiro Bodmer VII-VIII, III-IV sec.)", "reading": "ἀπὸ θεοῦ ἄνθρωποι", "status": "Testimone papiraceo più antico"},
            {"witness": "Codex Vaticanus (B 03, IV sec.)", "reading": "ἀπὸ θεοῦ ἄνθρωποι", "status": "Testo critico primario"},
            {"witness": "Codex Sinaiticus (א 01, IV sec.)", "reading": "ἅγιοι θεοῦ ἄνθρωποι (variante devozionale)", "status": "Variante nota con 'hagioi'"}
        ],
        "translation_comparison": [
            {"version": "Significato del Greco Koine del I Secolo", "text": "Poiché nessuna profezia fu mai portata per impulso di volontà umana, ma uomini mossi dallo Spirito Santo parlarono da parte del Theos.", "critique": "Standard di accuratezza primario: il participio passivo 'pheromenoi' indica l'azione sovrana della guida divina."},
            {"version": "CEI", "text": "Non da volontà umana fu mai mossa una profezia, ma mossi da Spirito Santo parlarono quegli uomini da parte di Dio.", "critique": "Rende fedelmente il moto passivo 'mossi da Spirito Santo'."},
            {"version": "KJV", "text": "For the prophecy came not in old time by the will of man: but holy men of God spake as they were moved by the Holy Ghost.", "critique": "Include l'aggettivo tardivo 'holy' assente nei manoscritti più antichi."},
            {"version": "ESV", "text": "For no prophecy was ever produced by the will of man, but men spoke from God as they were carried along by the Holy Spirit.", "critique": "Traduzione accurata del participio 'carried along by the Holy Spirit'."}
        ],
        "corpus_cross_references": [
            {"reference": "2 Timoteo 3:16", "connection": "Tutta la Scrittura è 'theopneustos' (ispirata/alata da Dio) e utile per insegnare."},
            {"reference": "Geremia 1:9", "connection": "YHWH stese la mano e toccò la mia bocca, dicendomi: 'Ecco, metto le mie parole nella tua bocca'."},
            {"reference": "Atti degli Apostoli 1:16", "connection": "La Scrittura doveva adempiersi, preannunciata dallo Spirito Santo per bocca di Davide."}
        ],
        "exegetical_synthesis": "2 Pietro 1:21 sancisce l'origine puramente divina della rivelazione profetica. Gli autori biblici hanno parlato non di propria iniziativa ma come strumenti guidati ('pheromenoi') dallo Spirito da parte di Dio, salvaguardando l'autorità oggettiva delle Scritture."
    },

    "1 Yohanes 5:7-8": {
        "passage_reference": "1 Yohanes 5:7-8",
        "original_language": "Koine Greek",
        "source_text_full": "ὅτι τρεῖς εἰσιν οἱ μαρτυροῦντες, τὸ πνεῦμα καὶ τὸ ὕδωρ καὶ τὸ αἷμα, καὶ οἱ τρεῖς εἰς τὸ ἕν εἰσιν.",
        "literal_translation": "Poiché tre sono coloro che testimoniano: lo Spirito e l'acqua e il sangue, e i tre sono concordi nell'uno.",
        "natural_translation": "Poiché tre sono quelli che rendono testimonianza: lo Spirito, l'acqua e il sangue, e questi tre concordano in uno.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Trattato epistolare dottrinale / Apologia apostolica",
            immediate_context="La testimonianza veridica di Dio riguardo a suo Figlio Gesù Cristo.",
            historical_cultural_setting="Fine del I secolo; opposizione al docetismo gnostico che negava l'incarnazione storica reale."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "perché / poiché", "syntactic_role": "Congiunzione Causale", "exegetical_note": "Hoti introduce la triplice attestazione."},
            {"index": 2, "literal_gloss": "tre", "syntactic_role": "Numerale Soggetto", "exegetical_note": "Tre testimoni terrestri."},
            {"index": 3, "literal_gloss": "sono", "syntactic_role": "Verbo di Esistenza", "exegetical_note": "Presente indicativo."},
            {"index": 4, "literal_gloss": "quelli che", "syntactic_role": "Articolo Maschile Plurale", "exegetical_note": "Personifica i testimoni."},
            {"index": 5, "literal_gloss": "testimoniano", "syntactic_role": "Participio Presente Attivo", "exegetical_note": "Attività testimoniale continua."},
            {"index": 6, "literal_gloss": "lo", "syntactic_role": "Articolo Neutro", "exegetical_note": "Determina pneuma."},
            {"index": 7, "literal_gloss": "Spirito", "syntactic_role": "Primo Testimone", "exegetical_note": "Lo Spirito di verità."},
            {"index": 8, "literal_gloss": "e", "syntactic_role": "Congiunzione", "exegetical_note": "Unione dei testimoni."},
            {"index": 9, "literal_gloss": "l'", "syntactic_role": "Articolo Neutro", "exegetical_note": "Determina hydōr."},
            {"index": 10, "literal_gloss": "acqua", "syntactic_role": "Secondo Testimone", "exegetical_note": "Battesimo di Gesù."},
            {"index": 11, "literal_gloss": "e", "syntactic_role": "Congiunzione", "exegetical_note": "Unione dei testimoni."},
            {"index": 12, "literal_gloss": "il", "syntactic_role": "Articolo Neutro", "exegetical_note": "Determina haima."},
            {"index": 13, "literal_gloss": "sangue", "syntactic_role": "Terzo Testimone", "exegetical_note": "Morte reale sulla croce."},
            {"index": 14, "literal_gloss": "e", "syntactic_role": "Congiunzione Conclusiva", "exegetical_note": "Sintesi dei tre."},
            {"index": 15, "literal_gloss": "i", "syntactic_role": "Articolo Maschile Plurale", "exegetical_note": "Riprende i tre testimoni."},
            {"index": 16, "literal_gloss": "tre", "syntactic_role": "Numerale", "exegetical_note": "I tre testimoni."},
            {"index": 17, "literal_gloss": "in / verso", "syntactic_role": "Preposizione con Accusativo", "exegetical_note": "Eis: convergenza di scopo."},
            {"index": 18, "literal_gloss": "l'", "syntactic_role": "Articolo Neutro", "exegetical_note": "Determina hen."},
            {"index": 19, "literal_gloss": "uno", "syntactic_role": "Accusativo Neutro", "exegetical_note": "Un'unica testimonianza concorde."},
            {"index": 20, "literal_gloss": "sono", "syntactic_role": "Predicato Verbale", "exegetical_note": "Eisin: armonia perfetta."}
        ],
        "syntactic_exegesis": {
            "poin_1": "Participio presente maschile plurale 'oi martyrountes' concordato con sostantivi neutri, personificando i tre testimoni storici terreni.",
            "poin_2": "La clausola 'eis to hen eisin' (convergono nell'uno) esprime armonia di testimonianza, non unità di essenza ontologica divina.",
            "poin_3": "Totale assenza del celebre 'Comma Johanneum' (il Padre, la Parola e lo Spirito Santo) in tutti i manoscritti greci antichi fino al XIV-XVI secolo."
        },
        "manuscript_witnesses": [
            {"witness": "Codex Sinaiticus (א 01, IV sec.)", "reading": "τρεῖς εἰσιν οἱ μαρτυροῦντες, τὸ πνεῦμα καὶ τὸ ὕδωρ καὶ τὸ αἷμα", "status": "Omette totalmente il Comma Johanneum"},
            {"witness": "Codex Vaticanus (B 03, IV sec.)", "reading": "τρεῖς εἰσιν οἱ μαρτυροῦντες, τὸ πνεῦμα καὶ τὸ ὕδωρ καὶ τὸ αἷμα", "status": "Omette totalmente il Comma Johanneum"},
            {"witness": "Codex Alexandrinus (A 02, V sec.)", "reading": "Omette totalmente il Comma Johanneum", "status": "Consenso unanime unciale"},
            {"witness": "Minuscolo 61 (XVI sec.)", "reading": "Prima apparizione forzata in un testo greco per soddisfare Erasmo", "status": "Manoscritto apologetico tardivo artificiale"}
        ],
        "translation_comparison": [
            {"version": "Significato del Greco Koine del I Secolo", "text": "Poiché tre sono coloro che testimoniano: lo Spirito, l'acqua e il sangue; e questi tre convergono nell'unica testimonianza.", "critique": "Standard di accuratezza primario: totale assenza del 'Comma Johanneum' nei manoscritti greci anteriori al XIV secolo; palese interpolazione dogmatica latina."},
            {"version": "CEI", "text": "Poiché tre sono quelli che danno testimonianza: lo Spirito, l'acqua e il sangue, e questi tre sono concordi.", "critique": "Omette rettamente il Comma Johanneum spurio, allineandosi con fedeltà al testo critico moderno NA28."},
            {"version": "KJV", "text": "For there are three that bear record in heaven, the Father, the Word, and the Holy Ghost: and these three are one. And there are three that bear witness in earth...", "critique": "Include l'interpolazione palesemente spuria del Comma Johanneum, respinta all'unanimità dalla critica testuale contemporanea."},
            {"version": "ESV", "text": "For there are three that testify: the Spirit and the water and the blood; and these three agree.", "critique": "Restaura la lezione originale autentica eliminando la corruzione medievale."}
        ],
        "corpus_cross_references": [
            {"reference": "Giovanni 19:34-35", "connection": "Dalla ferita al costato di Gesù uscirono sangue e acqua, a cui il testimone oculare attesta."},
            {"reference": "Deuteronomio 19:15", "connection": "La regola giuridica forense: un fatto deve essere confermato sulla parola di due o tre testimoni."},
            {"reference": "1 Giovanni 5:6", "connection": "Egli è colui che è venuto con acqua e sangue, Gesù Cristo; non con acqua soltanto, ma con acqua e con sangue."}
        ],
        "exegetical_synthesis": "1 Giovanni 5:7-8 rappresenta uno dei casi più celebri di interpolazione testuale nella storia della trasmissione manoscritta della Bibbia. Il cosiddetto 'Comma Johanneum' trinitario non esiste in nessun manoscritto greco originale antico ed è una glossa marginale latina introdotta nel testo stampato secoli dopo."
    },

    "Yesaya 9:5": {
        "passage_reference": "Yesaya 9:5",
        "original_language": "Biblical Hebrew",
        "source_text_full": "כִּי־יֶלֶד יֻלַּד־לָנוּ בֵּן נִתַּן־לָנוּ וַתְּהִי הַמִּשְׂרָה עַל־שִׁכְמוֹ וַיִּקְרָא שְׁמוֹ פֶּלֶא יוֹעֵץ אֵל גִּבּוֹר אֲבִיעַד שַׂר־שָׁלוֹם׃",
        "literal_translation": "Poiché un bambino è nato per noi, un figlio ci è stato dato; la sovranità sarà sulle sue spalle, e il suo nome sarà chiamato Consigliere di prodigi, Dio potente / Eroe divino, Padre perpetuo, Principe della pace.",
        "natural_translation": "Poiché per noi è nato un fanciullo, a noi è stato donato un figlio. L'autorità regale riposerà sulle sue spalle ed egli sarà chiamato: Consigliere Mirabile, Eroe Divino Potente, Padre per sempre, Principe della Pace.",
        "exegetical_context": ExegeticalContext(
            literary_genre="Profezia regale davidica / Canto di liberazione messianica",
            immediate_context="Isaia 9 segue l'invasione assira delle regioni di Zabulon e Neftali (Galilea), annunciando la liberazione mediante un re davidico giusto.",
            historical_cultural_setting="Regno di Giuda sotto Acaz (VIII sec. a.C.); nascita o insediamento del re Ezechia come segno di liberazione provvidenziale."
        ),
        "interlinear_tokens_override": [
            {"index": 1, "literal_gloss": "Poiché un bambino", "syntactic_role": "Congiunzione + Soggetto", "exegetical_note": "Yeled: fanciullo o infante nato."},
            {"index": 2, "literal_gloss": "è nato per noi", "syntactic_role": "Verbo Pual Perfetto", "exegetical_note": "Yullad-lanu: certezza del decreto profetico."},
            {"index": 3, "literal_gloss": "un figlio ci è stato dato", "syntactic_role": "Soggetto Parallelo + Verbo Nifal", "exegetical_note": "Ben nittan-lanu: dono regale di salvezza."},
            {"index": 4, "literal_gloss": "e la sovranità sarà", "syntactic_role": "Soggetto Politico Governativo", "exegetical_note": "Misrah: l'insegna del potere monarchico."},
            {"index": 5, "literal_gloss": "sulle sue spalle", "syntactic_role": "Complemento di Luogo Simbolico", "exegetical_note": "Sull'omero del re come mantello di governo."},
            {"index": 6, "literal_gloss": "e sarà chiamato il suo nome", "syntactic_role": "Verbo Qal con Waw Consecutivo", "exegetical_note": "Proclamazione della titolatura onorifica."},
            {"index": 7, "literal_gloss": "Consigliere Mirabile, Eroe Divino, Padre Perpetuo, Principe della Pace", "syntactic_role": "Titolatura Regale Quadrupla", "exegetical_note": "El Gibbor nel contesto dell'VIII sec. a.C. denota un guerriero valoroso assistito da Dio."}
        ],
        "syntactic_exegesis": {
            "poin_1": "I verbi al perfetto ebraico profetico 'yullad-lanu' e 'nittan-lanu' esprimono la certezza imminente del decreto divino.",
            "poin_2": "Il titolo 'El Gibbor': nel semitico antico, 'El' con l'aggettivo 'Gibbor' denota un campione o sovrano valoroso investito di potenza divina (cfr. Ezechiele 32:21 'elei gibborim').",
            "poin_3": "La formula 'Avi'ad' riflette la consuetudine orientale di chiamare il re benefattore 'padre del popolo in perpetuo'."
        },
        "manuscript_witnesses": [
            {"witness": "Grande Rotolo di Isaia (1QIsaa, II sec. a.C., Qumran)", "reading": "Testo consonantico fedele al Masoretico", "status": "Il manoscritto biblico completo più antico conosciuto"},
            {"witness": "Codex Leningradensis (B19a, 1008 d.C.)", "reading": "Testo Masoretico vocalizzato standard", "status": "Base della BHS"},
            {"witness": "Targum Jonathan (I sec. d.C.)", "reading": "Parafrasi aramaica messianica che attribuisce la titolatura regale all'inviato di Dio", "status": "Tradizione esegetica giudaica antica"}
        ],
        "translation_comparison": [
            {"version": "Significato dell'Ebraico Antico del I Secolo", "text": "Poiché un fanciullo è nato per noi, un figlio ci è stato donato; la sovranità poggerà sulle sue spalle, e il suo nome sarà proclamato: Consigliere di meraviglie, eroe divino potente, padre perpetuo del popolo, principe della pace.", "critique": "Standard di accuratezza primario: 'El Gibbor' nel contesto monarchico dell'VIII sec. a.C. designa un eroe o sovrano valoroso assistito da Dio, non l'Onnipotente YHWH."},
            {"version": "CEI", "text": "Poiché un bambino è nato per noi, ci è stato dato un figlio. Sulle sue spalle è il potere, e il suo nome sarà: Consigliere mirabile, Dio potente, Padre per sempre, Principe della pace.", "critique": "Traduce 'Dio potente' secondo la tradizione patristica anziché l'epiteto regale 'eroe divino potente' del contesto veterotestamentario."},
            {"version": "KJV", "text": "For unto us a child is born, unto us a son is given... and his name shall be called Wonderful, Counsellor, The mighty God, The everlasting Father, The Prince of Peace.", "critique": "Pone la maiuscola 'The mighty God', spingendo verso un'identificazione ontologica anacronistica rispetto alla teologia di Isaia."},
            {"version": "ESV", "text": "For to us a child is born, to us a son is given... and his name shall be called Wonderful Counselor, Mighty God, Everlasting Father, Prince of Peace.", "critique": "Ripete la formulazione classica senza rendere la sfumatura semantica dell'ufficio regale davidico."}
        ],
        "corpus_cross_references": [
            {"reference": "Ezechiele 32:21", "connection": "Uso del plurale 'elei gibborim' per indicare i sovrani e i capi guerrieri potenti della terra."},
            {"reference": "Salmi 45:6-7", "connection": "Il re viene apostrofato con 'Elohim', ma il versetto successivo chiarisce: 'Perciò Dio, il tuo Dio, ti ha unto con olio di letizia al di sopra dei tuoi compagni'."},
            {"reference": "Isaia 10:21", "connection": "Il resto d'Israele ritornerà all''El Gibbor', collegando la speranza davidica alla redenzione di YHWH."}
        ],
        "exegetical_synthesis": "In Isaia 9:5, l'annuncio della nascita del fanciullo regale utilizza titoli onorifici orientali che esaltano il ruolo del futuro sovrano davidico. Il titolo 'El Gibbor' denota un 'eroe divino' o 're potente per mezzo di Dio', e non può essere interpretato come identificazione dell'infante con l'Unico Dio YHWH, principio inconcepibile per la teologia del profeta Isaia."
    }
}
