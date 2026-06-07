// alert-engine.ts — notification dispatch (Telegram + Slack + Dashboard SSE)

import type { Repository, Finding } from './types.js';
import { config } from './config.js';
import { logAudit } from './db.js';

export async function sendAlerts(repo: Repository, findings: Finding[]) {
  const criticalHigh = findings.filter(f => f.severity === 'critical' || f.severity === 'high');
  if (criticalHigh.length === 0) return;

  // Slack
  if (config.alerts.slack.webhookUrl) {
    await sendSlackAlert(repo, criticalHigh);
  }

  // Telegram
  if (config.alerts.telegram.botToken && config.alerts.telegram.chatId) {
    await sendTelegramAlert(repo, criticalHigh);
  }

  // Email (future)
}

// ── Slack ──

async function sendSlackAlert(repo: Repository, findings: Finding[]) {
  const { webhookUrl } = config.alerts.slack;
  if (!webhookUrl) return;

  const blocks = buildSlackBlocks(repo, findings);

  try {
    const res = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: `🛡 LAON VaultGuard — ${findings.length} secrets found in ${repo.name}`,
        blocks,
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Slack API error: ${err}`);
    }

    logAudit('alert_sent', 'info', `Slack alert sent: ${findings.length} findings`, {
      repo: repo.name, channel: 'slack', findingsCount: findings.length,
    });
  } catch (err) {
    logAudit('alert_error', 'error',
      `Slack alert failed: ${err instanceof Error ? err.message : String(err)}`,
      { repo: repo.name, channel: 'slack' },
    );
  }
}

function buildSlackBlocks(repo: Repository, findings: Finding[]): Record<string, unknown>[] {
  const blocks: Record<string, unknown>[] = [];

  // Header
  blocks.push({
    type: 'header',
    text: { type: 'plain_text', text: `🛡 LAON VaultGuard — Secret Alert` },
  });

  // Summary
  const critical = findings.filter(f => f.severity === 'critical').length;
  const high = findings.filter(f => f.severity === 'high').length;
  blocks.push({
    type: 'section',
    text: {
      type: 'mrkdwn',
      text: `*Repo:* ${repo.name}\n*Findings:* ${findings.length} total (🔴 ${critical} critical, 🟠 ${high} high)`,
    },
  });

  blocks.push({ type: 'divider' });

  // Findings (max 5 to avoid message overflow)
  for (const f of findings.slice(0, 5)) {
    const emoji = f.severity === 'critical' ? '🔴' : '🟠';
    blocks.push({
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: `${emoji} *[${f.severity.toUpperCase()}] ${f.provider} — ${f.secretType}*\n` +
              `📁 \`${f.filePath}${f.line ? `:${f.line}` : ''}\`\n` +
              `🔑 \`${f.maskedFingerprint}\`\n` +
              `💡 ${f.remediation.slice(0, 100)}`,
      },
    });
  }

  if (findings.length > 5) {
    blocks.push({
      type: 'section',
      text: { type: 'mrkdwn', text: `_... and ${findings.length - 5} more findings_` },
    });
  }

  blocks.push({ type: 'divider' });

  // Actions
  blocks.push({
    type: 'actions',
    elements: [
      {
        type: 'button',
        text: { type: 'plain_text', text: '🔍 View Dashboard' },
        url: `http://localhost:3101/dashboard`,
      },
    ],
  });

  return blocks;
}

// ── Telegram ──

async function sendTelegramAlert(repo: Repository, findings: Finding[]) {
  const { botToken, chatId } = config.alerts.telegram;
  if (!botToken || !chatId) return;

  const lines = findings.map(f =>
    `🔴 [${f.severity.toUpperCase()}] ${f.provider} — ${f.secretType}\n` +
    `📁 ${repo.name}/${f.filePath}${f.line ? `:${f.line}` : ''}\n` +
    `🔑 ${f.maskedFingerprint}\n` +
    `💡 ${f.remediation.slice(0, 120)}`
  );

  const message =
    `🛡 *LAON VaultGuard* — Secret Alert\n\n` +
    `📦 Repo: *${repo.name}*\n` +
    `⚠️ Findings: ${findings.length} critical/high\n\n` +
    lines.join('\n\n');

  try {
    const url = `https://api.telegram.org/bot${botToken}/sendMessage`;
    const body = {
      chat_id: chatId,
      text: message,
      parse_mode: 'Markdown',
      disable_web_page_preview: true,
    };

    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Telegram API error: ${err}`);
    }

    logAudit('alert_sent', 'info', `Telegram alert sent: ${findings.length} findings`, {
      repo: repo.name, channel: 'telegram', findingsCount: findings.length,
    });
  } catch (err) {
    logAudit('alert_error', 'error',
      `Telegram alert failed: ${err instanceof Error ? err.message : String(err)}`,
      { repo: repo.name, channel: 'telegram' },
    );
  }
}
