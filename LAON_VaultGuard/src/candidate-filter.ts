// candidate-filter.ts — 1st pass: git grep keyword filter before LLM

import { simpleGit } from 'simple-git';
import type { Candidate } from './types.js';

const SUSPECT_PATTERNS = [
  // Cloud keys
  'AKIA',
  'ASIA',
  'AIza',
  '-----BEGIN',
  'client_secret',
  'AccountKey=',
  'aws_secret',
  'x-ncp',
  'ncloud',
  'ktcloud',
  'ucloudbiz',
  'api_key',
  'api-key',
  'secret_key',
  'secret-key',
  'NCP_ACCESS_KEY',
  'NCP_SECRET_KEY',
  'x-ncp-apigw-api-key',
  'x-ncp-iam-access-key',
  'OS_USERNAME',
  'OS_PASSWORD',
  'DefaultEndpointsProtocol',
  'service_account',
  'private_key_id',
  'ghp_',
  'gho_',
  'ghs_',
  'github_pat_',
  'xox[baprs]-',
  'sk-',
  'Bearer',
  'eyJ',
  'passwor?d\\s*=\\s*[\'"]',
  'token\\s*=\\s*[\'"]',

  // SQL injection
  'SELECT.*FROM.*WHERE.*=.*\\$',
  'INSERT\\s+INTO.*VALUES.*\\$',
  'execute\\s*\\(\\s*[\'"].*\\+',
  '\\.query\\s*\\(\\s*[\'"].*\\+',
  'PreparedStatement',
  'createQuery\\s*\\(\\s*[\'"].*\\+',
  'rawQuery',
  'db\\.execute\\s*\\(\\s*`.*\\$\\{',
  'sql\\.format',

  // DB connection exposure
  'jdbc:',
  'mongodb://',
  'mongodb\\+srv://',
  'redis://',
  'mysql://',
  'postgresql://',
  'postgres://',
  'sqlite://',
  'DB_CONNECTION',
  'DATABASE_URL',
  'DB_HOST.*=.*[\'"]\\d',
  'DB_PASSWORD\\s*=\\s*[\'"]',
  'DB_USER\\s*=\\s*[\'"].*[\'"]',
  'connectionString',

  // Outdated/ vulnerable versions
  'OpenSSL\\s+[01]\\.',
  'openssl-1\\.0',
  'TLSv1[^.]',
  'SSLv[23]',
  'apache2\\.2',
  'nginx/1\\.[0-9]\\.',
  'php[ -]5\\.',
  'php[ -]7\\.[0-3]',
  'python[ -]2\\.7',
  'python[ -]3\\.[0-5]',
  'node[ -]1[0-5]\\.',
  'mysql[ -]5\\.[0-6]',
  'postgres[ -]9\\.',
  'postgres[ -]1[0-1]\\.',
  'redis[ -][2-5]\\.',
  'mongodb[ -][2-4]\\.',
  'Image\\s+FROM\\s+.*:\\d+\\.\\d+[^-]',
  'wordpress[ -][1-5]\\.',
  'drupal[ -][7-8]\\.',
  'joomla[ -][1-3]\\.',
  'WAF.*disabled',
  'WAF.*bypass',
  'firewall.*off',
  'ssl\\s+off',
  'verify\\s+false',
  'insecure\\s*=\\s*true',
  'allowInsecure',
  'rejectUnauthorized.*false',
  'NODE_TLS_REJECT_UNAUTHORIZED\\s*=\\s*0',

  // Hardcoded credentials in DB context
  'mysql_connect\\s*\\(\\s*[\'"].*[\'"].*[\'"].*[\'"]',
  'pg_connect\\s*\\(\\s*[\'"].*[\'"]',
  'mongoClient\\.connect\\s*\\(\\s*[\'"]',
  'createConnection\\s*\\(\\s*\\{[^}]*password',
];

export function buildGrepPattern(): string {
  return SUSPECT_PATTERNS.join('|');
}

export async function extractCandidates(repoPath: string): Promise<Candidate[]> {
  const git = simpleGit(repoPath);
  const candidates: Candidate[] = [];
  const pattern = buildGrepPattern();

  try {
    // git grep with extended regex, line numbers, across all tracked files
    const result = await git.raw([
      'grep', '-nIE',
      pattern,
      '--', // end of options
    ]);
    if (!result.trim()) return candidates;

    for (const line of result.trim().split('\n')) {
      // format: filepath:linenum:content
      const match = line.match(/^(.+?):(\d+):(.*)$/);
      if (match) {
        const [, filePath, lineNum, content] = match;
        // skip obvious test fixtures and docs
        if (
          content.includes('example') ||
          content.includes('xxxx') ||
          content.includes('TODO') ||
          content.includes('placeholder')
        ) {
          // still include but mark separately — handled by LLM
        }
        candidates.push({
          filePath,
          lineNumber: parseInt(lineNum, 10),
          snippet: content.trim().slice(0, 200), // cap snippet length
          matchedPattern: pattern,
        });
      }
    }
  } catch (err) {
    // git grep returns exit code 1 when no matches — not an error
    if (err instanceof Error && !(err as Error & { code: number }).code) {
      throw err;
    }
  }

  return candidates;
}

// ── Shannon Entropy (pre-filter) ──

export function calculateEntropy(str: string): number {
  const len = str.length;
  if (len === 0) return 0;
  const freq: Record<string, number> = {};
  for (const ch of str) freq[ch] = (freq[ch] || 0) + 1;
  let entropy = 0;
  for (const count of Object.values(freq)) {
    const p = count / len;
    entropy -= p * Math.log2(p);
  }
  return entropy;
}

export function isHighEntropy(snippet: string, threshold = 3.5): boolean {
  // Extract the "value" part after =, :, or whitespace
  const valueMatch = snippet.match(/[=:]\s*(\S{8,})/);
  const value = valueMatch?.[1] || snippet;
  return calculateEntropy(value) >= threshold;
}

// ── Context Risk Classification ──

const LOW_RISK_FILES = [
  /\.env\.example$/,
  /\.env\.sample$/,
  /\.env\.template$/,
  /README/i,
  /\.md$/,
  /LICENSE/,
  /CHANGELOG/,
  /CONTRIBUTING/,
  /\.txt$/,
  /test/i,
  /spec/i,
  /mock/i,
  /fixture/i,
  /example/i,
];

export function classifyContextRisk(filePath: string): 'high' | 'medium' | 'low' {
  if (LOW_RISK_FILES.some(p => p.test(filePath))) return 'low';
  if (filePath.includes('config') || filePath.includes('env') || filePath.includes('secret') || filePath.includes('credential')) return 'high';
  return 'medium';
}
