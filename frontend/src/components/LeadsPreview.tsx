'use client'

import { useState, useEffect } from 'react'
import { FileText, Eye, Users, Columns } from 'lucide-react'
import ColumnVisibilityDropdown, { ColumnDefinition } from './ColumnVisibilityDropdown'

interface LeadsPreviewProps {
  uploadBatchId?: number | null
  limit?: number
}

interface Lead {
  id: string
  email: string
  first_name: string
  last_name: string | null
  phone: string | null
  company_name: string | null
  job_title: string | null
  city: string | null
  state: string | null
  country: string | null
  linkedin_url: string | null
  uploaded_at: string
  upload_batch_id: string
}

interface LeadsData {
  success: boolean
  leads: Lead[]
  total: number
  upload_batch_id?: string
}

// Column definitions
const COLUMN_DEFINITIONS: ColumnDefinition[] = [
  { key: 'name', label: 'Name', alwaysVisible: true },
  { key: 'email', label: 'Email', alwaysVisible: true },
  { key: 'company_name', label: 'Company', alwaysVisible: true },
  { key: 'job_title', label: 'Title' },
  { key: 'phone', label: 'Phone' },
  { key: 'location', label: 'Location' },
  { key: 'linkedin_url', label: 'LinkedIn' },
  { key: 'country', label: 'Country' },
  { key: 'state', label: 'State' },
  { key: 'city', label: 'City' },
]

const DEFAULT_VISIBLE_COLUMNS = new Set([
  'name',
  'email',
  'company_name',
  'job_title',
  'phone',
  'location',
])

export default function LeadsPreview({ uploadBatchId, limit = 100 }: LeadsPreviewProps) {
  const [leadsData, setLeadsData] = useState<LeadsData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [visibleColumns, setVisibleColumns] = useState<Set<string>>(DEFAULT_VISIBLE_COLUMNS)

  // Load column preferences from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('leadsColumnVisibility')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setVisibleColumns(new Set(parsed))
      } catch (e) {
        console.error('Failed to parse column visibility preferences', e)
      }
    }
  }, [])

  useEffect(() => {
    fetchLeads()
  }, [uploadBatchId, limit])

  const fetchLeads = async () => {
    setLoading(true)
    setError(null)

    try {
      let url = `/api/leads?limit=${limit}`
      if (uploadBatchId) {
        url += `&upload_batch_id=${uploadBatchId}`
      }

      const response = await fetch(url)
      const data = await response.json()

      if (!data.success) {
        throw new Error(data.error || 'Failed to load leads')
      }

      setLeadsData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load leads')
      setLeadsData(null)
    } finally {
      setLoading(false)
    }
  }

  const handleColumnVisibilityChange = (updates: Set<string>) => {
    setVisibleColumns(updates)

    // Save to localStorage
    localStorage.setItem('leadsColumnVisibility', JSON.stringify(Array.from(updates)))
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-center py-8">
          <div className="h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="ml-2 text-gray-600">Loading leads...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg border p-6">
        <div className="text-center py-8">
          <p className="text-red-500">Error: {error}</p>
        </div>
      </div>
    )
  }

  if (!leadsData || leadsData.leads.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-8 text-center">
        <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">No leads found</p>
      </div>
    )
  }

  const leads = leadsData.leads

  return (
    <div className="bg-white rounded-lg border p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Eye className="h-5 w-5 text-blue-500" />
          <h3 className="text-lg font-medium text-gray-900">Leads Preview</h3>
        </div>
        <ColumnVisibilityDropdown
          columns={COLUMN_DEFINITIONS}
          visibleColumns={visibleColumns}
          onVisibilityChange={handleColumnVisibilityChange}
        />
      </div>

      <div className="mb-6">
        <h4 className="font-medium text-gray-900">Database Leads</h4>
        <p className="text-sm text-gray-500">
          Showing {leads.length} of {leadsData.total} total leads
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <Users className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Total Leads</span>
          </div>
          <p className="text-2xl font-bold text-blue-600">{leadsData.total}</p>
        </div>

        <div className="bg-green-50 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <Columns className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-900">With Phone</span>
          </div>
          <p className="text-2xl font-bold text-green-600">
            {leads.filter(l => l.phone).length}
          </p>
        </div>

        <div className="bg-purple-50 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <Columns className="h-4 w-4 text-purple-600" />
            <span className="text-sm font-medium text-purple-900">With LinkedIn</span>
          </div>
          <p className="text-2xl font-bold text-purple-600">
            {leads.filter(l => l.linkedin_url).length}
          </p>
        </div>
      </div>

      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-gray-700">
            Preview ({leads.length} leads):
          </h4>
        </div>

        <div className="overflow-x-auto border rounded-lg max-h-96">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 sticky top-0">
              <tr>
                {visibleColumns.has('name') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                )}
                {visibleColumns.has('email') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                )}
                {visibleColumns.has('company_name') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Company
                  </th>
                )}
                {visibleColumns.has('job_title') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                )}
                {visibleColumns.has('phone') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Phone
                  </th>
                )}
                {visibleColumns.has('location') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                )}
                {visibleColumns.has('linkedin_url') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    LinkedIn
                  </th>
                )}
                {visibleColumns.has('city') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    City
                  </th>
                )}
                {visibleColumns.has('state') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    State
                  </th>
                )}
                {visibleColumns.has('country') && (
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Country
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {leads.map((lead, index) => (
                <tr key={lead.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  {visibleColumns.has('name') && (
                    <td className="px-3 py-2 text-sm text-gray-900">
                      {lead.first_name} {lead.last_name || ''}
                    </td>
                  )}
                  {visibleColumns.has('email') && (
                    <td className="px-3 py-2 text-sm text-gray-900 max-w-xs truncate" title={lead.email}>
                      {lead.email}
                    </td>
                  )}
                  {visibleColumns.has('company_name') && (
                    <td className="px-3 py-2 text-sm text-gray-900">
                      {lead.company_name || '-'}
                    </td>
                  )}
                  {visibleColumns.has('job_title') && (
                    <td className="px-3 py-2 text-sm text-gray-600">
                      {lead.job_title || '-'}
                    </td>
                  )}
                  {visibleColumns.has('phone') && (
                    <td className="px-3 py-2 text-sm text-gray-600">
                      {lead.phone || '-'}
                    </td>
                  )}
                  {visibleColumns.has('location') && (
                    <td className="px-3 py-2 text-sm text-gray-600">
                      {lead.city ? `${lead.city}, ${lead.state || lead.country}` : '-'}
                    </td>
                  )}
                  {visibleColumns.has('linkedin_url') && (
                    <td className="px-3 py-2 text-sm text-gray-600 max-w-xs truncate">
                      {lead.linkedin_url ? (
                        <a href={lead.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline" title={lead.linkedin_url}>
                          {lead.linkedin_url.replace('https://', '').replace('http://', '')}
                        </a>
                      ) : '-'}
                    </td>
                  )}
                  {visibleColumns.has('city') && (
                    <td className="px-3 py-2 text-sm text-gray-600">
                      {lead.city || '-'}
                    </td>
                  )}
                  {visibleColumns.has('state') && (
                    <td className="px-3 py-2 text-sm text-gray-600">
                      {lead.state || '-'}
                    </td>
                  )}
                  {visibleColumns.has('country') && (
                    <td className="px-3 py-2 text-sm text-gray-600">
                      {lead.country || '-'}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
