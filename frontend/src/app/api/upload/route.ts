import { NextRequest, NextResponse } from 'next/server'
import { v4 as uuidv4 } from 'uuid'
import { spawn } from 'child_process'
import path from 'path'
import { uploadCSVToSupabase } from '../../../lib/supabase'

export async function POST(request: NextRequest) {
  try {
    const data = await request.formData()
    const file: File | null = data.get('file') as unknown as File

    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 })
    }

    // Generate unique file ID
    const fileId = uuidv4()

    // Call Python CSV transformer API integration for analysis
    const buffer = Buffer.from(await file.arrayBuffer())
    const analysisResult = await callPythonModule('analyze_csv_structure', {
      file_content: buffer.toString('base64'),
      filename: file.name
    })

    if (analysisResult.error) {
      return NextResponse.json({ error: analysisResult.error }, { status: 500 })
    }

    // Upload to Supabase Storage and save metadata
    const uploadResult = await uploadCSVToSupabase(file, fileId, {
      filename: `${fileId}.csv`,
      original_name: file.name,
      total_rows: analysisResult.total_rows || 0,
      total_columns: analysisResult.columns?.length || 0,
      column_types: analysisResult.column_types || {},
      detected_key_columns: analysisResult.detected_key_columns || {},
      file_size: file.size
    })

    if (!uploadResult.success) {
      return NextResponse.json({ error: uploadResult.error }, { status: 500 })
    }

    return NextResponse.json({
      success: true,
      file_id: fileId,
      analysis: {
        rows: analysisResult.total_rows,
        columns: analysisResult.columns,
        column_types: analysisResult.column_types,
        detected_types: analysisResult.detected_key_columns
      },
      metadata: uploadResult.data
    })

  } catch (error) {
    console.error('Upload error:', error)
    return NextResponse.json({ error: 'Upload failed' }, { status: 500 })
  }
}

async function callPythonModule(method: string, args: any): Promise<any> {
  return new Promise((resolve, reject) => {
    // Path to the CSV transformer API integration
    const modulePath = path.join(process.cwd(), '..', 'modules', 'csv_transformer', 'api_integration.py')
    const moduleDir = path.dirname(modulePath)

    const python = spawn('py', [
      '-c',
      `
import sys
import json
sys.path.append(r'${moduleDir}')
sys.path.append(r'${path.join(moduleDir, '..')}')
from api_integration import csv_transformer_api
import base64

try:
    args = json.loads(r'''${JSON.stringify(args)}''')
    if 'file_content' in args:
        args['file_content'] = base64.b64decode(args['file_content'])

    result = getattr(csv_transformer_api, '${method}')(**args)
    print(json.dumps(result, default=str))
except Exception as e:
    print(json.dumps({"error": str(e)}))
`
    ], {
      cwd: moduleDir
    })

    let output = ''
    let error = ''

    python.stdout.on('data', (data) => {
      output += data.toString()
    })

    python.stderr.on('data', (data) => {
      error += data.toString()
    })

    python.on('close', (code) => {
      if (code !== 0 && !output) {
        reject(new Error(`Python script failed: ${error}`))
      } else {
        try {
          // Clean the output to get only JSON
          const lines = output.split('\n')
          const jsonLine = lines.find(line => line.trim().startsWith('{'))
          if (jsonLine) {
            resolve(JSON.parse(jsonLine))
          } else {
            resolve(JSON.parse(output))
          }
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${output}\nError: ${error}`))
        }
      }
    })
  })
}