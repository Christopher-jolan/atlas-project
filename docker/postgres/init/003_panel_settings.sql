-- Atlas Panel: Settings & Alert Rules
CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    threshold INTEGER NOT NULL DEFAULT 5,
    time_window_minutes INTEGER NOT NULL DEFAULT 60,
    enabled BOOLEAN DEFAULT TRUE,
    email_to VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS panel_settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO panel_settings (key, value) VALUES
    ('manager_email', ''),
    ('smtp_host', 'smtp.mail.yahoo.com'),
    ('smtp_port', '587'),
    ('smtp_user', ''),
    ('smtp_pass', ''),
    ('alert_cooldown_minutes', '60')
ON CONFLICT (key) DO NOTHING;

INSERT INTO alert_rules (name, rule_type, threshold, time_window_minutes, enabled) VALUES
    ('نارضایتی مکرر از پرسنل', 'staff_unsatisfied_count', 5, 60, true),
    ('تماس با اولویت فوری', 'urgent_ticket', 1, 0, true),
    ('افت رضایت مشتری', 'low_satisfaction', 40, 0, true),
    ('سرنخ داغ از دست رفته', 'hot_lead_no_followup', 3, 1440, true)
ON CONFLICT DO NOTHING;
