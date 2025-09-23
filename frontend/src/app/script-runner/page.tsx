'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import FileUpload from '@/components/FileUpload'
import CsvPreview from '@/components/CsvPreview'
import ConfigForm from '@/components/ConfigForm'
import JobStatus from '@/components/JobStatus'
import { Button } from '@/components/ui/button'

interface Script {
  name: string
  description: string
  config: any[]
  requiresFile: boolean
}

interface UploadedFile {
  id: string
  filename: string
  original_name: string
  upload_date: string
  rows: number
  columns: string[]
  size: number
}

export default function ScriptRunner() {
  const [scripts, setScripts] = useState<Script[]>([])
  const [selectedScript, setSelectedScript] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [currentJob, setCurrentJob] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [currentFileId, setCurrentFileId] = useState<string | null>(null)
  const [showFileManager, setShowFileManager] = useState(false)

  useEffect(() => {
    fetchScripts()
    fetchUploadedFiles()
  }, [])

  const fetchScripts = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/scripts')
      const data = await response.json()
      setScripts(data)
      if (data.length > 0) {
        setSelectedScript(data[0].name)
      }
    } catch (error) {
      console.error('Failed to fetch scripts:', error)
    }
  }

  const fetchUploadedFiles = async () => {
    try {
      const response = await fetch('http://localhost:8005/api/uploaded-files')
      const data = await response.json()
      setUploadedFiles(data)
    } catch (error) {
      console.error('Failed to fetch uploaded files:', error)
    }
  }

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file)

    // Auto-upload CSV file for processing
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8005/api/upload', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()
      if (result.file_id) {
        setCurrentFileId(result.file_id)
        fetchUploadedFiles() // Refresh the list
      }
    } catch (error) {
      console.error('Failed to upload file:', error)
    }
  }

  const handleLoadExistingFile = async (fileId: string) => {
    setCurrentFileId(fileId)
    setShowFileManager(false)

    // Load file preview
    try {
      const response = await fetch(`http://localhost:8005/api/files/${fileId}/preview`)
      const data = await response.json()
      // Update preview component with loaded data
    } catch (error) {
      console.error('Failed to load file:', error)
    }
  }

  const handleConfigSubmit = async (config: Record<string, any>) => {
    if (!selectedScript) return

    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('script_name', selectedScript)
      formData.append('config', JSON.stringify(config))

      if (selectedFile) {
        formData.append('file', selectedFile)
      }

      const response = await fetch('http://localhost:8001/api/run-script', {
        method: 'POST',
        body: formData,
      })

      const result = await response.json()
      if (result.job_id) {
        setCurrentJob(result.job_id)
      }
    } catch (error) {
      console.error('Failed to start script:', error)
    } finally {
      setLoading(false)
    }
  }

  const currentScriptData = scripts.find(s => s.name === selectedScript)

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 transition-colors"
          >
            ← Back to Home
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Lead Processing Center</h1>

            {/* File Manager Toggle */}
            <div className="flex gap-2">
              <Button
                onClick={() => setShowFileManager(!showFileManager)}
                variant="outline"
                className="flex items-center gap-2"
              >
                📁 Recent Files ({uploadedFiles.length})
              </Button>
            </div>
          </div>

          {/* File Manager Dropdown */}
          {showFileManager && (
            <div className="mb-6 border rounded-lg p-4 bg-gray-50">
              <h3 className="font-medium text-gray-900 mb-3">Previously Uploaded Files</h3>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {uploadedFiles.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 bg-white border rounded cursor-pointer hover:bg-blue-50"
                    onClick={() => handleLoadExistingFile(file.id)}
                  >
                    <div className="flex-1">
                      <div className="font-medium text-sm">{file.original_name}</div>
                      <div className="text-xs text-gray-500">
                        {file.rows} rows • {new Date(file.upload_date).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="text-right text-xs text-gray-400">
                      {(file.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                ))}
                {uploadedFiles.length === 0 && (
                  <div className="text-gray-500 text-center py-4">
                    No files uploaded yet
                  </div>
                )}
              </div>
            </div>
          )}

          {/* CSV Upload Section */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <label className="block text-sm font-medium text-gray-700">
                Upload CSV File with Leads
              </label>
              {currentFileId && (
                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                  File processed ✓
                </span>
              )}
            </div>
            <FileUpload onFileSelect={handleFileSelect} />
            <p className="text-xs text-gray-500 mt-2">
              Supported: CSV files with lead data (company names, websites, emails, phones)
            </p>
          </div>

          {/* Script Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Available Processing Scripts
            </label>
            <select
              value={selectedScript}
              onChange={(e) => setSelectedScript(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              {scripts.map((script) => (
                <option key={script.name} value={script.name}>
                  {script.name} - {script.description}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Note: Instantly upload will be available after processing is complete
            </p>
          </div>

          {/* CSV Preview */}
          <div className="mb-6">
            <CsvPreview fileId={currentFileId} />
          </div>

          {/* Configuration Form */}
          {currentScriptData && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Configuration</h3>
              <ConfigForm
                config={currentScriptData.config}
                onSubmit={handleConfigSubmit}
                isLoading={loading}
              />
            </div>
          )}

          {/* Job Status */}
          {currentJob && (
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Execution Status</h3>
              <JobStatus
                jobId={currentJob}
                onClose={() => setCurrentJob(null)}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}