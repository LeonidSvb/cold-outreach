import { NextRequest, NextResponse } from 'next/server'
import { writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'
import { v4 as uuidv4 } from 'uuid'
import { spawn } from 'child_process'

export async function POST(request: NextRequest) {
  try {
    const data = await request.formData()
    const file: File | null = data.get('file') as unknown as File

    if (!file) {
      return NextResponse.json({ error: 'No file uploaded' }, { status: 400 })
    }

    // Create uploads directory in /tmp for Vercel
    const uploadsDir = '/tmp/uploads'
    if (!existsSync(uploadsDir)) {
      await mkdir(uploadsDir, { recursive: true })
    }

    // Generate unique file ID and save file
    const fileId = uuidv4()
    const fileExtension = path.extname(file.name)
    const fileName = `${fileId}${fileExtension}`
    const filePath = path.join(uploadsDir, fileName)

    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(filePath, buffer)

    // Call Python CSV transformer API integration for analysis
    const analysisResult = await callPythonModule('analyze_csv_structure', {
      file_content: buffer.toString('base64'),
      filename: file.name
    })

    if (analysisResult.error) {
      return NextResponse.json({ error: analysisResult.error }, { status: 500 })
    }

    // Store file metadata for later use
    const fileMetadata = {
      id: fileId,
      filename: fileName,
      original_name: file.name,
      upload_date: new Date().toISOString(),
      analysis: analysisResult,
      path: filePath
    }

    // In production, you'd store this in a database
    // For now, we rely on the file system

    return NextResponse.json({
      file_id: fileId,
      analysis: {
        rows: analysisResult.total_rows,
        columns: analysisResult.columns,
        column_types: analysisResult.column_types,
        detected_types: analysisResult.detected_key_columns
      }
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