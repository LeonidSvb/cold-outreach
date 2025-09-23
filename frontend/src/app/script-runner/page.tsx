'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import FileUpload from '@/components/FileUpload'
import FilePreview from '@/components/FilePreview'
import ConfigForm from '@/components/ConfigForm'
import JobStatus from '@/components/JobStatus'
import { Button } from '@/components/ui/button'

interface Script {
  name: string
  description: string
  config: any[]
  requiresFile: boolean
}

export default function ScriptRunner() {
  const [scripts, setScripts] = useState<Script[]>([])
  const [selectedScript, setSelectedScript] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [currentJob, setCurrentJob] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchScripts()
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

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
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
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Script Runner</h1>

          {/* Script Selection */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Script
            </label>
            <select
              value={selectedScript}
              onChange={(e) => setSelectedScript(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
            >
              {scripts.map((script) => (
                <option key={script.name} value={script.name}>
                  {script.name} - {script.description}
                </option>
              ))}
            </select>
          </div>

          {/* File Upload */}
          {currentScriptData?.requiresFile && (
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Upload Data File
              </label>
              <FileUpload onFileSelect={handleFileSelect} />
            </div>
          )}

          {/* File Preview */}
          {selectedFile && (
            <div className="mb-6">
              <FilePreview file={selectedFile} />
            </div>
          )}

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