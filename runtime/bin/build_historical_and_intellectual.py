#!/usr/bin/env python3
"""
Build Historical and Intellectual Judaism Knowledge Layers
Adheres to Master Prompt Sections 17, 18, 19, 20, 21, 22, 30, 31.
"""
import json
import os

hist_dirs = [
    "/home/ubuntu/Polya-AI/data/judaism/historical",
    "/home/ubuntu/apologetica/data/judaism/historical"
]
intel_dirs = [
    "/home/ubuntu/Polya-AI/data/judaism/intellectual",
    "/home/ubuntu/apologetica/data/judaism/intellectual"
]

# -------------------------------------------------------------
# HISTORICAL KNOWLEDGE
# -------------------------------------------------------------
ancient_israel = {
    "version": "1.0.0",
    "period": "IRON_AGE_ISRAEL",
    "timeline": [
        {"era": "Patriarchal and Tribal League", "dates": "c. 13th–11th c. BCE", "key_events": ["Merneptah Stele (c. 1208 BCE: first extra-biblical mention of 'Israel')", "Shiloh sanctuary"]},
        {"era": "United Monarchy", "dates": "c. 1020–931 BCE", "key_events": ["Saul, David (Tel Dan Stele 'House of David'), Solomon", "First Temple built on Mount Moriah"]},
        {"era": "Divided Monarchy", "dates": "931–586 BCE", "key_events": ["Northern Kingdom of Israel (Samaria) fell 722 BCE to Sargon II of Assyria; 10 tribes dispersed", "Southern Kingdom of Judah (Jerusalem) survived Sennacherib's siege 701 BCE (Siloam inscription)"]},
        {"era": "Exile and Restoration", "dates": "586–332 BCE", "key_events": ["Nebuchadnezzar destroyed First Temple 586 BCE", "Cyrus the Great decreed return 538 BCE", "Second Temple completed 516 BCE under Zerubbabel", "Ezra the Scribe reinstated Torah public reading"]}
    ]
}

second_temple = {
    "version": "1.0.0",
    "period": "ROMAN_SECOND_TEMPLE",
    "sectarianism": {
        "pharisees": {
            "name": "Pharisees (Perushim)",
            "social_base": "Urban scribes, middle class, sages",
            "theology": ["Belief in Oral Torah alongside Written Torah", "Resurrection of the dead", "Angels and divine providence balanced with human free will", "Purity laws extended to the domestic table"],
            "successor": "Rabbinic Judaism is the direct historical heir to the Pharisaic movement"
        },
        "sadducees": {
            "name": "Sadducees (Tzedokim)",
            "social_base": "Aristocratic high priesthood, wealthy Temple elite",
            "theology": ["Rejection of the Oral Torah; adherence strictly to the written Pentateuch", "Denial of bodily resurrection of the dead", "Denial of angels and deterministic fate", "Strict literalism regarding purity and Temple penalties"],
            "disappearance": "Disappeared following the destruction of the Second Temple in 70 CE when the priestly sacrificial apparatus ceased"
        },
        "essenes": {
            "name": "Essenes (likely Qumran Community / Yahad)",
            "social_base": "Ascetic, monastic, priestly desert separatists",
            "theology": ["Rejection of the Jerusalem Temple priesthood as corrupt and illegitimate", "Solar 364-day calendar (vs lunisolar rabbinic calendar)", "Apocalyptic dualism: Sons of Light vs Sons of Darkness", "Extensive ritual immersion, communal property, strict hierarchy"],
            "evidence": "Dead Sea Scrolls (1QS, 1QM, Damascus Document, 4QMMT)"
        },
        "zealots_sicarii": {
            "name": "Zealots (Kannaim) & Sicarii",
            "social_base": "Militant nationalists founded by Judas the Galilean (6 CE)",
            "theology": ["No ruler but God (rejection of Roman tax as idolatry)", "Active military revolt to force divine intervention", "Led defense of Jerusalem (70 CE) and Masada (73 CE)"]
        }
    },
    "destruction_70_ce": {
        "event": "Siege and Destruction of Second Temple by Roman General Titus in 70 CE",
        "consequences": [
            "End of animal sacrifices and hereditary Aaronic priestly hegemony",
            "Yochanan ben Zakkai established the Academy at Yavneh (Kerem Be-Yavneh)",
            "Transformation from a localized Temple-sacrificial cult to a portable text-, prayer-, and halakha-based global religious system"
        ]
    }
}

rabbinic_era = {
    "version": "1.0.0",
    "stages": [
        {
            "stage": "Tannaitic Period",
            "dates": "c. 70–220 CE",
            "geographic_center": "Land of Israel (Yavneh, Usha, Beit She'arim, Sepphoris)",
            "prominent_sages": ["Rabbi Yochanan ben Zakkai", "Rabbi Akiva", "Rabbi Ishmael", "Rabbi Meir", "Rabbi Yehudah Ha-Nasi"],
            "master_work": "Mishnah (codified c. 200 CE), Tosefta, Midrash Halakha"
        },
        {
            "stage": "Amoraic Period",
            "dates": "c. 220–500 CE",
            "geographic_centers": ["Land of Israel (Tiberias, Caesarea)", "Babylonia (Sura, Pumbedita, Nehardea)"],
            "prominent_sages": ["Rav (Abba Arikha)", "Shmuel", "Rabbi Yochanan bar Nappaha", "Resh Lakish", "Rava", "Abaye", "Rav Ashi", "Ravina"],
            "master_works": ["Jerusalem Talmud (Talmud Yerushalmi, c. 380-400 CE)", "Babylonian Talmud (Talmud Bavli, c. 500-600 CE)"]
        },
        {
            "stage": "Savoraic Period",
            "dates": "c. 500–600 CE",
            "role": "Editorial smoothing, anonymous dialectical framing (Stamkait) of the Babylonian Talmud"
        },
        {
            "stage": "Geonic Period",
            "dates": "c. 600–1050 CE",
            "geographic_center": "Babylonia (Sura & Pumbedita academies under Abbasid Caliphate)",
            "prominent_geonim": ["Mar Rav Yehudai Gaon", "Rabbi Amram Gaon (first complete Siddur)", "Rabbi Saadia Gaon", "Rabbi Sherira Gaon (historical Iggeret)", "Rabbi Hai Gaon"],
            "impact": "Established Babylonian Talmud as the normative universal authority throughout the Islamic and Christian diaspora"
        }
    ]
}

medieval_era = {
    "version": "1.0.0",
    "period": "MEDIEVAL_RISHONIM (c. 1050–1500 CE)",
    "traditions": [
        {
            "stream": "Franco-German (Ashkenaz)",
            "centers": ["Troyes", "Sens", "Worms", "Speyer", "Mainz", "Regensburg"],
            "key_figures": ["Rabbeinu Gershom Me'or Ha-Golah (enactments banning polygamy and non-consensual divorce)", "Rashi (1040-1105)", "The Tosafists (Ba'alei Ha-Tosafot: Rashbam, Rabbeinu Tam, Ri of Dampierre)"],
            "focus": "Micro-dialectical Talmudic harmonization, contextual biblical peshat, liturgical poetry (Piyyut), martyr theology (Kiddush Ha-Shem during Crusades)"
        },
        {
            "stream": "Sephardic & Provencal (Sefarad & Provence)",
            "centers": ["Cordoba", "Toledo", "Lucena", "Barcelona", "Gerona", "Lunel", "Fustat/Old Cairo"],
            "key_figures": ["Isaac Alfasi (Rif)", "Judah Halevi", "Abraham Ibn Ezra", "Maimonides (Rambam)", "Nachmanides (Ramban)", "Solomon ben Aderet (Rashba)", "Yom Tov of Seville (Ritva)"],
            "focus": "Systematic legal codification, Hebrew grammar, Arabic-Aristotelian philosophy, science, medicine, and the emergence of classical Kabbalah"
        },
        {
            "historic_events": [
                "The First Crusade massacres (Rhineland, 1096)",
                "Expulsion of Jews from England (1290) and France (1306, 1394)",
                "Disputation of Barcelona (1263: Nachmanides vs Pablo Christiani)",
                "Disputation of Tortosa (1413–1414)",
                "Spanish Inquisition established 1478; Alhambra Decree and Expulsion from Spain (1492)"
            ]
        }
    ]
}

modern_era = {
    "version": "1.0.0",
    "developments": [
        {
            "name": "Haskalah (Jewish Enlightenment)",
            "dates": "c. 1770–1880 CE",
            "founder": "Moses Mendelssohn (Berlin)",
            "ideals": ["Integration into European society ('Be a Jew at home and a man in the street')", "Revival of pure biblical Hebrew", "Secular education, sciences, linguistic assimilation"]
        },
        {
            "name": "Emancipation and Modern Denominational Splintering",
            "dates": "19th century",
            "outcomes": [
                "Granting of citizenship to Jews across Western Europe",
                "Emergence of Reform Judaism in Germany (Abraham Geiger, Samuel Holdheim)",
                "Counter-reaction of Neo-Orthodoxy (Rabbi Samson Raphael Hirsch: Torah im Derekh Eretz)",
                "Positive-Historical Judaism / Conservative Judaism (Zechariah Frankel)"
            ]
        },
        {
            "name": "The Shoah (Holocaust)",
            "dates": "1933–1945 CE",
            "event": "Systematic, industrialized genocide orchestrated by Nazi Germany murdering 6 million Jews (two-thirds of European Jewry)",
            "theological_impact": "Post-Holocaust Jewish theology (Emil Fackenheim's 614th Commandment not to give Hitler posthumous victories; Richard Rubenstein; Elie Wiesel; Rabbi Joseph B. Soloveitchik Kol Dodi Dofek)"
        },
        {
            "name": "Zionism and the Re-establishment of the State of Israel",
            "dates": "1897 / 1948 CE",
            "principles": [
                "Modern political Zionism founded by Theodor Herzl (1897 First Zionist Congress in Basel)",
                "Proclamation of the State of Israel on 14 May 1948 (5 Iyar 5708)",
                "Crucial Distinction: Political Zionism as a modern national-liberation movement vs the eternal religious-covenantal yearning for Zion (Epistemic Rule 1.5)"
            ]
        }
    ]
}

# -------------------------------------------------------------
# INTELLECTUAL KNOWLEDGE
# -------------------------------------------------------------
philosophy = {
    "version": "1.0.0",
    "thinkers": [
        {
            "name": "Philo of Alexandria (c. 20 BCE–50 CE)",
            "school": "Hellenistic Jewish Platonism",
            "contribution": "Pioneered allegorical interpretation of the Pentateuch; formulated the concept of the Logos as the divine mind and creative instrument of God."
        },
        {
            "name": "Saadia Gaon (882–942 CE)",
            "school": "Judeo-Arabic Kalam Rationalism",
            "work": "Kitab al-Amanat wal-I'tiqadat (Beliefs and Opinions)",
            "contribution": "Demonstrated that divine revelation and human reason (aql) are mutually harmonious; categorized commandments into rational laws (mitzvot sikhliyyot) and revelatory laws (mitzvot shim'iyyot)."
        },
        {
            "name": "Moses Maimonides (Rambam, 1138–1204 CE)",
            "school": "Medieval Aristotelian Rationalism",
            "work": "Moreh Nevukhim (Guide of the Perplexed)",
            "contribution": "Radical negative theology (Via Negativa: God can only be described by what He is not); uncompromising rejection of anthropomorphism; formulated the Thirteen Principles of Faith (Shloshah Asar Ikkarim)."
        },
        {
            "name": "Hasdai Crescas (c. 1340–1410 CE)",
            "school": "Anti-Aristotelian Medieval Philosophy",
            "work": "Or Hashem (Light of the Lord)",
            "contribution": "Rigorous critique of Aristotelian physics and Maimonidean rationalism; emphasized divine love, joy, and emotional devotion over pure intellect."
        },
        {
            "name": "Baruch Spinoza (1632–1677 CE)",
            "school": "Early Modern Rationalist Metaphysics",
            "work": "Tractatus Theologico-Politicus / Ethics",
            "contribution": "Excommunicated by Amsterdam Portuguese-Jewish community; pioneered modern historical-critical biblical criticism; formulated pantheism/panentheism (Deus sive Natura)."
        },
        {
            "name": "Moses Mendelssohn (1729–1786 CE)",
            "school": "Haskalah Enlightenment Philosophy",
            "work": "Jerusalem: Or on Religious Power and Judaism (1783)",
            "contribution": "Argued Judaism contains no dogmatic coercion of belief; Judaism is 'revealed legislation' rather than 'revealed dogma'; defended state religious toleration and separation of church and state."
        },
        {
            "name": "Martin Buber (1878–1965 CE)",
            "school": "Dialogical Existentialism",
            "work": "Ich und Du (I and Thou, 1923)",
            "contribution": "Distinguished between instrumental objectifying relationships (I-It) and genuine reciprocal encounters (I-Thou); God is the Eternal Thou met in relation with humanity and creation."
        },
        {
            "name": "Franz Rosenzweig (1886–1929 CE)",
            "school": "Existential Jewish Philosophy",
            "work": "Der Stern der Erlösung (The Star of Redemption, 1921)",
            "contribution": "Formulated the relational triad of God, Man, and World linked by Creation, Revelation, and Redemption; viewed Judaism as eternal life within the covenant, while Christianity serves as eternal ray spreading outward to Gentiles."
        }
    ]
}

mysticism_kabbalah = {
    "version": "1.0.0",
    "schools": [
        {
            "name": "Early Merkavah and Hekhalot Literature",
            "dates": "c. 2nd–7th c. CE",
            "focus": "Visionary ascents through seven celestial palaces (Hekhalot) to behold the Divine Chariot (Merkavah) described in Ezekiel 1; Shi'ur Qomah anthropomorphic divine measurements."
        },
        {
            "name": "Sefer Yetzirah (Book of Formation)",
            "dates": "c. 3rd–6th c. CE",
            "focus": "Cosmogony based on the 32 Paths of Wisdom: 10 Sefirot (primordial numbers/dimensions) and 22 letters of the Hebrew alphabet."
        },
        {
            "name": "Classical Theosophic Kabbalah (The Zohar)",
            "dates": "Appeared c. 1280–1290 CE in Castile (attributed to Rabbi Shimon bar Yochai; redacted by Moses de Leon)",
            "focus": "The Ten Sefirot (Keter, Chokhmah, Binah, Chesed, Gevurah, Tiferet, Netzach, Hod, Yesod, Malkhut/Shekhinah) manifesting the concealed Infinite (Ein Sof); human mitzvot unify masculine and feminine divine aspects (Yichud Kudesha Berikh Hu u-Shekhintei)."
        },
        {
            "name": "Lurianic Kabbalah (Isaac Luria, The Ari)",
            "dates": "16th century (Safed, Galilee)",
            "focus": [
                "Tzimtzum (divine self-contraction creating a cosmic void for creation)",
                "Shevirat Ha-Kelim (Shattering of the Vessels under intense primordial light)",
                "Nitzotzot (holy divine sparks trapped within material reality and Klipot / shells of evil)",
                "Tikkun Olam (cosmic restoration accomplished through prayer, halakhic observance, and mystical intention / Kavanah)"
            ]
        },
        {
            "name": "Hasidism (Chasidut)",
            "dates": "18th century–Present",
            "founder": "Rabbi Israel Baal Shem Tov (Besht, 1698–1760)",
            "teachings": [
                "Panentheistic immanence of God in all things ('No place is void of Him')",
                "Avodah be-Gashmiyyut (serving God through physical acts and mundane activities)",
                "Joy (Simcha), ecstatic prayer (Devekut), and rejection of ascetic melancholy",
                "The Tzaddik / Rebbe as spiritual intercessor and channel of divine blessing",
                "Major branches: Chabad-Lubavitch, Satmar, Breslov, Ger, Belz, Vizhnitz"
            ]
        }
    ],
    "normative_boundary_clarification": "Normative traditional Judaism holds that Kabbalah and Hasidism are esoteric interpretations subordinate to the binding legal obligations of Halakha; mystical speculation never suspends or abrogates dietary laws, Shabbat, or interpersonal commandments."
}

denominations = {
    "version": "1.0.0",
    "movements": [
        {
            "id": "DENOM-ORTHODOX-HAREDI",
            "movement": "Haredi ('Ultra-Orthodox') Judaism",
            "halakhic_position": "Strict immutability of Halakha across all details; literal divine revelation of Written and Oral Torah at Sinai.",
            "view_of_modernity": "Cultural insulation, rejection of secular values, prioritization of full-time Yeshiva study (Torato Umanuto).",
            "sub_branches": ["Hasidim (reverence for dynamic Rebbe dynasties)", "Lithuanian / Yeshivish (Misnagdim: rigorous analytical Talmudic study)"],
            "messiah_position": "Awaits literal personal human King Messiah from Davidic line."
        },
        {
            "id": "DENOM-ORTHODOX-MODERN",
            "movement": "Modern Orthodox Judaism (Centrist Orthodoxy)",
            "halakhic_position": "Strict fidelity to Shulchan Aruch and traditional poskim; belief in Torah Mi-Sinai.",
            "view_of_modernity": "Torah U'Madda (Torah and secular knowledge/sciences integrated); active civic, professional, and military engagement.",
            "attitude_to_israel": "Strong Religious Zionism (viewing modern Israel as Reshit Tzemichat Ge'ulateinu — first flowering of our redemption)."
        },
        {
            "id": "DENOM-CONSERVATIVE",
            "movement": "Conservative / Masorti Judaism",
            "halakhic_position": "Halakha is binding and normative, but historically developmental and evolving to address modern ethics and scientific realities.",
            "view_of_scripture": "Revelation is divine-human encounter; accepts historical-critical biblical and talmudic scholarship.",
            "features": ["Egalitarian minyanim and ordination of women and LGBTQ+ rabbis", "CJLS responsa allowing driving to nearest synagogue on Shabbat if necessary"]
        },
        {
            "id": "DENOM-REFORM",
            "movement": "Reform / Progressive Judaism",
            "halakhic_position": "Halakha is non-binding counsel; autonomous individual moral conscience is supreme.",
            "view_of_scripture": "Continuous progressive revelation; biblical laws reflect historical contexts of ancient eras.",
            "features": ["Emphasis on prophetic ethical monotheism and Tikkun Olam (social justice)", "Gender egalitarianism, interfaith marriage welcoming, patrilineal descent recognition alongside matrilineal"]
        },
        {
            "id": "DENOM-RECONSTRUCTIONIST",
            "movement": "Reconstructionist Judaism",
            "halakhic_position": "Non-binding 'folkways'; Judaism is an evolving religious civilization (Mordecai Kaplan).",
            "god_concept": "Naturalistic religious humanism (God as the cosmic process that fosters human fulfillment)."
        },
        {
            "id": "DENOM-KARAITE",
            "movement": "Karaite Judaism (Bnei Mikra)",
            "halakhic_position": "Rejects the Oral Torah, Talmud, and rabbinic authority entirely.",
            "source_authority": "Direct autonomous interpretation of the Hebrew Tanakh using grammatical-contextual analysis (Peshuto shel Mikra)."
        },
        {
            "id": "DENOM-SECULAR",
            "movement": "Secular Jewish Identity (Hiloni)",
            "identity_basis": "Jewish peoplehood, national history, Hebrew literature, cultural heritage, and shared destiny without adherence to divine commandments or theological dogma."
        }
    ]
}

geographic_diversity = {
    "version": "1.0.0",
    "communities": [
        {
            "community": "Ashkenazi Jewry",
            "historical_geography": "Rhineland, France, Germany, Poland, Lithuania, Russia, Central/Eastern Europe",
            "language": "Yiddish (Judeo-German)",
            "liturgical_rite": "Nusach Ashkenaz / Nusach Sefard (Hasidic)",
            "halakhic_decisors": "Moses Isserles (Rema), Vilna Gaon, Chafetz Chaim"
        },
        {
            "community": "Sephardic Jewry",
            "historical_geography": "Iberian Peninsula (Spain & Portugal) prior to 1492; Ottoman Empire, Balkans, North Africa, Western Europe (Amsterdam, London)",
            "language": "Ladino / Judezmo (Judeo-Spanish)",
            "liturgical_rite": "Nusach Edot Ha-Mizrach / Western Sephardi",
            "halakhic_decisors": "Joseph Karo, Chida (Azulai), Ben Ish Chai, Rabbi Ovadia Yosef"
        },
        {
            "community": "Mizrahi Jewry",
            "historical_geography": "Middle East, Mesopotamia (Iraq/Babylon), Persia/Iran, Syria, Lebanon",
            "language": "Judeo-Arabic, Judeo-Persian",
            "heritage": "Direct heirs of the ancient Babylonian academies of Sura and Pumbedita"
        },
        {
            "community": "Teimani (Yemenite) Jewry",
            "historical_geography": "Yemen (Sanaa, Aden, Habban)",
            "language": "Judeo-Yemenite Arabic",
            "sub_streams": ["Baladi (follows Maimonides' Mishneh Torah exclusively, retaining ancient Palestinian vocalization)", "Shami (adopted later Sephardic codes and Kabbalah)"]
        },
        {
            "community": "Beta Israel (Ethiopian Jewry)",
            "historical_geography": "Gondar, Tigray (Ethiopia)",
            "language": "Ge'ez (liturgical) and Amharic",
            "scripture": "Orit (Octateuch in Ge'ez)",
            "uniqueness": "Preserved pre-rabbinic, non-talmudic biblical Judaism with monastic priesthood (Kohanim/Kessim) until mass airlift migrations to Israel (Operation Moses 1984, Operation Solomon 1991)"
        }
    ]
}

# Write historical files
for name, data in [
    ("ancient_israel.json", ancient_israel),
    ("second_temple.json", second_temple),
    ("rabbinic_era.json", rabbinic_era),
    ("medieval_era.json", medieval_era),
    ("modern_era.json", modern_era)
]:
    for base in hist_dirs:
        p = os.path.join(base, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {p}")

# Write intellectual files
for name, data in [
    ("philosophy.json", philosophy),
    ("mysticism_kabbalah.json", mysticism_kabbalah),
    ("denominations.json", denominations),
    ("geographic_diversity.json", geographic_diversity)
]:
    for base in intel_dirs:
        p = os.path.join(base, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {p}")

print("Historical and Intellectual Judaism layers generated successfully.")
