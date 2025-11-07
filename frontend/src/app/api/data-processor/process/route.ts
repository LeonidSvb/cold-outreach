import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import { writeFile, mkdir } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'
import { v4 as uuidv4 } from 'uuid'

const UPLOAD_DIR = path.join(process.cwd(), '..', 'data', 'uploads')
const OUTPUT_DIR = path.join(process.cwd(), '..', 'data', 'processed')

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const file = formData.get('file') as File
    const mode = formData.get('mode') as string // 'ai-processor' or 'web-scraper'
    const prompt = formData.get('prompt') as string
    const model = formData.get('model') as string || 'gpt-4o-mini'
    const concurrency = formData.get('concurrency') as string || '25'
    const temperature = formData.get('temperature') as string || '0.3'
    const workers = formData.get('workers') as string || '25'
    const scraperMode = formData.get('scraperMode') as string || 'quick'

    if (!file) {
      return NextResponse.json(
        { success: false, error: 'No file provided' },
        { status: 400 }
      )
    }

    if (!mode || (mode !== 'ai-processor' && mode !== 'web-scraper')) {
      return NextResponse.json(
        { success: false, error: 'Invalid mode' },
        { status: 400 }
      )
    }

    // Create directories if they don't exist
    if (!existsSync(UPLOAD_DIR)) {
      await mkdir(UPLOAD_DIR, { recursive: true })
    }
    if (!existsSync(OUTPUT_DIR)) {
      await mkdir(OUTPUT_DIR, { recursive: true })
    }

    // Save uploaded file
    const fileId = uuidv4()
    const inputFileName = `${fileId}_input.csv`
    const outputFileName = `${fileId}_output.csv`
    const inputPath = path.join(UPLOAD_DIR, inputFileName)
    const outputPath = path.join(OUTPUT_DIR, outputFileName)

    const bytes = await file.arrayBuffer()
    const buffer = Buffer.from(bytes)
    await writeFile(inputPath, buffer)

    // Run appropriate Python script
    let result
    if (mode === 'ai-processor') {
      result = await runOpenAIProcessor(inputPath, outputPath, {
        prompt,
        model,
        concurrency,
        temperature
      })
    } else {
      result = await runWebScraper(inputPath, outputPath, {
        workers,
        mode: scraperMode
      })
    }

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      fileId,
      outputPath,
      stats: result.stats
    })

  } catch (error) {
    console.error('Processing error:', error)
    return NextResponse.json(
      { success: false, error: 'Processing failed' },
      { status: 500 }
    )
  }
}

async function runOpenAIProcessor(
  inputPath: string,
  outputPath: string,
  options: { prompt: string; model: string; concurrency: string; temperature: string }
): Promise<{ success: boolean; error?: string; stats?: any }> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'openai_mass_processor.py')

    const args = [
      scriptPath,
      '--input', inputPath,
      '--output', outputPath,
      '--model', options.model,
      '--concurrency', options.concurrency,
      '--temperature', options.temperature
    ]

    if (options.prompt) {
      args.push('--prompt', options.prompt)
    }

    const python = spawn('py', args, {
      cwd: path.dirname(scriptPath)
    })

    let output = ''
    let error = ''

    python.stdout.on('data', (data) => {
      output += data.toString()
      console.log(`[OpenAI Processor] ${data}`)
    })

    python.stderr.on('data', (data) => {
      error += data.toString()
      console.error(`[OpenAI Processor Error] ${data}`)
    })

    python.on('close', (code) => {
      if (code !== 0) {
        resolve({ success: false, error: `Script failed: ${error}` })
      } else {
        // Parse stats from output
        const stats = parseScriptStats(output)
        resolve({ success: true, stats })
      }
    })
  })
}

async function runWebScraper(
  inputPath: string,
  outputPath: string,
  options: { workers: string; mode: string }
): Promise<{ success: boolean; error?: string; stats?: any }> {
  return new Promise((resolve) => {
    const scriptPath = path.join(process.cwd(), '..', 'scripts', 'scraping_parallel_website_email_extractor.py')

    const args = [
      scriptPath,
      '--input', inputPath,
      '--output', outputPath,
      '--workers', options.workers,
      '--mode', options.mode
    ]

    const python = spawn('py', args, {
      cwd: path.dirname(scriptPath)
    })

    let output = ''
    let error = ''

    python.stdout.on('data', (data) => {
      output += data.toString()
      console.log(`[Web Scraper] ${data}`)
    })

    python.stderr.on('data', (data) => {
      error += data.toString()
      console.error(`[Web Scraper Error] ${data}`)
    })

    python.on('close', (code) => {
      if (code !== 0) {
        resolve({ success: false, error: `Script failed: ${error}` })
      } else {
        // Parse stats from output
        const stats = parseScriptStats(output)
        resolve({ success: true, stats })
      }
    })
  })
}

function parseScriptStats(output: string): any {
  // Extract stats from script output
  // Looking for patterns like "Total cost: $X.XX" or "Processing completed: X items"
  const stats: any = {}

  const costMatch = output.match(/Total cost[:\s]+\$?([\d.]+)/i)
  if (costMatch) {
    stats.cost = parseFloat(costMatch[1])
  }

  const itemsMatch = output.match(/Processing completed[:\s]+([\d,]+)\s+items/i)
  if (itemsMatch) {
    stats.itemsProcessed = parseInt(itemsMatch[1].replace(/,/g, ''))
  }

  const timeMatch = output.match(/Processing time[:\s]+([\d.]+)s/i)
  if (timeMatch) {
    stats.processingTime = parseFloat(timeMatch[1])
  }

  return stats
}
