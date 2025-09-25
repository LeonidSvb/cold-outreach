import { NextRequest, NextResponse } from 'next/server'
import { readdir, stat } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

export async function GET() {
  try {
    const uploadsDir = '/tmp/uploads'

    if (!existsSync(uploadsDir)) {
      return NextResponse.json([])
    }

    const files = await readdir(uploadsDir)
    const fileList = []

    for (const filename of files) {
      if (filename.endsWith('.csv')) {
        const filePath = path.join(uploadsDir, filename)
        const fileStat = await stat(filePath)

        // Extract UUID from filename (before extension)
        const fileId = path.basename(filename, path.extname(filename))

        fileList.push({
          id: fileId,
          filename: filename,
          original_name: filename, // In real app, store original names
          upload_date: fileStat.mtime.toISOString(),
          rows: 0, // Would be stored in metadata
          columns: [], // Would be stored in metadata
          size: fileStat.size
        })
      }
    }

    // Sort by upload date (newest first)
    fileList.sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime())

    return NextResponse.json(fileList)

  } catch (error) {
    console.error('Error fetching uploaded files:', error)
    return NextResponse.json([])
  }
}