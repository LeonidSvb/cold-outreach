'use client'

import { useState } from 'react'
import { Columns, Eye, EyeOff, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export interface ColumnDefinition {
  key: string
  label: string
  alwaysVisible?: boolean
}

interface ColumnVisibilityDropdownProps {
  columns: ColumnDefinition[]
  visibleColumns: Set<string>
  onVisibilityChange: (updates: Set<string>) => void
}

export default function ColumnVisibilityDropdown({
  columns,
  visibleColumns,
  onVisibilityChange,
}: ColumnVisibilityDropdownProps) {
  const [open, setOpen] = useState(false)
  const [pendingChanges, setPendingChanges] = useState<Set<string>>(visibleColumns)

  const visibleCount = columns.filter(col => visibleColumns.has(col.key)).length
  const totalCount = columns.length
  const hasChanges = JSON.stringify(Array.from(pendingChanges).sort()) !== JSON.stringify(Array.from(visibleColumns).sort())

  const handleToggle = (columnKey: string, checked: boolean) => {
    setPendingChanges(prev => {
      const newSet = new Set(prev)
      if (checked) {
        newSet.add(columnKey)
      } else {
        newSet.delete(columnKey)
      }
      return newSet
    })
  }

  const handleApply = () => {
    onVisibilityChange(pendingChanges)
    setOpen(false)
  }

  const handleCancel = () => {
    setPendingChanges(visibleColumns)
    setOpen(false)
  }

  return (
    <DropdownMenu open={open} onOpenChange={(newOpen) => {
      if (!newOpen) {
        setPendingChanges(visibleColumns)
      }
      setOpen(newOpen)
    }}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="h-9 gap-2"
        >
          <Columns className="h-4 w-4" />
          <span className="text-sm">
            Columns ({visibleCount}/{totalCount})
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56" onInteractOutside={(e) => e.preventDefault()}>
        <DropdownMenuLabel className="flex items-center gap-2">
          <Columns className="h-4 w-4" />
          Toggle Columns
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {columns.map((column) => {
          const isVisible = pendingChanges.has(column.key)
          const isDisabled = column.alwaysVisible

          return (
            <DropdownMenuCheckboxItem
              key={column.key}
              checked={isVisible}
              disabled={isDisabled}
              onCheckedChange={(checked) => {
                if (!isDisabled) {
                  handleToggle(column.key, checked)
                }
              }}
              onSelect={(e) => e.preventDefault()}
              className="flex items-center gap-2"
            >
              {isVisible ? (
                <Eye className="h-3 w-3 text-blue-500" />
              ) : (
                <EyeOff className="h-3 w-3 text-gray-400" />
              )}
              <span className={isDisabled ? 'text-gray-500 font-medium' : ''}>
                {column.label}
              </span>
              {isDisabled && (
                <span className="ml-auto text-xs text-gray-400">Always</span>
              )}
            </DropdownMenuCheckboxItem>
          )
        })}

        <DropdownMenuSeparator />

        <div className="p-2 space-y-2">
          <div className="text-xs text-gray-500">
            {pendingChanges.size} of {totalCount} columns will be visible
          </div>

          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={handleCancel}
              className="flex-1 h-8"
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleApply}
              disabled={!hasChanges}
              className="flex-1 h-8 gap-1"
            >
              <Check className="h-3 w-3" />
              Apply
            </Button>
          </div>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
