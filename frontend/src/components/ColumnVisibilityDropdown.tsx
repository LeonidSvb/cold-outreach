'use client'

import { useState, useEffect } from 'react'
import { Columns, Eye, EyeOff } from 'lucide-react'
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
  onVisibilityChange: (columnKey: string, visible: boolean) => void
}

export default function ColumnVisibilityDropdown({
  columns,
  visibleColumns,
  onVisibilityChange,
}: ColumnVisibilityDropdownProps) {
  const [open, setOpen] = useState(false)

  const visibleCount = columns.filter(col => visibleColumns.has(col.key)).length
  const totalCount = columns.length

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
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
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex items-center gap-2">
          <Columns className="h-4 w-4" />
          Toggle Columns
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        {columns.map((column) => {
          const isVisible = visibleColumns.has(column.key)
          const isDisabled = column.alwaysVisible

          return (
            <DropdownMenuCheckboxItem
              key={column.key}
              checked={isVisible}
              disabled={isDisabled}
              onCheckedChange={(checked) => {
                if (!isDisabled) {
                  onVisibilityChange(column.key, checked)
                }
              }}
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
        <div className="px-2 py-1.5 text-xs text-gray-500">
          {visibleCount} of {totalCount} columns visible
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
