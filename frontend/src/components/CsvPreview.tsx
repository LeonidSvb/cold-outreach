'use client'

import { useState, useEffect } from 'react'
import { FileText, Eye, Users, Columns, CheckCircle, Circle } from 'lucide-react'

interface CsvPreviewProps {
  fileId: string | null
}

interface PreviewData {
  columns: string[]
  column_types: Record<string, any>
  rows: Record<string, string>[]
  total_rows: number
  preview_rows: number
}

const COLUMN_TYPES = {
  company_name: { label: 'Company Name', color: 'bg-blue-100 text-blue-800', icon: '🏢' },
  website: { label: 'Website', color: 'bg-green-100 text-green-800', icon: '🌐' },
  email: { label: 'Email', color: 'bg-purple-100 text-purple-800', icon: '📧' },
  phone: { label: 'Phone', color: 'bg-orange-100 text-orange-800', icon: '📞' },
  first_name: { label: 'First Name', color: 'bg-yellow-100 text-yellow-800', icon: '👤' },
  last_name: { label: 'Last Name', color: 'bg-yellow-100 text-yellow-800', icon: '👤' },
  full_name: { label: 'Full Name', color: 'bg-yellow-100 text-yellow-800', icon: '👤' },
  title: { label: 'Title', color: 'bg-indigo-100 text-indigo-800', icon: '💼' }
}

export default function CsvPreview({ fileId }: CsvPreviewProps) {
  const [previewData, setPreviewData] = useState<PreviewData | null>(null)
  const [loading, setLoading] = useState(false)
  const [visibleColumns, setVisibleColumns] = useState<string[]>([])
  const [showAllColumns, setShowAllColumns] = useState(true)

  useEffect(() => {
    if (fileId) {
      fetchPreview(fileId)
    } else {
      setPreviewData(null)
    }
  }, [fileId])

  useEffect(() => {
    if (previewData) {
      // Initialize visible columns - show detected columns by default
      const detectedCols = Object.keys(previewData.column_types).filter(col =>
        ['company', 'website', 'email', 'phone', 'name', 'title', 'location'].includes(previewData.column_types[col]?.type)
      )
      setVisibleColumns(showAllColumns ? previewData.columns : detectedCols)
    }
  }, [previewData, showAllColumns])

  const fetchPreview = async (id: string) => {
    setLoading(true)
    try {
      const response = await fetch(`/api/files/${id}/preview`)
      const data = await response.json()
      setPreviewData(data)
    } catch (error) {
      console.error('Failed to fetch preview:', error)
      setPreviewData(null)
    } finally {
      setLoading(false)
    }
  }

  const getColumnType = (columnName: string) => {
    const columnInfo = previewData?.column_types[columnName]
    if (!columnInfo) return null

    return columnInfo.type as keyof typeof COLUMN_TYPES
  }

  if (!fileId) {
    return (
      <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-8 text-center">
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">Upload a CSV file to see preview</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-center py-8">
          <div className="h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-2 text-gray-600">Loading preview...</span>
        </div>
      </div>
    )
  }

  if (!previewData) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="text-center py-8">
          <p className="text-gray-500">Failed to load file preview</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Eye className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-medium text-gray-900">CSV Preview</h3>
        </div>

        {/* Column Filter Toggle */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAllColumns(!showAllColumns)}
            className="text-sm px-3 py-1 rounded border hover:bg-gray-50"
          >
            {showAllColumns ? 'Show Key Columns Only' : 'Show All Columns'}
          </button>
        </div>
      </div>

      {/* File Info */}
      <div className="mb-6">
        <h4 className="font-medium text-gray-900">CSV File Preview</h4>
        <p className="text-sm text-gray-500">
          {previewData.total_rows} rows with {previewData.columns.length} columns
        </p>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <Users className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Total Rows</span>
          </div>
          <p className="text-2xl font-bold text-blue-600">{previewData.total_rows}</p>
        </div>

        <div className="bg-green-50 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <Columns className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-900">Total Columns</span>
          </div>
          <p className="text-2xl font-bold text-green-600">{previewData.columns.length}</p>
        </div>

        <div className="bg-purple-50 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-900">Detected Types</span>
          </div>
          <p className="text-2xl font-bold text-purple-600">
            {Object.keys(previewData.column_types).filter(col =>
              ['company', 'website', 'email', 'phone', 'name', 'title', 'location'].includes(previewData.column_types[col]?.type)
            ).length}
          </p>
        </div>
      </div>

      {/* Detected Columns */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-700 mb-3">Detected Column Types:</h4>
        <div className="flex flex-wrap gap-2">
          {Object.entries(previewData.column_types).map(([columnName, columnInfo]) => {
            if (!['company', 'website', 'email', 'phone', 'name', 'title', 'location'].includes(columnInfo.type)) return null

            const typeInfo = COLUMN_TYPES[columnInfo.type as keyof typeof COLUMN_TYPES]
            return (
              <div
                key={columnName}
                className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${typeInfo?.color || 'bg-gray-100 text-gray-800'}`}
              >
                <span className="mr-1">{columnInfo.icon || typeInfo?.icon}</span>
                {typeInfo?.label}: {columnName}
              </div>
            )
          })}
          {Object.keys(previewData.column_types).filter(col =>
            ['company', 'website', 'email', 'phone', 'name', 'title', 'location'].includes(previewData.column_types[col]?.type)
          ).length === 0 && (
            <span className="text-sm text-gray-500">No columns detected automatically</span>
          )}
        </div>
      </div>

      {/* Data Table */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-700">
            Preview ({previewData.preview_rows} rows):
          </h4>
          <span className="text-xs text-gray-500">
            Showing {visibleColumns.length} of {previewData.columns.length} columns
          </span>
        </div>

        <div className="overflow-x-auto border rounded-lg max-h-96">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  #
                </th>
                {visibleColumns.map((header) => {
                  const columnType = getColumnType(header)
                  const typeInfo = columnType ? COLUMN_TYPES[columnType] : null

                  return (
                    <th
                      key={header}
                      className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      <div className="flex items-center space-x-1">
                        {typeInfo && <span>{typeInfo.icon}</span>}
                        <span>{header}</span>
                        {columnType && (
                          <CheckCircle className="h-3 w-3 text-green-500" />
                        )}
                      </div>
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {previewData.rows.map((row, rowIndex) => (
                <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-3 py-2 text-xs text-gray-500 font-mono">
                    {rowIndex + 1}
                  </td>
                  {visibleColumns.map((header) => (
                    <td
                      key={header}
                      className="px-3 py-2 text-sm text-gray-900 max-w-xs truncate"
                      title={row[header] || ''}
                    >
                      {row[header] || '-'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="text-xs text-gray-500 mt-2">
          Showing {previewData.preview_rows} rows out of {previewData.total_rows} total rows
        </p>
      </div>

      {/* All Columns List */}
      {!showAllColumns && (
        <div className="bg-gray-50 rounded p-3">
          <h4 className="text-sm font-medium text-gray-700 mb-2">All Columns ({previewData.columns.length}):</h4>
          <div className="flex flex-wrap gap-1">
            {previewData.columns.map((header) => {
              const columnType = getColumnType(header)
              const isVisible = visibleColumns.includes(header)
              const columnInfo = previewData.column_types[header]

              return (
                <span
                  key={header}
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                    columnType
                      ? COLUMN_TYPES[columnType].color
                      : isVisible
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {columnInfo?.icon && (
                    <span className="mr-1">{columnInfo.icon}</span>
                  )}
                  {header}
                  {columnType && <CheckCircle className="h-3 w-3 ml-1" />}
                </span>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}