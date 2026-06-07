// config.ts — environment variable loader with defaults

import 'dotenv/config';

export const config = {
  port: parseInt(process.env.PORT || '3101', 10),
  host: process.env.HOST || '127.0.0.1',

  llm: {
    providers: (process.env.LLM_PROVIDERS || 'openai').split(',').map(p => p.trim()),
    mode: (process.env.LLM_MODE || 'parallel') as 'parallel' | 'sequential' | 'majority',
    openai: {
      apiKey: process.env.OPENAI_API_KEY || '',
      baseUrl: process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1',
      model: process.env.OPENAI_MODEL || 'gpt-4o',
    },
    deepseek: {
      apiKey: process.env.DEEPSEEK_API_KEY || '',
      baseUrl: process.env.DEEPSEEK_BASE_URL || 'https://api.deepseek.com/v1',
      model: process.env.DEEPSEEK_MODEL || 'deepseek-chat',
    },
    minimax: {
      apiKey: process.env.MINIMAX_API_KEY || '',
      baseUrl: process.env.MINIMAX_BASE_URL || 'https://api.minimaxi.com/v1',
      model: process.env.MINIMAX_MODEL || 'abab6.5s-chat',
    },
    mimo: {
      apiKey: process.env.MIMO_API_KEY || '',
      baseUrl: process.env.MIMO_BASE_URL || '',
      model: process.env.MIMO_MODEL || '',
    },
  },

  github: {
    token: process.env.GITHUB_TOKEN || '',
  },

  scan: {
    cron: process.env.SCAN_CRON || '0 */6 * * *',
    timeoutMs: parseInt(process.env.SCAN_TIMEOUT_MS || '60000', 10),
    maxCandidates: parseInt(process.env.SCAN_MAX_CANDIDATES || '500', 10),
    maxFileSizeKb: parseInt(process.env.SCAN_MAX_FILE_SIZE_KB || '1024', 10),
  },

  db: {
    path: process.env.DB_PATH || './data',
  },

  alerts: {
    slack: {
      webhookUrl: process.env.SLACK_WEBHOOK_URL || '',
    },
    telegram: {
      botToken: process.env.TELEGRAM_BOT_TOKEN || '',
      chatId: process.env.TELEGRAM_CHAT_ID || '',
    },
    email: {
      host: process.env.EMAIL_HOST || '',
      port: parseInt(process.env.EMAIL_PORT || '587', 10),
      user: process.env.EMAIL_USER || '',
      pass: process.env.EMAIL_PASS || '',
      to: process.env.EMAIL_TO || '',
    },
  },

  isMacOS: process.platform === 'darwin',
};

// validate: at least one LLM key
export function validateConfig(): string[] {
  const errors: string[] = [];
  const providers = config.llm.providers;
  const hasKey = providers.some(p => {
    const key = config.llm[p as keyof typeof config.llm] as { apiKey: string };
    return key?.apiKey;
  });
  if (!hasKey) errors.push('At least one LLM API key must be provided (OPENAI_API_KEY, DEEPSEEK_API_KEY, etc)');
  return errors;
}
