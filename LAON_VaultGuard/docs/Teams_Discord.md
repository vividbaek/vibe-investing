# Teams / Discord Setup Guide

> Microsoft Teams and Discord webhook integration for real-time secret alerts.

## Teams

### 1. Create Incoming Webhook

1. Open Teams -> channel -> "..." menu -> **Connectors**
2. Search "Incoming Webhook" -> **Add** -> **Configure**
3. Name: `LAON VaultGuard` -> **Create**
4. Copy the webhook URL

### 2. .env

```bash
TEAMS_WEBHOOK_URL=https://xxx.webhook.office.com/webhookb2/.../IncomingWebhook/...
```

### 3. Enable in Dashboard

Dashboard -> "Alert Settings" -> toggle **Teams** ON.

### 4. Message Format

Teams receives **Adaptive Card** messages:

```
LAON VaultGuard — Secret Alert

Device:    Dennis-MacBook
Repo:      my-project
Critical:  2
High:      1

[CRITICAL] AWS — AWS Access Key ID
src/config.ts:42 | AKIA...7Q

[HIGH] Generic — Hardcoded Password
.env.production:8 | [REDACTED]
```

---

## Discord

### 1. Create Webhook

1. Discord -> Server Settings -> **Integrations** -> **Webhooks**
2. **New Webhook** -> Name: `LAON VaultGuard`
3. Select target channel -> **Copy Webhook URL**

### 2. .env

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 3. Enable in Dashboard

Dashboard -> "Alert Settings" -> toggle **Discord** ON.

### 4. Message Format

Discord receives **Embed** messages:

```
[LAON VaultGuard — Secret Alert]

Device: Dennis-MacBook
Repo: my-project
Findings: 3 (critical: 2, high: 1)

[CRITICAL] AWS — AWS Access Key ID
File: src/config.ts:42
Fingerprint: AKIA...7Q

[HIGH] Generic — Hardcoded Password
File: .env.production:8
Fingerprint: [REDACTED]
```

---

## All Alert Channels

| Channel | Setup | Format |
|---|---|---|
| Dashboard | Built-in | SSE real-time |
| Telegram | Bot Token + Chat ID | Markdown |
| Slack | Incoming Webhook | Block Kit |
| Teams | Incoming Webhook | Adaptive Card |
| Discord | Webhook | Embed |
| Email | SMTP | HTML |

Each channel can be independently toggled ON/OFF from the dashboard "Alert Settings" panel.
