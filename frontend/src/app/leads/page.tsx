'use client'

import { useState } from 'react'
import Link from 'next/link'
import LeadsPreview from '@/components/LeadsPreview'
import UploadHistoryDrawer from '@/components/UploadHistoryDrawer'
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

    logger.info('CSV upload to Supabase started', { filename: file.name })

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
        setTimeout(() => {
          window.location.reload()
        }, 1500)
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

          <div className="flex items-center gap-2">
            <UploadHistoryDrawer
              onSelectBatch={setSelectedBatchId}
              selectedBatch={selectedBatchId}
            />

            <Button
              onClick={() => setShowUpload(!showUpload)}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              {showUpload ? 'Cancel Upload' : 'Upload CSV'}
            </Button>
          </div>
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

            {uploadResult ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-green-900">
                      Upload Successful!
                    </h3>
                    <p className="text-sm text-green-700 mt-1">
                      {uploadResult.data?.count} leads uploaded to Supabase. Page will reload...
                    </p>
                  </div>
                </div>
              </div>
            ) : uploading ? (
              <div className="text-center py-8">
                <div className="inline-flex items-center gap-2 text-blue-600">
                  <div className="h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                  Uploading to Supabase...
                </div>
              </div>
            ) : (
              <FileUpload onFileSelect={handleFileSelect} />
            )}
          </div>
        )}

        <LeadsPreview
          uploadBatchId={selectedBatchId}
          limit={selectedBatchId ? 1000 : 100}
        />
      </div>
    </div>
  )
}
