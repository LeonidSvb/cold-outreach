import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { v4 as uuidv4 } from 'uuid'
import { spawn } from 'child_process'
import path from 'path'

export async function POST(request: NextRequest) {
  try {
    const data = await request.formData()
    const scriptName = data.get('script_name') as string
    const config = JSON.parse(data.get('config') as string)
    const file = data.get('file') as File | null

    if (!scriptName) {
      return NextResponse.json({ error: 'Script name required' }, { status: 400 })
    }

    const jobId = uuidv4()

    // Handle CSV Column Transformer
    if (scriptName === 'csv_column_transformer') {
      if (!file) {
        return NextResponse.json({ error: 'CSV file required for transformation' }, { status: 400 })
      }

      try {
        // Convert file to buffer
        const bytes = await file.arrayBuffer()
        const buffer = Buffer.from(bytes)

        // Call Python CSV transformer module
        const transformResult = await callPythonModule('transform_csv_column', {
          file_content: buffer.toString('base64'),
          web_config: config
        })

        if (transformResult.error) {
          return NextResponse.json({
            job_id: jobId,
            status: 'failed',
            error: transformResult.error
          }, { status: 500 })
        }

        return NextResponse.json({
          job_id: jobId,
          status: 'completed',
          message: 'CSV transformation completed successfully',
          result: transformResult
        })

      } catch (error) {
        return NextResponse.json({
          job_id: jobId,
          status: 'failed',
          error: `Transformation failed: ${error instanceof Error ? error.message : String(error)}`
        }, { status: 500 })
      }
    }

    // Handle OpenAI Mass Processor
    if (scriptName === 'openai_mass_processor') {
      // This would be implemented similarly with its own API integration
      return NextResponse.json({
        job_id: jobId,
        status: 'started',
        message: 'OpenAI mass processing started',
        estimated_time: '5-10 minutes'
      })
    }

    return NextResponse.json({
      job_id: jobId,
      status: 'started',
      message: `Script ${scriptName} started successfully`
    })

  } catch (error) {
    console.error('Script execution error:', error)
    return NextResponse.json({ error: 'Failed to start script' }, { status: 500 })
  }
}

async function callPythonModule(method: string, args: any): Promise<any> {
  return new Promise((resolve, reject) => {
    const modulePath = path.join(process.cwd(), '..', 'modules', 'csv_transformer', 'api_integration.py')

    const python = spawn('python', [
      '-c',
      `
import sys
import json
sys.path.append('${path.dirname(modulePath)}')
from api_integration import csv_transformer_api
import base64

try:
    args = json.loads('${JSON.stringify(args)}')
    if 'file_content' in args:
        args['file_content'] = base64.b64decode(args['file_content'])

    result = getattr(csv_transformer_api, '${method}')(**args)
    print(json.dumps(result, default=str))
except Exception as e:
    print(json.dumps({"error": str(e)}))
`
    ])

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
          resolve(JSON.parse(output))
        } catch (e) {
          reject(new Error(`Failed to parse Python output: ${output}\nError: ${error}`))
        }
      }
    })
  })
}