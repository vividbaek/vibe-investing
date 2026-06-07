// setup.ts — LAON VaultGuard interactive setup (DeepSeek API key)
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

async function ask(rl: ReturnType<typeof createInterface>, question: string): Promise<string> {
  return new Promise(resolve => {
    rl.question(question, (answer: string) => {
      resolve(answer.trim());
    });
  });
}

async function main() {
  const rl = createInterface({ input: process.stdin, output: process.stdout });

  console.log('\n🛡  LAON VaultGuard — 초기 설정\n');

  let lines = readEnvLines(ENV_PATH);

  // DeepSeek API Key
  console.log('DeepSeek API 키를 입력하세요 (https://platform.deepseek.com/api_keys)');
  console.log('입력한 키는 .env 파일에 저장되며, GitHub에 커밋되지 않습니다.\n');

  const deepseekKey = await ask(rl, 'DEEPSEEK_API_KEY: ');

  if (deepseekKey) {
    lines = setKey(lines, 'DEEPSEEK_API_KEY', deepseekKey);
    lines = setKey(lines, 'LLM_PROVIDERS', 'deepseek');
    lines = setKey(lines, 'LLM_MODE', 'sequential');
    console.log('✅ DeepSeek API 키가 설정되었습니다.');
  } else {
    console.log('⚠️  키를 입력하지 않았습니다. 나중에 .env 파일에서 직접 설정하세요.');
  }

  writeEnv(lines);
  console.log(`\n설정이 .env 파일에 저장되었습니다.`);
  console.log(`서버 시작: npm run dev\n`);

  rl.close();
}

main().catch(console.error);
