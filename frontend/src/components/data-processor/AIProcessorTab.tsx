'use client'

import { useState } from 'react'

interface CsvInfo {
  rowCount: number
  columns: string[]
}

export default function AIProcessorTab() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [csvInfo, setCsvInfo] = useState<CsvInfo | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [fileId, setFileId] = useState<string>('')
  const [prompt, setPrompt] = useState<string>('')
  const [model, setModel] = useState<string>('gpt-4o-mini')
  const [concurrency, setConcurrency] = useState<number>(25)
  const [temperature, setTemperature] = useState<number>(0.3)
  const [stats, setStats] = useState<any>(null)
  const [error, setError] = useState<string>('')

  const parseCSV = async (file: File): Promise<CsvInfo> => {
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

        resolve({ rowCount, columns: headers })
      }
      reader.onerror = () => reject(new Error('Failed to read file'))
      reader.readAsText(file)
    })
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

    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    setIsProcessing(true)
    setError('')

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('mode', 'ai-processor')
      formData.append('prompt', prompt)
      formData.append('model', model)
      formData.append('concurrency', concurrency.toString())
      formData.append('temperature', temperature.toString())

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
      a.download = `processed_${fileId}.csv`
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
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Upload CSV</h2>

        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 hover:bg-blue-50 transition cursor-pointer">
          <input
            type="file"
            accept=".csv,.json"
            onChange={handleFileUpload}
            className="hidden"
            id="ai-file-upload"
          />
          <label htmlFor="ai-file-upload" className="cursor-pointer">
            <svg className="mx-auto h-10 w-10 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              <span className="font-medium text-blue-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500 mt-1">CSV or JSON files</p>
          </label>
        </div>

        {/* Preview (shown when file uploaded) */}
        {uploadedFile && csvInfo && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                <div>
                  <p className="text-sm font-medium text-gray-900">{uploadedFile.name}</p>
                  <p className="text-xs text-gray-500">{csvInfo.rowCount.toLocaleString()} rows</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setUploadedFile(null)
                  setCsvInfo(null)
                }}
                className="text-xs text-red-600 hover:text-red-700 font-medium"
              >
                Remove
              </button>
            </div>
            <div className="pt-2 border-t border-gray-200">
              <p className="text-xs font-medium text-gray-700 mb-1.5">Columns:</p>
              <div className="flex flex-wrap gap-1.5">
                {csvInfo.columns.map((col, idx) => (
                  <span
                    key={idx}
                    className={`px-2 py-0.5 text-xs rounded ${
                      idx === 0
                        ? 'bg-blue-100 text-blue-700 font-medium'
                        : idx === 1
                        ? 'bg-purple-100 text-purple-700 font-medium'
                        : idx === 2
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {col}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Prompt */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 mb-4">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">
          Custom Prompt
          <span className="text-gray-500 font-normal text-xs ml-2">(use {'{{'} column_name {'}}'}  placeholders)</span>
        </h2>

        <textarea
          rows={6}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
          placeholder={`Example:

Analyze {{company_name}} from {{website}}.

Return JSON: {pain_points, tech_stack, decision_makers}`}
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </div>

      {/* Settings + Process */}
      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <div className="flex items-end gap-3">
          <div className="flex-1 grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
              >
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Parallel Requests</label>
              <input
                type="number"
                value={concurrency}
                onChange={(e) => setConcurrency(parseInt(e.target.value))}
                min={1}
                max={50}
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1.5">Temperature</label>
              <input
                type="number"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                min={0}
                max={1}
                step={0.1}
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
              />
            </div>
          </div>
          <button
            onClick={handleProcess}
            disabled={isProcessing || !uploadedFile}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-md text-sm font-medium transition"
          >
            {isProcessing ? 'Processing...' : 'Start Processing'}
          </button>
        </div>

        {/* Progress (shown when processing) */}
        {isProcessing && !isComplete && csvInfo && (
          <div className="mt-5 space-y-3">
            <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <div>
                <p className="text-sm font-medium text-blue-900">Processing {csvInfo.rowCount.toLocaleString()} rows with AI...</p>
                <p className="text-xs text-blue-700 mt-1">This may take several minutes. Do not close this page.</p>
              </div>
            </div>

            <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
              <p className="text-xs text-gray-600">
                <span className="font-medium">Model:</span> {model} |
                <span className="font-medium ml-2">Concurrency:</span> {concurrency} parallel requests |
                <span className="font-medium ml-2">Temperature:</span> {temperature}
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
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p className="text-sm font-medium text-green-900">
                  Complete! {csvInfo.rowCount.toLocaleString()} rows processed successfully
                </p>
              </div>
              {stats && (
                <p className="text-xs text-green-700 mt-1 ml-7">
                  {stats.cost && `Total cost: $${stats.cost.toFixed(2)}`}
                  {stats.processingTime && ` | Time: ${Math.floor(stats.processingTime / 60)}m ${Math.floor(stats.processingTime % 60)}s`}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleDownload}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition flex items-center justify-center gap-2 text-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                </svg>
                Download CSV
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
