'use client'

import { TrendingUp, TrendingDown, Mail, Users, Target, MessageCircle, AlertTriangle, Award } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface MetricsOverviewProps {
  metrics: {
    totalEmailsSent: number
    replyRate: number
    realReplyRate: number
    positiveReplyRate: number
    activeAccounts: number
    activeCampaigns: number
    bounceRate: number
    opportunityRate: number
  }
  loading?: boolean
}

export default function MetricsOverview({ metrics, loading }: MetricsOverviewProps) {
  const metricCards = [
    {
      title: 'Total Emails Sent',
      value: metrics.totalEmailsSent.toLocaleString(),
      icon: Mail,
      color: 'blue',
      gradient: 'from-blue-500 to-blue-600',
      description: 'Total outreach volume'
    },
    {
      title: 'Reply Rate',
      value: `${metrics.replyRate}%`,
      icon: MessageCircle,
      color: 'green',
      gradient: 'from-green-500 to-green-600',
      description: 'All responses received'
    },
    {
      title: 'Real Reply Rate',
      value: `${metrics.realReplyRate}%`,
      icon: TrendingUp,
      color: 'emerald',
      gradient: 'from-emerald-500 to-emerald-600',
      description: 'Excluding auto-replies'
    },
    {
      title: 'Positive Rate',
      value: `${metrics.positiveReplyRate}%`,
      icon: Award,
      color: 'yellow',
      gradient: 'from-yellow-500 to-yellow-600',
      description: 'Interested prospects'
    },
    {
      title: 'Active Campaigns',
      value: metrics.activeCampaigns.toString(),
      icon: Target,
      color: 'purple',
      gradient: 'from-purple-500 to-purple-600',
      description: 'Running campaigns'
    },
    {
      title: 'Active Accounts',
      value: metrics.activeAccounts.toString(),
      icon: Users,
      color: 'indigo',
      gradient: 'from-indigo-500 to-indigo-600',
      description: 'Email accounts sending'
    },
    {
      title: 'Bounce Rate',
      value: `${metrics.bounceRate}%`,
      icon: AlertTriangle,
      color: 'red',
      gradient: 'from-red-500 to-red-600',
      description: 'Delivery failures'
    },
    {
      title: 'Opportunity Rate',
      value: `${metrics.opportunityRate}%`,
      icon: TrendingUp,
      color: 'pink',
      gradient: 'from-pink-500 to-pink-600',
      description: 'Qualified leads'
    }
  ]

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 8 }).map((_, i) => (
          <Card key={i} className="bg-white/80 backdrop-blur-sm border-gray-200/50">
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-10 h-10 bg-gray-200 rounded-lg"></div>
                  <div className="h-4 bg-gray-200 rounded w-24"></div>
                </div>
                <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-20"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {metricCards.map((metric, index) => {
        const Icon = metric.icon

        return (
          <Card
            key={metric.title}
            className="bg-white/80 backdrop-blur-sm border-gray-200/50 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 group"
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 bg-gradient-to-r ${metric.gradient} rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>

                {/* Trend indicator - could be made dynamic with real data */}
                <div className="flex items-center space-x-1 text-xs">
                  {index % 3 === 0 ? (
                    <>
                      <TrendingUp className="w-3 h-3 text-green-500" />
                      <span className="text-green-600 font-medium">+{(Math.random() * 10 + 1).toFixed(1)}%</span>
                    </>
                  ) : index % 3 === 1 ? (
                    <>
                      <TrendingDown className="w-3 h-3 text-red-500" />
                      <span className="text-red-600 font-medium">-{(Math.random() * 5 + 1).toFixed(1)}%</span>
                    </>
                  ) : (
                    <span className="text-gray-400 font-medium">—</span>
                  )}
                </div>
              </div>

              <div className="space-y-1">
                <p className="text-sm font-medium text-gray-600 leading-tight">
                  {metric.title}
                </p>
                <p className="text-2xl font-bold text-gray-900 tracking-tight">
                  {metric.value}
                </p>
                <p className="text-xs text-gray-500">
                  {metric.description}
                </p>
              </div>

              {/* Progress bar for percentage metrics */}
              {metric.value.includes('%') && (
                <div className="mt-4">
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className={`bg-gradient-to-r ${metric.gradient} h-1.5 rounded-full transition-all duration-1000`}
                      style={{
                        width: `${Math.min(parseFloat(metric.value) * 10, 100)}%`
                      }}
                    ></div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}