// setup.ts — LAON VaultGuard interactive setup (masked API key input)
import { createInterface } from 'node:readline';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

const ENV_PATH = resolve(import.meta.dirname || '.', '../.env');
const ENV_EXAMPLE = resolve(import.meta.dirname || '.', '../.env.example');

function readEnvLines(path: string): string[] {
  if (existsSync(path)) {
    return readFileSync(path, 'utf-8').split('\n');
  }
  return readFileSync(ENV_EXAMPLE, 'utf-8').split('\n');
}

function writeEnv(lines: string[]) {
  writeFileSync(ENV_PATH, lines.join('\n'), 'utf-8');
}

function setKey(lines: string[], key: string, value: string): string[] {
  const prefix = `${key}=`;
  const idx = lines.findIndex(l => l.startsWith(prefix) || l.startsWith(`# ${prefix}`));
  if (idx !== -1) {
    lines[idx] = `${key}=${value}`;
  } else {
    lines.push(`${key}=${value}`);
  }
  return lines;
}

function maskedInput(prompt: string): Promise<string> {
  return new Promise(resolve => {
    process.stdout.write(prompt);
    let input = '';
    const prev = process.stdin.isRaw;
    process.stdin.setRawMode?.(true);
    process.stdin.resume();
    process.stdin.on('data', (chunk: Buffer) => {
      const str = chunk.toString();
      for (const ch of str) {
        if (ch === '\r' || ch === '\n') {
          process.stdout.write('\n');
          process.stdin.setRawMode?.(Boolean(prev));
          process.stdin.pause();
          resolve(input);
          return;
        }
        if (ch === '\x7f' || ch === '\b') {
          // backspace
          if (input.length > 0) {
            input = input.slice(0, -1);
            process.stdout.write('\b \b');
          }
        } else if (ch === '\x03') {
          // Ctrl+C
          process.stdout.write('\n');
          process.exit(1);
        } else {
          input += ch;
          process.stdout.write('*');
        }
      }
    });
  });
}

async function main() {
  const rl = createInterface({ input: process.stdin, output: process.stdout });

  console.log('\n  LAON VaultGuard — Setup\n');

  let lines = readEnvLines(ENV_PATH);

  console.log('Enter your API keys. Keys are stored in .env and never committed to Git.');
  console.log('Input is masked (***) for security.\n');
  console.log('Get keys at:');
  console.log('  DeepSeek:  https://platform.deepseek.com/api_keys');
  console.log('  Claude:    https://console.anthropic.com/');
  console.log('  OpenAI:    https://platform.openai.com/api-keys\n');

  const deepseekKey = await maskedInput('DEEPSEEK_API_KEY: ');
  if (deepseekKey) {
    lines = setKey(lines, 'DEEPSEEK_API_KEY', deepseekKey);
    console.log('  -> DeepSeek key saved');
  } else {
    console.log('  -> skipped');
  }

  const claudeKey = await maskedInput('CLAUDE_API_KEY: ');
  if (claudeKey) {
    lines = setKey(lines, 'CLAUDE_API_KEY', claudeKey);
    console.log('  -> Claude key saved');
  } else {
    console.log('  -> skipped');
  }

  const openaiKey = await maskedInput('OPENAI_API_KEY: ');
  if (openaiKey) {
    lines = setKey(lines, 'OPENAI_API_KEY', openaiKey);
    console.log('  -> OpenAI key saved');
  } else {
    console.log('  -> skipped');
  }

  // Auto-detect providers from keys
  const providers: string[] = [];
  if (deepseekKey) providers.push('deepseek');
  if (claudeKey) providers.push('claude');
  if (openaiKey) providers.push('openai');
  if (providers.length > 0) {
    lines = setKey(lines, 'LLM_PROVIDERS', providers.join(','));
    lines = setKey(lines, 'LLM_MODE', providers.length >= 2 ? 'parallel' : 'sequential');
  }

  writeEnv(lines);
  console.log(`\nConfig saved to .env (${providers.length} provider(s): ${providers.join(', ') || 'none'})`);
  console.log('Start: npm run dev\n');

  rl.close();
}

main().catch(console.error);
