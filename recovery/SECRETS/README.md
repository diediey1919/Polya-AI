# Secrets

**WARNING: NEVER COMMIT SECRETS TO GIT**

The following secrets must be supplied during restoration but are NOT included in this repository.

## Required Secrets

### 1. ~/.hermes/.env

Environment variables file containing:
- `OPENROUTER_API_KEY` - API key for OpenRouter (Qwen models)
- `GEMINI_API_KEY` - Google Gemini API key
- `DASHSCOPE_API_KEY` - Alibaba DashScope API key (Qwen)
- `ELEVENLABS_API_KEY` - ElevenLabs TTS API key
- `DISCORD_BOT_TOKEN` - Discord bot authentication token

### 2. ~/.hermes/auth.json

Authentication credentials for various services.

## Restoration Procedure

1. **Obtain API keys** from respective providers:
   - OpenRouter: https://openrouter.ai/
   - Google AI Studio: https://aistudio.google.com/
   - DashScope: https://dashscope.aliyun.com/
   - ElevenLabs: https://elevenlabs.io/
   - Discord Developer Portal: https://discord.com/developers/applications

2. **Create .env file**:
   ```bash
   nano ~/.hermes/.env
   ```

3. **Add secrets** (format):
   ```bash
   OPENROUTER_API_KEY=your-key-here
   GEMINI_API_KEY=your-key-here
   DASHSCOPE_API_KEY=your-key-here
   ELEVENLABS_API_KEY=your-key-here
   DISCORD_BOT_TOKEN=your-token-here
   ```

4. **Set permissions**:
   ```bash
   chmod 600 ~/.hermes/.env
   ```

5. **Create auth.json** (if required by specific services):
   ```bash
   nano ~/.hermes/auth.json
   chmod 600 ~/.hermes/auth.json
   ```

## Security Notes

- Never commit `.env` or `auth.json` to Git
- Use environment-specific secrets
- Rotate keys regularly
- Consider using a secrets manager for production