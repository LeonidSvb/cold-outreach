import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY!

// Client for frontend (with anon key)
export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Admin client for backend (with service role key)
export const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})

// Database types
export interface FileMetadata {
  id: string
  filename: string
  original_name: string
  upload_date: string
  total_rows: number
  total_columns: number
  column_types: Record<string, string>
  detected_key_columns: Record<string, string>
  file_size: number
  storage_path: string
}

// Storage bucket name
export const CSV_BUCKET = 'csv-files'

// File upload utility
export async function uploadCSVToSupabase(
  file: File,
  fileId: string,
  metadata: Omit<FileMetadata, 'id' | 'upload_date' | 'storage_path'>
): Promise<{ success: boolean; error?: string; data?: FileMetadata }> {
  try {
    const fileName = `${fileId}.csv`
    const storagePath = `uploads/${fileName}`

    // Upload file to storage
    const { error: uploadError } = await supabaseAdmin.storage
      .from(CSV_BUCKET)
      .upload(storagePath, file, {
        contentType: 'text/csv',
        upsert: false
      })

    if (uploadError) {
      throw new Error(`Storage upload failed: ${uploadError.message}`)
    }

    // Save metadata to database
    const fileMetadata: FileMetadata = {
      ...metadata,
      id: fileId,
      upload_date: new Date().toISOString(),
      storage_path: storagePath
    }

    const { error: dbError } = await supabaseAdmin
      .from('file_metadata')
      .insert(fileMetadata)

    if (dbError) {
      // Cleanup storage if database insert fails
      await supabaseAdmin.storage.from(CSV_BUCKET).remove([storagePath])
      throw new Error(`Database insert failed: ${dbError.message}`)
    }

    return { success: true, data: fileMetadata }

  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

// Get file list utility
export async function getUploadedFiles(): Promise<FileMetadata[]> {
  const { data, error } = await supabaseAdmin
    .from('file_metadata')
    .select('*')
    .order('upload_date', { ascending: false })

  if (error) {
    console.error('Error fetching files:', error)
    return []
  }

  return data || []
}

// Get file content utility
export async function getFileContent(fileId: string): Promise<{ content?: string; error?: string }> {
  try {
    // Get file metadata
    const { data: metadata, error: metaError } = await supabaseAdmin
      .from('file_metadata')
      .select('storage_path')
      .eq('id', fileId)
      .single()

    if (metaError || !metadata) {
      return { error: 'File not found' }
    }

    // Download file from storage
    const { data: fileData, error: downloadError } = await supabaseAdmin.storage
      .from(CSV_BUCKET)
      .download(metadata.storage_path)

    if (downloadError) {
      return { error: `Download failed: ${downloadError.message}` }
    }

    const content = await fileData.text()
    return { content }

  } catch (error) {
    return {
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

// Delete file utility
export async function deleteFile(fileId: string): Promise<{ success: boolean; error?: string }> {
  try {
    // Get file metadata
    const { data: metadata, error: metaError } = await supabaseAdmin
      .from('file_metadata')
      .select('storage_path')
      .eq('id', fileId)
      .single()

    if (metaError || !metadata) {
      return { success: false, error: 'File not found' }
    }

    // Delete from storage
    const { error: storageError } = await supabaseAdmin.storage
      .from(CSV_BUCKET)
      .remove([metadata.storage_path])

    if (storageError) {
      console.error('Storage deletion error:', storageError)
    }

    // Delete from database
    const { error: dbError } = await supabaseAdmin
      .from('file_metadata')
      .delete()
      .eq('id', fileId)

    if (dbError) {
      return { success: false, error: `Database deletion failed: ${dbError.message}` }
    }

    return { success: true }

  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}