import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Script Runner',
  description: 'Execute and monitor your Python scripts with a web interface',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}