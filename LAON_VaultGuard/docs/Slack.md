# Slack 연동 가이드 — LAON VaultGuard

> 🇰🇷 Slack 웹훅을 통해 탐지 결과를 팀 채널로 실시간 전송하는 방법.
> 🇺🇸 How to send real-time detection results to Slack channels via webhook.
> 🇨🇳 通过 Slack Webhook 将检测结果实时发送到团队频道。

## 1. Slack Webhook URL 생성

1. https://api.slack.com/apps → **Create New App** → **From scratch**
2. App Name: `LAON VaultGuard`, Workspace 선택 → **Create App**
3. 좌측 메뉴 **Incoming Webhooks** → **Activate Incoming Webhooks**
4. **Add New Webhook to Workspace** → 알림 받을 채널 선택 → **Allow**
5. 생성된 Webhook URL 복사 (예: `https://hooks.slack.com/services/T.../B.../xxx`)

## 2. .env 설정

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../xxx
```

## 3. 작동 확인

```bash
npm run dev
# → critical/high finding 발생 시 자동으로 Slack 채널에 메시지 전송
```

## 4. Slack 메시지 형식

![Slack message example](https://img.shields.io/badge/Slack-4A154B?style=flat&logo=slack&logoColor=white)

```
🛡 LAON VaultGuard — Secret Alert

Repo: my-project
Findings: 3 total (🔴 2 critical, 🟠 1 high)

─────────────────────
🔴 [CRITICAL] AWS — AWS Access Key ID
📁 src/config.ts:42
🔑 AKIA…7Q
💡 1) Rotate/revoke immediately. 2) Move to secrets manager.

🟠 [HIGH] Generic — Hardcoded Password
📁 .env.production:8
🔑 [REDACTED]
─────────────────────

[🔍 View Dashboard] → http://localhost:3101/dashboard
```

## 5. 여러 채널로 분기 (고급)

서로 다른 severity를 다른 채널로 보내려면 Slack App에서 여러 Webhook을 생성하고, `.env` 확장:

```bash
# .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/...  # critical+high 전체
SLACK_CRITICAL_WEBHOOK_URL=https://hooks.slack.com/...  # critical 전용 (추후 지원)
```

## 6. 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| 메시지가 안 옴 | Webhook URL 오류 | `.env`에서 URL 재확인 |
| 403 Forbidden | App이 채널에 추가 안 됨 | Slack App → Incoming Webhooks → 채널 재선택 |
| 메시지 형식 깨짐 | Markdown 파싱 오류 | Slack API 문서에서 Block Kit 포맷 확인 |

## 7. Slack App 아이콘 커스터마이징

Slack App 설정 → **Basic Information** → **Display Information** 에서:
- App name: `LAON VaultGuard`
- Icon: 원하는 보안 관련 아이콘 업로드
- Background color: `#0d1117`

---

> 💡 Slack + Telegram을 함께 연동하면 팀은 Slack에서, 개인은 Telegram에서 알림을 받을 수 있습니다.
