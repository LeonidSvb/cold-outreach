'use client'

import { useState, useEffect } from 'react'
import { Clock, CheckCircle, AlertCircle, RefreshCw, Wifi, WifiOff } from 'lucide-react'

interface SyncStatusProps {
  lastSync?: string
  isOnline?: boolean
}

export default function SyncStatus({ lastSync, isOnline = true }: SyncStatusProps) {
  const [timeAgo, setTimeAgo] = useState('')

  useEffect(() => {
    if (!lastSync) return

    const updateTimeAgo = () => {
      const now = new Date()
      const syncDate = new Date(lastSync)
      const diffInMinutes = Math.floor((now.getTime() - syncDate.getTime()) / 60000)

      if (diffInMinutes < 1) {
        setTimeAgo('Just now')
      } else if (diffInMinutes < 60) {
        setTimeAgo(`${diffInMinutes}m ago`)
      } else if (diffInMinutes < 1440) {
        const hours = Math.floor(diffInMinutes / 60)
        setTimeAgo(`${hours}h ago`)
      } else {
        const days = Math.floor(diffInMinutes / 1440)
        setTimeAgo(`${days}d ago`)
      }
    }

    updateTimeAgo()
    const interval = setInterval(updateTimeAgo, 60000) // Update every minute

    return () => clearInterval(interval)
  }, [lastSync])

  const getSyncStatus = () => {
    if (!lastSync) {
      return { status: 'never', color: 'gray', icon: AlertCircle, label: 'Never synced' }
    }

    const now = new Date()
    const syncDate = new Date(lastSync)
    const diffInMinutes = Math.floor((now.getTime() - syncDate.getTime()) / 60000)

    if (diffInMinutes < 5) {
      return { status: 'fresh', color: 'green', icon: CheckCircle, label: 'Up to date' }
    } else if (diffInMinutes < 60) {
      return { status: 'recent', color: 'blue', icon: Clock, label: 'Recently synced' }
    } else {
      return { status: 'stale', color: 'yellow', icon: AlertCircle, label: 'Needs update' }
    }
  }

  const syncStatus = getSyncStatus()
  const Icon = syncStatus.icon

  const getStatusColors = () => {
    switch (syncStatus.status) {
      case 'fresh':
        return {
          bg: 'bg-green-50',
          border: 'border-green-200',
          text: 'text-green-700',
          icon: 'text-green-500'
        }
      case 'recent':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-700',
          icon: 'text-blue-500'
        }
      case 'stale':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-700',
          icon: 'text-yellow-500'
        }
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-700',
          icon: 'text-gray-500'
        }
    }
  }

  const colors = getStatusColors()

  return (
    <div className={`
      inline-flex items-center space-x-2 px-3 py-1.5 rounded-full text-sm
      ${colors.bg} ${colors.border} ${colors.text} border
      transition-all duration-200 hover:shadow-sm
    `}>
      {/* Online/Offline Indicator */}
      <div className="flex items-center space-x-1">
        {isOnline ? (
          <Wifi className="w-3 h-3 text-green-500" />
        ) : (
          <WifiOff className="w-3 h-3 text-red-500" />
        )}
      </div>

      {/* Sync Status */}
      <div className="flex items-center space-x-1">
        <Icon className={`w-4 h-4 ${colors.icon}`} />
        <span className="font-medium">{syncStatus.label}</span>
      </div>

      {/* Time Ago */}
      {timeAgo && (
        <>
          <div className={`w-1 h-1 rounded-full ${colors.icon.replace('text-', 'bg-')}`}></div>
          <span className="text-xs opacity-75">{timeAgo}</span>
        </>
      )}
    </div>
  )
}