'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

interface SyncResult {
  success: boolean
  campaigns_synced: number
  accounts_synced: number
  daily_synced: number
  errors?: string[]
  message: string
}

interface DBStats {
  campaigns: number
  accounts: number
  daily_analytics: number
  email_events: number
}

interface PreviewSummary {
  campaigns: {
    new: number
    updates: number
    duplicates: number
    total: number
  }
  accounts: {
    new: number
    updates: number
    duplicates: number
    total: number
  }
  daily_analytics: {
    new: number
    updates: number
    duplicates: number
    total: number
  }
}

interface DuplicateItem {
  type: string
  identifier: string
  action: string
}

interface PreviewResponse {
  valid: boolean
  summary: PreviewSummary
  duplicates: DuplicateItem[]
  errors: string[]
}

export default function InstantlySyncPage() {
  const [syncing, setSyncing] = useState(false)
  const [result, setResult] = useState<SyncResult | null>(null)
  const [dbStats, setDbStats] = useState<DBStats>({
    campaigns: 4,
    accounts: 10,
    daily_analytics: 17,
    email_events: 0
  })
  const [lastSync, setLastSync] = useState<string>('2 hours ago')
  const [progress, setProgress] = useState(0)

  // Preview state
  const [preview, setPreview] = useState<PreviewResponse | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [showPreview, setShowPreview] = useState(false)

  useEffect(() => {
    // Simulate progress during sync
    if (syncing) {
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev
          return prev + 10
        })
      }, 300)
      return () => clearInterval(interval)
    } else {
      setProgress(0)
    }
  }, [syncing])

  const handleSyncNow = async () => {
    setSyncing(true)
    setResult(null)
    setProgress(0)

    try {
      const response = await fetch('http://localhost:8002/api/instantly/sync-from-api', {
        method: 'POST'
      })

      const data = await response.json()
      setProgress(100)
      setResult(data)
      setLastSync('Just now')

      // Update stats if successful
      if (data.success) {
        setDbStats({
          campaigns: data.campaigns_synced,
          accounts: data.accounts_synced,
          daily_analytics: data.daily_synced,
          email_events: dbStats.email_events
        })
      }

    } catch (error) {
      setProgress(100)
      setResult({
        success: false,
        campaigns_synced: 0,
        accounts_synced: 0,
        daily_synced: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error'],
        message: 'Sync failed'
      })
    } finally {
      setTimeout(() => setSyncing(false), 500)
    }
  }

  // Step 1: Preview file upload
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    console.log('=== FILE SELECT DEBUG ===')
    console.log('File:', file.name, file.size, 'bytes')

    setSelectedFile(file)
    setSyncing(true)
    setPreview(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      console.log('Fetching preview from backend...')
      const response = await fetch('http://localhost:8002/api/instantly/preview-upload', {
        method: 'POST',
        body: formData
      })

      console.log('Response status:', response.status)
      const data = await response.json()
      console.log('Preview data received:', data)

      setPreview(data)
      setShowPreview(true)
      console.log('Preview state updated, showPreview:', true)

    } catch (error) {
      setPreview({
        valid: false,
        summary: {
          campaigns: { new: 0, updates: 0, duplicates: 0, total: 0 },
          accounts: { new: 0, updates: 0, duplicates: 0, total: 0 },
          daily_analytics: { new: 0, updates: 0, duplicates: 0, total: 0 }
        },
        duplicates: [],
        errors: [error instanceof Error ? error.message : 'Unknown error']
      })
      setShowPreview(true)
    } finally {
      setSyncing(false)
    }
  }

  // Step 2: Confirm upload
  const handleConfirmUpload = async () => {
    if (!selectedFile) return

    setSyncing(true)
    setShowPreview(false)
    setProgress(0)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const response = await fetch('http://localhost:8002/api/instantly/sync-from-file', {
        method: 'POST',
        body: formData
      })

      const data = await response.json()
      setProgress(100)
      setResult(data)
      setLastSync('Just now')
      setPreview(null)
      setSelectedFile(null)

      // Update stats if successful
      if (data.success) {
        setDbStats({
          campaigns: data.campaigns_synced,
          accounts: data.accounts_synced,
          daily_analytics: data.daily_synced,
          email_events: dbStats.email_events
        })
      }

    } catch (error) {
      setProgress(100)
      setResult({
        success: false,
        campaigns_synced: 0,
        accounts_synced: 0,
        daily_synced: 0,
        errors: [error instanceof Error ? error.message : 'Unknown error'],
        message: 'File sync failed'
      })
    } finally {
      setTimeout(() => setSyncing(false), 500)
    }
  }

  // Cancel preview
  const handleCancelPreview = () => {
    setShowPreview(false)
    setPreview(null)
    setSelectedFile(null)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8 space-y-6 max-w-6xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Instantly Sync</h1>
            <p className="text-gray-600 mt-1">
              Synchronize campaign data from Instantly to your database
            </p>
          </div>
          <Badge
            variant="outline"
            className="h-8 px-3 bg-green-50 text-green-700 border-green-200"
          >
            <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
            Connected
          </Badge>
        </div>

        {/* Main Sync Card */}
        <Card className="border-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Data Synchronization</CardTitle>
                <CardDescription className="mt-1">
                  Last sync: {lastSync}
                </CardDescription>
              </div>
              <Button
                onClick={handleSyncNow}
                disabled={syncing}
                size="lg"
                className="min-w-[200px]"
              >
                {syncing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Syncing...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Sync Now
                  </>
                )}
              </Button>
            </div>
          </CardHeader>

          {syncing && (
            <CardContent className="pt-0">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm text-gray-600">
                  <span>Fetching data from Instantly API...</span>
                  <span>{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            </CardContent>
          )}
        </Card>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Campaigns
              </CardTitle>
              <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dbStats.campaigns}</div>
              <p className="text-xs text-gray-500 mt-1">Active campaigns synced</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Email Accounts
              </CardTitle>
              <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dbStats.accounts}</div>
              <p className="text-xs text-gray-500 mt-1">
                <span className="text-green-600 font-medium">5 active</span>
                {' · '}
                <span className="text-gray-400">5 inactive</span>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Daily Analytics
              </CardTitle>
              <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{dbStats.daily_analytics}</div>
              <p className="text-xs text-gray-500 mt-1">Records available</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Email Events
              </CardTitle>
              <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline gap-2">
                <div className="text-2xl font-bold">{dbStats.email_events}</div>
                <Badge variant="destructive" className="text-xs">Missing</Badge>
              </div>
              <p className="text-xs text-gray-500 mt-1">Not synced yet</p>
            </CardContent>
          </Card>
        </div>

        {/* Sync Result */}
        {result && (
          <Alert variant={result.success ? "default" : "destructive"} className="border-2">
            <AlertDescription>
              <div className="flex items-start gap-3">
                {result.success ? (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-green-100">
                    <svg className="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-red-100">
                    <svg className="h-5 w-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </div>
                )}

                <div className="flex-1 space-y-3">
                  <p className="font-semibold text-lg">{result.message}</p>

                  <div className="grid grid-cols-3 gap-6">
                    <div className="space-y-1">
                      <p className="text-sm text-gray-600">Campaigns</p>
                      <p className="text-2xl font-bold">{result.campaigns_synced}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-gray-600">Accounts</p>
                      <p className="text-2xl font-bold">{result.accounts_synced}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-sm text-gray-600">Analytics</p>
                      <p className="text-2xl font-bold">{result.daily_synced}</p>
                    </div>
                  </div>

                  {result.errors && result.errors.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-red-200">
                      <p className="font-semibold text-sm mb-2 text-red-900">Errors occurred:</p>
                      <ul className="space-y-1">
                        {result.errors.map((err, i) => (
                          <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                            <span className="text-red-400 mt-0.5">•</span>
                            <span>{err}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Preview Upload Results */}
        {showPreview && preview && (
          <Card className="border-2 border-blue-200 bg-blue-50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-blue-900">Upload Preview</CardTitle>
                  <CardDescription className="text-blue-700 mt-1">
                    Review changes before confirming upload
                  </CardDescription>
                </div>
                {preview.valid && (
                  <Badge className="bg-blue-600">Ready to upload</Badge>
                )}
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {/* Summary Stats */}
              {preview.valid && (
                <div className="grid grid-cols-3 gap-4">
                  {/* Campaigns */}
                  <div className="bg-white rounded-lg p-4 border border-blue-200">
                    <div className="text-sm font-medium text-gray-600 mb-2">Campaigns</div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">New:</span>
                        <span className="font-bold text-green-600">{preview.summary.campaigns.new}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Updates:</span>
                        <span className="font-bold text-blue-600">{preview.summary.campaigns.updates}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total:</span>
                        <span className="font-bold">{preview.summary.campaigns.total}</span>
                      </div>
                    </div>
                  </div>

                  {/* Accounts */}
                  <div className="bg-white rounded-lg p-4 border border-blue-200">
                    <div className="text-sm font-medium text-gray-600 mb-2">Accounts</div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">New:</span>
                        <span className="font-bold text-green-600">{preview.summary.accounts.new}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Updates:</span>
                        <span className="font-bold text-blue-600">{preview.summary.accounts.updates}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total:</span>
                        <span className="font-bold">{preview.summary.accounts.total}</span>
                      </div>
                    </div>
                  </div>

                  {/* Daily Analytics */}
                  <div className="bg-white rounded-lg p-4 border border-blue-200">
                    <div className="text-sm font-medium text-gray-600 mb-2">Daily Analytics</div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">New:</span>
                        <span className="font-bold text-green-600">{preview.summary.daily_analytics.new}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Updates:</span>
                        <span className="font-bold text-blue-600">{preview.summary.daily_analytics.updates}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total:</span>
                        <span className="font-bold">{preview.summary.daily_analytics.total}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Duplicates Warning */}
              {preview.duplicates && preview.duplicates.length > 0 && (
                <Alert className="bg-yellow-50 border-yellow-200">
                  <AlertDescription>
                    <div className="flex items-start gap-2">
                      <svg className="w-5 h-5 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <div className="flex-1">
                        <p className="font-semibold text-yellow-900 mb-2">
                          {preview.duplicates.length} duplicate(s) will be updated
                        </p>
                        <div className="space-y-1 max-h-40 overflow-y-auto">
                          {preview.duplicates.map((dup, i) => (
                            <div key={i} className="text-sm text-yellow-800 flex items-center gap-2">
                              <Badge variant="outline" className="text-xs">{dup.type}</Badge>
                              <span className="font-mono text-xs">{dup.identifier}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>
              )}

              {/* Errors */}
              {preview.errors && preview.errors.length > 0 && (
                <Alert variant="destructive">
                  <AlertDescription>
                    <div className="space-y-1">
                      {preview.errors.map((err, i) => (
                        <p key={i} className="text-sm">{err}</p>
                      ))}
                    </div>
                  </AlertDescription>
                </Alert>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-2">
                <Button
                  onClick={handleConfirmUpload}
                  disabled={!preview.valid || syncing}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                  size="lg"
                >
                  {syncing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Confirm Upload
                    </>
                  )}
                </Button>
                <Button
                  onClick={handleCancelPreview}
                  disabled={syncing}
                  variant="outline"
                  size="lg"
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Alternative: File Upload */}
        {!showPreview && (
          <Card className="border border-dashed">
            <CardContent className="pt-6">
              <div className="flex items-center justify-center">
                <label className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 cursor-pointer transition-colors">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload JSON file (for manual testing)
                  <input
                    type="file"
                    accept=".json"
                    onChange={handleFileSelect}
                    className="hidden"
                    disabled={syncing}
                  />
                </label>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
