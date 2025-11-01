-- ============================================================================
-- INSTANTLY RAW DATA - SQLITE SCHEMA
-- Created: 2025-11-01
-- Purpose: Store all raw data from Instantly API v2
-- Database: SQLite 3.38+
-- ============================================================================

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Enable JSON support
PRAGMA journal_mode = WAL;

-- ============================================================================
-- HELPER TRIGGERS
-- ============================================================================

-- Trigger function to update updated_at timestamp
-- Note: SQLite doesn't have trigger functions, we'll create triggers per table

-- ============================================================================
-- TABLE 1: CAMPAIGNS RAW
-- ============================================================================
-- Source: GET /api/v2/campaigns/analytics
-- Stores campaign-level analytics and metadata

CREATE TABLE IF NOT EXISTS instantly_campaigns_raw (
    -- Primary identification
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Instantly campaign ID (unique identifier from API)
    instantly_campaign_id TEXT UNIQUE NOT NULL,

    -- Campaign metadata (extracted for quick queries)
    campaign_name TEXT,
    campaign_status INTEGER,
    -- Status codes: 1=Active, 2=Paused, 3=Completed, -1=Unhealthy, -2=Bounce

    -- Campaign metrics (key performance indicators)
    leads_count INTEGER DEFAULT 0,
    contacted_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    bounced_count INTEGER DEFAULT 0,
    emails_sent_count INTEGER DEFAULT 0,
    total_opportunities INTEGER DEFAULT 0,
    total_opportunity_value REAL DEFAULT 0.0,

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json TEXT NOT NULL,

    -- Sync tracking
    synced_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_campaigns_name ON instantly_campaigns_raw(campaign_name);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON instantly_campaigns_raw(campaign_status);
CREATE INDEX IF NOT EXISTS idx_campaigns_synced ON instantly_campaigns_raw(synced_at DESC);

-- Trigger for updated_at
CREATE TRIGGER IF NOT EXISTS update_campaigns_timestamp
AFTER UPDATE ON instantly_campaigns_raw
BEGIN
    UPDATE instantly_campaigns_raw SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- TABLE 2: LEADS RAW
-- ============================================================================
-- Source: POST /api/v2/leads/list
-- Stores individual lead data from campaigns

CREATE TABLE IF NOT EXISTS instantly_leads_raw (
    -- Primary identification
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Instantly IDs
    instantly_lead_id TEXT NOT NULL,
    instantly_campaign_id TEXT,  -- Can be NULL for leads without campaign

    -- Main fields for quick queries (extracted from JSON)
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    company_name TEXT,

    -- Lead status from Instantly
    lead_status TEXT,
    -- Common values: 'active', 'completed', 'paused', 'bounced', 'replied'

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json TEXT NOT NULL,

    -- Sync tracking
    synced_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- Foreign key to campaigns
    FOREIGN KEY (instantly_campaign_id)
        REFERENCES instantly_campaigns_raw(instantly_campaign_id)
        ON DELETE SET NULL,

    -- UNIQUE: Lead ID must be unique (one lead can't be in multiple campaigns in Instantly)
    UNIQUE(instantly_lead_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_leads_email ON instantly_leads_raw(email);
CREATE INDEX IF NOT EXISTS idx_leads_campaign ON instantly_leads_raw(instantly_campaign_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON instantly_leads_raw(lead_status);
CREATE INDEX IF NOT EXISTS idx_leads_synced ON instantly_leads_raw(synced_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_name ON instantly_leads_raw(first_name, last_name);

-- Trigger for updated_at
CREATE TRIGGER IF NOT EXISTS update_leads_timestamp
AFTER UPDATE ON instantly_leads_raw
BEGIN
    UPDATE instantly_leads_raw SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- TABLE 3: STEPS RAW
-- ============================================================================
-- Source: GET /api/v2/campaigns/analytics/steps?campaign_id={id}
-- Stores step-by-step analytics for each campaign sequence

CREATE TABLE IF NOT EXISTS instantly_steps_raw (
    -- Primary identification
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Campaign relationship
    instantly_campaign_id TEXT NOT NULL,

    -- Step identification (extracted from JSON)
    step_number INTEGER,
    step_name TEXT,
    step_type TEXT,
    -- Common types: 'email', 'follow_up', 'delay', 'conditional'

    -- Step metrics (extracted for quick queries)
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json TEXT NOT NULL,

    -- Sync tracking
    synced_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- Foreign key to campaigns
    FOREIGN KEY (instantly_campaign_id)
        REFERENCES instantly_campaigns_raw(instantly_campaign_id)
        ON DELETE CASCADE,

    -- Unique constraint: one record per campaign+step combination
    UNIQUE(instantly_campaign_id, step_number)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_steps_campaign ON instantly_steps_raw(instantly_campaign_id);
CREATE INDEX IF NOT EXISTS idx_steps_number ON instantly_steps_raw(step_number);
CREATE INDEX IF NOT EXISTS idx_steps_synced ON instantly_steps_raw(synced_at DESC);

-- Trigger for updated_at
CREATE TRIGGER IF NOT EXISTS update_steps_timestamp
AFTER UPDATE ON instantly_steps_raw
BEGIN
    UPDATE instantly_steps_raw SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- TABLE 4: ACCOUNTS RAW
-- ============================================================================
-- Source: GET /api/v2/accounts
-- Stores email account information and warmup status

CREATE TABLE IF NOT EXISTS instantly_accounts_raw (
    -- Primary identification
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Account identification
    email TEXT UNIQUE NOT NULL,
    organization TEXT,

    -- Account status (extracted for quick queries)
    status INTEGER,
    -- Status codes: 1=Active, -1=Inactive
    warmup_status INTEGER,
    stat_warmup_score REAL,

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json TEXT NOT NULL,

    -- Sync tracking
    synced_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_accounts_status ON instantly_accounts_raw(status);
CREATE INDEX IF NOT EXISTS idx_accounts_warmup ON instantly_accounts_raw(warmup_status);
CREATE INDEX IF NOT EXISTS idx_accounts_synced ON instantly_accounts_raw(synced_at DESC);

-- Trigger for updated_at
CREATE TRIGGER IF NOT EXISTS update_accounts_timestamp
AFTER UPDATE ON instantly_accounts_raw
BEGIN
    UPDATE instantly_accounts_raw SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- TABLE 5: EMAILS RAW
-- ============================================================================
-- Source: GET /api/v2/emails?limit=100
-- Stores detailed email messages and interactions

CREATE TABLE IF NOT EXISTS instantly_emails_raw (
    -- Primary identification
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Email identification
    instantly_email_id TEXT UNIQUE,
    instantly_campaign_id TEXT,

    -- Email metadata (extracted for quick queries)
    recipient_email TEXT,
    subject TEXT,
    email_type TEXT,
    -- Types: 'sent', 'opened', 'replied', 'bounced', 'clicked'

    sent_at TEXT,
    opened_at TEXT,
    replied_at TEXT,

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json TEXT NOT NULL,

    -- Sync tracking
    synced_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- Foreign key to campaigns
    FOREIGN KEY (instantly_campaign_id)
        REFERENCES instantly_campaigns_raw(instantly_campaign_id)
        ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_emails_recipient ON instantly_emails_raw(recipient_email);
CREATE INDEX IF NOT EXISTS idx_emails_campaign ON instantly_emails_raw(instantly_campaign_id);
CREATE INDEX IF NOT EXISTS idx_emails_type ON instantly_emails_raw(email_type);
CREATE INDEX IF NOT EXISTS idx_emails_sent ON instantly_emails_raw(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_emails_synced ON instantly_emails_raw(synced_at DESC);

-- Trigger for updated_at
CREATE TRIGGER IF NOT EXISTS update_emails_timestamp
AFTER UPDATE ON instantly_emails_raw
BEGIN
    UPDATE instantly_emails_raw SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- TABLE 6: DAILY ANALYTICS RAW
-- ============================================================================
-- Source: GET /api/v2/campaigns/analytics/daily?start_date=X&end_date=Y
-- Stores day-by-day performance metrics

CREATE TABLE IF NOT EXISTS instantly_daily_analytics_raw (
    -- Primary identification
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Date identification
    date TEXT NOT NULL,

    -- Daily metrics (extracted for quick queries)
    sent INTEGER DEFAULT 0,
    opened INTEGER DEFAULT 0,
    unique_opened INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    unique_replies INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    unique_clicks INTEGER DEFAULT 0,

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json TEXT NOT NULL,

    -- Sync tracking
    synced_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    -- Unique constraint: one record per date
    UNIQUE(date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_daily_date ON instantly_daily_analytics_raw(date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_synced ON instantly_daily_analytics_raw(synced_at DESC);

-- Trigger for updated_at
CREATE TRIGGER IF NOT EXISTS update_daily_timestamp
AFTER UPDATE ON instantly_daily_analytics_raw
BEGIN
    UPDATE instantly_daily_analytics_raw SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- TABLE 7: OVERVIEW RAW
-- ============================================================================
-- Source: GET /api/v2/campaigns/analytics/overview
-- Stores account-wide overview analytics

CREATE TABLE IF NOT EXISTS instantly_overview_raw (
    -- Primary identification
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    -- Overview metrics (extracted for quick queries)
    total_campaigns INTEGER DEFAULT 0,
    total_leads INTEGER DEFAULT 0,
    total_emails_sent INTEGER DEFAULT 0,
    total_replies INTEGER DEFAULT 0,
    total_opportunities INTEGER DEFAULT 0,

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json TEXT NOT NULL,

    -- Sync tracking
    synced_at TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_overview_synced ON instantly_overview_raw(synced_at DESC);

-- Trigger for updated_at
CREATE TRIGGER IF NOT EXISTS update_overview_timestamp
AFTER UPDATE ON instantly_overview_raw
BEGIN
    UPDATE instantly_overview_raw SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Summary:
-- ✅ 7 tables created for complete Instantly API v2 coverage
-- ✅ All tables have raw_json preservation
-- ✅ Key fields extracted for fast queries
-- ✅ Proper indexes for performance
-- ✅ Foreign keys for data integrity
-- ✅ Triggers for automatic updated_at timestamps
-- ✅ Unique constraints to prevent duplicates

-- Tables:
-- 1. instantly_campaigns_raw      - Campaign analytics
-- 2. instantly_leads_raw           - Lead data
-- 3. instantly_steps_raw           - Step-by-step analytics
-- 4. instantly_accounts_raw        - Email accounts
-- 5. instantly_emails_raw          - Detailed emails
-- 6. instantly_daily_analytics_raw - Daily metrics
-- 7. instantly_overview_raw        - Account overview
