'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { CalendarDays, TrendingUp, Mail, Users, Target, RefreshCw, ArrowLeft, Play } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import TimelineSelector from '@/components/dashboard/TimelineSelector'
import MetricsOverview from '@/components/dashboard/MetricsOverview'
import TimelineChart from '@/components/dashboard/TimelineChart'
import CampaignBreakdown from '@/components/dashboard/CampaignBreakdown'
import SyncStatus from '@/components/dashboard/SyncStatus'

interface DashboardData {
  summary: {
    totalEmailsSent: number
    replyRate: number
    realReplyRate: number
    positiveReplyRate: number
    activeAccounts: number
    activeCampaigns: number
    bounceRate: number
    opportunityRate: number
  }
  campaigns: any[]
  dailyData: any[]
  lastSync: string
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedPeriod, setSelectedPeriod] = useState<string>('7days')
  const [customDateRange, setCustomDateRange] = useState<{start: string, end: string} | null>(null)
  const [syncing, setSyncing] = useState(false)

  useEffect(() => {
    fetchDashboardData()
  }, [selectedPeriod, customDateRange])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      // Calculate date range based on selected period
      const { startDate, endDate } = getDateRange(selectedPeriod, customDateRange)

      // Fetch real data from API
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_DASHBOARD_API_URL || 'http://localhost:8002'}/api/dashboard-data?start_date=${startDate}&end_date=${endDate}`
      )

      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data')
      }

      const result = await response.json()

      if (result.success) {
        const apiData = result.data

        // Transform API data to match our interface
        const transformedData: DashboardData = {
          summary: apiData.summary || generateMockSummary(),
          campaigns: apiData.campaigns || [],
          dailyData: apiData.daily_trends?.length ? apiData.daily_trends : generateMockDailyData(startDate, endDate),
          lastSync: apiData.metadata?.generated_at || new Date().toISOString()
        }

        setData(transformedData)
      } else {
        throw new Error('API returned error')
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)

      // Fallback to mock data if API fails
      const mockData: DashboardData = {
        summary: generateMockSummary(),
        campaigns: [
          { id: '1', name: 'AI Agencies B2B', sent: 850, replies: 24, opportunities: 3 },
          { id: '2', name: 'Marketing Coaches US', sent: 720, replies: 18, opportunities: 5 },
          { id: '3', name: 'SaaS Companies CA', sent: 580, replies: 12, opportunities: 2 }
        ],
        dailyData: generateMockDailyData(getDateRange(selectedPeriod, customDateRange).startDate, getDateRange(selectedPeriod, customDateRange).endDate),
        lastSync: new Date().toISOString()
      }

      setData(mockData)
    } finally {
      setLoading(false)
    }
  }

  const getDateRange = (period: string, customRange: {start: string, end: string} | null) => {
    const today = new Date()
    let startDate = ''
    let endDate = today.toISOString().split('T')[0]

    if (period === 'custom' && customRange) {
      return { startDate: customRange.start, endDate: customRange.end }
    }

    switch (period) {
      case 'today':
        startDate = endDate
        break
      case 'yesterday':
        const yesterday = new Date(today)
        yesterday.setDate(yesterday.getDate() - 1)
        startDate = endDate = yesterday.toISOString().split('T')[0]
        break
      case '7days':
        const week = new Date(today)
        week.setDate(week.getDate() - 7)
        startDate = week.toISOString().split('T')[0]
        break
      case '2weeks':
        const twoWeeks = new Date(today)
        twoWeeks.setDate(twoWeeks.getDate() - 14)
        startDate = twoWeeks.toISOString().split('T')[0]
        break
      case '30days':
        const month = new Date(today)
        month.setDate(month.getDate() - 30)
        startDate = month.toISOString().split('T')[0]
        break
      case '3months':
        const threeMonths = new Date(today)
        threeMonths.setDate(threeMonths.getDate() - 90)
        startDate = threeMonths.toISOString().split('T')[0]
        break
      case 'all':
        const allTime = new Date(today)
        allTime.setFullYear(allTime.getFullYear() - 1)
        startDate = allTime.toISOString().split('T')[0]
        break
      default:
        const defaultPeriod = new Date(today)
        defaultPeriod.setDate(defaultPeriod.getDate() - 7)
        startDate = defaultPeriod.toISOString().split('T')[0]
    }

    return { startDate, endDate }
  }

  const generateMockSummary = () => ({
    totalEmailsSent: 2150,
    replyRate: 2.8,
    realReplyRate: 1.4,
    positiveReplyRate: 0.6,
    activeAccounts: 5,
    activeCampaigns: 4,
    bounceRate: 3.2,
    opportunityRate: 0.4
  })

  const handleSync = async () => {
    setSyncing(true)
    try {
      const { startDate, endDate } = getDateRange(selectedPeriod, customDateRange)

      // Call real sync API
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_DASHBOARD_API_URL || 'http://localhost:8002'}/api/sync`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            start_date: startDate,
            end_date: endDate,
            force: false
          })
        }
      )

      if (response.ok) {
        // Wait for sync to complete, then refresh data
        await new Promise(resolve => setTimeout(resolve, 2000))
        await fetchDashboardData()
      } else {
        throw new Error('Sync request failed')
      }
    } catch (error) {
      console.error('Sync failed:', error)
      // Still refresh data in case of error
      await fetchDashboardData()
    } finally {
      setSyncing(false)
    }
  }

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200/50 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
                  Instantly Analytics
                </h1>
                <p className="text-sm text-gray-500">Real-time campaign performance</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <SyncStatus lastSync={data?.lastSync} />
              <Link href="/">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Scripts
                </Button>
              </Link>
              <Button
                onClick={handleSync}
                disabled={syncing}
                size="sm"
                className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Sync Data'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Timeline Selector */}
        <div className="mb-8">
          <TimelineSelector
            selectedPeriod={selectedPeriod}
            onPeriodChange={setSelectedPeriod}
            customDateRange={customDateRange}
            onCustomDateChange={setCustomDateRange}
          />
        </div>

        {/* Metrics Overview */}
        {data && (
          <div className="mb-8">
            <MetricsOverview metrics={data.summary} loading={loading} />
          </div>
        )}

        {/* Charts Section */}
        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Timeline Chart */}
          <Card className="lg:col-span-2 bg-white/80 backdrop-blur-sm border-gray-200/50 shadow-xl">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl font-semibold flex items-center space-x-2">
                <CalendarDays className="w-5 h-5 text-blue-500" />
                <span>Performance Timeline</span>
              </CardTitle>
              <CardDescription>
                Email performance metrics over time with detailed intervals
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data && (
                <TimelineChart
                  data={data.dailyData}
                  period={selectedPeriod}
                  loading={loading}
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Campaign Breakdown */}
        <div className="mb-8">
          <Card className="bg-white/80 backdrop-blur-sm border-gray-200/50 shadow-xl">
            <CardHeader>
              <CardTitle className="text-xl font-semibold flex items-center space-x-2">
                <Target className="w-5 h-5 text-purple-500" />
                <span>Campaign Breakdown</span>
              </CardTitle>
              <CardDescription>
                Individual campaign performance with interactive controls
              </CardDescription>
            </CardHeader>
            <CardContent>
              {data && (
                <CampaignBreakdown
                  campaigns={data.campaigns}
                  dailyData={data.dailyData}
                  loading={loading}
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function generateMockDailyData(startDate?: string, endDate?: string) {
  const data = []
  const end = endDate ? new Date(endDate) : new Date()
  const start = startDate ? new Date(startDate) : new Date(end.getTime() - 29 * 24 * 60 * 60 * 1000)

  const diffTime = Math.abs(end.getTime() - start.getTime())
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  for (let i = diffDays; i >= 0; i--) {
    const date = new Date(end)
    date.setDate(date.getDate() - i)

    data.push({
      date: date.toISOString().split('T')[0],
      emailsSent: Math.floor(Math.random() * 100) + 50,
      replies: Math.floor(Math.random() * 8) + 1,
      opens: Math.floor(Math.random() * 40) + 20,
      clicks: Math.floor(Math.random() * 15) + 5,
      bounces: Math.floor(Math.random() * 5) + 1,
      opportunities: Math.floor(Math.random() * 3)
    })
  }

  return data
}