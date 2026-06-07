// config.ts — environment variable loader with defaults

import 'dotenv/config';
import { hostname } from 'node:os';

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
    ollama: {
      apiKey: 'ollama',
      baseUrl: process.env.OLLAMA_BASE_URL || 'http://localhost:11434/v1',
      model: process.env.OLLAMA_MODEL || 'llama3.1',
    },
    claude: {
      apiKey: process.env.CLAUDE_API_KEY || process.env.ANTHROPIC_API_KEY || '',
      baseUrl: process.env.CLAUDE_BASE_URL || 'https://api.anthropic.com/v1',
      model: process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514',
    },
  },

  github: {
    token: process.env.GITHUB_TOKEN || '',
    oauthToken: '', // set at runtime via OAuth flow
    clientId: process.env.GITHUB_CLIENT_ID || '',
    clientSecret: process.env.GITHUB_CLIENT_SECRET || '',
    redirectUri: process.env.GITHUB_REDIRECT_URI || 'http://localhost:3101/api/oauth/github/callback',
  },

  scan: {
    cron: process.env.SCAN_CRON || '0 */6 * * *',
    timeoutMs: parseInt(process.env.SCAN_TIMEOUT_MS || '60000', 10),
    maxCandidates: parseInt(process.env.SCAN_MAX_CANDIDATES || '500', 10),
    maxFileSizeKb: parseInt(process.env.SCAN_MAX_FILE_SIZE_KB || '1024', 10),
    cacheEnabled: process.env.SCAN_CACHE_ENABLED !== 'false',
    tieredLLM: process.env.SCAN_TIERED_LLM !== 'false',
    lightProviders: (process.env.SCAN_LIGHT_PROVIDERS || 'minimax,ollama').split(',').map(p => p.trim()),
    heavyProviders: (process.env.SCAN_HEAVY_PROVIDERS || 'claude,deepseek').split(',').map(p => p.trim()),
    batchSize: parseInt(process.env.SCAN_BATCH_SIZE || '50', 10),
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
    teams: {
      webhookUrl: process.env.TEAMS_WEBHOOK_URL || '',
    },
    discord: {
      webhookUrl: process.env.DISCORD_WEBHOOK_URL || '',
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
  isLinux: process.platform === 'linux',
  isWindows: process.platform === 'win32',
  platform: process.platform as 'darwin' | 'linux' | 'win32',
  deviceName: process.env.DEVICE_NAME || hostname(),
  reportSchedule: (process.env.REPORT_SCHEDULE || 'daily') as 'daily' | 'weekly' | 'off',
};

// validate: at least one LLM key
export function validateConfig(): string[] {
  const errors: string[] = [];
  const providers = config.llm.providers;
  const hasKey = providers.some(p => {
    if (p === 'ollama') return true; // ollama doesn't need API key
    if (p === 'claude') {
      const c = config.llm.claude;
      return !!c.apiKey;
    }
    const key = config.llm[p as keyof typeof config.llm] as { apiKey: string };
    return key?.apiKey && !key.apiKey.startsWith('sk-your-');
  });
  if (!hasKey) errors.push('At least one LLM provider must be configured (CLAUDE_API_KEY, DEEPSEEK_API_KEY, OPENAI_API_KEY, or Ollama)');
  if (providers.length < 1) errors.push('LLM_PROVIDERS must have at least 1 provider');
  if (providers.length > 0 && providers.length < 2) {
    // not an error, just a recommendation
  }
  return errors;
}
