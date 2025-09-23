'use client'

import { useState } from 'react'
import { Target, Eye, EyeOff, BarChart3, TrendingUp, Users, Mail, MessageCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface Campaign {
  id?: string
  campaign_id?: string
  name?: string
  campaign_name?: string
  sent?: number
  emails_sent_count?: number
  replies?: number
  reply_count?: number
  opportunities?: number
  total_opportunities?: number
}

interface CampaignBreakdownProps {
  campaigns: Campaign[]
  dailyData: Array<{
    date: string
    [key: string]: any
  }>
  loading?: boolean
}

const CAMPAIGN_COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'
]

export default function CampaignBreakdown({ campaigns, dailyData, loading }: CampaignBreakdownProps) {
  const [viewMode, setViewMode] = useState<'aggregate' | 'individual'>('aggregate')
  const [visibleCampaigns, setVisibleCampaigns] = useState<Set<string>>(
    new Set(campaigns.map(c => c.id || c.campaign_id || ''))
  )

  if (loading || !campaigns.length) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="flex space-x-2 mb-4">
            <div className="h-10 bg-gray-200 rounded w-32"></div>
            <div className="h-10 bg-gray-200 rounded w-32"></div>
          </div>
          <div className="h-64 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const toggleCampaignVisibility = (campaignId: string) => {
    const newVisible = new Set(visibleCampaigns)
    if (newVisible.has(campaignId)) {
      newVisible.delete(campaignId)
    } else {
      newVisible.add(campaignId)
    }
    setVisibleCampaigns(newVisible)
  }

  const getAggregateData = () => {
    return campaigns.reduce(
      (acc, campaign) => ({
        totalSent: acc.totalSent + (campaign.sent || campaign.emails_sent_count || 0),
        totalReplies: acc.totalReplies + (campaign.replies || campaign.reply_count || 0),
        totalOpportunities: acc.totalOpportunities + (campaign.opportunities || campaign.total_opportunities || 0)
      }),
      { totalSent: 0, totalReplies: 0, totalOpportunities: 0 }
    )
  }

  const aggregateData = getAggregateData()

  return (
    <div className="space-y-6">
      {/* View Mode Toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <BarChart3 className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Campaign Performance</h3>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant={viewMode === 'aggregate' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('aggregate')}
            className={`
              transition-all duration-200
              ${viewMode === 'aggregate'
                ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md'
                : 'bg-white/80 hover:bg-white/90'
              }
            `}
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            All Together
          </Button>
          <Button
            variant={viewMode === 'individual' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('individual')}
            className={`
              transition-all duration-200
              ${viewMode === 'individual'
                ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-md'
                : 'bg-white/80 hover:bg-white/90'
              }
            `}
          >
            <Target className="w-4 h-4 mr-2" />
            By Campaign
          </Button>
        </div>
      </div>

      {/* Aggregate View */}
      {viewMode === 'aggregate' && (
        <Card className="bg-gradient-to-br from-blue-50 to-purple-50 border-blue-200/50">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-4 h-4 text-white" />
              </div>
              <span>Combined Performance</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-white/70 rounded-lg">
                <Mail className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">
                  {(aggregateData.totalSent || 0).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600">Total Emails Sent</p>
              </div>
              <div className="text-center p-4 bg-white/70 rounded-lg">
                <MessageCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">
                  {aggregateData.totalReplies || 0}
                </p>
                <p className="text-sm text-gray-600">Total Replies</p>
                <p className="text-xs text-green-600 mt-1">
                  {aggregateData.totalSent > 0 ? (((aggregateData.totalReplies / aggregateData.totalSent) * 100).toFixed(2)) : '0.00'}% rate
                </p>
              </div>
              <div className="text-center p-4 bg-white/70 rounded-lg">
                <TrendingUp className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                <p className="text-2xl font-bold text-gray-900">
                  {aggregateData.totalOpportunities || 0}
                </p>
                <p className="text-sm text-gray-600">Opportunities</p>
                <p className="text-xs text-purple-600 mt-1">
                  {aggregateData.totalSent > 0 ? (((aggregateData.totalOpportunities / aggregateData.totalSent) * 100).toFixed(2)) : '0.00'}% rate
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Individual Campaign View */}
      {viewMode === 'individual' && (
        <div className="space-y-4">
          {/* Campaign Toggle Controls */}
          <div className="bg-white/50 rounded-lg p-4 border border-gray-200/50">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Toggle Campaigns:</h4>
            <div className="flex flex-wrap gap-2">
              {campaigns.map((campaign, index) => {
                const campaignId = campaign.id || campaign.campaign_id || index.toString()
                const isVisible = visibleCampaigns.has(campaignId)
                const color = CAMPAIGN_COLORS[index % CAMPAIGN_COLORS.length]

                return (
                  <Button
                    key={campaignId}
                    variant="outline"
                    size="sm"
                    onClick={() => toggleCampaignVisibility(campaignId)}
                    className={`
                      transition-all duration-200 text-xs
                      ${isVisible
                        ? 'shadow-md border-2'
                        : 'opacity-50 bg-gray-100'
                      }
                    `}
                    style={{
                      borderColor: isVisible ? color : undefined,
                      backgroundColor: isVisible ? `${color}10` : undefined
                    }}
                  >
                    {isVisible ? <Eye className="w-3 h-3 mr-1" /> : <EyeOff className="w-3 h-3 mr-1" />}
                    <div
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ backgroundColor: color }}
                    ></div>
                    {campaign.name}
                  </Button>
                )
              })}
            </div>
          </div>

          {/* Individual Campaign Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {campaigns
              .filter(campaign => visibleCampaigns.has(campaign.id))
              .map((campaign, index) => {
                const color = CAMPAIGN_COLORS[index % CAMPAIGN_COLORS.length]
                const replyRate = ((campaign.replies / campaign.sent) * 100).toFixed(2)
                const opportunityRate = ((campaign.opportunities / campaign.sent) * 100).toFixed(2)

                return (
                  <Card
                    key={campaign.id}
                    className="bg-white/80 backdrop-blur-sm border-gray-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
                  >
                    <CardHeader className="pb-3">
                      <CardTitle className="flex items-center space-x-2 text-base">
                        <div
                          className="w-6 h-6 rounded-full"
                          style={{ backgroundColor: color }}
                        ></div>
                        <span className="truncate">{campaign.name}</span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Emails Sent</span>
                          <span className="font-semibold">{(campaign.sent || campaign.emails_sent_count || 0).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Replies</span>
                          <div className="text-right">
                            <span className="font-semibold">{campaign.replies || campaign.reply_count || 0}</span>
                            <span className="text-xs text-green-600 ml-1">({replyRate.toFixed(1)}%)</span>
                          </div>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-gray-600">Opportunities</span>
                          <div className="text-right">
                            <span className="font-semibold">{campaign.opportunities || campaign.total_opportunities || 0}</span>
                            <span className="text-xs text-purple-600 ml-1">({opportunityRate}%)</span>
                          </div>
                        </div>

                        {/* Performance Bar */}
                        <div className="pt-2">
                          <div className="flex justify-between text-xs text-gray-500 mb-1">
                            <span>Performance</span>
                            <span>{replyRate}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="h-2 rounded-full transition-all duration-1000"
                              style={{
                                backgroundColor: color,
                                width: `${Math.min(parseFloat(replyRate) * 20, 100)}%`
                              }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
          </div>
        </div>
      )}

      {/* Performance Comparison */}
      <Card className="bg-white/80 backdrop-blur-sm border-gray-200/50">
        <CardHeader>
          <CardTitle className="text-lg">Campaign Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {campaigns.map((campaign, index) => {
              const color = CAMPAIGN_COLORS[index % CAMPAIGN_COLORS.length]
              const sent = campaign.sent || campaign.emails_sent_count || 0
              const replies = campaign.replies || campaign.reply_count || 0
              const replyRate = sent > 0 ? (replies / sent) * 100 : 0
              const maxRate = Math.max(...campaigns.map(c => {
                const cSent = c.sent || c.emails_sent_count || 0
                const cReplies = c.replies || c.reply_count || 0
                return cSent > 0 ? (cReplies / cSent) * 100 : 0
              }))

              return (
                <div key={campaign.id || campaign.campaign_id || index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: color }}
                      ></div>
                      <span className="text-sm font-medium">{campaign.name || campaign.campaign_name || 'Unknown Campaign'}</span>
                    </div>
                    <span className="text-sm text-gray-600">{replyRate.toFixed(2)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all duration-1000"
                      style={{
                        backgroundColor: color,
                        width: `${maxRate > 0 ? (replyRate / maxRate) * 100 : 0}%`
                      }}
                    ></div>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}