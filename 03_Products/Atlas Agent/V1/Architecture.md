\# معماری محصول | Product Architecture



\## هدف | Goal



ایجاد یک Agent هوشمند که بتواند سوالات کاربران را از روی مستندات شرکت پاسخ دهد و در صورت نیاز تیکت ایجاد کند.



\---



\## جریان داده | Data Flow



User

&#x20;  │

&#x20;  ▼

Webhook

&#x20;  │

&#x20;  ▼

Validation

&#x20;  │

&#x20;  ▼

Database (PostgreSQL)

&#x20;  │

&#x20;  ▼

AI Model

&#x20;  │

&#x20;  ▼

Knowledge Base (PDF / DOCX / TXT)

&#x20;  │

&#x20;  ▼

Response

&#x20;  │

&#x20;  ▼

Telegram / Web / CRM



\---



\## سرویس‌ها



\- n8n

\- PostgreSQL

\- Qdrant (Phase 2)

\- Redis (Phase 2)

\- OpenRouter (Phase 2)



\---



\## وضعیت



🟢 Designing

