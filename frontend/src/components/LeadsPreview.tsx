'use client'

import { useState, useEffect } from 'react'
import { FileText, Eye, Users, Columns } from 'lucide-react'

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

export default function LeadsPreview({ uploadBatchId, limit = 100 }: LeadsPreviewProps) {
  const [leadsData, setLeadsData] = useState<LeadsData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Company
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Title
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phone
                </th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Location
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {leads.map((lead, index) => (
                <tr key={lead.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-3 py-2 text-sm text-gray-900">
                    {lead.first_name} {lead.last_name || ''}
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-900 max-w-xs truncate" title={lead.email}>
                    {lead.email}
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-900">
                    {lead.company_name || '-'}
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-600">
                    {lead.job_title || '-'}
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-600">
                    {lead.phone || '-'}
                  </td>
                  <td className="px-3 py-2 text-sm text-gray-600">
                    {lead.city ? `${lead.city}, ${lead.state || lead.country}` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
