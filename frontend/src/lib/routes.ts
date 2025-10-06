/**
 * Centralized route constants for the Cold Outreach Platform
 *
 * Use these constants instead of hardcoded strings throughout the application.
 * This ensures consistency and makes refactoring easier.
 *
 * @example
 * import { ROUTES } from '@/lib/routes'
 * <Link href={ROUTES.LEADS}>Go to Leads</Link>
 */

export const ROUTES = {
  // Pages
  HOME: '/',
  LEADS: '/leads',
  DASHBOARD: '/dashboard',
  INSTANTLY_SYNC: '/instantly-sync',
  SCRIPT_RUNNER: '/script-runner',
  COMPONENTS_TEST: '/components-test',

  // API Routes
  API: {
    CSV_UPLOAD: '/api/csv-upload',
    LEADS: '/api/leads',
    UPLOAD_HISTORY: '/api/upload-history',
    SCRIPTS: '/api/scripts',
    RUN_SCRIPT: '/api/run-script',
    UPLOAD: '/api/upload',
    FILE_PREVIEW: (fileId: string) => `/api/files/${fileId}/preview`,
  }
} as const

/**
 * Route metadata for home page cards
 */
export const ROUTE_METADATA = {
  LEADS: {
    id: 'leads',
    name: 'Leads Database',
    description: 'View and manage leads from Supabase with AI column transformation',
    href: ROUTES.LEADS,
    status: 'ready',
    color: 'bg-purple-500 hover:bg-purple-600'
  },
  SCRIPT_RUNNER: {
    id: 'script-runner',
    name: 'Script Runner',
    description: 'Execute Python scripts with file uploads and configuration',
    href: ROUTES.SCRIPT_RUNNER,
    status: 'ready',
    color: 'bg-blue-500 hover:bg-blue-600'
  },
  DASHBOARD: {
    id: 'dashboard',
    name: 'Instantly Dashboard',
    description: 'Analytics and metrics for email campaigns',
    href: ROUTES.DASHBOARD,
    status: 'ready',
    color: 'bg-green-500 hover:bg-green-600'
  },
  INSTANTLY_SYNC: {
    id: 'instantly-sync',
    name: 'Instantly Sync',
    description: 'Sync campaigns and analytics from Instantly API',
    href: ROUTES.INSTANTLY_SYNC,
    status: 'ready',
    color: 'bg-cyan-500 hover:bg-cyan-600'
  },
  COMPONENTS_TEST: {
    id: 'components-test',
    name: 'UI Components Test',
    description: 'Test and showcase shadcn/ui components and interactions',
    href: ROUTES.COMPONENTS_TEST,
    status: 'ready',
    color: 'bg-pink-500 hover:bg-pink-600'
  }
} as const

export type RouteStatus = 'ready' | 'dev' | 'planned'
