# LLM Assistants for C# Development in Visual Studio — Verified Edition + DeepSeek & Multi-LLM Guide

> Recommendations for C# coding AI assistants in Visual Studio, plus concrete ways to connect DeepSeek and other LLMs. Key items were verified against public sources (marketplace, vendor docs).
> Companion doc: [MiniMax Coding Guide](minimax-coding-guide.en.md) (VS Code–centric)

- **As of**: 2026-06-04
- **Verification sources**: official marketplace, vendor docs, public material (cross-checked)
- **Status labels**: Verified / Corrected / Unverified

---

## 0. Fact-Check Results

The result of cross-checking key items related to Visual Studio C# AI assistants against public sources. Items whose existence/maintenance could not be confirmed from public sources are simply labeled **Unverified**.

| Item | Status | Basis / Notes |
|---|---|---|
| GitHub Copilot agent mode | Verified | Agent Mode is GA with MCP support. Supported on VS 2022 17.14+ / VS 2026. Multi-file edits, iterative error fixing, tool calls |
| MCP + Roslyn semantic understanding | Corrected | Copilot offers language-aware symbol navigation via the `find_symbol` tool. "Direct Roslyn comms" holds via a separate MCP server extension (e.g., MCP AI Server) |
| MCP AI Server | Verified | `LadislavSopko/mcp-ai-server-visual-studio`. Roslyn-based 20 tools, for MCP clients |
| OpenCode AI Assistant | Verified | Real on marketplace (`NatanaelNunez.opencode-ai-assistant-vs`). Multi-provider |
| Visual chatGPT Studio | Verified | Free, needs OpenAI API key. Provides refactor/bug-find/test-gen commands |
| Tongyi Lingma | Corrected | Rebranded to "Qoder (formerly Lingma)". 3.5M+ cumulative downloads across channels. Free trial / limited-time free |
| MS C# ext usage in Cursor | Verified | MS restricts C#/C++/C# Dev Kit to MS-family editors. Anysphere ships its own netcoredbg-based C# extension (`@id:anysphere.csharp`) |
| ReSharper for VS Code | Verified | Released 2026-03-05 (supports VS Code & Cursor). AI Assistant is paid (free for non-commercial/learning) |
| DeepSeek integration | Verified | DeepSeek is OpenAI-compatible (`https://api.deepseek.com`). Connectable from any extension that accepts an OpenAI-compatible base_url |
| IntelliCode | Verified | Built into MS. Completion based on learned code patterns |
| A3sist | Unverified | Could not confirm existence/maintenance from public sources. Verify on marketplace/GitHub before adopting |
| L.AI | Unverified | Could not confirm from public sources. Verify directly |
| Fitten Code / CodeAnalyzerAI | Unverified | Details/current maintenance need direct verification |

> **Bottom line**: The big picture (Copilot agent mode, MCP+Roslyn, Cursor's C# limitation, ReSharper for VS Code, the free extensions) is largely accurate. However, some minor extensions (A3sist, L.AI, etc.) cannot be confirmed for existence/maintenance from public sources and need direct verification before adoption.

---

## 1. Built-in AI in Visual Studio (check first)

- **GitHub Copilot** (Verified) — Real-time completion + agent mode (VS 2022 17.14+ / VS 2026). Agent mode supports multi-file edits, iterative error fixing, tool calls, and MCP server connections. Custom agents can be defined via `.agent.md`.
- **IntelliCode** (Verified) — Context-aware completion based on learned code patterns (no model setup needed).

> To start with no extra keys/config, Copilot + IntelliCode is the baseline. Note Copilot's default models are OpenAI/Anthropic, and direct wiring to arbitrary external OpenAI-compatible endpoints (e.g., DeepSeek) is limited (route via the third-party extensions in Sections 2–3).

---

## 2. Recommended AI Extensions for C# Developers (Visual Studio)

> Install counts and prices change over time — read on the premise that you'll reconfirm current figures on the marketplace.

| Extension | Core value | Multi-LLM connection | Price/License | Status |
|---|---|---|---|---|
| **Visual chatGPT Studio** | Refactor/bug-find/test-gen commands, in-editor chat | OpenAI-compatible key + Base URL override → DeepSeek/MiniMax/local | Free (key needed) | Verified |
| **OpenCode AI Assistant** | Large-solution focus, Roslyn symbol indexing | OpenAI/Anthropic/Ollama multi-provider | Free (MIT, key needed) | Verified |
| **MCP AI Server** | Exposes 20 Roslyn tools via MCP (AI understands by meaning) | Model-agnostic (MCP client picks model) | Key/client separate | Verified |
| **Qoder (formerly Tongyi Lingma)** | NL→code, multi-line generation | Alibaba's own models | Free trial / limited-time free | Corrected (rebranded) |
| **ReSharper + AI Assistant** | Best static analysis/refactoring + AI chat/completion | JetBrains AI Service (model choice) | Paid (free non-commercial) | Verified |
| A3sist / L.AI | Claims local (Ollama) privacy focus | verify | verify | Unverified |

**Recommendations by situation**
- **Official, latest, safe**: GitHub Copilot (agent mode) + IntelliCode
- **Flexible across many LLMs**: OpenCode AI Assistant or Visual chatGPT Studio (Base URL override)
- **AI that understands code semantically (accurate nav/refactor)**: MCP AI Server (+ Copilot agent mode or another MCP client)
- **Top refactoring quality**: ReSharper + AI Assistant (paid)
- **Local/privacy**: prefer Ollama + an OpenAI-compatible extension first (see 3.4). Adopt A3sist/L.AI only after confirming existence/maintenance

---

## 3. How to Connect DeepSeek and Various LLMs (the core)

The principle is singular. Most commercial LLMs expose an OpenAI-compatible (`/v1/chat/completions`) endpoint, so you can use many models from the same extension just by changing "Base URL + API Key + model name."

### 3.1 OpenAI-Compatible Endpoints

| Provider | Base URL | Example model | Notes |
|---|---|---|---|
| **DeepSeek** | `https://api.deepseek.com` (`/v1` ok) | `deepseek-chat`, `deepseek-reasoner` | OpenAI-compatible. Confirm current model IDs in console |
| **MiniMax** | `https://api.minimax.io/v1` | `MiniMax-M3`, `MiniMax-M2.5` | Both OpenAI & Anthropic compatible ([guide](minimax-coding-guide.en.md)) |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-5.5`, `gpt-5.4-mini` | Reference impl |
| **OpenRouter** | `https://openrouter.ai/api/v1` | `deepseek/deepseek-chat`, etc. | Route many models with one key |
| **Local Ollama** | `http://localhost:11434/v1` | `qwen2.5-coder`, `deepseek-coder-v2` | Fully offline/private |

> Get a DeepSeek API key: `https://platform.deepseek.com` → API Keys. Model identifiers (deepseek-chat/-reasoner, etc.) change over time — confirm the current names in the console before entering.

### 3.2 Wiring DeepSeek via Visual chatGPT Studio (easiest)

1. Install Visual chatGPT Studio from the marketplace
2. Open `Tools → Options → Visual chatGPT Studio`
3. **API Key**: enter your DeepSeek key
4. **Base URL / Base API URL** (the OpenAI endpoint override field): `https://api.deepseek.com`
5. **Model**: `deepseek-chat` (or the current model name from the console)
6. Select code → right-click or use commands to run refactor/bug-find/test-gen

> The same way, just change the Base URL to `https://api.minimax.io/v1` (MiniMax), `https://openrouter.ai/api/v1` (OpenRouter), or `http://localhost:11434/v1` (Ollama) to swap models in the same UI.

### 3.3 Multi-Provider via OpenCode AI Assistant

- After install, choose a Provider (OpenAI / Anthropic / Ollama / custom OpenAI-compatible)
- Pick custom OpenAI-compatible and set Base URL + Key + model name to DeepSeek/MiniMax/local
- On large solutions, Roslyn symbol indexing gives whole-project type awareness → accurate context

### 3.4 Local (offline) — Ollama + any extension

1. Install Ollama and pull a model: `ollama pull qwen2.5-coder` (or `deepseek-coder-v2`)
2. Ollama serves OpenAI-compatible at `http://localhost:11434/v1`
3. In Visual chatGPT Studio / OpenCode, set Base URL to the address above and any value as the key (`ollama`)
4. Suitable for air-gapped environments / sensitive code (fully local)

### 3.5 Make "AI understand code semantically" via MCP

- Install MCP AI Server (20 Roslyn tools) so an MCP client (e.g., Copilot agent mode) can call compiler-level tools like `FindSymbols` and operate on symbols rather than plain text.
- The model itself can be anything (commercial/DeepSeek/local), chosen in the client — a separation where the MCP server handles "accurate code understanding" and the model handles "reasoning."

---

## 4. Hybrid Routing (optimize cost & quality together)

Splitting models by task difficulty cuts cost substantially (detailed pricing/rationale in [MiniMax guide, Sections 4 & 6](minimax-coding-guide.en.md)).

| Task | Recommended |
|---|---|
| Autocomplete / simple queries | Local (Ollama) or a low-cost DeepSeek model |
| Function-level generation | DeepSeek / MiniMax M2.5 |
| Multi-file refactoring | MiniMax M3 / a 1M-context model |
| High-precision code review | Claude Opus / top GPT (failover only when needed) |

> Key: default to cheap/local, fail over to a top model only when precision is needed. Switch manually by changing the Base URL in Visual chatGPT Studio/OpenCode, or delegate routing to one key via OpenRouter.

---

## 5. Selection Guide (summary)

| Priority | Recommended setup |
|---|---|
| Safe & official | GitHub Copilot (agent mode) + IntelliCode |
| Free with DeepSeek/multi-LLM | Visual chatGPT Studio or OpenCode AI Assistant (Base URL override) |
| Local/privacy | Ollama + an OpenAI-compatible extension |
| Semantic accuracy (nav/refactor) | MCP AI Server + agent mode |
| Best refactoring (paid) | ReSharper + AI Assistant |
| Prefer VS Code's lightness | ReSharper for VS Code (C#/Razor/Blazor) |

---

## References (verified 2026-06-04)

- Visual Studio Agent Mode + MCP: https://learn.microsoft.com/en-us/visualstudio/ide/copilot-agent-mode · https://learn.microsoft.com/en-us/visualstudio/ide/mcp-servers
- MCP AI Server (Roslyn): https://github.com/LadislavSopko/mcp-ai-server-visual-studio
- OpenCode AI Assistant: https://marketplace.visualstudio.com/items?itemName=NatanaelNunez.opencode-ai-assistant-vs
- Visual chatGPT Studio: https://marketplace.visualstudio.com/items?itemName=jefferson-pires.VisualChatGPTStudio · https://github.com/jeffdapaz/VisualChatGPTStudio
- Qoder (formerly Tongyi Lingma): https://marketplace.visualstudio.com/items?itemName=Alibaba-Cloud.tongyi-lingma
- ReSharper for VS Code (release): https://blog.jetbrains.com/dotnet/2026/03/05/resharper-for-visual-studio-code-cursor-and-compatible-editors-is-out/
- Cursor C# license/netcoredbg: https://devclass.com/2025/04/08/vs-code-extension-marketplace-wars-cursor-users-hit-roadblocks/
- DeepSeek API (OpenAI-compatible): https://api-docs.deepseek.com/

---

> **Disclaimer**: This document is a reference that verifies/organizes public information as of 2026-06-04. Extension install counts, prices, model names, and maintenance status change rapidly — reconfirm via official sources before adopting. For tools labeled Unverified (A3sist, L.AI, etc.), verify existence/reliability directly before use. Manage API keys via environment variables / the IDE's secure storage and never commit them to a repository.

*— End of document —*
