'use client'

import { useState, useEffect } from 'react'
import { Clock, Users, History, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'

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

interface UploadHistoryDrawerProps {
  onSelectBatch?: (batchId: number | null) => void
  selectedBatch?: number | null
}

export default function UploadHistoryDrawer({ onSelectBatch, selectedBatch }: UploadHistoryDrawerProps) {
  const [history, setHistory] = useState<UploadHistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (open) {
      fetchHistory()
    }
  }, [open])

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
    if (onSelectBatch) {
      onSelectBatch(selectedBatch === batchId ? null : batchId)
    }
    setOpen(false)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="h-9 gap-2">
          <History className="h-4 w-4" />
          <span className="text-sm">
            History {history.length > 0 && `(${history.length})`}
          </span>
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Upload History
          </SheetTitle>
          <SheetDescription>
            Select a batch to filter leads, or view all leads
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-2 overflow-y-auto max-h-[calc(100vh-120px)]">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              <span className="ml-2 text-sm text-gray-600">Loading...</span>
            </div>
          )}

          {error && (
            <div className="text-sm text-red-500 p-4 bg-red-50 rounded-lg">
              {error}
            </div>
          )}

          {!loading && !error && history.length === 0 && (
            <div className="text-sm text-gray-500 text-center py-8">
              No upload history
            </div>
          )}

          {!loading && history.map((item) => {
            const isSelected = selectedBatch === item.upload_batch_id

            return (
              <div
                key={item.upload_batch_id}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  isSelected
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
                onClick={() => handleSelectBatch(item.upload_batch_id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      Batch #{item.upload_batch_id}
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatDate(item.uploaded_at)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-blue-600">
                      {item.total_leads}
                    </div>
                    <div className="text-xs text-gray-500">leads</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="flex items-center gap-1.5 text-xs bg-white rounded px-2 py-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-gray-600">New:</span>
                    <span className="font-medium text-green-600">{item.new_leads}</span>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs bg-white rounded px-2 py-1">
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span className="text-gray-600">Updated:</span>
                    <span className="font-medium text-orange-600">{item.updated_leads}</span>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </SheetContent>
    </Sheet>
  )
}
