'use client'

import { useState, useEffect } from 'react'
import { Clock, Users, Phone, Linkedin } from 'lucide-react'

interface UploadHistoryItem {
  upload_batch_id: number
  uploaded_at: string
  total_leads: number
  new_leads: number
  updated_leads: number
  unique_emails: number
  leads_with_phone: number
  leads_with_linkedin: number
}

interface UploadHistoryProps {
  onSelectBatch?: (batchId: number) => void
}

export default function UploadHistory({ onSelectBatch }: UploadHistoryProps) {
  const [history, setHistory] = useState<UploadHistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedBatch, setSelectedBatch] = useState<number | null>(null)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/upload-history')
      const data = await response.json()

      if (!data.success) {
        throw new Error(data.error || 'Failed to load upload history')
      }

      setHistory(data.history)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectBatch = (batchId: number) => {
    setSelectedBatch(batchId)
    if (onSelectBatch) {
      onSelectBatch(batchId)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center justify-center py-4">
          <div className="h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-2 text-sm text-gray-600">Loading history...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <p className="text-sm text-red-500">Error: {error}</p>
      </div>
    )
  }

  if (history.length === 0) {
    return (
      <div className="bg-white rounded-lg border p-4">
        <p className="text-sm text-gray-500 text-center">No upload history</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border">
      <div className="p-4 border-b">
        <h3 className="font-medium text-gray-900 flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Upload History ({history.length})
        </h3>
      </div>

      <div className="divide-y max-h-96 overflow-y-auto">
        {history.map((item) => (
          <div
            key={item.upload_batch_id}
            className={`p-4 cursor-pointer hover:bg-gray-50 transition-colors ${
              selectedBatch === item.upload_batch_id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
            }`}
            onClick={() => handleSelectBatch(item.upload_batch_id)}
          >
            <div className="flex items-start justify-between mb-2">
              <div>
                <div className="text-sm font-medium text-gray-900">
                  {formatDate(item.uploaded_at)}
                </div>
                <div className="text-xs text-gray-500">
                  Batch #{item.upload_batch_id}
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-blue-600">
                  {item.total_leads}
                </div>
                <div className="text-xs text-gray-500">leads</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 mt-3">
              <div className="flex items-center gap-1 text-xs">
                <Users className="h-3 w-3 text-green-600" />
                <span className="text-gray-600">New:</span>
                <span className="font-medium text-green-600">{item.new_leads}</span>
              </div>

              <div className="flex items-center gap-1 text-xs">
                <Users className="h-3 w-3 text-orange-600" />
                <span className="text-gray-600">Updated:</span>
                <span className="font-medium text-orange-600">{item.updated_leads}</span>
              </div>

              <div className="flex items-center gap-1 text-xs">
                <Phone className="h-3 w-3 text-blue-600" />
                <span className="text-gray-600">Phone:</span>
                <span className="font-medium">{item.leads_with_phone}</span>
              </div>

              <div className="flex items-center gap-1 text-xs">
                <Linkedin className="h-3 w-3 text-purple-600" />
                <span className="text-gray-600">LinkedIn:</span>
                <span className="font-medium">{item.leads_with_linkedin}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
