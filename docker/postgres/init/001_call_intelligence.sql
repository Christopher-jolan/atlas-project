-- Atlas Call Intelligence schema
-- Stores per-call AI analysis and monthly aggregated reports

CREATE TABLE IF NOT EXISTS call_analyses (
    id              SERIAL PRIMARY KEY,
    call_id         VARCHAR(255) NOT NULL,
    analyzed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    department      VARCHAR(50),
    agent_id        VARCHAR(100),
    agent_name      VARCHAR(255),
    customer_phone  VARCHAR(50),
    customer_name   VARCHAR(255),
    call_date       TIMESTAMPTZ,
    call_direction  VARCHAR(20),
    call_duration_seconds INTEGER,
    audio_url       TEXT,
    transcript_text TEXT,
    analysis_json   JSONB NOT NULL,
    purchase_intent_score     INTEGER,
    satisfaction_final_score  INTEGER,
    agent_quality_score       INTEGER,
    ticket_priority           VARCHAR(20),
    needs_human_review        BOOLEAN DEFAULT FALSE,
    workflow_version          VARCHAR(20) DEFAULT '1.0.0',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (call_id)
);

CREATE INDEX IF NOT EXISTS idx_call_analyses_analyzed_at ON call_analyses (analyzed_at);
CREATE INDEX IF NOT EXISTS idx_call_analyses_agent_id ON call_analyses (agent_id);
CREATE INDEX IF NOT EXISTS idx_call_analyses_department ON call_analyses (department);
CREATE INDEX IF NOT EXISTS idx_call_analyses_call_date ON call_analyses (call_date);

CREATE TABLE IF NOT EXISTS monthly_reports (
    id              SERIAL PRIMARY KEY,
    report_month    DATE NOT NULL,
    department      VARCHAR(50) NOT NULL DEFAULT 'all',
    report_json     JSONB NOT NULL,
    total_calls     INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (report_month, department)
);

CREATE INDEX IF NOT EXISTS idx_monthly_reports_month ON monthly_reports (report_month);
