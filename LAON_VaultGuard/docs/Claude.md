# Claude Multi-LLM Cross-Validation Guide

> Anthropic Claude integration for multi-LLM security audit cross-validation.
> Claude Claude Multi-LLM Audit .

## 1. API Key

1. https://console.anthropic.com/ -> API Keys -> Create Key
2. Copy the key (starts with `sk-ant-`)

## 2. .env Configuration

```bash
# Single Claude
CLAUDE_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
LLM_PROVIDERS=claude
LLM_MODE=sequential

# Cross-validation: Claude + DeepSeek + Ollama (recommended)
CLAUDE_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxx
LLM_PROVIDERS=claude,deepseek,ollama
LLM_MODE=parallel
```

## 3. LLM Modes

| Mode | Behaviour | Use Case |
|---|---|---|
| `parallel` | All LLMs called simultaneously, results merged | Highest accuracy, higher cost |
| `sequential` | LLMs called in order, first high-confidence result used | Failover, lower cost |
| `majority` | All LLMs called, only majority-agreed findings kept | Minimal false positives |

## 4. Recommended Configurations

| Environment | Providers | Mode | Rationale |
|---|---|---|---|
| Personal, offline | `ollama` | sequential | Free, no internet needed |
| Personal, online | `deepseek,claude` | parallel | Low-cost + high-accuracy |
| Team, sensitive repos | `ollama,claude` | sequential | Local first, cloud fallback |
| Enterprise | `claude,deepseek,ollama` | majority | 3-LLM consensus, minimal false alarms |

## 5. How Cross-Validation Works

```
Candidate lines (from git grep)
         |
    +---------+
    |         |
  Claude   DeepSeek   Ollama
    |         |         |
    v         v         v
  Finding   Finding   Finding
    \         |         /
     \        |        /
      Result Aggregator
            |
    +--------+--------+
    |        |        |
  Slack   Email   Dashboard
```

### parallel mode
All 3 LLMs called simultaneously. Each finding from any LLM is kept. Duplicates (same file + same fingerprint) are deduplicated.

### majority mode
All LLMs called. A finding must be reported by >50% of responding providers to be kept. Requires at least 3 providers for meaningful majority.

### sequential mode
LLMs called in priority order. If the first LLM returns findings with high confidence, the result is used immediately without calling subsequent LLMs. If the first LLM fails (network, quota, auth), the next provider is automatically tried.

## 6. Cost Comparison

| Provider | Model | Cost per 1M tokens (approx) |
|---|---|---|
| Claude (Anthropic) | claude-sonnet-4 | $3.00 / $15.00 (input/output) |
| DeepSeek | deepseek-chat | $0.14 / $0.28 |
| OpenAI | gpt-4o | $2.50 / $10.00 |
| Ollama | llama3.1 | Free (local) |

## 7. Troubleshooting

| Symptom | Cause | Solution |
|---|---|---|
| `LLM auth failed: claude` | Invalid API key | Check `CLAUDE_API_KEY` in .env |
| `LLM auth failed: claude` with correct key | Wrong base URL | Use `CLAUDE_BASE_URL=https://api.anthropic.com/v1` |
| Claude slower than DeepSeek | Normal | Claude does deeper reasoning; use parallel mode |
| `LLM parse error` | Response format mismatch | Claude returns text, not JSON by default; set `temperature=0` |

## 8. Claude Model Selection

| Model | Best For |
|---|---|
| `claude-sonnet-4-20250514` | General security audit (default, balanced speed/accuracy) |
| `claude-opus-4-20250514` | Maximum accuracy, sensitive repos (slower, more expensive) |
| `claude-haiku-3-5-20241022` | Fast scanning, low cost (may miss edge cases) |

Set via `.env`:
```bash
CLAUDE_MODEL=claude-opus-4-20250514
```
