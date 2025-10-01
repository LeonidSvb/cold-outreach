import { NextRequest, NextResponse } from 'next/server'
import { getFileContent } from '../../../../../lib/supabase'

export async function GET(
  request: NextRequest,
  { params }: { params: { fileId: string } }
) {
  try {
    const { fileId } = params

    // Get file content from Supabase
    const result = await getFileContent(fileId)

    if (result.error || !result.content) {
      return NextResponse.json({ error: result.error || 'File not found' }, { status: 404 })
    }

    // Read and parse CSV
    const content = result.content
    const lines = content.split('\n').filter(line => line.trim())

    if (lines.length === 0) {
      return NextResponse.json({ error: 'Empty file' }, { status: 400 })
    }

    // Parse CSV (basic parsing - in production use a proper CSV parser)
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''))
    const rows = lines.slice(1, Math.min(16, lines.length)).map(line => {
      const values = line.split(',').map(v => v.trim().replace(/"/g, ''))
      const row: Record<string, string> = {}
      headers.forEach((header, index) => {
        row[header] = values[index] || ''
      })
      return row
    })

    // Detect column types
    const columnTypes: Record<string, string> = {}
    headers.forEach(header => {
      const lowerHeader = header.toLowerCase()
      if (lowerHeader.includes('company') || lowerHeader.includes('business')) {
        columnTypes[header] = 'company'
      } else if (lowerHeader.includes('website') || lowerHeader.includes('url')) {
        columnTypes[header] = 'website'
      } else if (lowerHeader.includes('email')) {
        columnTypes[header] = 'email'
      } else if (lowerHeader.includes('phone') || lowerHeader.includes('tel')) {
        columnTypes[header] = 'phone'
      } else if (lowerHeader.includes('name') && !lowerHeader.includes('company')) {
        columnTypes[header] = 'name'
      } else if (lowerHeader.includes('title') || lowerHeader.includes('position')) {
        columnTypes[header] = 'title'
      } else if (lowerHeader.includes('city') || lowerHeader.includes('location')) {
        columnTypes[header] = 'location'
      } else {
        columnTypes[header] = 'text'
      }
    })

    return NextResponse.json({
      columns: headers,
      column_types: columnTypes,
      rows: rows,
      total_rows: lines.length - 1,
      preview_rows: rows.length
    })

  } catch (error) {
    console.error('Preview error:', error)
    return NextResponse.json({ error: 'Failed to generate preview' }, { status: 500 })
  }
}