#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const tsx = resolve(__dirname, '..', 'node_modules', '.bin', 'tsx');
const scriptName = process.argv[1].includes('setup') ? 'setup.ts' : 'cli.ts';
const script = resolve(__dirname, '..', 'src', scriptName);

const result = spawnSync(tsx, [script, ...process.argv.slice(2)], { stdio: 'inherit' });
process.exit(result.status ?? 0);
