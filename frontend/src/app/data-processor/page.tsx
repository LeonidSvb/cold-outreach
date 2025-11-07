'use client'

import { useState } from 'react'
import AIProcessorTab from '@/components/data-processor/AIProcessorTab'
import WebScraperTab from '@/components/data-processor/WebScraperTab'

type TabType = 'ai-processor' | 'web-scraper'

export default function DataProcessorPage() {
  const [activeTab, setActiveTab] = useState<TabType>('ai-processor')

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Header with Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6">
          <div className="flex items-center justify-between py-4 border-b border-gray-200">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Data Processor</h1>
              <p className="text-sm text-gray-500 mt-0.5">Process CSV data with AI or scrape websites</p>
            </div>
          </div>

          {/* Tabs Navigation */}
          <div className="flex gap-6 -mb-px">
            <button
              className={`border-b-2 py-3 px-1 text-sm font-medium transition ${
                activeTab === 'ai-processor'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('ai-processor')}
            >
              AI Mass Processor
            </button>
            <button
              className={`border-b-2 py-3 px-1 text-sm font-medium transition ${
                activeTab === 'web-scraper'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              onClick={() => setActiveTab('web-scraper')}
            >
              Website Scraper
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-5xl mx-auto px-6 py-6">
        {activeTab === 'ai-processor' ? <AIProcessorTab /> : <WebScraperTab />}
      </div>
    </div>
  )
}
