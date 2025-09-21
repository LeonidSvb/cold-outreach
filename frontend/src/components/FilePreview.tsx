'use client'

import { useState, useEffect } from 'react'
import { FileText, Eye, Users, Columns } from 'lucide-react'

interface FilePreviewProps {
  file: File | null
}

interface CsvData {
  headers: string[]
  rows: string[][]
  totalRows: number
  totalColumns: number
}

export default function FilePreview({ file }: FilePreviewProps) {
  const [csvData, setCsvData] = useState<CsvData | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (file && file.type === 'text/csv') {
      parseCSV(file)
    } else {
      setCsvData(null)
    }
  }, [file])

  const parseCSV = async (csvFile: File) => {
    setLoading(true)
    try {
      const text = await csvFile.text()
      const lines = text.split('\n').filter(line => line.trim())

      if (lines.length === 0) {
        setCsvData(null)
        return
      }

      const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim())
      const dataRows = lines.slice(1)

      // Get first 20 data rows for preview
      const previewRows = dataRows.slice(0, 20).map(line =>
        line.split(',').map(cell => cell.replace(/"/g, '').trim())
      )

      setCsvData({
        headers,
        rows: previewRows,
        totalRows: dataRows.length,
        totalColumns: headers.length
      })
    } catch (error) {
      console.error('Error parsing CSV:', error)
      setCsvData(null)
    } finally {
      setLoading(false)
    }
  }

  if (!file) {
    return null
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center space-x-2 mb-4">
          <FileText className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-medium text-gray-900">File Preview</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <div className="h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-2 text-gray-600">Parsing CSV file...</span>
        </div>
      </div>
    )
  }

  if (!csvData) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center space-x-2 mb-4">
          <FileText className="h-5 w-5 text-gray-500" />
          <h3 className="text-lg font-medium text-gray-900">File Info</h3>
        </div>
        <div className="text-sm text-gray-600">
          <p><strong>Name:</strong> {file.name}</p>
          <p><strong>Size:</strong> {(file.size / 1024).toFixed(1)} KB</p>
          <p><strong>Type:</strong> {file.type || 'Unknown'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border p-6">
      <div className="flex items-center space-x-2 mb-4">
        <Eye className="h-5 w-5 text-blue-500" />
        <h3 className="text-lg font-medium text-gray-900">File Preview</h3>
      </div>

      {/* File Statistics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <Users className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Total Rows</span>
          </div>
          <p className="text-2xl font-bold text-blue-600">{csvData.totalRows}</p>
        </div>

        <div className="bg-green-50 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <Columns className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-900">Columns</span>
          </div>
          <p className="text-2xl font-bold text-green-600">{csvData.totalColumns}</p>
        </div>

        <div className="bg-purple-50 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <FileText className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-900">File Size</span>
          </div>
          <p className="text-2xl font-bold text-purple-600">{(file.size / 1024).toFixed(1)} KB</p>
        </div>
      </div>

      {/* CSV Table Preview */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">
          First {Math.min(csvData.rows.length, 20)} rows preview:
        </h4>

        <div className="overflow-x-auto border rounded-lg">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  #
                </th>
                {csvData.headers.map((header, index) => (
                  <th
                    key={index}
                    className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {csvData.rows.map((row, rowIndex) => (
                <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-3 py-2 text-xs text-gray-500 font-mono">
                    {rowIndex + 1}
                  </td>
                  {row.map((cell, cellIndex) => (
                    <td
                      key={cellIndex}
                      className="px-3 py-2 text-sm text-gray-900 max-w-xs truncate"
                      title={cell}
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {csvData.totalRows > 20 && (
          <p className="text-xs text-gray-500 mt-2">
            Showing first 20 rows out of {csvData.totalRows} total rows
          </p>
        )}
      </div>

      {/* Column Headers Info */}
      <div className="bg-gray-50 rounded p-3">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Detected Columns:</h4>
        <div className="flex flex-wrap gap-1">
          {csvData.headers.map((header, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            >
              {header}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}