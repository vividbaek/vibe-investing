# CI/CD Integration Guide

> Run LAON VaultGuard in GitHub Actions or GitLab CI pipelines.

## GitHub Actions

```yaml
# .github/workflows/laon-scan.yml
name: LAON VaultGuard Security Scan
on:
  push:
    branches: [main, dev]
  schedule:
    - cron: '0 6 * * *'   # daily 6am

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 50

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install LAON VaultGuard
        run: |
          cd LAON_VaultGuard
          npm install

      - name: Run Security Scan
        run: |
          cd LAON_VaultGuard
          npx laon-vaultguard scan $GITHUB_WORKSPACE
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}

      - name: Upload Findings
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: scan-findings
          path: LAON_VaultGuard/data/findings.json
```

## GitLab CI

```yaml
# .gitlab-ci.yml
laon-scan:
  image: node:20
  script:
    - cd LAON_VaultGuard && npm install
    - npx laon-vaultguard scan $CI_PROJECT_DIR
  variables:
    DEEPSEEK_API_KEY: $DEEPSEEK_API_KEY
  artifacts:
    when: on_failure
    paths:
      - LAON_VaultGuard/data/findings.json
```

## Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/sh
cd LAON_VaultGuard
npx laon-vaultguard scan "$(git rev-parse --show-toplevel)" --no-llm
if [ $? -ne 0 ]; then
  echo "Security scan failed. Review findings before committing."
  exit 1
fi
```

## Recommended Multi-Gate Defense

```
Gate 1: gitleaks (pre-commit, regex, milliseconds)
Gate 2: LAON VaultGuard (periodic CI, LLM context, 60s)
Gate 3: TruffleHog (CI, credential verification)
Gate 4: GitHub Secret Scanning (post-push, platform)
```
