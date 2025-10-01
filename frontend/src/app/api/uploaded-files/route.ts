import { NextResponse } from 'next/server'
import { getUploadedFiles } from '../../../lib/supabase'

export async function GET() {
  try {
    const files = await getUploadedFiles()

    // Transform to match frontend expectations
    const fileList = files.map(file => ({
      id: file.id,
      filename: file.filename,
      original_name: file.original_name,
      upload_date: file.upload_date,
      rows: file.total_rows,
      columns: Object.keys(file.column_types || {}),
      size: file.file_size,
      detected_types: file.detected_key_columns
    }))

    return NextResponse.json(fileList)

  } catch (error) {
    console.error('Error fetching uploaded files:', error)
    return NextResponse.json([])
  }
}