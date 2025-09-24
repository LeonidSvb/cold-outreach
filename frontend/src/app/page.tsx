import Link from 'next/link'

interface Tool {
  id: string
  name: string
  description: string
  href: string
  status: 'ready' | 'dev' | 'planned'
  color: string
}

const tools: Tool[] = [
  {
    id: 'script-runner',
    name: 'Script Runner',
    description: 'Execute Python scripts with file uploads and configuration',
    href: '/script-runner',
    status: 'ready',
    color: 'bg-blue-500 hover:bg-blue-600'
  },
  {
    id: 'dashboard',
    name: 'Instantly Dashboard',
    description: 'Analytics and metrics for email campaigns',
    href: '/dashboard',
    status: 'ready',
    color: 'bg-green-500 hover:bg-green-600'
  },
  {
    id: 'components-test',
    name: 'UI Components Test',
    description: 'Test and showcase shadcn/ui components and interactions',
    href: '/components-test',
    status: 'ready',
    color: 'bg-pink-500 hover:bg-pink-600'
  },
  {
    id: 'apollo',
    name: 'Apollo Leads',
    description: 'Lead collection and management from Apollo API',
    href: '/apollo',
    status: 'dev',
    color: 'bg-purple-500 hover:bg-purple-600'
  },
  {
    id: 'openai',
    name: 'AI Processor',
    description: 'OpenAI-powered content analysis and generation',
    href: '/openai',
    status: 'dev',
    color: 'bg-orange-500 hover:bg-orange-600'
  },
  {
    id: 'scraping',
    name: 'Web Scraper',
    description: 'Website content extraction and analysis',
    href: '/scraping',
    status: 'planned',
    color: 'bg-red-500 hover:bg-red-600'
  },
  {
    id: 'sheets',
    name: 'Google Sheets',
    description: 'Spreadsheet data management and automation',
    href: '/sheets',
    status: 'planned',
    color: 'bg-indigo-500 hover:bg-indigo-600'
  }
]

const statusLabels = {
  ready: 'Ready',
  dev: 'Development',
  planned: 'Planned'
}

const statusColors = {
  ready: 'bg-green-100 text-green-800',
  dev: 'bg-yellow-100 text-yellow-800',
  planned: 'bg-gray-100 text-gray-800'
}

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Cold Outreach Platform
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Comprehensive automation platform for lead generation, email campaigns, and analytics
          </p>
        </div>

        {/* Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tools.map((tool) => (
            <div key={tool.id} className="group">
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 h-full transition-all duration-300 hover:shadow-lg hover:scale-105">
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 rounded-lg ${tool.color} flex items-center justify-center transition-colors duration-300`}>
                    <div className="w-6 h-6 bg-white rounded"></div>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[tool.status]}`}>
                    {statusLabels[tool.status]}
                  </span>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {tool.name}
                </h3>
                <p className="text-gray-600 text-sm mb-4 flex-grow">
                  {tool.description}
                </p>

                {tool.status === 'ready' ? (
                  <Link
                    href={tool.href}
                    className={`inline-block w-full text-center px-4 py-2 rounded-lg text-white font-medium transition-colors duration-300 ${tool.color}`}
                  >
                    Open Tool
                  </Link>
                ) : (
                  <button
                    disabled
                    className="w-full px-4 py-2 rounded-lg bg-gray-300 text-gray-500 font-medium cursor-not-allowed"
                  >
                    {tool.status === 'dev' ? 'In Development' : 'Coming Soon'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Stats */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
            <div className="text-2xl font-bold text-blue-600 mb-2">7</div>
            <div className="text-gray-600">Active Modules</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
            <div className="text-2xl font-bold text-green-600 mb-2">3</div>
            <div className="text-gray-600">Ready Tools</div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
            <div className="text-2xl font-bold text-purple-600 mb-2">v7.2.0</div>
            <div className="text-gray-600">Current Version</div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-16 text-center text-gray-500 text-sm">
          <p>Cold Outreach Automation Platform - Built with Next.js & Python</p>
        </div>
      </div>
    </div>
  )
}