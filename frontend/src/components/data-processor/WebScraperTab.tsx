'use client'

import { useState } from 'react'

export default function WebScraperTab() {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [mode, setMode] = useState<'quick' | 'full'>('quick')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isComplete, setIsComplete] = useState(false)

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setUploadedFile(e.target.files[0])
    }
  }

  return (
    <div>
      {/* Upload CSV */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 mb-4">
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Upload CSV with Websites</h2>

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
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              <span className="font-medium text-purple-600">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500 mt-1">CSV with "website" or "url" column</p>
          </label>
        </div>

        {/* Preview (shown when file uploaded) */}
        {uploadedFile && (
          <div className="mt-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                </svg>
                <div>
                  <p className="text-sm font-medium text-gray-900">{uploadedFile.name}</p>
                  <p className="text-xs text-gray-500">523 rows</p>
                </div>
              </div>
              <button
                onClick={() => setUploadedFile(null)}
                className="text-xs text-red-600 hover:text-red-700 font-medium"
              >
                Remove
              </button>
            </div>
            <div className="pt-2 border-t border-gray-200">
              <p className="text-xs font-medium text-gray-700 mb-1.5">Columns:</p>
              <div className="flex flex-wrap gap-1.5">
                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded font-medium">website</span>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">company_name</span>
                <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">location</span>
              </div>
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
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
                defaultValue={25}
                min={10}
                max={50}
                className="w-full px-2 py-1.5 text-sm border border-gray-300 rounded-md"
              />
            </div>
          </div>
          <button
            onClick={() => setIsProcessing(true)}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md text-sm font-medium transition"
          >
            Start Processing
          </button>
        </div>

        {/* Progress (shown when processing) */}
        {isProcessing && !isComplete && (
          <div className="mt-5 space-y-3">
            <div className="flex items-center gap-2 p-2 bg-purple-50 rounded-lg border border-purple-200">
              <div className="w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center animate-pulse">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/>
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-900">Scraping websites...</p>
                <p className="text-xs text-gray-500">Extracting clean text from pages</p>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1.5">
                <span>Processing...</span>
                <span className="font-medium">187 / 523 (36%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-purple-600 h-2 rounded-full transition-all" style={{ width: '36%' }}></div>
              </div>
            </div>

            <div className="grid grid-cols-5 gap-2 p-3 bg-gray-50 rounded-lg">
              <div className="text-center">
                <p className="text-lg font-semibold text-gray-900">187</p>
                <p className="text-xs text-gray-500">Processed</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold text-green-600">142</p>
                <p className="text-xs text-gray-500">Success</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold text-yellow-600">23</p>
                <p className="text-xs text-gray-500">Dynamic</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold text-red-600">22</p>
                <p className="text-xs text-gray-500">Failed</p>
              </div>
              <div className="text-center">
                <p className="text-lg font-semibold text-blue-600">$0.47</p>
                <p className="text-xs text-gray-500">Cost</p>
              </div>
            </div>

            <div className="bg-gray-900 text-gray-100 rounded-lg p-3 font-mono text-xs space-y-1 max-h-28 overflow-y-auto">
              <p><span className="text-green-400">[15:34:12]</span> Scraping: https://example.com</p>
              <p><span className="text-green-400">[15:34:13]</span> Success | 3,842 chars</p>
              <p><span className="text-blue-400">[15:34:14]</span> AI extraction...</p>
              <p><span className="text-green-400">[15:34:15]</span> AI complete | $0.004</p>
            </div>
          </div>
        )}

        {/* Download (shown when complete) */}
        {isComplete && (
          <div className="mt-5">
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg mb-3">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <p className="text-sm font-medium text-green-900">Complete! 523 websites in 4m 23s</p>
              </div>
              <p className="text-xs text-green-700 mt-1 ml-7">Scraped: 412 (79%) | AI extraction: 412 | Cost: $1.23</p>
            </div>
            <button className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-md transition flex items-center justify-center gap-2 text-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
              </svg>
              Download Enriched CSV
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
