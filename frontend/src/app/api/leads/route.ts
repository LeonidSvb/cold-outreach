import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8003'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const limit = searchParams.get('limit') || '100'
    const uploadBatchId = searchParams.get('upload_batch_id')

    let url = `${BACKEND_URL}/api/csv/leads?limit=${limit}`
    if (uploadBatchId) {
      url += `&upload_batch_id=${uploadBatchId}`
    }

    const response = await fetch(url, {
      cache: 'no-store'
    })

    const result = await response.json()

    if (!response.ok) {
      return NextResponse.json(result, { status: response.status })
    }

    return NextResponse.json(result)

  } catch (error) {
    console.error('Leads API proxy error:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to fetch leads' },
      { status: 500 }
    )
  }
}
