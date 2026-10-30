# VansRouter Extension for Tau (`vansrouter`)

Registers the local VansRouter OpenAI-compatible router (`http://127.0.0.1:20128/v1`) as a model provider in Tau.

## Capabilities
- Dynamic model resolution via `http://127.0.0.1:20128/v1/models`
- Real context length extraction (`context_length`, `max_completion_tokens`)
- Vision and reasoning flag detection
- Startup connectivity check (`/api/health`)

## Testing
```bash
bun test /home/toxic/pens/estate/config/tau/extensions/vansrouter/index.test.ts
```
