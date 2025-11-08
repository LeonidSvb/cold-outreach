import { NextRequest } from 'next/server'
import { spawn } from 'child_process'
import { writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'
import { v4 as uuidv4 } from 'uuid'

const UPLOAD_DIR = path.join(process.cwd(), '..', 'data', 'uploads')
const OUTPUT_DIR = path.join(process.cwd(), '..', 'data', 'processed')

export async function POST(request: NextRequest) {
  const formData = await request.formData()
  const file = formData.get('file') as File
  const mode = formData.get('mode') as string
  const prompt = formData.get('prompt') as string || ''
  const model = formData.get('model') as string || 'gpt-4o-mini'
  const concurrency = formData.get('concurrency') as string || '25'
  const temperature = formData.get('temperature') as string || '0.3'
  const workers = formData.get('workers') as string || '25'
  const scraperMode = formData.get('scraperMode') as string || 'quick'
  const maxContentLength = formData.get('maxContentLength') as string || '15000'

  if (!file) {
    return new Response('No file provided', { status: 400 })
  }

  if (!existsSync(UPLOAD_DIR)) {
    await mkdir(UPLOAD_DIR, { recursive: true })
  }
  if (!existsSync(OUTPUT_DIR)) {
    await mkdir(OUTPUT_DIR, { recursive: true })
  }

  const fileId = uuidv4()
  const inputFileName = `${fileId}_input.csv`
  const outputFileName = `${fileId}_output.csv`
  const inputPath = path.join(UPLOAD_DIR, inputFileName)
  const outputPath = path.join(OUTPUT_DIR, outputFileName)

  const bytes = await file.arrayBuffer()
  const buffer = Buffer.from(bytes)
  await writeFile(inputPath, buffer)

  const encoder = new TextEncoder()

  const stream = new ReadableStream({
    async start(controller) {
      const sendEvent = (event: string, data: any) => {
        controller.enqueue(encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`))
      }

      try {
        let scriptPath: string
        let args: string[]

        if (mode === 'ai-processor') {
          scriptPath = path.join(process.cwd(), '..', 'scripts', 'openai_mass_processor.py')
          args = [
            scriptPath,
            '--input', inputPath,
            '--output', outputPath,
            '--model', model,
            '--concurrency', concurrency,
            '--temperature', temperature
          ]
          if (prompt) {
            args.push('--prompt', prompt)
          }
        } else {
          if (scraperMode === 'full') {
            scriptPath = path.join(process.cwd(), '..', 'scripts', 'scraping_website_personalization_enricher.py')
            args = [
              scriptPath,
              '--input', inputPath,
              '--output', outputPath,
              '--workers', workers,
              '--model', model,
              '--max-content-length', maxContentLength
            ]
            if (prompt) {
              args.push('--prompt', prompt)
            }
          } else {
            scriptPath = path.join(process.cwd(), '..', 'scripts', 'scraping_parallel_website_email_extractor.py')
            args = [
              scriptPath,
              '--input', inputPath,
              '--output', outputPath,
              '--workers', workers
            ]
          }
        }

        const python = spawn('py', args, {
          cwd: path.dirname(scriptPath)
        })

        python.stdout.on('data', (data) => {
          const lines = data.toString().split('\n').filter((line: string) => line.trim())
          lines.forEach((line: string) => {
            sendEvent('log', { message: line, type: 'info' })
          })
        })

        python.stderr.on('data', (data) => {
          const lines = data.toString().split('\n').filter((line: string) => line.trim())
          lines.forEach((line: string) => {
            sendEvent('log', { message: line, type: 'error' })
          })
        })

        python.on('close', (code) => {
          if (code !== 0) {
            sendEvent('error', { message: 'Processing failed', code })
            controller.close()
          } else {
            sendEvent('complete', { fileId, outputPath })
            controller.close()
          }
        })

        python.on('error', (err) => {
          sendEvent('error', { message: err.message })
          controller.close()
        })

      } catch (error) {
        sendEvent('error', { message: 'Failed to start processing' })
        controller.close()
      }
    }
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  })
}
