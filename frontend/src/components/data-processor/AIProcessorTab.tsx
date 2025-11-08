'use client'

import { useState } from 'react'

interface CsvInfo {
  rowCount: number
  columns: string[]
  previewRows: string[][]
  originalColumns?: string[]
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
  const [logs, setLogs] = useState<Array<{ message: string; type: 'info' | 'error' }>>([])
  const logsEndRef = useState<HTMLDivElement | null>(null)
  const [activeLogTab, setActiveLogTab] = useState<'logs' | 'summary'>('logs')
  const [processingStats, setProcessingStats] = useState<{
    totalProcessed: number
    successful: number
    failed: number
    duration: number
    errors: number
    tokenCount?: number
    cost?: number
  }>({ totalProcessed: 0, successful: 0, failed: 0, duration: 0, errors: 0 })

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

  const copyLogsToClipboard = () => {
    const logsText = logs.map(log => `[${log.type.toUpperCase()}] ${log.message}`).join('\n')
    navigator.clipboard.writeText(logsText)
      .then(() => alert('Logs copied to clipboard!'))
      .catch(() => alert('Failed to copy logs'))
  }

  const parseStatsFromLogs = (logs: Array<{ message: string; type: string }>) => {
    let totalProcessed = 0
    let successful = 0
    let failed = 0
    let duration = 0
    let tokenCount = 0
    let cost = 0

    logs.forEach(log => {
      const msg = log.message

      const progressMatch = msg.match(/\[(\d+)\/(\d+)\]/)
      if (progressMatch) {
        totalProcessed = Math.max(totalProcessed, parseInt(progressMatch[1]))
      }

      if (msg.includes('Processing completed') || msg.includes('successfully processed')) {
        successful++
      }

      if (msg.includes('failed') || msg.includes('error') || log.type === 'error') {
        failed++
      }

      const timeMatch = msg.match(/completed in ([\d.]+) seconds/)
      if (timeMatch) {
        duration = parseFloat(timeMatch[1])
      }

      const tokenMatch = msg.match(/tokens?[:\s]+(\d+)/i)
      if (tokenMatch) {
        tokenCount += parseInt(tokenMatch[1])
      }

      const costMatch = msg.match(/\$?([\d.]+)\s*(?:USD|dollars?)?/i)
      if (costMatch && msg.toLowerCase().includes('cost')) {
        cost += parseFloat(costMatch[1])
      }
    })

    setProcessingStats({
      totalProcessed,
      successful,
      failed,
      duration,
      errors: logs.filter(l => l.type === 'error').length,
      tokenCount: tokenCount > 0 ? tokenCount : undefined,
      cost: cost > 0 ? cost : undefined
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
    setLogs([])

    try {
      const formData = new FormData()
      formData.append('file', uploadedFile)
      formData.append('mode', 'ai-processor')
      formData.append('prompt', prompt)
      formData.append('model', model)
      formData.append('concurrency', concurrency.toString())
      formData.append('temperature', temperature.toString())

      const response = await fetch('/api/data-processor/stream', {
        method: 'POST',
        body: formData
      })

      if (!response.ok || !response.body) {
        throw new Error('Failed to start processing')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue

          const eventMatch = line.match(/^event: (\w+)\ndata: ([\s\S]+)$/)
          if (!eventMatch) continue

          const [, event, dataStr] = eventMatch
          const data = JSON.parse(dataStr)

          if (event === 'log') {
            setLogs(prev => [...prev, { message: data.message, type: data.type }])
          } else if (event === 'complete') {
            setFileId(data.fileId)
            setIsComplete(true)
            setIsProcessing(false)

            setLogs(prevLogs => {
              parseStatsFromLogs(prevLogs)
              return prevLogs
            })

            await loadProcessedCSV(data.fileId)
          } else if (event === 'error') {
            setError(data.message || 'Processing failed')
            setIsProcessing(false)
          }
        }
      }

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
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-gray-900">
            {csvInfo ? 'Data Preview' : 'Upload CSV'}
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

        {/* Logs and Summary (shown during and after processing) */}
        {logs.length > 0 && csvInfo && (
          <div className="mt-5 space-y-3">
            {isProcessing && !isComplete && (
              <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-blue-900">Processing {csvInfo.rowCount.toLocaleString()} rows with AI...</p>
                  <p className="text-xs text-blue-700 mt-1">
                    {model} | {concurrency} parallel requests | {logs.length} log entries
                  </p>
                </div>
              </div>
            )}

            {/* Tabs: Logs / Summary */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="flex border-b border-gray-200">
                <button
                  onClick={() => setActiveLogTab('logs')}
                  className={`flex-1 px-4 py-2 text-sm font-medium ${
                    activeLogTab === 'logs'
                      ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Logs ({logs.length})
                </button>
                <button
                  onClick={() => setActiveLogTab('summary')}
                  className={`flex-1 px-4 py-2 text-sm font-medium ${
                    activeLogTab === 'summary'
                      ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Summary
                </button>
                <button
                  onClick={copyLogsToClipboard}
                  className="px-4 py-2 text-sm font-medium bg-gray-50 text-gray-600 hover:bg-gray-100 border-l border-gray-200"
                  title="Copy all logs to clipboard"
                >
                  <svg className="w-4 h-4 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span className="ml-1">Copy Logs</span>
                </button>
              </div>

              {activeLogTab === 'logs' ? (
                <div className="bg-gray-900 text-gray-100 p-3 font-mono text-xs max-h-64 overflow-y-auto">
                  {logs.map((log, idx) => (
                    <div key={idx} className="mb-1">
                      <span className={log.type === 'error' ? 'text-red-400' : 'text-green-400'}>
                        [{log.type.toUpperCase()}]
                      </span>
                      <span className="ml-2">{log.message}</span>
                    </div>
                  ))}
                  <div ref={(el) => {
                    if (el && isProcessing) el.scrollIntoView({ behavior: 'smooth' })
                  }} />
                </div>
              ) : (
                <div className="bg-white p-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <p className="text-xs text-blue-600 font-medium mb-1">Total Processed</p>
                      <p className="text-2xl font-bold text-blue-900">{processingStats.totalProcessed}</p>
                    </div>
                    <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                      <p className="text-xs text-green-600 font-medium mb-1">Successful</p>
                      <p className="text-2xl font-bold text-green-900">{processingStats.successful}</p>
                    </div>
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <p className="text-xs text-red-600 font-medium mb-1">Failed</p>
                      <p className="text-2xl font-bold text-red-900">{processingStats.failed}</p>
                    </div>
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                      <p className="text-xs text-purple-600 font-medium mb-1">Duration</p>
                      <p className="text-2xl font-bold text-purple-900">{processingStats.duration}s</p>
                    </div>
                  </div>
                  {processingStats.tokenCount && (
                    <div className="mt-3 bg-indigo-50 border border-indigo-200 rounded-lg p-3">
                      <p className="text-sm font-medium text-indigo-800">Tokens: {processingStats.tokenCount.toLocaleString()}</p>
                    </div>
                  )}
                  {processingStats.cost && (
                    <div className="mt-3 bg-green-50 border border-green-200 rounded-lg p-3">
                      <p className="text-sm font-medium text-green-800">Cost: ${processingStats.cost.toFixed(4)}</p>
                    </div>
                  )}
                  {processingStats.errors > 0 && (
                    <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <p className="text-sm font-medium text-yellow-800">{processingStats.errors} errors encountered</p>
                    </div>
                  )}
                </div>
              )}
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
