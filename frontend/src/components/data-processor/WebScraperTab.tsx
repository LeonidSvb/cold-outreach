'use client'

import { useState } from 'react'

interface CsvInfo {
  rowCount: number
  columns: string[]
  previewRows: string[][]
  originalColumns?: string[]
}

export default function WebScraperTab() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [csvInfo, setCsvInfo] = useState<CsvInfo | null>(null)
  const [mode, setMode] = useState<'quick' | 'full'>('quick')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [fileId, setFileId] = useState<string>('')
  const [workers, setWorkers] = useState<number>(25)
  const [stats, setStats] = useState<any>(null)
  const [error, setError] = useState<string>('')

  const parseCSV = async (file: File, maxRows: number = 7): Promise<CsvInfo> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const text = e.target?.result as string
        const lines = text.split('\n').filter(line => line.trim())

        if (lines.length === 0) {
          reject(new Error('Empty CSV file'))
          return
        }

        const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
        const rowCount = lines.length - 1

        const previewRows: string[][] = []
        for (let i = 1; i <= Math.min(maxRows, rowCount); i++) {
          const row = lines[i].split(',').map(cell => cell.trim().replace(/^"|"$/g, ''))
          previewRows.push(row)
        }

        resolve({
          rowCount,
          columns: headers,
          previewRows,
          originalColumns: headers
        })
      }
      reader.onerror = () => reject(new Error('Failed to read file'))
      reader.readAsText(file)
    })
  }

  const loadProcessedCSV = async (fileId: string): Promise<void> => {
    try {
      const response = await fetch(`/api/data-processor/download/${fileId}`)
      const text = await response.text()
      const lines = text.split('\n').filter(line => line.trim())

      if (lines.length === 0) return

      const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
      const previewRows: string[][] = []

      for (let i = 1; i <= Math.min(7, lines.length - 1); i++) {
        const row = lines[i].split(',').map(cell => cell.trim().replace(/^"|"$/g, ''))
        previewRows.push(row)
      }

      setCsvInfo(prev => prev ? {
        ...prev,
        columns: headers,
        previewRows
      } : null)
    } catch (err) {
      console.error('Failed to load processed CSV:', err)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setUploadedFile(file)
      setError('')

      try {
        const info = await parseCSV(file)
        setCsvInfo(info)
      } catch (err) {
        setError('Failed to parse CSV file')
        setCsvInfo(null)
      }
    }
  }

  const handleProcess = async () => {
    if (!uploadedFile) {
      setError('Please upload a CSV file first')
      return
    }

    setIsProcessing(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('mode', 'web-scraper')
      formData.append('workers', workers.toString())
      formData.append('scraperMode', mode)

      const response = await fetch('/api/data-processor/process', {
        method: 'POST',
        body: formData
      })

      const result = await response.json()

      if (!result.success) {
        setError(result.error || 'Processing failed')
        setIsProcessing(false)
        return
      }

      setFileId(result.fileId)
      setStats(result.stats)
      setIsComplete(true)
      setIsProcessing(false)

      await loadProcessedCSV(result.fileId)

    } catch (err) {
      setError('Processing failed. Please try again.')
      setIsProcessing(false)
    }
  }

  const handleDownload = async () => {
    if (!fileId) return

    try {
      const response = await fetch(`/api/data-processor/download/${fileId}`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `scraped_${fileId}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError('Download failed')
    }
  }

  return (
    <div>
      {/* Upload CSV */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-900">
            {csvInfo ? 'Data Preview' : 'Upload CSV with Websites'}
            {csvInfo && (
              <span className="ml-2 text-xs font-normal text-gray-500">
                ({csvInfo.rowCount.toLocaleString()} total rows)
              </span>
            )}
          </h2>
          {csvInfo && (
            <button
              onClick={() => {
                setUploadedFile(null)
                setCsvInfo(null)
                setIsComplete(false)
                setFileId('')
              }}
              className="text-xs text-red-600 hover:text-red-700 font-medium"
            >
              Remove & Upload New
            </button>
          )}
        </div>

        {!csvInfo ? (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-purple-400 hover:bg-purple-50 transition cursor-pointer">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              className="hidden"
              id="scraper-file-upload"
            />
            <label htmlFor="scraper-file-upload" className="cursor-pointer">
              <svg className="mx-auto h-10 w-10 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <p className="mt-2 text-sm text-gray-600">
                <span className="font-medium text-purple-600">Click to upload</span> or drag and drop
              </p>
              <p className="text-xs text-gray-500 mt-1">CSV with "website" or "url" column</p>
            </label>
          </div>
        ) : (
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {csvInfo.columns.map((col, idx) => {
                      const isNewColumn = csvInfo.originalColumns && !csvInfo.originalColumns.includes(col)
                      return (
                        <th
                          key={idx}
                          className={`px-3 py-2 text-left text-xs font-medium uppercase tracking-wider ${
                            isNewColumn
                              ? 'bg-green-50 text-green-700'
                              : 'text-gray-500'
                          }`}
                        >
                          <div className="flex items-center gap-1">
                            {col}
                            {isNewColumn && (
                              <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded font-normal normal-case">new</span>
                            )}
                          </div>
                        </th>
                      )
                    })}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {csvInfo.previewRows.map((row, rowIdx) => (
                    <tr key={rowIdx} className="hover:bg-gray-50">
                      {row.map((cell, cellIdx) => {
                        const isNewColumn = csvInfo.originalColumns && !csvInfo.originalColumns.includes(csvInfo.columns[cellIdx])
                        return (
                          <td
                            key={cellIdx}
                            className={`px-3 py-2 text-sm whitespace-nowrap ${
                              isNewColumn
                                ? 'bg-green-50/50 text-green-900 font-medium'
                                : 'text-gray-900'
                            }`}
                          >
                            {cell.length > 50 ? cell.substring(0, 50) + '...' : cell}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="bg-gray-50 px-3 py-2 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                Showing first {csvInfo.previewRows.length} rows of {csvInfo.rowCount.toLocaleString()}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Mode Selection + Prompt */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 mb-4">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Processing Mode</h2>

        <div className="grid grid-cols-2 gap-3 mb-4">
          {/* Quick Mode */}
          <label
            className={`relative flex flex-col p-3 border-2 rounded-lg cursor-pointer ${
              mode === 'quick'
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-300 hover:border-purple-400'
            }`}
          >
            <input
              type="radio"
              name="scraper-mode"
              value="quick"
              checked={mode === 'quick'}
              onChange={() => setMode('quick')}
              className="absolute top-3 right-3"
            />
            <div className="flex items-center gap-2 mb-1">
              <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
              <h3 className="font-semibold text-sm text-gray-900">Quick Scrape</h3>
            </div>
            <p className="text-xs text-gray-600 mb-1.5">Extract clean text only</p>
            <ul className="text-xs text-gray-500 space-y-0.5">
              <li>• HTTP-only scraping</li>
              <li>• ~2-3 sec/site | No AI costs</li>
            </ul>
          </label>

          {/* Full Mode */}
          <label
            className={`relative flex flex-col p-3 border-2 rounded-lg cursor-pointer ${
              mode === 'full'
                ? 'border-purple-500 bg-purple-50'
                : 'border-gray-300 hover:border-purple-400'
            }`}
          >
            <input
              type="radio"
              name="scraper-mode"
              value="full"
              checked={mode === 'full'}
              onChange={() => setMode('full')}
              className="absolute top-3 right-3"
            />
            <div className="flex items-center gap-2 mb-1">
              <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
              <h3 className="font-semibold text-sm text-gray-900">Full Pipeline</h3>
            </div>
            <p className="text-xs text-gray-600 mb-1.5">Scrape + AI extraction</p>
            <ul className="text-xs text-gray-500 space-y-0.5">
              <li>• Text + AI data extraction</li>
              <li>• ~5-8 sec/site | $0.003-0.01/site</li>
            </ul>
          </label>
        </div>

        {/* AI Prompt (shown only for Full mode) */}
        {mode === 'full' && (
          <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <label className="block text-sm font-semibold text-gray-900 mb-2">AI Extraction Prompt</label>
            <textarea
              rows={5}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-sm"
              placeholder={`From {{scraped_text}}, extract JSON:
{
  "owner_name": "...",
  "business_type": "..."
}`}
            />
          </div>
        )}
      </div>

      {/* Settings + Process */}
      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <div className="flex items-end gap-3">
          <div className="flex-1 grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Model (Full mode)</label>
              <select className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md">
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Max Content Length</label>
              <input
                type="number"
                defaultValue={15000}
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Parallel Workers</label>
              <input
                type="number"
                value={workers}
                onChange={(e) => setWorkers(parseInt(e.target.value))}
                min={10}
                max={50}
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
              />
            </div>
          </div>
          <button
            onClick={handleProcess}
            disabled={isProcessing || !uploadedFile}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-md text-sm font-medium transition"
          >
            {isProcessing ? 'Processing...' : 'Start Processing'}
          </button>
        </div>

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

        {/* Progress (shown when processing) */}
        {isProcessing && !isComplete && csvInfo && (
          <div className="mt-5 space-y-3">
            <div className="flex items-center gap-3 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
              <div>
                <p className="text-sm font-medium text-purple-900">
                  Scraping {csvInfo.rowCount.toLocaleString()} websites...
                </p>
                <p className="text-xs text-purple-700 mt-1">
                  {mode === 'quick' ? 'HTTP-only scraping' : 'Full pipeline with AI extraction'} | This may take several minutes
                </p>
              </div>
            </div>

            <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-600">
                <span className="font-medium">Mode:</span> {mode === 'quick' ? 'Quick Scrape' : 'Full Pipeline'} |
                <span className="font-medium ml-2">Workers:</span> {workers} parallel
              </p>
            </div>
          </div>
        )}

        {/* Download (shown when complete) */}
        {isComplete && csvInfo && (
          <div className="mt-5">
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg mb-3">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p className="text-sm font-medium text-green-900">
                  Complete! {csvInfo.rowCount.toLocaleString()} websites processed successfully
                </p>
              </div>
              {stats && (
                <p className="text-xs text-green-700 mt-1 ml-7">
                  {stats.itemsProcessed && `Scraped: ${stats.itemsProcessed} sites`}
                  {stats.cost && ` | Cost: $${stats.cost.toFixed(2)}`}
                  {stats.processingTime && ` | Time: ${Math.floor(stats.processingTime / 60)}m ${Math.floor(stats.processingTime % 60)}s`}
                </p>
              )}
            </div>
            <button
              onClick={handleDownload}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition flex items-center justify-center gap-2 text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
              Download Enriched CSV
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
