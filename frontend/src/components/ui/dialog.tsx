import * as React from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

const Dialog = ({ open, onOpenChange, children }: {
  open: boolean
  onOpenChange: (open: boolean) => void
  children: React.ReactNode
}) => {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
      <div className="fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 sm:rounded-lg">
        <button
          onClick={() => onOpenChange(false)}
          className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        >
          <X className="h-4 w-4" />
        </button>
        {children}
      </div>
    </div>
  )
}

const DialogContent = ({ children, className }: {
  children: React.ReactNode
  className?: string
}) => (
  <div className={cn("grid gap-4", className)}>
    {children}
  </div>
)

const DialogHeader = ({ children }: { children: React.ReactNode }) => (
  <div className="flex flex-col space-y-1.5 text-center sm:text-left">
    {children}
  </div>
)

const DialogTitle = ({ children }: { children: React.ReactNode }) => (
  <h3 className="text-lg font-semibold leading-none tracking-tight">
    {children}
  </h3>
)

export { Dialog, DialogContent, DialogHeader, DialogTitle }