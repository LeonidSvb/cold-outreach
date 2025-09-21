'use client'

import { useState, useEffect } from 'react'
import { Progress } from './ui/progress'
import { Button } from './ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog'
import { Copy, Download, AlertCircle, CheckCircle } from 'lucide-react'

interface JobStatusProps {
  jobId: string | null
  onClose: () => void
}

interface JobData {
  status: 'running' | 'completed' | 'error'
  progress: number
  message: string
  logs: string[]
  results?: any
  error?: string
}

export default function JobStatus({ jobId, onClose }: JobStatusProps) {
  const [jobData, setJobData] = useState<JobData | null>(null)
  const [showLogs, setShowLogs] = useState(false)

  useEffect(() => {
    if (!jobId) return

    const fetchJobStatus = async () => {
      try {
        const response = await fetch(`http://localhost:8001/api/job/${jobId}`)
        const data = await response.json()
        setJobData(data)
      } catch (error) {
        console.error('Failed to fetch job status:', error)
      }
    }

    // Initial fetch
    fetchJobStatus()

    // Poll every 2 seconds
    const interval = setInterval(fetchJobStatus, 2000)

    return () => clearInterval(interval)
  }, [jobId])

  const copyLogs = () => {
    if (jobData?.logs) {
      navigator.clipboard.writeText(jobData.logs.join('\n'))
    }
  }

  const downloadResults = () => {
    if (jobData?.results) {
      const blob = new Blob([JSON.stringify(jobData.results, null, 2)], {
        type: 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `results_${jobId}.json`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  if (!jobId || !jobData) {
    return null
  }

  const getStatusIcon = () => {
    switch (jobData.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <div className="h-5 w-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    }
  }

  const getStatusColor = () => {
    switch (jobData.status) {
      case 'completed':
        return 'text-green-600'
      case 'error':
        return 'text-red-600'
      default:
        return 'text-blue-600'
    }
  }

  return (
    <div className="bg-white rounded-lg border p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className={`font-medium ${getStatusColor()}`}>
            {jobData.status.charAt(0).toUpperCase() + jobData.status.slice(1)}
          </span>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          ×
        </Button>
      </div>

      {jobData.status === 'running' && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Progress</span>
            <span>{jobData.progress}%</span>
          </div>
          <Progress value={jobData.progress} />
        </div>
      )}

      <div className="text-sm text-gray-600">
        {jobData.message}
      </div>

      {jobData.error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <p className="text-sm text-red-800">{jobData.error}</p>
        </div>
      )}

      <div className="flex space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowLogs(true)}
        >
          View Logs
        </Button>

        {jobData.status === 'completed' && jobData.results && (
          <Button
            variant="outline"
            size="sm"
            onClick={downloadResults}
          >
            <Download className="h-4 w-4 mr-1" />
            Download Results
          </Button>
        )}
      </div>

      <Dialog open={showLogs} onOpenChange={setShowLogs}>
        <DialogContent className="max-w-2xl max-h-96 overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Execution Logs</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <div className="flex justify-end">
              <Button variant="outline" size="sm" onClick={copyLogs}>
                <Copy className="h-4 w-4 mr-1" />
                Copy All
              </Button>
            </div>
            <pre className="bg-gray-100 p-3 rounded text-xs overflow-x-auto">
              {jobData.logs?.join('\n') || 'No logs available'}
            </pre>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}