import express from 'express';
import cors from 'cors';
import path from 'path';
import dotenv from 'dotenv';
import { readFileSync, existsSync } from 'fs';
import apiRoutes from './routes/api';

// Load .env file if it exists
const envPath = path.join(__dirname, '..', '.env');
if (existsSync(envPath)) {
  dotenv.config({ path: envPath });
} else {
  dotenv.config(); // fallback to default .env resolution
}

const app = express();
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '..', 'public')));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, '..', 'views'));

// API routes
app.use('/api', apiRoutes);

// Dashboard page
app.get('/', (_req, res) => {
  res.render('dashboard', {
    title: 'AI Supercycle Investment Quant Strategy',
    version: '2.0.0',
  });
});

// Runtime config: get/set API keys
let runtimeApiKey: string | null = null;

app.get('/api/config', (_req, res) => {
  res.json({
    hasClaudeApiKey: !!process.env.CLAUDE_API_KEY,
    hasDeepSeekApiKey: !!process.env.DEEPSEEK_API_KEY,
    hasRuntimeApiKey: !!runtimeApiKey,
    envFileExists: existsSync(path.join(__dirname, '..', '.env')),
    availableProviders: ['claude', 'deepseek', 'rule-based'],
  });
});

app.post('/api/config', (req, res) => {
  const { apiKey } = req.body || {};
  if (apiKey) {
    runtimeApiKey = apiKey;
    res.json({ success: true, message: 'API key set for this session. It will be cleared on server restart.' });
  } else {
    res.json({ success: true, message: 'API key cleared.' });
  }
});

// Start server
app.listen(PORT, () => {
  const hasClaude = !!process.env.CLAUDE_API_KEY;
  const hasDeepseek = !!process.env.DEEPSEEK_API_KEY;
  const hasEnvFile = existsSync(path.join(__dirname, '..', '.env'));

  console.log(`\n========================================`);
  console.log(`  AI Supercycle Quant Dashboard`);
  console.log(`  http://localhost:${PORT}`);
  console.log(`========================================`);
  console.log(`  API Base: http://localhost:${PORT}/api`);
  console.log(``);
  console.log(`  LLM Providers:`);
  console.log(`    - Rule-Based Engine: Always available (no key needed)`);
  console.log(`    - Claude:    ${hasClaude ? '✓ API key loaded from .env' : '✗ Set CLAUDE_API_KEY in .env'}`);
  console.log(`    - DeepSeek:  ${hasDeepseek ? '✓ API key loaded from .env' : '✗ Set DEEPSEEK_API_KEY in .env'}`);
  console.log(``);
  console.log(`  To add an API key:`);
  console.log(`    Option 1 (persistent):`);
  console.log(`      cp .env.example .env`);
  console.log(`      # Edit .env and add your key:`);
  console.log(`      DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx`);
  console.log(`      CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxx`);
  console.log(``);
  console.log(`    Option 2 (terminal, this session only):`);
  console.log(`      DEEPSEEK_API_KEY=sk-xxx npm run dev`);
  console.log(``);
  console.log(`    Option 3 (dashboard):`);
  console.log(`      Enter key in the API Key input field on the dashboard.`);
  console.log(``);
  if (!hasEnvFile) {
    console.log(`  ℹ  No .env file found. Run: cp .env.example .env`);
  }
  console.log(`========================================\n`);
});

export default app;
