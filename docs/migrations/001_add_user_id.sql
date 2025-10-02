-- Migration: Add user_id column to all tables for multi-user support
-- Date: 2025-10-02
-- Description: Prepares database for future multi-user mode by adding user_id column
--              Currently defaults to '1' for single user, will be replaced with auth.uid() later

-- Add user_id to file_metadata table
ALTER TABLE file_metadata
ADD COLUMN IF NOT EXISTS user_id TEXT DEFAULT '1';

-- Create index for faster user queries
CREATE INDEX IF NOT EXISTS idx_file_metadata_user_id
ON file_metadata(user_id);

-- Add comment
COMMENT ON COLUMN file_metadata.user_id IS
'User identifier. Currently defaults to 1 for single user. Will be replaced with Supabase Auth user ID when multi-user mode is enabled.';

-- Future migration will:
-- 1. Enable Supabase Auth
-- 2. Update default: ALTER TABLE file_metadata ALTER COLUMN user_id SET DEFAULT auth.uid()
-- 3. Enable RLS: ALTER TABLE file_metadata ENABLE ROW LEVEL SECURITY
-- 4. Create policy: CREATE POLICY user_isolation ON file_metadata FOR ALL USING (user_id = auth.uid())
