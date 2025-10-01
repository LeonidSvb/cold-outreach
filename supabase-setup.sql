-- Supabase Setup Script for CSV File Storage
-- Run this in your Supabase SQL Editor

-- Create file_metadata table
CREATE TABLE IF NOT EXISTS file_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_rows INTEGER NOT NULL DEFAULT 0,
    total_columns INTEGER NOT NULL DEFAULT 0,
    column_types JSONB NOT NULL DEFAULT '{}',
    detected_key_columns JSONB NOT NULL DEFAULT '{}',
    file_size INTEGER NOT NULL DEFAULT 0,
    storage_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS file_metadata_upload_date_idx ON file_metadata(upload_date DESC);
CREATE INDEX IF NOT EXISTS file_metadata_filename_idx ON file_metadata(filename);

-- Enable Row Level Security (RLS)
ALTER TABLE file_metadata ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust based on your auth needs)
CREATE POLICY "Allow all operations on file_metadata" ON file_metadata
    FOR ALL USING (true);

-- Create storage bucket for CSV files
INSERT INTO storage.buckets (id, name, public)
VALUES ('csv-files', 'csv-files', false)
ON CONFLICT (id) DO NOTHING;

-- Create storage policy for CSV bucket
CREATE POLICY "Allow all operations on csv-files bucket" ON storage.objects
    FOR ALL USING (bucket_id = 'csv-files');

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_file_metadata_updated_at
    BEFORE UPDATE ON file_metadata
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Verification queries (run these to check setup)
-- SELECT COUNT(*) FROM file_metadata;
-- SELECT * FROM storage.buckets WHERE name = 'csv-files';
-- SELECT * FROM storage.policies WHERE bucket_id = 'csv-files';