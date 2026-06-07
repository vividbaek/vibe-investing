# LAON VaultGuard ／ 澜安 VaultGuard

> **LLM-based Automated Observer for Non-public Keys**
>
> 跨平台安全审计工具，定期监控开发者和团队环境中的 Git 仓库，防止云端私钥（AWS、Azure、GCP、KT Cloud、Naver Cloud）泄露。

[한국어](./README.md) | [English](./README_EN.md) | 中文 | [日本語](./README_JA.md)

## 为什么选择 LAON VaultGuard

**2026年6月，Tving 的 GitHub 仓库公开了硬编码的 AWS 访问令牌**，再次证明单次失误即可危及整个基础设施。`gitleaks`、`trufflehog` 等正则扫描器虽快但缺乏上下文理解。而 LLM 能通过"语义"检测变量名普通或拼接形式的密钥。

**依赖单一 LLM 是新的单点故障**。LAON VaultGuard 采用**多 LLM 交叉验证**架构：
- Claude（规则导向）、DeepSeek（高性能·低成本）、GPT（系统化）、**Ollama（本地·离线）**
- **多数决模式**减少误报，**顺序回退**确保单 LLM 故障不中断扫描
- gitleaks → **LAON VaultGuard** → TruffleHog → GitHub Secret Scanning 四层防线

## 核心功能

- **定期仓库监控** — cron 调度器自动扫描 GitHub、GitLab、本地仓库
- **多 LLM 检测** — OpenAI、DeepSeek、Claude、Ollama 交叉验证
- **离线模式** — Ollama 支持完全断网环境下的密钥检测
- **两级检测** — ① git grep 关键词过滤 → ② LLM 上下文分析
- **Web 仪表板** — 团队共享的本地 Web UI
- **多通道告警** — Slack、Telegram、邮件、Discord、Teams
- **v0.5 新增**: SQLite WAL 存储、差分隐私、SARIF 导出、Prometheus `/metrics`、Docker

## 使用场景

### 🧑‍💻 个人开发者

```bash
npm run setup        # 仅输入 DeepSeek API 密钥（月费 < $1）
npm run dev          # http://localhost:3101/dashboard
```

- 仅用 DeepSeek 快速低成本扫描（$0.14/百万令牌）
- VS Code 插件保存时实时警告
- 安装 Ollama 后 API 费用为零

### 🏢 中小企业 / 团队

```bash
LLM_PROVIDERS=claude,deepseek,ollama
LLM_MODE=majority   # 三重交叉验证
SCAN_CRON=0 */4 * * *
```

- Claude + DeepSeek + Ollama 三重交叉验证
- 团队仪表板：`HOST=0.0.0.0` → 局域网访问
- Docker 部署：`docker-compose up -d`

### 🔒 离线 / 内网环境

```bash
brew install ollama
ollama pull deepseek-r1:8b
LLM_PROVIDERS=ollama
STORAGE_ENGINE=sqlite
```

- 所有 LLM 推理在本地执行，源代码永不外泄
- deepseek-r1 (推理) + securereview-7b (安全微调) 双重交叉验证
- 满足国防、金融、政府等合规要求

## Docker 安装

```bash
cd LAON_VaultGuard
cp .env.example .env
docker-compose up -d              # 仅应用
docker-compose --profile ollama up -d   # 包含 GPU 加速 Ollama
```

## VS Code 插件安装

```bash
cd LAON_VaultGuard/vscode-extension
npm install && npm run compile
# VS Code: Cmd+Shift+P → Developer: Install Extension from Location...
```

| 功能 | 说明 |
|------|------|
| **实时高亮** | 13 种密钥模式自动检测，虚线下划线 |
| **问题面板** | 仅显示脱敏指纹 (`AKIA****7Q`) |
| **状态栏** | `LAON: clean` / `LAON: 3` 实时指示 |

## 快速开始

```bash
git clone https://github.com/gameworkerkim/vibe-investing.git
cd vibe-investing/LAON_VaultGuard
npm install
npm run setup
npm run dev
```

## CLI 扫描

```bash
npx laon-vaultguard scan .
npx laon-vaultguard scan . --mode secrets
npx laon-vaultguard scan . --no-llm
```

## 技术栈

| 层 | 技术 |
|---|------|
| **运行时** | Node.js ≥18, TypeScript |
| **存储** | SQLite (WAL, ACID) / JSON |
| **LLM** | OpenAI, DeepSeek, Claude, Ollama |
| **调度** | node-cron |
| **仪表板** | Express + SSE |
| **容器** | Docker + docker-compose |

## 路线图

### v0.5 ✅ 已完成

- [x] SQLite 迁移（WAL, ACID, `npm run migrate`）
- [x] SARIF v2.1.0 导出（`npm run export-sarif`）
- [x] 差分隐私（14 种密钥掩码规则）
- [x] Prometheus `/metrics` 端点
- [x] Docker 镜像 + docker-compose
- [x] VS Code 插件
- [x] 多语言安装向导（한/EN/中/日）

### v0.6（计划中）

- [ ] 误报反馈循环
- [ ] 微调模型评估流水线
- [ ] pre-commit hook 集成

## 回测结果 (v0.5)

`npm run backtest` — **54 项自动化测试全部通过** ✅

| 模块 | 通过 | 已验证 |
|------|------|--------|
| 存储 (SQLite + JSON) | 12/12 | CRUD, WAL, 迁移 |
| 差分隐私 | 10/10 | 14 种密钥掩码规则 |
| SARIF 导出 | 4/4 | v2.1.0, GitHub Code Scanning |
| Prometheus 指标 | 5/5 | `/metrics` 端点 |
| 候选过滤器 | 4/4 | 60+ 模式, grep 集成 |
| 配置 + 版本 | 7/7 | 验证, 默认值 |

→ [完整清单](./docs/BACKTEST_CHECKLIST.md)

## 许可证

MIT

---

> *"在公开之前发现，比事后补救容易一百倍。"*
> — 来自 Tving AWS 密钥泄露事件 (2026.06)
