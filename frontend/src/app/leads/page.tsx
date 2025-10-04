'use client'

import { useState } from 'react'
import Link from 'next/link'
import LeadsPreview from '@/components/LeadsPreview'
import UploadHistory from '@/components/UploadHistory'
import FileUpload from '@/components/FileUpload'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Upload } from 'lucide-react'
import { logger } from '@/lib/logger'

export default function LeadsPage() {
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null)
  const [showUpload, setShowUpload] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)

  const handleFileSelect = async (file: File) => {
    setUploading(true)
    setUploadResult(null)

    logger.info('CSV upload started', { filename: file.name, size: file.size })

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/csv-upload', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()

      if (result.success) {
        logger.info('CSV upload successful', {
          filename: file.name,
          rows: result.data?.count
        })
        setUploadResult(result)
        setShowUpload(false)
        window.location.reload()
      } else {
        logger.error('CSV upload failed', null, {
          filename: file.name,
          error: result.error
        })
        alert('Upload failed: ' + (result.error || 'Unknown error'))
      }
    } catch (error) {
      logger.error('CSV upload error', error as Error, {
        filename: file.name
      })
      alert('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <div className="mb-6 flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Home
          </Link>

          <Button
            onClick={() => setShowUpload(!showUpload)}
            className="flex items-center gap-2"
          >
            <Upload className="h-4 w-4" />
            {showUpload ? 'Cancel Upload' : 'Upload CSV'}
          </Button>
        </div>

        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Leads Database</h1>
          <p className="text-gray-600 mt-2">
            View and manage all uploaded leads from Supabase
          </p>
        </div>

        {showUpload && (
          <div className="mb-6 bg-white rounded-lg border p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Upload CSV File</h2>
            <FileUpload onFileSelect={handleFileSelect} />
            {uploading && (
              <div className="mt-4 text-center">
                <div className="inline-flex items-center gap-2 text-blue-600">
                  <div className="h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  Uploading and processing...
                </div>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <UploadHistory onSelectBatch={setSelectedBatchId} />
          </div>

          <div className="lg:col-span-2">
            <LeadsPreview
              uploadBatchId={selectedBatchId}
              limit={selectedBatchId ? 1000 : 100}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
