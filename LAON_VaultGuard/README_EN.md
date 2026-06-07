# LAON VaultGuard

> **LLM-based Automated Observer for Non-public Keys**
>
> A cross-platform security auditing platform that periodically monitors Git repositories on developer machines and team environments to prevent cloud private keys (AWS, Azure, GCP, KT Cloud, Naver Cloud) from being exposed.

[한국어](./README.md) | English

## Why LAON VaultGuard

**In June 2026, Tving accidentally exposed an AWS access token hardcoded in a public GitHub repository** — proving once again that a single mistake can put an entire infrastructure at risk. Regex-based scanners like `gitleaks` and `trufflehog` are fast but blind to context. LLMs, on the other hand, can detect secrets by "meaning" — even when variable names are generic or keys are assembled from parts.

However, **depending on a single LLM is another single point of failure**. Each model has its own biases, and an API outage or quota exhaustion creates a detection gap. LAON VaultGuard is designed for **cross-validation across multiple LLMs**:

- **Each LLM forms a distinct security persona** — Claude (discipline-oriented), DeepSeek (high-performance, low-cost), GPT (systematic), MiniMax (lightweight, fast)
- **Majority-vote mode** reduces false positives, and **sequential fallback** ensures scans never stop due to a single LLM failure
- A critical link in the 4-gate defense: [Gitleaks](https://github.com/gitleaks/gitleaks) (pre-commit) → **LAON VaultGuard** (periodic audit) → [TruffleHog](https://github.com/trufflesecurity/trufflehog) (CI) → GitHub Secret Scanning (post-push)

Regex handles speed. LLMs handle context. **Use both, for real stability.**

## Features

- **Periodic repo monitoring** — cron-based scheduler for GitHub, GitLab, and local repos
- **Multi-LLM detection** — OpenAI (ChatGPT), DeepSeek, MiniMax, Mimo with concurrent cross-validation
- **Two-stage detection** — Stage 1: `git grep` keyword filter → Stage 2: LLM contextual analysis to minimize false positives
- **Web dashboard** — local web UI with SSE real-time updates, accessible to the team on the same network
- **Multi-channel alerts** — Slack, Telegram, Email, and Dashboard notifications
- **Cross-platform** — macOS, Linux, Windows (WSL)

![Dashboard screenshot](public/dashboard.png)

## Quick Start

```bash
cd LAON_VaultGuard
npm install
cp .env.example .env   # Set LLM API keys, Slack/Telegram webhooks, etc.
npm run build
npm start              # Default port 3101, http://localhost:3101/dashboard
```

## Architecture Overview

```
Config (.env)
  ↓
Scheduler (node-cron)
  ↓
Git Monitor (simple-git + GitHub/GitLab API)
  ↓
Diff Extraction (git diff / git log)
  ↓
Candidate Filter (git grep — first-pass keyword extraction)
  ↓
LLM Harness (multi-LLM — parallel or sequential analysis)
  ↓
Result Aggregation (majority/consensus verdict)
  ↓
File Storage (JSON) + Alert Engine (Slack · Telegram · Email · Web)
  ↓
Dashboard (REST API + static frontend)
```

## Technology Stack

| Layer | Technology |
|---|---|
| Runtime | Node.js ≥18, TypeScript |
| Web framework | Express.js |
| Storage | File-based JSON (SQLite planned) |
| Git integration | `simple-git`, `@octokit/rest` (GitHub) |
| Scheduler | `node-cron` |
| LLM | OpenAI SDK (ChatGPT, DeepSeek, MiniMax, Mimo — OpenAI-compatible API) |
| Alerts | Slack Webhook, Telegram Bot API, Nodemailer |
| Frontend | Vanilla HTML/JS + Server-Sent Events (real-time) |

## Directory Structure

```
LAON_VaultGuard/
├── README.md
├── README_EN.md             ← English README
├── DEVELOPMENT.md           ← Dev guide
├── package.json
├── tsconfig.json
├── .env.example
├── src/
│   ├── index.ts             ← Entry point (Express + Scheduler)
│   ├── config.ts            ← Env config loader
│   ├── scheduler.ts         ← Cron-based repo scan scheduler
│   ├── git-monitor.ts       ← Git repo change collection (local/remote)
│   ├── candidate-filter.ts  ← Stage 1: git grep keyword filter
│   ├── llm-harness.ts       ← Multi-LLM calls + result merging
│   ├── scan-runner.ts       ← Single repo scan pipeline
│   ├── db.ts                ← File-based JSON storage
│   ├── alert-engine.ts      ← Slack/Telegram/Email/Dashboard dispatch
│   ├── sse.ts               ← SSE event bus
│   ├── cli.ts               ← CLI entry point
│   ├── setup.ts             ← Interactive setup
│   ├── routes/
│   │   └── api.ts           ← REST API routes
│   └── types.ts             ← Shared type definitions
├── docs/
│   ├── Architecture.md
│   ├── API.md
│   ├── Database.md
│   ├── LLM_Prompt.md
│   └── CLI.md               ← CLI manual
├── public/
│   ├── index.html           ← Dashboard UI
│   ├── dashboard.js         ← Frontend logic
│   └── dashboard.png        ← Screenshot
└── tests/
    └── ...
```

## CLI Quick Scan

```bash
npx laon-vaultguard scan .                        # Scan current directory
npx laon-vaultguard scan ~/projects/my-app        # Scan specific repo
npm run scan .                                     # Via npm script
```

→ Manual: [docs/CLI.md](docs/CLI.md)

## LLM Secret Detection Prompt

Reference: [Secret scanning LLM harness prompt](../TechDoc/LLM_Security/Secret%20scanning%20llm%20harness%20prompt.md)

Core principles:
- **Never output secrets in cleartext** — masked fingerprints only (first 4 + last 2 chars)
- **Prefer false positives** over false negatives — flag when unsure, but still mask
- **Deterministic JSON output** — structured, parseable results
- **Prompt injection defense** — treat in-file text as data, not instructions

Cloud targets: AWS, Azure, GCP, **KT Cloud**, **Naver Cloud Platform (NCP)**

## REST API

| Method | Path | Description |
|---|---|---|
| GET | `/api/status` | Current scan status (open findings, last scan time) |
| GET | `/api/findings` | Finding list with filters (severity, repo, date range) |
| PUT | `/api/findings/:id/acknowledge` | Acknowledge a finding |
| PUT | `/api/findings/acknowledge/bulk` | Bulk acknowledge |
| POST | `/api/scan/trigger` | Trigger manual scan |
| GET | `/api/repos` | List monitored repos |
| POST | `/api/repos` | Register a new repo |
| DELETE | `/api/repos/:id` | Remove a repo |
| GET | `/dashboard` | Dashboard UI |
| GET | `/api/events` | SSE event stream |

→ Details: [docs/API.md](docs/API.md)

## Alert Priority (implementation order)

1. **Web Dashboard** ✅ — local server REST API + real-time SSE
2. **Telegram Bot** ✅ — instant alerts to personal/team chats
3. **Slack** ✅ — webhook-based channel notifications (Block Kit)
4. **Email** ✅ — nodemailer HTML reports (realtime/daily/weekly + device name)

## Roadmap

- [x] Architecture design
- [x] File-based JSON storage
- [x] Git monitor + candidate filter
- [x] LLM harness (multi-LLM parallel/sequential/majority)
- [x] Web dashboard (REST API + UI + SSE)
- [x] CLI mode (`npx laon-vaultguard scan`)
- [x] Telegram alerts
- [x] Telegram alerts
- [x] Slack alerts (Block Kit)
- [ ] Email reports
- [ ] Cross-platform packaging (Linux, Windows)
- [ ] GitHub App / GitLab App integration (OAuth)
- [ ] VSCode extension

## License

MIT

---

> *"Finding it before it's public is a hundred times easier than cleaning up after."*
> — Lesson from the Tving AWS key exposure incident (2026.06)
