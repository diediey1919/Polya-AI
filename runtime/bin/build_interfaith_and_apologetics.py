#!/usr/bin/env python3
"""
Build Interfaith, Comparative, and Apologetics Knowledge Layers
Adheres to Master Prompt Sections 23, 24, 25, 26, 27, 28, 29, 30, 37, 51.
"""
import json
import os

inter_dirs = [
    "/home/ubuntu/Polya-AI/data/judaism/interfaith",
    "/home/ubuntu/apologetica/data/judaism/interfaith"
]
apol_dirs = [
    "/home/ubuntu/Polya-AI/data/judaism/apologetics",
    "/home/ubuntu/apologetica/data/judaism/apologetics"
]

judaism_and_jesus = {
    "version": "1.0.0",
    "historical_context": "Jesus of Nazareth (Yeshua ben Yosef, c. 4 BCE–30/33 CE) operated strictly within the late Second Temple Jewish world of Roman-occupied Galilee and Judea. His teachings mirrored contemporary debates between Beit Hillel and Beit Shammai.",
    "torah_stance": {
        "historical_critical_view": "Jesus affirmed the perpetual validity of the Torah ('Do not think that I have come to abolish the Law or the Prophets... not one iota, not a dot will pass' Matt 5:17-18). His halakhic disputes with the Pharisees centered on internal matters of stringency: Shabbat healing (permitted in rabbinic halakha where life/limb is at stake), table fellowship, and handwashing (a non-biblical rabbinic purity expansion).",
        "rabbinic_perspective": "Rabbinic traditions (Talmud Sanhedrin 43a, 107b - censored in medieval printings) view him as a Jewish sectarian teacher who deviated into heresy or led others astray, but never accepted his claims to messiahship or divine authority."
    },
    "reasons_for_jewish_rejection": [
        {
            "criterion": "Unfulfilled Prophetic Messianic Mandates",
            "explanation": "Biblical prophecies define the Messianic era by tangible historical transformations: universal disarmament and global peace (Isaiah 2:4), ingathering of all Jewish exiles to the Land of Israel (Isaiah 11:12), rebuilding of the Holy Temple (Ezekiel 37:26-28), and universal knowledge of God (Zechariah 14:9). None of these occurred during Jesus's lifetime or following his death."
        },
        {
            "criterion": "Incompatibility with Radical Monotheism",
            "explanation": "Claiming divinity, ontological divine sonship, or equal status with the Creator directly violates the foundation of Jewish monotheism (Exodus 20:2-3, Deuteronomy 6:4, Isaiah 42:8: 'I am the Lord; that is My name; My glory I give to no other'). Any being born of a woman, subject to bodily needs, suffering, and physical death cannot be God."
        },
        {
            "criterion": "Genealogy and Davidic Patrilineage",
            "explanation": "According to biblical law (Numbers 1:18, Leviticus 24:10), tribal identity and monarchic Davidic rights pass exclusively through the biological human father. If the Christian doctrine of the Virgin Birth is true, Jesus had no human biological father, meaning he cannot inherit legal Davidic kingship through Joseph. If Joseph was his biological father, then the Virgin Birth is negated, and furthermore Joseph's lineage through Jeconiah (Matt 1:11) falls under the curse of Jeremiah 22:30 ('No man of his seed shall prosper, sitting upon the throne of David')."
        },
        {
            "criterion": "Torah Abrogation Test",
            "explanation": "Deuteronomy 13:1-5 explicitly commands that even if a prophet or dreamer performs signs and wonders, but instructs Israel to worship other entities or abandon the eternal commandments of the Torah, that prophet is false and must not be followed."
        }
    ]
}

judaism_and_christianity = {
    "version": "1.0.0",
    "parting_of_the_ways": "Gradual historical separation spanning 70 CE (Temple destruction) to the 4th century (Nicene Christianity becoming Roman imperial state religion). Early Jewish-Christian sects (Ebionites, Nazarenes) vanished as Gentile Christianity defined orthodoxy.",
    "core_debates": [
        {
            "locus": "Isaiah 7:14",
            "christian_claim": "Predicts the miraculous Virgin Birth of Jesus Christ ('Behold, a virgin shall conceive and bear a son, and shall call his name Immanuel').",
            "jewish_refutation": "The original Hebrew text reads 'ha-almah' (הָעַלְמָה), meaning 'the young woman' of marriageable age (often with the definite article pointing to someone present in the room). The Hebrew for anatomical virgin is Bethulah (בְּתוּלָה). The historical context (Isa 7:1-16) was a contemporary military crisis in 734 BCE: King Ahaz was terrified of the coalition between King Rezin of Aram and Pekah of Israel. Isaiah gave Ahaz a sign that before the child is old enough to refuse evil and choose good, the land of both enemy kings will be deserted."
        },
        {
            "locus": "Isaiah 52:13–53:12 (The Suffering Servant)",
            "christian_claim": "The premier Old Testament prophecy of Jesus's vicarious substitutionary atonement and crucifixion for the sins of the world.",
            "jewish_refutation": "Throughout Isaiah's second section, God explicitly and repeatedly identifies the 'Servant' by name as the collective Nation of Israel: 'You, Israel, My servant Jacob whom I have chosen' (Isa 41:8-9), 'You are My servant, Israel, in whom I will be glorified' (Isa 49:3), 'Yet now hear, O Jacob My servant; and Israel, whom I have chosen' (Isa 44:1, 44:21). Chapter 53 is spoken from the perspective of the Gentile kings (52:15) marveling in astonishment at the end of days that the Jewish people, whom they despised, persecuted, and regarded as struck down by God, were actually suffering innocent hardship among the nations while preserving divine truth."
        },
        {
            "locus": "Psalm 22:17 (MT) / 22:16 (Christian)",
            "christian_claim": "'They pierced my hands and my feet', proving the crucifixion.",
            "jewish_refutation": "The Masoretic Text reads 'Ka-ari yadai ve-raglai' (כָּאֲרִי יָדַי וְרַגְלָי) — 'Like a lion [they are at] my hands and my feet'. The word is 'Ka-ari' (like a lion, from אֲרִי), not a verb 'pierced'. David is composing a poetic lament describing his encirclement by predatory adversaries."
        },
        {
            "locus": "Covenant and Supersessionism",
            "christian_claim": "The Church is the 'New Israel' (Verus Israel) replacing the Jewish people whose covenant was broken (Hebrews 8:13).",
            "jewish_refutation": "The Hebrew Bible explicitly declares the covenant with Israel to be eternal and irrevocable: 'I will establish My covenant... for an everlasting covenant' (Gen 17:7); 'Even when they are in the land of their enemies, I will not reject them, neither will I abhor them, to destroy them utterly and to break My covenant with them' (Lev 26:44); 'If heaven above can be measured... only then will I cast off all the offspring of Israel' (Jer 31:37)."
        }
    ]
}

judaism_and_islam = {
    "version": "1.0.0",
    "comparative_theology": "Judaism and Islam share an uncompromising dedication to pure, non-incarnational, non-trinitarian monotheism (Yihud Ha-Shem and Tawhid). Maimonides (Hilkhot Ma'akhalot Asurot 11:7, Teshuvot Ha-Rambam 448) famously ruled that Muslims are strictly monotheistic, and Islam is not idolatry (Avodah Zarah).",
    "prophetic_parallels": [
        {"name": "Moses / Musa", "status": "In Judaism: Master of all prophets (Moshe Rabbenu), saw God face-to-face (Num 12:6-8); in Islam: Kalimullah (the one who spoke with God) and Ulul Azm messenger who brought the original Tawrat."},
        {"name": "Abraham / Ibrahim", "status": "Father of the covenant (Avraham Avinu); in Islam: Khalilullah, the archetype of pure Hanif monotheism."},
        {"name": "David & Solomon / Dawud & Sulayman", "status": "Kings of Israel; in Judaism: King David is author of Psalms and progenitor of Messiah, King Solomon built First Temple; in Islam: regarded primarily as righteous prophets (anbiya') endowed with wisdom."}
    ],
    "halakha_vs_sharia": {
        "structural_harmony": "Both systems are legalistic religions (Nomocracy) without a centralized sacramental clergy. Both emphasize jurisprudence (Fiqh / Halakha), dietary slaughter regulations (Dhabihah / Shechita), ritual circumcisions (Khitan / Brit Milah), strict ritual ablutions, daily prayers, and charity."
    },
    "historical_relations": "Jews lived under Islamic rule as Dhimmi (protected people of the book under the Pact of Umar). While subject to civil restrictions and poll taxes (Jizya), Jews generally experienced far greater cultural, intellectual, and economic integration in the Islamic world than in medieval Christendom, resulting in the Golden Age of Spain and Judeo-Arabic scholarship."
}

tahrif_models = {
    "version": "1.0.0",
    "definition": "Tahrif (تحريف) is the Islamic theological term for the alteration or corruption of prior divine scriptures (Tawrat and Injil).",
    "scholarly_distinctions": [
        {
            "category": "Tahrif al-Ma'na (تحريف المعنى)",
            "meaning": "Corruption of interpretation and meaning.",
            "theological_position": "The physical text of the Hebrew Bible remains substantially intact, but Jewish rabbis and interpreters deliberately misinterpreted, distorted, or concealed verses predicting the Prophet Muhammad or altered legal ordinances.",
            "classical_advocates": [
                "Muhammad ibn Jarir al-Tabari (Tafsir al-Tabari): emphasized Jews twist meanings with their tongues (Surah Al-Imran 3:78).",
                "Fakhr al-Din al-Razi (Mafatih al-Ghayb): argued it is practically impossible for an entire nation spread across east and west to conspire together to physically alter every copy of their holy scripture without detection.",
                "Shah Waliullah al-Dahlawi & Muhammad Abduh: modern reformist advocates of Tahrif al-Ma'na."
            ]
        },
        {
            "category": "Tahrif al-Nass / Tahrif al-Lafz (تحريف النص / تحريف اللفظ)",
            "meaning": "Corruption of the physical text itself.",
            "theological_position": "The original text of the Tawrat was lost or physically rewritten, corrupted, interpolated, and falsified by human scribes.",
            "classical_advocates": [
                "Ibn Hazm of Cordoba (Al-Fasl fi al-Milal, 11th c.): claimed Ezra (Uzayr) fabricated the Torah after the Babylonian exile; compiled internal contradictions and numerical discrepancies in Genesis and Samuel.",
                "Al-Maqrizi & Al-Qurtubi: adopted severe textual alteration positions."
            ]
        }
    ],
    "jewish_and_academic_response": {
        "manuscript_evidence": "The Dead Sea Scrolls (c. 250 BCE–68 CE) prove that the Hebrew Bible existed in virtually identical consonantal form hundreds of years before the rise of Islam in the 7th century CE. The Great Isaiah Scroll (1QIsa-a) and Proto-Masoretic fragments demonstrate that no wholesale post-Islamic or late pre-Islamic rewritings occurred.",
        "distribution_impossibility": "By the 1st century CE, Jewish communities were dispersed across Rome, Alexandria, Babylon, Persia, Greece, and Yemen. A centralized coordinated conspiracy to alter every scroll simultaneously without leaving textual dissent or ancient manuscript traces is historically and logistically impossible."
    }
}

triangular_comparisons = {
    "version": "1.0.0",
    "description": "Comparative matrix contrasting Judaism, Christianity, and Islam across 10 foundational theological and historical dimensions.",
    "themes": [
        {
            "theme": "Concept of God (Monotheism)",
            "judaism": "Absolute, non-composite, incorporeal unity (Yihud Ha-Shem). Rejects Trinity and Incarnation as blasphemous/impossible.",
            "christianity": "Trinitarian monotheism: One God in three co-equal, consubstantial persons (Father, Son, Holy Spirit).",
            "islam": "Strict Tawhid (Tawhid al-Rububiyyah, al-Uluhiyyah, al-Asma' was-Sifat). Rejects Trinity (Shirk) and Incarnation."
        },
        {
            "theme": "Scripture and Revelation",
            "judaism": "Tanakh (Written Torah) accompanied by Sinai Oral Torah; open to rabbinic dialectical interpretation and progressive rabbinic enactment.",
            "christianity": "Old and New Testaments; inspired scripture fulfilling Old Testament covenants through Christ.",
            "islam": "The Qur'an as literal uncreated verbatim speech of Allah revealed to Muhammad via Jibril; earlier scriptures corrupted (Tahrif)."
        },
        {
            "theme": "Original Sin & Human Nature",
            "judaism": "No Original Sin dogma. Humans are born morally neutral with Yetzer Ha-Tov and Yetzer Ha-Ra; free will is absolute.",
            "christianity": "Original Sin inherited from Adam; humanity is fallen and unable to attain salvation without divine grace in Christ.",
            "islam": "Fitrah (innate primordial monotheistic human purity); no inherited guilt; Adam erred and was forgiven upon repentance."
        },
        {
            "theme": "Sin, Repentance, and Atonement",
            "judaism": "Sin is rectified directly through Teshuvah (remorse, cessation, confession, restitution), prayer, and charity without vicarious human sacrifice.",
            "christianity": "Atonement achieved through the vicarious, substitutionary sacrificial death and bodily resurrection of Jesus Christ.",
            "islam": "Forgiveness obtained directly from Allah through sincere repentance (Tawbah), good deeds (Hasanaat), and divine Rahmah."
        },
        {
            "theme": "Messiah / Eschatology",
            "judaism": "Awaits mortal human Davidic King Messiah who will rebuild Temple, gather exiles, and bring universal peace.",
            "christianity": "Jesus is the divine Messiah and Savior who accomplished spiritual redemption and will return in the Second Coming.",
            "islam": "Isa al-Masih is a revered prophet/messenger who was not crucified (Qur'an 4:157), was raised to heaven, and will return before Judgment Day."
        },
        {
            "theme": "Sacrificial System",
            "judaism": "Ceased in 70 CE due to halakhic prohibition of sacrificing outside Temple Mount (Deut 12); replaced by prayer and repentance.",
            "christianity": "Sacrifices permanently fulfilled and abolished once for all by the final sacrifice of Christ on the cross (Hebrews 10).",
            "islam": "Animal sacrifice continues as non-atoning devotional commemoration during Eid al-Adha (Udhiyah/Qurbani)."
        },
        {
            "theme": "Law and Observance",
            "judaism": "Halakha: 613 Mitzvot binding exclusively upon the Jewish people; Gentiles obligated only in 7 Noahide Laws.",
            "christianity": "Freedom from Mosaic ritual law; moral commandments retained through the Law of the Spirit / Love of Christ.",
            "islam": "Sharia: Comprehensive divine legal code (Halal/Haram) binding upon all Muslims globally."
        },
        {
            "theme": "Eschatological Afterlife (Salvation)",
            "judaism": "Righteous of all nations have a share in the World to Come (Olam Ha-Ba); no eternal hellfire dogma.",
            "christianity": "Eternal life granted to believers through faith in Jesus Christ; eternal separation/hell for the unredeemed.",
            "islam": "Paradise (Jannah) for monotheistic believers; Hell (Jahannam) for disbelievers (Kuffar), with varying scholarly views on permanence."
        },
        {
            "theme": "Jerusalem and the Temple Mount",
            "judaism": "Har Ha-Bayit (Mount Moriah): holiest site on earth, place of First/Second Temples and Holy of Holies; direction of all prayer.",
            "christianity": "Holy city of Christ's passion, death, and resurrection; Church of the Holy Sepulchre.",
            "islam": "Al-Haram al-Sharif / Al-Quds: third holiest sanctuary (Masjid al-Aqsa and Dome of the Rock), destination of Isra and Mi'raj."
        },
        {
            "theme": "Identity, Land, and Peoplehood",
            "judaism": "Particularist covenant with a specific historical people (Am Yisrael) tied to a specific geographical Land (Eretz Yisrael).",
            "christianity": "Universal spiritual body (Ecclesia) transcending ethnic and geographic national boundaries.",
            "islam": "Universal global community of believers (Ummah) transcending race and nation."
        }
    ]
}

jewish_apologetics = {
    "version": "1.0.0",
    "polemical_milestones": [
        {
            "work": "Sefer Milhamot Hashem (The Wars of the Lord)",
            "author": "Jacob ben Reuben",
            "date": "1170 CE",
            "content": "Systematic critique of the Gospels, identifying chronological errors and misapplied prophetic verses."
        },
        {
            "work": "Disputation of Barcelona",
            "date": "1263 CE",
            "protagonists": "Rabbi Moses ben Nachman (Nachmanides / Ramban) vs Pablo Christiani",
            "outcome": "Nachmanides successfully argued before King James I of Aragon that Aggadic Midrashim are non-binding homilies, and that the Messiah has not yet come because world peace and end of war have manifestly not arrived."
        },
        {
            "work": "Hizzuk Emunah (Faith Strengthened)",
            "author": "Isaac ben Abraham of Troki",
            "date": "1593 CE",
            "content": "Comprehensive 50-chapter polemic dissecting New Testament contradictions, demonstrating the perpetuity of the Mosaic Law, and analyzing all Christian Christological proof-texts."
        }
    ]
}

argument_bank = {
    "version": "1.0.0",
    "arguments": [
        {
            "arg_id": "ARG-JEW-SINAI-PUBLIC",
            "title": "National Public Revelation at Sinai as Epistemic Guarantee",
            "premises": [
                "P1: Claims of private revelation to single individuals (e.g. visions in a cave or personal revelations) can be easily fabricated or suffer from hallucination.",
                "P2: The Sinaitic revelation was witnessed simultaneously by an entire nation of over 600,000 adult men (plus women and children) hearing the divine voice directly (Exod 19:9, Deut 4:32-35).",
                "P3: It is historically and sociologically impossible to fabricate a national collective memory to a population ('Your ancestors all heard God speak from the fire') if it never occurred, because the population would reject the claim based on ancestral absence.",
                "Conclusion: The Sinaitic revelation possesses a unique empirical-historical epistemic warrant superior to private revelations (Judah Halevi, Kuzari 1:87-89)."
            ],
            "confidence": "ESTABLISHED_INTERNAL_ARGUMENT"
        },
        {
            "arg_id": "ARG-JEW-TORAH-ETERNAL",
            "title": "Perpetuity and Non-Abrogation of the Torah",
            "premises": [
                "P1: The Torah repeatedly and emphatically designates its commandments as 'Chukat Olam' (an everlasting statute) throughout all generations (e.g. Exod 12:14, 31:16; Lev 3:17, 16:34).",
                "P2: God is unchanging and does not revoke His divine law or change His mind (Num 23:19, Malachi 3:6).",
                "P3: Deuteronomy 13:1-5 explicitly warns Israel that any future figure claiming divine authority who advocates adding to, subtracting from, or abolishing the commandments is a false prophet.",
                "Conclusion: Neither Christian abrogation of the Law nor Islamic naskh (abrogation) of the Mosaic covenant is valid according to Hebrew scripture."
            ],
            "confidence": "ESTABLISHED_INTERNAL_ARGUMENT"
        }
    ]
}

counterargument_bank = {
    "version": "1.0.0",
    "counterarguments": [
        {
            "counter_id": "COUNTER-CHRISTIAN-SINAI",
            "target_arg": "ARG-JEW-SINAI-PUBLIC",
            "tradition": "CHRISTIAN",
            "objection": "The historical testimony of the resurrection of Jesus is attested by multiple independent early eyewitnesses (1 Cor 15:3-8 lists over 500 brethren at once), who were willing to endure martyrdom for their testimony, providing equal or superior historical confirmation."
        },
        {
            "counter_id": "COUNTER-ISLAMIC-SINAI",
            "target_arg": "ARG-JEW-SINAI-PUBLIC",
            "tradition": "ISLAMIC",
            "objection": "Islam fully affirms the miraculous event of Sinai (Tur) and the revelation to Musa, but maintains that succeeding generations of Israelites broke the covenant, engaged in golden calf worship, killed prophets, and altered the text (Tahrif)."
        },
        {
            "counter_id": "COUNTER-ACADEMIC-SINAI",
            "target_arg": "ARG-JEW-SINAI-PUBLIC",
            "tradition": "ACADEMIC_CRITICAL",
            "objection": "Textual-historical criticism dates the written composition of the Pentateuch narratives to centuries after the purported events, reflecting retrojected national mythmaking rather than contemporaneous archival eyewitness documentation."
        }
    ]
}

debate_structures = {
    "version": "1.0.0",
    "debates": [
        {
            "theme_id": "DEBATE-JEW-MASHIACH",
            "theme_title": "The Identity, Nature, and Accomplishments of the Messiah",
            "jewish_position": {
                "summary": "Messiah is a mortal human Davidic king who will accomplish physical, political, and spiritual redemption in this world: gathering exiles, rebuilding Temple, inaugurating world peace.",
                "sources": ["Isaiah 2:1-4", "Isaiah 11:1-12", "Ezekiel 37:21-28", "Rambam Hilkhot Melakhim 11-12"]
            },
            "christian_position": {
                "summary": "Jesus of Nazareth is the divine Son of God and Messiah whose primary mission was spiritual atonement on the cross, resurrection, and whose physical kingdom will be realized at the Second Coming.",
                "sources": ["Luke 1:32-33", "Matthew 26:63-64", "Romans 1:3-4", "Hebrews 9:11-28"]
            },
            "islamic_position": {
                "summary": "Isa ibn Maryam is the Messiah (Al-Masih) and prophet of Allah, born of a virgin without a father, who performed miracles, was not crucified, and will descend before the Day of Judgment to defeat the Dajjal.",
                "sources": ["Qur'an 3:45", "Qur'an 4:157-159", "Sahih al-Bukhari 2222"]
            },
            "primary_evidence": ["SRC-JEW-MT-001", "SRC-JEW-DSS-001", "SRC-JEW-RAMBAM-MT-001"],
            "jewish_evidence": ["SRC-JEW-TROKI-001", "SRC-JEW-RAMBAN-TORAH-001"],
            "christian_evidence": ["Novum Testamentum Graece (NA28)"],
            "islamic_evidence": ["Qur'an / Tafsir Ibn Kathir"],
            "historical_context": "First-century Judea experienced intense apocalyptic and messianic fervor under brutal Roman occupation, spawning various messianic claimants (Theudas, the Egyptian, Jesus, Simon bar Kokhba).",
            "textual_context": "Tanakh prophetic passages consistently describe the messianic era in this-worldly historical and political terms of justice, national security, and world peace.",
            "linguistic_context": "The root mashach denotes anointing with oil, applied to priests, prophets, and kings.",
            "theological_context": "Fundamental divergence between Jewish this-worldly social-covenantal restoration vs Christian other-worldly spiritual salvation from original sin.",
            "common_arguments": [
                {"claim": "Jesus fulfilled all Old Testament prophecies", "speaker": "Christian Apologist"},
                {"claim": "World peace has not arrived, so the Messiah has not yet come", "speaker": "Jewish Disputant"}
            ],
            "counterarguments": [
                {"claim": "Prophecies are split between First Coming (suffering servant) and Second Coming (triumphant king)", "speaker": "Christian Apologist"}
            ],
            "counter_counterarguments": [
                {"claim": "The Tanakh never mentions a 'Second Coming' or a split messianic career; a king who fails to deliver peace and dies has simply failed the biblical test", "speaker": "Jewish Disputant (Rambam 11:4)"}
            ],
            "common_misrepresentations": [
                "Claiming Jews rejected Jesus out of superficial desire for a military conqueror rather than serious textual-theological adherence to biblical criteria.",
                "Claiming Judaism teaches that the Messiah must be divine."
            ],
            "unresolved_questions": [
                "How early did the distinction between Messiah ben Joseph (the suffering martyr) and Messiah ben David (the triumphant king) arise in rabbinic eschatology (Talmud Sukkah 52a)?"
            ]
        }
    ]
}

# Write interfaith files
for name, data in [
    ("judaism_and_jesus.json", judaism_and_jesus),
    ("judaism_and_christianity.json", judaism_and_christianity),
    ("judaism_and_islam.json", judaism_and_islam),
    ("tahrif_models.json", tahrif_models),
    ("triangular_comparisons.json", triangular_comparisons)
]:
    for base in inter_dirs:
        p = os.path.join(base, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {p}")

# Write apologetics files
for name, data in [
    ("jewish_apologetics.json", jewish_apologetics),
    ("argument_bank.json", argument_bank),
    ("counterargument_bank.json", counterargument_bank),
    ("debate_structures.json", debate_structures)
]:
    for base in apol_dirs:
        p = os.path.join(base, name)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {p}")

print("Interfaith, Comparative, and Apologetics Knowledge Layers generated successfully.")
