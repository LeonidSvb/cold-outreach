import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

const OUTPUT_DIR = path.join(process.cwd(), '..', 'data', 'processed')

export async function GET(
  request: NextRequest,
  { params }: { params: { fileId: string } }
) {
  try {
    const fileId = params.fileId
    const outputFileName = `${fileId}_output.csv`
    const filePath = path.join(OUTPUT_DIR, outputFileName)

    if (!existsSync(filePath)) {
      return NextResponse.json(
        { success: false, error: 'File not found' },
        { status: 404 }
      )
    }

    const fileBuffer = await readFile(filePath)

    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="processed_${fileId}.csv"`,
      },
    })

  } catch (error) {
    console.error('Download error:', error)
    return NextResponse.json(
      { success: false, error: 'Download failed' },
      { status: 500 }
    )
  }
}
