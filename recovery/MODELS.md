# TTS Models

## Chatterbox Indonesian

### Model Details

- **Name**: Chatterbox-TTS-Indonesian
- **Source**: External large asset — must be restored from a verified external backup or verified official model source
- **Size**: ~5GB (5,338,044 KB total directory)
- **Location**: /home/ubuntu/tts-models/chatterbox-indonesian/
- **Voice**: Young Indonesian female

### Required Files

| File | Size | Purpose |
|------|------|---------|
| model.safetensors | 2.0GB | Main TTS model |
| s3gen.safetensors | 1.0GB | S3 generator |
| t3_cfg.safetensors | 2.0GB | T3 config model |
| ve.safetensors | 5.4MB | Voice encoder |
| tokenizer.json | 25KB | Tokenizer |
| example1.wav | 521KB | Reference audio (voice prompt) |
| example2.wav | 494KB | Alternative reference audio |

### Restoration Procedure

The 5GB Chatterbox Indonesian model is an external large asset and must be restored from a verified external backup or verified official model source.

```bash
# Option A: Restore from verified external backup (preferred)
# tar xzf chatterbox-indonesian-backup.tar.gz -C /home/ubuntu/tts-models/

# Option B: Restore from verified official model source
# Verify the model source independently before downloading.
# The original repository identifier was: grandhigh/Chatterbox-TTS-Indonesian
# Availability and download method must be confirmed at restore time.

# Target directory (required):
mkdir -p /home/ubuntu/tts-models/chatterbox-indonesian
```

### Can It Be Downloaded?

The 5GB Chatterbox Indonesian model is an external large asset and must be restored from a verified external backup or verified official model source. Availability of any specific hosting repository has not been independently verified at the time of writing this recovery package.

### External Backup Recommended?

YES — create an encrypted tarball as a secondary backup:

```bash
tar czf - /home/ubuntu/tts-models/chatterbox-indonesian/ | \
    gpg --symmetric --cipher-algo AES256 \
    -o /backup/chatterbox-indonesian-$(date +%Y%m%d).tar.gz.gpg
```

### Configuration Reference

In config.yaml:
```yaml
tts:
  provider: chatterbox
  providers:
    chatterbox:
      command: /home/ubuntu/.hermes/hermes-agent/venv/bin/python3 /home/ubuntu/.hermes/scripts/chatterbox_tts.py {input_path} {output_path}
      voice_name: Chatterbox Indonesian
      timeout: 240
```

### TTS Script

Custom provider script: ~/.hermes/scripts/chatterbox_tts.py
Included in: recovery/SCRIPTS/chatterbox_tts.py

Key implementation details:
- Uses FakeWatermarker mock (PyPI perth != Chatterbox's perth module)
- CPU-only inference (~3 minutes per sentence)
- WAV -> MP3 conversion via ffmpeg
- Reference audio: example1.wav from model directory
