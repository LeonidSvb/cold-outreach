'use client'

import { useState, useEffect } from 'react'
import { toast } from 'sonner'
import Link from 'next/link'
import { ArrowLeft, Calendar, RefreshCw, TrendingUp, Mail, Target } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'

interface DailyData {
  date: string
  sent: number
  opened: number
  replies: number
  clicks: number
}

interface CampaignData {
  campaign_name: string
  campaign_id: string
  emails_sent_count: number
  reply_count: number
  contacted_count: number
  bounced_count: number
  total_opportunities: number
}

interface DashboardData {
  dailyData: DailyData[]
  campaigns: CampaignData[]
  overview: {
    emails_sent_count: number
    reply_count: number
    open_count: number
    bounced_count: number
    total_opportunities: number
  }
}

export default function InstantlyDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedPeriod, setSelectedPeriod] = useState<string>('all')
  const [selectedCampaigns, setSelectedCampaigns] = useState<string[]>([])

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Simulate API call with potential failure
      if (Math.random() > 0.8) {
        throw new Error('Failed to fetch dashboard data from API')
      }

      // Mock data loading - later we'll replace with real API
      const mockData: DashboardData = {
        dailyData: [
          { date: '2025-08-21', sent: 96, opened: 0, replies: 0, clicks: 0 },
          { date: '2025-08-22', sent: 131, opened: 64, replies: 0, clicks: 0 },
          { date: '2025-08-25', sent: 128, opened: 14, replies: 1, clicks: 0 },
          { date: '2025-08-26', sent: 78, opened: 1, replies: 2, clicks: 0 },
          { date: '2025-08-27', sent: 233, opened: 0, replies: 2, clicks: 0 },
          { date: '2025-08-28', sent: 90, opened: 0, replies: 1, clicks: 0 },
          { date: '2025-08-29', sent: 70, opened: 0, replies: 2, clicks: 0 },
          { date: '2025-09-01', sent: 139, opened: 0, replies: 0, clicks: 0 },
          { date: '2025-09-02', sent: 3, opened: 0, replies: 0, clicks: 0 },
          { date: '2025-09-13', sent: 250, opened: 0, replies: 1, clicks: 0 },
          { date: '2025-09-15', sent: 150, opened: 0, replies: 1, clicks: 0 },
          { date: '2025-09-16', sent: 150, opened: 0, replies: 1, clicks: 0 },
          { date: '2025-09-17', sent: 150, opened: 0, replies: 1, clicks: 0 }
        ],
        campaigns: [
          {
            campaign_name: "Marketing agencies",
            campaign_id: "8ad64aaf-8294-4538-8400-4a99dcf016e8",
            emails_sent_count: 700,
            reply_count: 4,
            contacted_count: 552,
            bounced_count: 18,
            total_opportunities: 0
          },
          {
            campaign_name: "coaches 200 US b2b C-lvl",
            campaign_id: "864e8605-a24e-4881-9e96-8544b912d7e7",
            emails_sent_count: 482,
            reply_count: 7,
            contacted_count: 250,
            bounced_count: 12,
            total_opportunities: 1
          },
          {
            campaign_name: "RealEstate Reactivation System Dubai",
            campaign_id: "23189011-78cc-49db-8e32-da035d1b1135",
            emails_sent_count: 265,
            reply_count: 0,
            contacted_count: 138,
            bounced_count: 10,
            total_opportunities: 1
          },
          {
            campaign_name: "756 - Aus RE 1-10 size 22.08",
            campaign_id: "bfa00ac1-2fe7-4da7-936f-0b93afeedc80",
            emails_sent_count: 221,
            reply_count: 2,
            contacted_count: 221,
            bounced_count: 20,
            total_opportunities: 0
          }
        ],
        overview: {
          emails_sent_count: 1668,
          reply_count: 13,
          open_count: 82,
          bounced_count: 60,
          total_opportunities: 2
        }
      }

      setData(mockData)
      // Initialize with all campaigns selected
      setSelectedCampaigns(mockData.campaigns.map(c => c.campaign_id))
      toast.success('Dashboard data loaded successfully')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      setError(errorMessage)
      toast.error(`Failed to load dashboard: ${errorMessage}`)
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getFilteredData = () => {
    if (!data) return { dailyData: [], campaigns: [] }

    const now = new Date()
    let startDate = new Date(0) // All time by default

    switch (selectedPeriod) {
      case 'week':
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        break
      case 'month':
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
        break
      case 'all':
      default:
        startDate = new Date(0)
        break
    }

    const filteredDailyData = data.dailyData.filter(day =>
      new Date(day.date) >= startDate
    )

    const filteredCampaigns = data.campaigns.filter(campaign =>
      selectedCampaigns.includes(campaign.campaign_id)
    )

    return { dailyData: filteredDailyData, campaigns: filteredCampaigns }
  }

  const toggleCampaign = (campaignId: string) => {
    setSelectedCampaigns(prev =>
      prev.includes(campaignId)
        ? prev.filter(id => id !== campaignId)
        : [...prev, campaignId]
    )
  }

  const selectAllCampaigns = () => {
    if (!data) return
    setSelectedCampaigns(data.campaigns.map(c => c.campaign_id))
  }

  const deselectAllCampaigns = () => {
    setSelectedCampaigns([])
  }

  const { dailyData: filteredDailyData, campaigns: filteredCampaigns } = getFilteredData()

  const totalSent = filteredDailyData.reduce((sum, day) => sum + day.sent, 0)
  const totalReplies = filteredCampaigns.reduce((sum, campaign) => sum + campaign.reply_count, 0)
  const avgReplyRate = totalSent > 0 ? ((totalReplies / totalSent) * 100).toFixed(2) : '0.00'

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <Alert className="border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive">
            <AlertDescription className="text-sm">
              {error}
            </AlertDescription>
          </Alert>
          <div className="mt-4 text-center">
            <Button onClick={loadDashboardData} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Try Again
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Mail className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Instantly Analytics</h1>
                <p className="text-sm text-muted-foreground">Email campaign performance</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <Link href="/">
                <Button variant="outline" size="sm">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
              </Link>
              <Button onClick={loadDashboardData} disabled={loading} size="sm">
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Controls */}
        <div className="flex flex-col lg:flex-row gap-4 mb-8">
          {/* Time Period Filter */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Time Period</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                <SelectTrigger>
                  <Calendar className="w-4 h-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="week">Last 7 days</SelectItem>
                  <SelectItem value="month">Last 30 days</SelectItem>
                  <SelectItem value="all">All time</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* Campaign Filter */}
          <Card className="flex-1">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Campaigns</CardTitle>
                <div className="space-x-2">
                  <Button variant="ghost" size="sm" onClick={selectAllCampaigns}>
                    All
                  </Button>
                  <Button variant="ghost" size="sm" onClick={deselectAllCampaigns}>
                    None
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {data?.campaigns.map(campaign => (
                  <Badge
                    key={campaign.campaign_id}
                    variant={selectedCampaigns.includes(campaign.campaign_id) ? "default" : "outline"}
                    className="cursor-pointer"
                    onClick={() => toggleCampaign(campaign.campaign_id)}
                  >
                    {campaign.campaign_name}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Mail className="w-5 h-5 text-blue-500" />
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Emails Sent</p>
                  <p className="text-2xl font-bold">{totalSent.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Replies</p>
                  <p className="text-2xl font-bold">{totalReplies}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <Target className="w-5 h-5 text-purple-500" />
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Reply Rate</p>
                  <p className="text-2xl font-bold">{avgReplyRate}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Daily Timeline Chart */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Daily Email Activity</CardTitle>
            <CardDescription>
              Email sending volume over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={filteredDailyData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="date"
                    className="text-xs"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis className="text-xs" tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="sent"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    name="Emails Sent"
                  />
                  <Line
                    type="monotone"
                    dataKey="replies"
                    stroke="hsl(var(--chart-2))"
                    strokeWidth={2}
                    name="Replies"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Campaigns Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle>Campaign Performance</CardTitle>
            <CardDescription>
              Performance breakdown by campaign
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80 mb-6">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={filteredCampaigns}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="campaign_name"
                    className="text-xs"
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={80}
                  />
                  <YAxis className="text-xs" tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar
                    dataKey="emails_sent_count"
                    fill="hsl(var(--primary))"
                    name="Emails Sent"
                  />
                  <Bar
                    dataKey="reply_count"
                    fill="hsl(var(--chart-2))"
                    name="Replies"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Campaign Details Table */}
            <div className="space-y-4">
              {filteredCampaigns.map(campaign => (
                <div key={campaign.campaign_id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{campaign.campaign_name}</h3>
                    <Badge variant="outline">
                      {((campaign.reply_count / campaign.emails_sent_count) * 100).toFixed(2)}% reply rate
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Sent:</span>
                      <div className="font-medium">{campaign.emails_sent_count.toLocaleString()}</div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Replies:</span>
                      <div className="font-medium">{campaign.reply_count}</div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Contacted:</span>
                      <div className="font-medium">{campaign.contacted_count.toLocaleString()}</div>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Opportunities:</span>
                      <div className="font-medium">{campaign.total_opportunities}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}