'use client'

import { useState } from 'react'
import { TrendingUp, Mail, MessageCircle, MousePointer, Eye, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface TimelineChartProps {
  data: Array<{
    date: string
    emailsSent: number
    replies: number
    opens: number
    clicks: number
    bounces: number
    opportunities: number
  }>
  period: string
  loading?: boolean
}

const METRICS = [
  { key: 'emailsSent', label: 'Emails Sent', color: '#3B82F6', icon: Mail },
  { key: 'replies', label: 'Replies', color: '#10B981', icon: MessageCircle },
  { key: 'opens', label: 'Opens', color: '#8B5CF6', icon: Eye },
  { key: 'clicks', label: 'Clicks', color: '#F59E0B', icon: MousePointer },
  { key: 'bounces', label: 'Bounces', color: '#EF4444', icon: AlertTriangle },
  { key: 'opportunities', label: 'Opportunities', color: '#EC4899', icon: TrendingUp }
]

export default function TimelineChart({ data, period, loading }: TimelineChartProps) {
  const [selectedMetrics, setSelectedMetrics] = useState(['emailsSent', 'replies', 'opens'])
  const [hoveredPoint, setHoveredPoint] = useState<{index: number, metric: string} | null>(null)

  if (loading || !data.length) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="animate-pulse space-y-4 w-full">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
          <div className="flex space-x-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-8 bg-gray-200 rounded w-20"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const toggleMetric = (metricKey: string) => {
    setSelectedMetrics(prev =>
      prev.includes(metricKey)
        ? prev.filter(m => m !== metricKey)
        : [...prev, metricKey]
    )
  }

  // Calculate dimensions and scales
  const width = 800
  const height = 300
  const padding = { top: 20, right: 20, bottom: 40, left: 60 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom

  // Get max values for scaling
  const maxValues = METRICS.reduce((acc, metric) => {
    const values = data.map(d => {
      const value = d[metric.key as keyof typeof d] as number
      return typeof value === 'number' && !isNaN(value) ? value : 0
    }).filter(v => v > 0)

    acc[metric.key] = values.length > 0 ? Math.max(...values) : 1
    return acc
  }, {} as Record<string, number>)

  const getY = (value: number, metricKey: string) => {
    const max = maxValues[metricKey] || 1
    const normalizedValue = typeof value === 'number' && !isNaN(value) ? value : 0
    const result = padding.top + chartHeight - (normalizedValue / max) * chartHeight
    return isNaN(result) ? padding.top + chartHeight : result
  }

  const getX = (index: number) => {
    if (data.length <= 1) return padding.left
    const result = padding.left + (index / (data.length - 1)) * chartWidth
    return isNaN(result) ? padding.left : result
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    if (period === 'today' || period === 'yesterday') {
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else if (period === '7days' || period === '2weeks') {
      return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }
  }

  const createPath = (metricKey: string) => {
    return data.map((point, index) => {
      const x = getX(index)
      const y = getY(point[metricKey as keyof typeof point] as number, metricKey)
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`
    }).join(' ')
  }

  return (
    <div className="space-y-6">
      {/* Metric Toggles */}
      <div className="flex flex-wrap gap-2">
        {METRICS.map((metric) => {
          const Icon = metric.icon
          const isSelected = selectedMetrics.includes(metric.key)

          return (
            <Button
              key={metric.key}
              variant={isSelected ? "default" : "outline"}
              size="sm"
              onClick={() => toggleMetric(metric.key)}
              className={`
                transition-all duration-200 text-xs
                ${isSelected
                  ? 'shadow-md transform scale-105'
                  : 'bg-white/80 hover:bg-white/90 border-gray-200'
                }
              `}
              style={{
                backgroundColor: isSelected ? metric.color : undefined,
                borderColor: isSelected ? metric.color : undefined
              }}
            >
              <Icon className="w-3 h-3 mr-2" />
              {metric.label}
            </Button>
          )
        })}
      </div>

      {/* Chart Container */}
      <div className="relative bg-gradient-to-br from-gray-50 to-white rounded-xl p-4 border border-gray-200/50">
        <svg
          width={width}
          height={height}
          className="overflow-visible"
          viewBox={`0 0 ${width} ${height}`}
        >
          {/* Grid Lines */}
          <defs>
            <pattern id="grid" width="40" height="30" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 30" fill="none" stroke="#f1f5f9" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width={width} height={height} fill="url(#grid)" />

          {/* Y-Axis */}
          <line
            x1={padding.left}
            y1={padding.top}
            x2={padding.left}
            y2={height - padding.bottom}
            stroke="#e2e8f0"
            strokeWidth="2"
          />

          {/* X-Axis */}
          <line
            x1={padding.left}
            y1={height - padding.bottom}
            x2={width - padding.right}
            y2={height - padding.bottom}
            stroke="#e2e8f0"
            strokeWidth="2"
          />

          {/* Data Lines */}
          {selectedMetrics.map((metricKey) => {
            const metric = METRICS.find(m => m.key === metricKey)!
            return (
              <g key={metricKey}>
                {/* Line */}
                <path
                  d={createPath(metricKey)}
                  fill="none"
                  stroke={metric.color}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="drop-shadow-sm"
                />

                {/* Data Points */}
                {data.map((point, index) => {
                  const x = getX(index)
                  const y = getY(point[metricKey as keyof typeof point] as number, metricKey)

                  return (
                    <circle
                      key={index}
                      cx={x}
                      cy={y}
                      r="4"
                      fill={metric.color}
                      stroke="white"
                      strokeWidth="2"
                      className="cursor-pointer hover:r-6 transition-all duration-200 drop-shadow-sm"
                      onMouseEnter={() => setHoveredPoint({ index, metric: metricKey })}
                      onMouseLeave={() => setHoveredPoint(null)}
                    />
                  )
                })}
              </g>
            )
          })}

          {/* X-Axis Labels */}
          {data.map((point, index) => {
            if (index % Math.ceil(data.length / 8) === 0 || index === data.length - 1) {
              const x = getX(index)
              return (
                <text
                  key={index}
                  x={x}
                  y={height - padding.bottom + 20}
                  textAnchor="middle"
                  className="text-xs fill-gray-600"
                >
                  {formatDate(point.date)}
                </text>
              )
            }
            return null
          })}
        </svg>

        {/* Tooltip */}
        {hoveredPoint && (
          <div
            className="absolute bg-white/95 backdrop-blur-sm border border-gray-200 rounded-lg p-3 shadow-xl pointer-events-none z-10"
            style={{
              left: getX(hoveredPoint.index) + 10,
              top: getY(data[hoveredPoint.index][hoveredPoint.metric as keyof typeof data[0]] as number, hoveredPoint.metric) - 10
            }}
          >
            <p className="text-sm font-medium text-gray-900">
              {formatDate(data[hoveredPoint.index].date)}
            </p>
            <div className="space-y-1 mt-1">
              {selectedMetrics.map(metricKey => {
                const metric = METRICS.find(m => m.key === metricKey)!
                const value = data[hoveredPoint.index][metricKey as keyof typeof data[0]]
                return (
                  <div key={metricKey} className="flex items-center space-x-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: metric.color }}
                    ></div>
                    <span className="text-xs text-gray-600">
                      {metric.label}: <span className="font-medium">{value}</span>
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      {/* Chart Stats */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-4 text-center">
        {METRICS.map((metric) => {
          const total = data.reduce((sum, point) =>
            sum + (point[metric.key as keyof typeof point] as number), 0
          )
          const average = total / data.length

          return (
            <div key={metric.key} className="bg-white/50 rounded-lg p-3 border border-gray-200/50">
              <p className="text-xs text-gray-600 mb-1">{metric.label}</p>
              <p className="font-semibold text-gray-900">{Math.round(average)}</p>
              <p className="text-xs text-gray-500">avg/day</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}