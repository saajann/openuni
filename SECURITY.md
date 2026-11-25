# Security Policy

The OpenUni team takes the security of our application, API services, and the data of students and universities seriously. We appreciate the responsible disclosure of any vulnerabilities found by security researchers, contributors, and users.

## Supported Versions

Security updates are actively applied to the latest release and the current `main` branch.

| Version / Branch | Supported          |
| ---------------- | ------------------ |
| `main`           | :white_check_mark: |
| Latest Release   | :white_check_mark: |
| Older releases   | :x:                |

We strongly recommend always running the latest version of OpenUni and keeping your Docker containers and dependencies up to date.

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues, discussions, or pull requests.**

If you believe you have discovered a vulnerability, please report it privately through one of the following methods:

1. **GitHub Security Advisory (Preferred):**  
   Open a private advisory via [GitHub Security Advisories](https://github.com/saajann/openuni/security/advisories/new). This enables private communication and collaborative remediation before public disclosure.

2. **Email:**  
   If you cannot use GitHub Security Advisories, email the maintainers directly at [sainisaaji@gmail.com](mailto:sainisaaji@gmail.com) with the subject line `[SECURITY] OpenUni Vulnerability Report`.

### What to Include in Your Report

To help us triage and resolve the issue quickly, please include:
- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- The affected component(s) (e.g., `apps/api`, `apps/web`, `packages/ingestion`, or environment configuration).
- Any proposed remediation or patches, if available.

## Response Expectations & Disclosure Timeline

- **Initial Acknowledgment:** You can expect an initial response acknowledging receipt within **48 hours**.
- **Assessment & Triage:** Within **5 business days**, we will confirm whether the issue is reproducible and share an estimated timeline for a fix.
- **Remediation & Patching:** A fix will be developed and tested privately.
- **Coordinated Disclosure:** Once a fix is released, we will coordinate public disclosure and credit you for the discovery (unless you prefer to remain anonymous).
