// db.ts — unified storage facade (JSON file or SQLite based on STORAGE_ENGINE)
// All exported functions have identical signatures regardless of backend.

import { config } from './config.js';

const engine = config.db.storageEngine;

let backend: typeof import('./db-sqlite.js');

if (engine === 'sqlite') {
  // lazy import so JSON users don't need better-sqlite3
  backend = await import('./db-sqlite.js');
} else {
  backend = await import('./db-json.js');
}

// ── re-export entire API ──
export const {
  DATA_DIR,
  listRepos,
  getRepo,
  addRepo,
  removeRepo,
  updateRepoLastScan,
  listFindings,
  getFinding,
  saveFindings,
  acknowledgeFinding,
  unacknowledgeFinding,
  addFindingComment,
  countOpenFindings,
  saveScanRun,
  getScanRun,
  getLatestScan,
  getScanCount,
  getScanHistory,
  logAudit,
  rotateLogs,
  getAlertConfig,
  updateAlertConfig,
  readJson,
  writeJson,
} = backend;
