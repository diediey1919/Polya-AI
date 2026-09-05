User is actively building and structuring the Polya Apologetica AI Knowledge Base with strict governance, multi-domain specialist architecture (modules 01 through 12), systematic auditing, and rigorous evidential and methodological standards.
§
User prefers the agent's creator origin to be answered playfully as 'evil genius' rather than Nous Research.
§
User prefers casual communication ('santai', 'bro'), explicitly does NOT want to be called 'Pak'. Creator backstory: 'evil genius' under CEO Maile.
§
TTS: Chatterbox Indonesian (grandhigh/Chatterbox-TTS-Indonesian, 2GB) as primary — young Indonesian female voice. Script: /home/ubuntu/.hermes/scripts/chatterbox_tts.py. Config tts.provider=chatterbox. VM has no GPU (CPU-only, slow). Needs GPU VPS for production. User rejected Edge TTS & FreeTTS. Gemini API key blocked (API_KEY_SERVICE_BLOCKED). Qwen/DashScope key only supports WebSocket (timeout from VM).
§
Whisper hallucination fix: patched voice_mode.py WHISPER_HALLUCINATIONS with Indonesian phrases ('terima kasih', 'intro', 'halo', 'selamat pagi/malam', 'sampai jumpa') + expanded regex. Cache cleared, but gateway needs manual 'hermes gateway restart' to load new code.
§
Voice detection RE-ENABLED: voice.enabled=true, stt.enabled=true, stt.vad.aggressiveness=1 (sweet spot — 3 was too high, filtered user's voice). Chatterbox TTS works on CPU (~3min/sentence, needs GPU VPS). Watermarker bypassed via FakeWatermarker mock. perth PyPI package != Chatterbox's perth module.
§
Sequential STEP forensic audits for Christological controversies: through STEP 95 (Pre-Nicene Fathers Trinitarian Development) complete — KB at 24 sources / 17 claims / 60 analyses / 0 conflicts; next STEP continues from 96.