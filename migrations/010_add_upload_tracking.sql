-- Migration: Add upload batch tracking to leads table
-- This allows filtering leads by upload session and viewing upload history

-- Add upload tracking columns
ALTER TABLE leads
ADD COLUMN upload_batch_id UUID,
ADD COLUMN uploaded_at TIMESTAMPTZ;

-- Create index for fast filtering by upload batch
CREATE INDEX idx_leads_upload_batch ON leads(upload_batch_id);

-- Update existing leads to have a single batch (retroactive)
UPDATE leads
SET
  upload_batch_id = '00000000-0000-0000-0000-000000000001'::uuid,
  uploaded_at = created_at
WHERE upload_batch_id IS NULL;

-- Create VIEW for upload history statistics
CREATE OR REPLACE VIEW upload_history AS
SELECT
  upload_batch_id,
  MIN(uploaded_at) as uploaded_at,
  COUNT(*) as total_leads,
  COUNT(CASE WHEN created_at = uploaded_at THEN 1 END) as new_leads,
  COUNT(CASE WHEN created_at < uploaded_at THEN 1 END) as updated_leads,
  COUNT(DISTINCT email) as unique_emails,
  COUNT(CASE WHEN phone IS NOT NULL THEN 1 END) as leads_with_phone,
  COUNT(CASE WHEN linkedin_url IS NOT NULL THEN 1 END) as leads_with_linkedin
FROM leads
WHERE upload_batch_id IS NOT NULL
GROUP BY upload_batch_id
ORDER BY uploaded_at DESC;

-- Add comment
COMMENT ON VIEW upload_history IS 'Aggregated statistics for each CSV upload batch';
