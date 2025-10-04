import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8003'

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/csv/history`, {
      cache: 'no-store'
    })

    const result = await response.json()

    if (!response.ok) {
      return NextResponse.json(result, { status: response.status })
    }

    return NextResponse.json(result)

  } catch (error) {
    console.error('Upload history proxy error:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to fetch upload history' },
      { status: 500 }
    )
  }
}
