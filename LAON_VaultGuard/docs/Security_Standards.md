# Security Standards Mapping

> LAON VaultGuard detection categories mapped to CWE, OWASP Top 10, and KISA standards.

## OWASP Top 10 (2021) Mapping

| OWASP | Description | LAON VaultGuard Detection |
|---|---|---|
| A01:2021 | Broken Access Control | -- |
| A02:2021 | Cryptographic Failures | TLS misconfig, SSL off, insecure=true |
| A03:2021 | Injection | SQL injection patterns, raw queries |
| A04:2021 | Insecure Design | -- |
| A05:2021 | Security Misconfiguration | `rejectUnauthorized: false`, WAF disabled, TLSv1.0 |
| A06:2021 | Vulnerable Components | Outdated OpenSSL, PHP, MySQL, WordPress versions |
| A07:2021 | Auth Failures | Hardcoded passwords, DB credentials, tokens |
| A08:2021 | Software/Data Integrity | -- |
| A09:2021 | Logging/Monitoring | -- |
| A10:2021 | SSRF | -- |

## CWE Mapping

| CWE | Description | Detection Category |
|---|---|---|
| CWE-798 | Hardcoded Credentials | Secrets (cloud keys, API tokens, passwords) |
| CWE-89 | SQL Injection | SQL Injection |
| CWE-259 | Hardcoded Password | DB passwords in connection strings |
| CWE-327 | Broken Cryptography | TLSv1.0, SSLv3, MD5 |
| CWE-319 | Cleartext Transmission | `ssl off`, `verify false` |
| CWE-937 | OWASP Top 10 (2013) | A6 - Sensitive Data Exposure |
| CWE-1104 | Use of Unmaintained Software | Outdated PHP 5.x, Python 2.7, Apache 2.2 |
| CWE-200 | Information Exposure | DB connection strings in code |
| CWE-522 | Insufficiently Protected Credentials | `DB_PASSWORD` in plaintext |
| CWE-693 | Protection Mechanism Failure | WAF disabled, firewall off |

## KISA (Korea Internet & Security Agency)

| KISA Guideline | Detection |
|---|---|
| Secure Coding (SW Development Security) | SQL injection, hardcoded credentials |
| Cloud Security Certification (CSAP) | Cloud API key exposure (AWS, Azure, GCP, NCP, KT Cloud) |
| Personal Information Protection Act (PIPA) | DB connection strings with credentials |
| Critical Infrastructure Protection | Outdated TLS versions |

## NIST CSF Mapping

| Function | Category | Detection |
|---|---|---|
| Identify | Asset Management | Outdated software versions |
| Protect | Data Security | Secret detection |
| Detect | Anomalies & Events | Real-time scan alerts |
| Respond | Analysis | Categorized findings with remediation |
| Recover | Improvements | Acknowledge/false-positive feedback loop |
