-- Migration 003: CSV Imports Raw Layer
-- Created: 2025-01-19
-- Purpose: Preserve original CSV uploads for reprocessing and audit trail
-- Dependencies: 001_users_table.sql

-- ============================================================================
-- TABLE: csv_imports_raw
-- ============================================================================
-- Stores complete original CSV data as JSONB
-- Links leads back to their source file
-- Enables reprocessing if schema changes

CREATE TABLE IF NOT EXISTS csv_imports_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- File metadata
    file_name TEXT NOT NULL,
    file_size_bytes BIGINT,
    uploaded_by UUID REFERENCES users(id),

    -- CSV content
    raw_data JSONB NOT NULL,  -- Full CSV as JSON array: [{ first_name: "...", email: "..." }, ...]
    total_rows INTEGER NOT NULL DEFAULT 0,

    -- Processing status
    import_status TEXT NOT NULL DEFAULT 'uploaded',
    -- Values: uploaded, processing, completed, failed
    processed_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    error_log JSONB,  -- [{ row: 5, error: "Invalid email" }, ...]

    -- Timestamps
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Fast lookup by status for processing queue
CREATE INDEX idx_csv_imports_status ON csv_imports_raw(import_status);

-- Recent uploads first
CREATE INDEX idx_csv_imports_uploaded_desc ON csv_imports_raw(uploaded_at DESC);

-- Query by uploader (when multi-user enabled)
CREATE INDEX idx_csv_imports_user ON csv_imports_raw(uploaded_by);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE csv_imports_raw ENABLE ROW LEVEL SECURITY;

-- Users can see their own uploads
CREATE POLICY csv_imports_select_own ON csv_imports_raw
    FOR SELECT
    USING (uploaded_by = auth.uid());

-- Users can insert their own uploads
CREATE POLICY csv_imports_insert_own ON csv_imports_raw
    FOR INSERT
    WITH CHECK (uploaded_by = auth.uid());

-- Users can update their own uploads
CREATE POLICY csv_imports_update_own ON csv_imports_raw
    FOR UPDATE
    USING (uploaded_by = auth.uid());

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE csv_imports_raw IS 'Preserves original CSV uploads for audit trail and reprocessing';
COMMENT ON COLUMN csv_imports_raw.raw_data IS 'Full CSV content as JSONB array - never modified';
COMMENT ON COLUMN csv_imports_raw.import_status IS 'Processing status: uploaded, processing, completed, failed';
COMMENT ON COLUMN csv_imports_raw.error_log IS 'JSONB array of processing errors with row numbers';

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================

-- After running this migration, verify with:
-- SELECT id, file_name, total_rows, import_status, uploaded_at
-- FROM csv_imports_raw
-- ORDER BY uploaded_at DESC;
