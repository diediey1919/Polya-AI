#!/usr/bin/env python3
"""
Build Core Judaism Knowledge Objects
Adheres to Master Prompt Sections 9, 10, 11, 12, 13, 14, 15, 16.
"""
import json
import os

dirs = [
    "/home/ubuntu/Polya-AI/data/judaism/core",
    "/home/ubuntu/apologetica/data/judaism/core"
]

tanakh_canon = {
    "version": "1.0.0",
    "canon_name": "Tanakh (Torah, Nevi'im, Ketuvim)",
    "total_books_traditional": 24,
    "divisions": [
        {
            "division": "TORAH",
            "hebrew": "תורה",
            "translation": "Instruction / Teaching / Law",
            "books": [
                {
                    "hebrew_title": "בראשית", "transliteration": "Bereshit", "english_title": "Genesis",
                    "chapters": 50, "genre": "Cosmogony, Primeval History, Ancestral Narratives",
                    "key_themes": ["Creation ex nihilo vs ordering chaos", "Image of God (Tzelem Elohim)", "Covenant with Noah", "Abrahamic election & covenant", "Patriarchs and Joseph narrative"],
                    "primary_witnesses": ["Codex Leningradensis B19a", "Aleppo Codex", "4QGen-b", "4QGen-j"],
                    "scholarly_dating_notes": "Classical documentary hypothesis sees J, E, P, D strata compiled in post-exilic Persian era; traditional rabbinic view asserts unitary Mosaic authorship at Sinai."
                },
                {
                    "hebrew_title": "שמות", "transliteration": "Shemot", "english_title": "Exodus",
                    "chapters": 40, "genre": "Historical Epic, Legal Code, Cultic Architecture",
                    "key_themes": ["Liberation from Egyptian bondage", "Theophany at Mount Sinai", "Decalogue (Ten Words)", "Book of the Covenant (Exod 21-23)", "Mishkan (Tabernacle) design"],
                    "primary_witnesses": ["4QExod-a", "4QpaleoExod-m", "Codex Leningradensis B19a"]
                },
                {
                    "hebrew_title": "ויקרא", "transliteration": "Vayikra", "english_title": "Leviticus",
                    "chapters": 27, "genre": "Priestly Ritual Law, Holiness Code",
                    "key_themes": ["Korbanot (Sacrificial offerings)", "Priestly consecration", "Kashrut & dietary boundaries", "Yom Kippur ritual (Lev 16)", "Holiness Code (Lev 17-26: 'Love your neighbor as yourself' Lev 19:18)"],
                    "primary_witnesses": ["11QpaleoLev", "4QLev-b", "Codex Leningradensis B19a"]
                },
                {
                    "hebrew_title": "במדבר", "transliteration": "Bamidbar", "english_title": "Numbers",
                    "chapters": 36, "genre": "Wilderness Census, Narrative, Legal Additions",
                    "key_themes": ["Desert encampment & marching orders", "Rebellions of Korah and the Spies", "Priestly Blessing (Birkat Kohanim 6:24-26)", "Balaam oracles and Star of Jacob (Num 24:17)"],
                    "primary_witnesses": ["Ketef Hinnom silver amulets (KH1/KH2 - c. 600 BCE)", "4QNum-b"]
                },
                {
                    "hebrew_title": "דברים", "transliteration": "Devarim", "english_title": "Deuteronomy",
                    "chapters": 34, "genre": "Farewell Orations, Covenant Renewal, Legal Restatement",
                    "key_themes": ["Shema Yisrael (Deut 6:4-9)", "Centralization of sacrificial cult in Jerusalem (Deut 12)", "Prophetic test & prohibition of adding/subtracting (Deut 13, 18)", "Death of Moses"],
                    "primary_witnesses": ["4QDeut-n (All Souls Deuteronomy)", "4QDeut-q", "Nash Papyrus"]
                }
            ]
        },
        {
            "division": "NEVI'IM",
            "hebrew": "נביאים",
            "translation": "Prophets",
            "subdivisions": [
                {
                    "subdivision": "FORMER_PROPHETS",
                    "hebrew": "נביאים ראשונים",
                    "books": [
                        {"hebrew_title": "יהושע", "english_title": "Joshua", "chapters": 24},
                        {"hebrew_title": "שופטים", "english_title": "Judges", "chapters": 21},
                        {"hebrew_title": "שמואל", "english_title": "Samuel (1-2 Samuel as 1 book)", "chapters": 55},
                        {"hebrew_title": "מלכים", "english_title": "Kings (1-2 Kings as 1 book)", "chapters": 47}
                    ]
                },
                {
                    "subdivision": "LATTER_PROPHETS",
                    "hebrew": "נביאים אחרונים",
                    "books": [
                        {"hebrew_title": "ישעיהו", "english_title": "Isaiah", "chapters": 66, "notes": "Witnesses include 1QIsa-a. Academic scholarship identifies Proto-Isaiah (1-39), Deutero-Isaiah (40-55), Trito-Isaiah (56-66); rabbinic tradition views Isaiah as a unitary prophetic work."},
                        {"hebrew_title": "ירמיהו", "english_title": "Jeremiah", "chapters": 52, "notes": "LXX text is ~15% shorter than MT and has different chapter arrangement, corroborated by 4QJer-b."},
                        {"hebrew_title": "יחזקאל", "english_title": "Ezekiel", "chapters": 48, "notes": "Merkavah divine chariot vision (ch. 1) founding Jewish mystical speculation; Temple restoration vision (ch. 40-48)."},
                        {"hebrew_title": "תרי עשר", "english_title": "The Twelve Minor Prophets (counted as 1 book)", "books": ["Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"]}
                    ]
                }
            ]
        },
        {
            "division": "KETUVIM",
            "hebrew": "כתובים",
            "translation": "Writings",
            "books": [
                {"hebrew_title": "תהלים", "english_title": "Psalms (Tehillim)", "chapters": 150, "notes": "Divided into 5 books mirroring Torah; extensive Qumran witnesses (11QPsa)."},
                {"hebrew_title": "משלי", "english_title": "Proverbs (Mishlei)", "chapters": 31},
                {"hebrew_title": "איוב", "english_title": "Job (Iyyov)", "chapters": 42},
                {"hebrew_title": "שיר השירים", "english_title": "Song of Songs", "megillah": True},
                {"hebrew_title": "רות", "english_title": "Ruth", "megillah": True},
                {"hebrew_title": "איכה", "english_title": "Lamentations", "megillah": True},
                {"hebrew_title": "קהלת", "english_title": "Ecclesiastes", "megillah": True},
                {"hebrew_title": "אסתר", "english_title": "Esther", "megillah": True},
                {"hebrew_title": "דניאל", "english_title": "Daniel", "chapters": 12, "notes": "Bilingual Hebrew and Aramaic (Dan 2:4b–7:28); apocalypses and Son of Man vision."},
                {"hebrew_title": "עזרא ונחמיה", "english_title": "Ezra-Nehemiah (counted as 1 book)", "chapters": 23},
                {"hebrew_title": "דברי הימים", "english_title": "Chronicles (1-2 Chronicles as 1 book)", "chapters": 65, "notes": "Final book of the Tanakh in traditional Jewish canonical order ending with Cyrus's proclamation of return."}
            ]
        }
    ],
    "tanakh_vs_old_testament_differences": {
        "canon_count": {
            "tanakh": 24,
            "protestant_ot": 39,
            "catholic_ot": 46,
            "eastern_orthodox_ot": 49
        },
        "order_significance": {
            "tanakh_conclusion": "Chronicles ends with 2 Chron 36:23: 'Whoever among you of all His people... let him go up (ve-ya'al) to Jerusalem' — an open-ended invitation to return to the Land.",
            "christian_ot_conclusion": "Concludes with Malachi 4:5-6 predicting Elijah's coming before the Day of the Lord, structurally serving as an immediate theological bridge to John the Baptist in Matthew."
        },
        "categorization_differences": "Christian Bibles group Daniel among the Major Prophets; Jewish canon places Daniel in Ketuvim (Writings) because Daniel was a court visionary rather than a classical public prophet (Navi)."
    }
}

textual_traditions = {
    "version": "1.0.0",
    "traditions": [
        {
            "name": "Masoretic Text (MT)",
            "definition": "The standard authoritative Hebrew text preserved and pointed by the Tiberian Masoretes (8th-10th c. CE), featuring consonants, vowels (nikkud), cantillation (te'amim), and marginal notes.",
            "major_manuscripts": [
                {"name": "Codex Leningradensis B19a", "date": "1008 CE", "significance": "Complete Tanakh, basis for critical scholarly editions (BHS, BHQ)."},
                {"name": "Aleppo Codex", "date": "c. 920 CE", "significance": "Most accurate Masoretic codex verified by Maimonides."}
            ],
            "scribal_rules": "Strict Sofer rules: ink made from soot and gallnut, parchment from kosher skins, exact spacing, prohibition of copying from memory, counting of words and middle letters."
        },
        {
            "name": "Dead Sea Scrolls (DSS)",
            "definition": "Over 220 biblical manuscripts found at Qumran (c. 250 BCE–68 CE) demonstrating textual pluralism in the late Second Temple era.",
            "textual_families_identified": [
                {"family": "Proto-Rabbinic / Proto-Masoretic", "share": "~50%", "examples": ["1QIsa-b", "4QGen-b"]},
                {"family": "Pre-Samaritan", "share": "~15%", "examples": ["4QpaleoExod-m", "4QNum-b"]},
                {"family": "Septuagintal Hebrew Vorlage", "share": "~5%", "examples": ["4QJer-b", "4QSam-a"]},
                {"family": "Non-Aligned / Sectarian Orthography", "share": "~30%", "examples": ["1QIsa-a", "4QDeut-m"]}
            ]
        },
        {
            "name": "Septuagint (LXX)",
            "definition": "Ancient Greek translation of the Hebrew Scriptures begun in 3rd c. BCE in Alexandria, reflecting pre-Masoretic Hebrew Vorlagen and Hellenistic Jewish theology."
        },
        {
            "name": "Samaritan Pentateuch (SP)",
            "definition": "Independent transmission of the Torah in Paleo-Hebrew script preserved by the Samaritan community, containing Mount Gerizim cultic additions and linguistic regularizations."
        },
        {
            "name": "Aramaic Targumim",
            "definition": "Aramaic interpretive translations recited in ancient synagogues: Targum Onkelos (Torah) and Targum Jonathan (Prophets), capturing early rabbinic interpretations."
        }
    ]
}

hebrew_aramaic_lexicon = {
    "version": "1.0.0",
    "terms": [
        {
            "term": "Almah",
            "hebrew": "עַלְמָה",
            "morphology": "Noun feminine singular",
            "semantic_range": "Young woman of childbearing age, adolescent girl; does not denote anatomical virginity (which is specifically בְּתוּלָה / Bethulah).",
            "biblical_occurrences": ["Gen 24:43", "Exod 2:8", "Isa 7:14", "Ps 68:26", "Prov 30:19", "Song 1:3", "Song 6:8"],
            "apologetic_debate": {
                "locus": "Isaiah 7:14 ('Hineh ha-almah harah ve-yoledet ben...')",
                "christian_interpretation": "Interprets as 'virgin birth' based on LXX translation 'parthenos' (παρθένος) cited in Matthew 1:23.",
                "jewish_refutation": "The Hebrew word for virgin is Bethulah (used elsewhere in Isaiah, e.g. 23:12, 37:22, 62:5). 'Almah refers to a young woman present in King Ahaz's 8th-century BCE court (likely the prophet's wife or Queen Abi), whose impending child's birth serves as a contemporary sign of deliverance from Pekah and Rezin."
            }
        },
        {
            "term": "Mashiach",
            "hebrew": "מָשִׁיחַ",
            "morphology": "Passive participle masculine singular of the verb מָשַׁח (mashach - to smear or anoint with oil)",
            "semantic_range": "Anointed one; applied in the Tanakh to Aaron and the High Priests (Lev 4:3), Saul (1 Sam 24:6), David (2 Sam 19:22), and even the Persian King Cyrus (Isa 45:1).",
            "theological_evolution": "Evolved in late Second Temple and Rabbinic Judaism to denote the future human Davidic monarch who will gather the Jewish exiles, restore the Temple, and inaugurate global peace."
        },
        {
            "term": "Elohim",
            "hebrew": "אֱלֹהִים",
            "morphology": "Noun masculine plural (grammatically construed with singular verbs and adjectives when referring to the True God)",
            "semantic_range": "God (singular supreme deity when taking singular verb); gods/pagan deities (when taking plural verb, Exod 20:3); judges/magistrates (Exod 21:6, 22:7); supernatural celestial beings (Ps 8:6).",
            "apologetic_debate": {
                "christian_claim": "Argues the plural ending '-im' hints at the Trinity.",
                "jewish_refutation": "Pluralis excellentiae / majestic plural standard in Semitic grammar (similar to Adonim / Ba'alim). When referring to YHWH, the accompanying verb is always strictly singular (e.g. Genesis 1:1 'Bara Elohim', not 'Bar'u Elohim')."
            }
        },
        {
            "term": "Teshuvah",
            "hebrew": "תְּשׁוּבָה",
            "morphology": "Abstract verbal noun from the root שׁ-ו-ב (shuv - to return / turn back)",
            "semantic_range": "Repentance, returning to the divine path.",
            "components_in_halakha": [
                "Hakarat ha-chet (recognition of sin)",
                "Charatah (sincere remorse)",
                "Azivat ha-chet (practical cessation and abandonment of the sinful behavior)",
                "Viduy (verbal confession)",
                "Kabbalah le-haba (solemn resolution not to repeat the act)",
                "Piyus / Mechilah (asking forgiveness and making financial/interpersonal restitution if the sin harmed a fellow human)"
            ]
        },
        {
            "term": "Go'el",
            "hebrew": "גֹּאֵל",
            "morphology": "Participle of root ג-א-ל (ga'al - to redeem)",
            "semantic_range": "Kinsman-redeemer who buys back family land (Lev 25:25), redeems relatives from servitude (Lev 25:48), or acts as blood avenger (Num 35:19); applied metonymically to God redeeming Israel from Egypt and Babylon."
        }
    ]
}

halakha_mitzvot = {
    "version": "1.0.0",
    "structure": {
        "oral_and_written_torah": {
            "written_torah": "The text of the Pentateuch (Chumash), containing commandments that are frequently brief, ambiguous, or dependent on unwritten definitions (e.g. 'You shall bind them for a sign upon your hand' — the Written Torah never describes Tefillin; 'You shall slaughter of your cattle... as I have commanded you' Deut 12:21 — the slaughter procedure is nowhere written in the Torah).",
            "oral_torah": "The divine explanations, definitions, and jurisprudential hermeneutical principles (Thirteen Middot of Rabbi Ishmael) revealed at Sinai and transmitted orally from Moses to Joshua, Elders, Prophets, and the Men of the Great Assembly until codified in the Mishnah and Talmud."
        },
        "613_commandments": {
            "enumeration": "Taryag Mitzvot (613): 248 positive commandments (corresponding traditionally to the limbs of the human body) and 365 negative commandments (corresponding to the solar days).",
            "authoritative_catalog": "Maimonides Sefer Ha-Mitzvot (Book of the Commandments), organizing each command with scriptural proof-texts."
        },
        "shabbat": {
            "definition": "Weekly day of cessation and holy sanctification from Friday sunset to Saturday nightfall.",
            "core_halakha": "Prohibition of 39 categories of creative work (Avot Melakhot) derived from the construction of the Tabernacle in the wilderness.",
            "supreme_principle": "Pikuach Nefesh dohe Shabbat: Saving a human life overrides all Shabbat prohibitions (except idolatry, murder, and forbidden sexual relations)."
        },
        "kashrut": {
            "definition": "Jewish dietary laws based on biblical commands in Leviticus 11 and Deuteronomy 14.",
            "categories": [
                "Land animals must chew the cud and have split hooves.",
                "Aquatic creatures must have both fins and scales (excluding shellfish and catfish).",
                "Birds must not be birds of prey (24 forbidden species listed in Torah).",
                "Shechita (instantaneous ritual severance of trachea and esophagus with a surgically sharp knife without nicks).",
                "Bedikah (inspection of lungs for adhesions or perforations).",
                "Removal of blood (Salting / Melichah or broiling) and the sciatic nerve (Gid Ha-Nasheh, Gen 32:33).",
                "Strict separation of meat and dairy based on the threefold prohibition: 'Do not boil a kid in its mother's milk' (Exod 23:19, 34:26; Deut 14:21)."
            ]
        },
        "cessation_of_sacrifice": {
            "reason": "Halakhic prohibition: Deuteronomy 12:13-14 strictly forbids offering sacrifices anywhere except the chosen place (Jerusalem Temple Mount). Once the Second Temple was destroyed by Rome in 70 CE, offering animal sacrifices became halakhically illegal.",
            "replacement": "Rabbinic Judaism activated existing biblical mechanisms: Prayer ('We will render the prayer of our lips as calves' Hosea 14:3), Teshuvah (repentance), Charity (Tzedakah), and Torah study (Talmud Berakhot 26b, Pesikta de-Rav Kahana 16)."
        }
    }
}

theology = {
    "version": "1.0.0",
    "concepts": [
        {
            "id": "THEO-MONO",
            "title": "Absolute Divine Unity (Yihud Ha-Shem)",
            "definition": "God is singular, indivisible, non-composite, eternal, incorporeal, and completely transcendent. Rejects all forms of dualism, polytheism, and Trinity.",
            "primary_prooftexts": ["Deuteronomy 6:4 (Shema)", "Isaiah 45:5-7 ('I am YHWH and there is no other...')"],
            "maimonidean_principles": "Principles 1, 2, and 3 of Rambam's Thirteen Principles: God exists, God is an absolute non-composite unity, God is non-physical and without bodily form or accident."
        },
        {
            "id": "THEO-COVENANT",
            "title": "The Covenants (Britot)",
            "types": [
                {"name": "Noahic Covenant", "scope": "All humankind (7 Noahide Laws: no idolatry, blasphemy, murder, theft, sexual immorality, eating flesh from living animal, establishing courts of justice). Non-Jews who observe these are righteous of the nations and merit the World to Come."},
                {"name": "Abrahamic Covenant", "scope": "Abraham and his physical seed; sealed by circumcision (Brit Milah) and promise of Land."},
                {"name": "Sinaitic Covenant", "scope": "The entire nation of Israel; mutual bilateral treaty accepting Torah and 613 Mitzvot."}
            ]
        },
        {
            "id": "THEO-SIN-ATONEMENT",
            "title": "Sin and Atonement without Original Sin",
            "doctrine": "Judaism does not teach that humanity inherits the moral guilt or fallen nature of Adam and Eve. Every human is born morally pure with a Yetzer Ha-Tov (inclination toward good) and Yetzer Ha-Ra (inclination toward self-interest/passion). Sin (chet) is a failure to hit the mark or violation of command, rectified directly through Teshuvah, restitution, and divine mercy (Ezekiel 18:20-23)."
        },
        {
            "id": "THEO-MASHIACH",
            "title": "The Jewish Concept of Messiah (Mashiach)",
            "criteria": [
                "Mortal human king, physical descendant of King David and Solomon via direct patrilineal lineage (Jer 23:5, 33:17).",
                "Rebuilder of the Third Temple in Jerusalem (Ezekiel 37:26-28).",
                "Ingatherer of all Jewish exiles from global dispersion back to the Land of Israel (Isaiah 11:12).",
                "Inaugurator of universal disarmament and global peace: 'Nation shall not lift up sword against nation, neither shall they learn war anymore' (Isaiah 2:4, Micah 4:3).",
                "Universal knowledge of the One True God throughout the earth (Isaiah 11:9, Zechariah 14:9).",
                "Full restoration of Torah observance and judicial Sanhedrin (Isaiah 1:26).",
                "He does NOT die prior to completing these tasks. If a claimant is killed without achieving them, he is not the Messiah (Maimonides, Hilkhot Melakhim 11:4)."
            ]
        }
    ]
}

worship_and_lifecycle = {
    "version": "1.0.0",
    "worship": {
        "synagogue": "Beit Knesset (House of Gathering) and Beit Midrash (House of Study). Requires a Minyan (quorum of 10 adults).",
        "daily_prayers": [
            {"service": "Shacharit", "time": "Morning", "established_by": "Traditional patriarch Abraham"},
            {"service": "Minchah", "time": "Afternoon", "established_by": "Traditional patriarch Isaac"},
            {"service": "Maariv", "time": "Evening", "established_by": "Traditional patriarch Jacob"}
        ],
        "core_prayers": ["Shema Yisrael", "Amidah (The 19 blessings of the Standing Prayer)", "Aleinu Le-Shabe'ach", "Kaddish"]
    },
    "lifecycle": [
        {"rite": "Brit Milah", "timing": "8th day after birth", "significance": "Covenant of circumcision entering child into Abrahamic covenant"},
        {"rite": "Bar Mitzvah / Bat Mitzvah", "timing": "Age 13 for boys / Age 12-13 for girls", "significance": "Legal adulthood where the individual becomes obligated in all mitzvot"},
        {"rite": "Kiddushin & Chuppah", "timing": "Marriage", "significance": "Wedding canopy, Ketubah (marriage contract protecting bride's rights), Seven Blessings (Sheva Berakhot)"},
        {"rite": "Avelut (Mourning)", "stages": ["Aninut (death to burial)", "Shiva (7-day intensive mourning)", "Shloshim (30-day transition)", "Yahrzeit & Kaddish (11 months recitation for parent)"]}
    ]
}

festivals = {
    "version": "1.0.0",
    "calendar_system": "Lunisolar calendar (months pegged to moon cycle, leap month Adar II added 7 times in 19 years to keep Pesach in the spring).",
    "holidays": [
        {
            "name": "Pesach (Passover)",
            "date": "15–21/22 Nisan",
            "biblical_origin": "Exodus 12: liberation from Egypt, sacrifice of paschal lamb.",
            "rabbinic_development": "Seder night, eating Matzah and Maror, recitation of the Haggadah, four cups of wine.",
            "modern_observance": "Celebrated worldwide by all denominations as festival of freedom and national birth."
        },
        {
            "name": "Shavuot (Feast of Weeks)",
            "date": "6–7 Sivan",
            "biblical_origin": "Exodus 23, 34; Leviticus 23: Feast of first fruits (Bikkurim) and wheat harvest 50 days after Pesach.",
            "rabbinic_development": "Zman Matan Torateinu (Time of the Giving of the Torah at Mount Sinai), all-night Torah study (Tikkun Leil Shavuot), reading Book of Ruth."
        },
        {
            "name": "Sukkot (Feast of Booths)",
            "date": "15–21 Tishrei",
            "biblical_origin": "Leviticus 23: dwelling in temporary booths commemorating wilderness wanderings.",
            "observance": "Dwelling in Sukkah, waving Four Species (Arba'at Ha-Minim: Etrog, Lulav, Hadas, Aravah), followed by Shemini Atzeret and Simchat Torah."
        },
        {
            "name": "Rosh Hashanah (Jewish New Year)",
            "date": "1–2 Tishrei",
            "biblical_origin": "Leviticus 23:24: Yom Teru'ah (Day of Shofar Blasting).",
            "rabbinic_development": "Yom Ha-Din (Day of Judgment for all creatures), sounding 100 blasts of the ram's horn, dipping apples in honey."
        },
        {
            "name": "Yom Kippur (Day of Atonement)",
            "date": "10 Tishrei",
            "biblical_origin": "Leviticus 16 & 23: Sabbath of Sabbaths, ritual purgation of sanctuary.",
            "rabbinic_development": "25-hour complete fast from food, drink, washing, leather shoes, and marital relations; extensive communal confession (Al Chet) and final Ne'ilah service."
        },
        {
            "name": "Hanukkah (Festival of Lights)",
            "date": "25 Kislev–2/3 Tevet",
            "origin": "Historical Second Temple victory (164 BCE) of Maccabees over Seleucid Syrian-Greeks and rededication of the Temple.",
            "observance": "Kindling 8-branched Menorah (Hanukkiah), eating oil-fried foods (latkes, sufganiyot) commemorating the miracle of the oil flask."
        },
        {
            "name": "Purim",
            "date": "14 Adar (15 Adar in walled cities / Shushan Purim)",
            "origin": "Book of Esther: deliverance of Persian Jews from Haman's genocide decree.",
            "observance": "Reading Megillat Esther, sending gifts of food (Mishloach Manot), charity to the poor (Matanot La-Evyonim), festive meal."
        }
    ]
}

data_map = {
    "tanakh_canon.json": tanakh_canon,
    "textual_traditions.json": textual_traditions,
    "hebrew_aramaic_lexicon.json": hebrew_aramaic_lexicon,
    "halakha_mitzvot.json": halakha_mitzvot,
    "theology.json": theology,
    "worship_and_lifecycle.json": worship_and_lifecycle,
    "festivals.json": festivals
}

for name, payload in data_map.items():
    for base in dirs:
        p = os.path.join(base, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Wrote {p}")

print("Core Judaism Knowledge Layer generated successfully.")
