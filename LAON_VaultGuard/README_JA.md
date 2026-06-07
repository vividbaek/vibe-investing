# LAON VaultGuard

> **LLM-based Automated Observer for Non-public Keys**
>
> 開発者PCやチーム環境でGitリポジトリを定期的に監視し、AWS、Azure、GCP、KT Cloud、Naver Cloud のクラウドプライベートキーが露出するのを未然に防ぐクロスプラットフォームセキュリティ監査ツール。

[한국어](./README.md) | [English](./README_EN.md) | [中文](./README_ZH.md) | 日本語

## なぜ LAON VaultGuard か

**2026年6月、Tving の GitHub リポジトリに AWS アクセストークンがハードコーディングされたまま公開された事件**は、単一のミスがインフラ全体を危険に晒すことを再証明しました。`gitleaks`や`trufflehog`のような正規表現ベースのスキャナーは高速ですが、文脈を理解しません。一方 LLM は変数名が平凡でも、組み立てられた形のシークレットも「意味」で検出できます。

しかし**単一LLMへの依存は新たな単一障害点**です。LAON VaultGuard は**複数LLMの同時クロス検証**構造で設計されています：
- Claude（規律ベース）、DeepSeek（高性能・低コスト）、GPT（体系的）、**Ollama（ローカル・オフライン）**
- **多数決モード**で誤検知を減らし、**逐次フォールバック**で単一LLM障害時もスキャンを継続

## 主要機能

- **定期リポジトリ監視** — cron スケジューラーで GitHub、GitLab、ローカルリポジトリを自動スキャン
- **マルチLLM検出** — OpenAI、DeepSeek、Claude、Ollama のクロス検証
- **オフラインモード** — Ollama 連携でインターネットなし完全ローカル検出
- **2段階検出** — ① git grep キーワードフィルター → ② LLM 文脈分析
- **Webダッシュボード** — 同一ネットワークのチームで監視可能
- **マルチアラート** — Slack、Telegram、メール、Discord、Teams
- **v0.5 新機能**: SQLite WAL ストレージ、差分プライバシー、SARIF エクスポート、Prometheus `/metrics`、Docker

## 利用シーン

### 🧑‍💻 個人開発者

```bash
npm run setup        # DeepSeek APIキーのみ入力（月額 $1未満）
npm run dev
```

- DeepSeek 単独で高速・低コスト
- VS Code 拡張が保存時にリアルタイム警告
- Ollama 導入でAPIコストゼロ

### 🏢 中小企業 / チーム

```bash
LLM_PROVIDERS=claude,deepseek,ollama
LLM_MODE=majority
SCAN_CRON=0 */4 * * *
```

- 3重クロス検証で誤検知最小化
- Docker: `docker-compose up -d`

### 🔒 オフライン / エアギャップ

```bash
brew install ollama
ollama pull deepseek-r1:8b
LLM_PROVIDERS=ollama
```

- 全LLM推論がローカル実行、ソースコード外部流出ゼロ
- deepseek-r1 + securereview-7b の2重クロス検証
- 防衛・金融・公共機関のコンプライアンス対応

## Docker インストール

```bash
cd LAON_VaultGuard
cp .env.example .env
docker-compose up -d
docker-compose --profile ollama up -d   # GPU Ollama 含む
```

## VS Code 拡張インストール

```bash
cd LAON_VaultGuard/vscode-extension
npm install && npm run compile
# VS Code: Cmd+Shift+P → Developer: Install Extension from Location...
```

| 機能 | 説明 |
|------|------|
| **リアルタイム強調** | 13種類のシークレットパターン自動検出 |
| **問題パネル** | マスク済み指紋のみ表示 (`AKIA****7Q`) |
| **ステータスバー** | `LAON: clean` / `LAON: 3` 表示 |

## クイックスタート

```bash
git clone https://github.com/gameworkerkim/vibe-investing.git
cd vibe-investing/LAON_VaultGuard
npm install
npm run setup
npm run dev
```

## CLI スキャン

```bash
npx laon-vaultguard scan .
npx laon-vaultguard scan . --mode secrets
npx laon-vaultguard scan . --no-llm
```

## ロードマップ

### v0.5 ✅ 完了

- [x] SQLite 移行（WAL, ACID, `npm run migrate`）
- [x] SARIF v2.1.0 エクスポート
- [x] 差分プライバシー（14種シークレットマスクルール）
- [x] Prometheus `/metrics` エンドポイント
- [x] Docker イメージ + docker-compose
- [x] VS Code 拡張
- [x] 多言語セットアップウィザード（한/EN/中/日）

### v0.6（計画）

- [ ] 誤検知フィードバックループ
- [ ] ファインチューニングモデル評価パイプライン
- [ ] pre-commit hook 統合

## バックテスト結果 (v0.5)

`npm run backtest` — **54 の自動テストすべて合格** ✅

| モジュール | 合格 | 検証項目 |
|------------|------|----------|
| ストレージ (SQLite + JSON) | 12/12 | CRUD, WAL, 移行 |
| 差分プライバシー | 10/10 | 14 種類のシークレットマスクルール |
| SARIF エクスポート | 4/4 | v2.1.0, GitHub Code Scanning |
| Prometheus メトリクス | 5/5 | `/metrics` エンドポイント |
| 候補フィルター | 4/4 | 60+ パターン, grep 統合 |
| 設定 + バージョン | 7/7 | 検証, デフォルト値 |

→ [詳細チェックリスト](./docs/BACKTEST_CHECKLIST.md)

## ライセンス

MIT

---

> *"公開前に見つけることは、公開後に後始末するより百倍簡単だ。"*
> — Tving AWSキー露出事件 (2026.06) からの教訓
