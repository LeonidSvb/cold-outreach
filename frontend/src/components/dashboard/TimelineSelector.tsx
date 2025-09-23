'use client'

import { useState } from 'react'
import { Calendar, Clock, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'

interface TimelineSelectorProps {
  selectedPeriod: string
  onPeriodChange: (period: string) => void
  customDateRange?: { start: string; end: string } | null
  onCustomDateChange?: (range: { start: string; end: string }) => void
}

const TIME_PERIODS = [
  { id: 'today', label: 'Today', description: 'Current day' },
  { id: 'yesterday', label: 'Yesterday', description: 'Previous day' },
  { id: '7days', label: 'Last 7 Days', description: 'Previous week' },
  { id: '2weeks', label: 'Last 2 Weeks', description: 'Previous 14 days' },
  { id: '30days', label: 'Last 30 Days', description: 'Previous month' },
  { id: '3months', label: 'Last 3 Months', description: 'Previous 90 days' },
  { id: 'all', label: 'All Time', description: 'Complete history' },
  { id: 'custom', label: 'Custom Range', description: 'Choose dates' }
]

export default function TimelineSelector({
  selectedPeriod,
  onPeriodChange,
  customDateRange,
  onCustomDateChange
}: TimelineSelectorProps) {
  const [showCustomDialog, setShowCustomDialog] = useState(false)
  const [tempDateRange, setTempDateRange] = useState(
    customDateRange || { start: '', end: '' }
  )

  const selectedPeriodInfo = TIME_PERIODS.find(p => p.id === selectedPeriod)

  const handlePeriodSelect = (periodId: string) => {
    if (periodId === 'custom') {
      setShowCustomDialog(true)
    } else {
      onPeriodChange(periodId)
    }
  }

  const handleCustomDateApply = () => {
    if (tempDateRange.start && tempDateRange.end) {
      onCustomDateChange?.(tempDateRange)
      onPeriodChange('custom')
      setShowCustomDialog(false)
    }
  }

  const formatDateRange = () => {
    if (selectedPeriod === 'custom' && customDateRange) {
      const start = new Date(customDateRange.start).toLocaleDateString()
      const end = new Date(customDateRange.end).toLocaleDateString()
      return `${start} - ${end}`
    }
    return selectedPeriodInfo?.description || ''
  }

  return (
    <Card className="bg-white/90 backdrop-blur-sm border-gray-200/50 shadow-lg">
      <CardContent className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          {/* Current Selection Display */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Clock className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedPeriodInfo?.label || 'Select Period'}
                </h3>
                <p className="text-sm text-gray-500">
                  {formatDateRange()}
                </p>
              </div>
            </div>
          </div>

          {/* Period Selection Buttons */}
          <div className="flex flex-wrap gap-2">
            {TIME_PERIODS.map((period) => (
              <Button
                key={period.id}
                variant={selectedPeriod === period.id ? "default" : "outline"}
                size="sm"
                onClick={() => handlePeriodSelect(period.id)}
                className={`
                  transition-all duration-200 text-xs
                  ${selectedPeriod === period.id
                    ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md transform scale-105'
                    : 'bg-white/80 hover:bg-white/90 border-gray-200 text-gray-700 hover:text-gray-900 hover:border-gray-300'
                  }
                `}
              >
                {period.id === 'custom' && <Calendar className="w-3 h-3 mr-1" />}
                {period.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Custom Date Range Dialog */}
        <Dialog open={showCustomDialog} onOpenChange={setShowCustomDialog}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>
                <div className="flex items-center space-x-2">
                  <Calendar className="w-5 h-5 text-blue-500" />
                  <span>Custom Date Range</span>
                </div>
              </DialogTitle>
              <p className="text-sm text-gray-600">
                Select start and end dates for your custom analysis period
              </p>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Start Date</label>
                <Input
                  type="date"
                  value={tempDateRange.start}
                  onChange={(e) => setTempDateRange(prev => ({ ...prev, start: e.target.value }))}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">End Date</label>
                <Input
                  type="date"
                  value={tempDateRange.end}
                  onChange={(e) => setTempDateRange(prev => ({ ...prev, end: e.target.value }))}
                  className="w-full"
                />
              </div>

              <div className="flex space-x-2 pt-4">
                <Button
                  onClick={handleCustomDateApply}
                  disabled={!tempDateRange.start || !tempDateRange.end}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
                >
                  Apply Range
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowCustomDialog(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  )
}