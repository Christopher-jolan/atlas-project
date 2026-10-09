---
kind: external_dependency
name: Yahoo SMTP — outbound email delivery for manager notifications
slug: yahoo-smtp
category: external_dependency
category_hints:
    - vendor_identity
    - auth_protocol
scope:
    - '**'
---

A lightweight Python HTTP server (`mailer.py`) exposes `/send` and `/` endpoints on port 8765. It sends emails via Yahoo SMTP (`smtp.mail.yahoo.com:587`) using STARTTLS and username/password authentication provided through `SMTP_USER` / `SMTP_PASS` environment variables. Default recipients come from `ATLAS_MANAGER_EMAIL`. This is called by n8n workflows to deliver call-analysis tickets and monthly reports to the manager. Credentials must be supplied at runtime; without `SMTP_PASS` the service returns an error instead of sending.