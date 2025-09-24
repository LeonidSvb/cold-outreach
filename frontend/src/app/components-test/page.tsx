'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, Plus, Settings, User, Bell, Search, Filter } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { toast } from 'sonner'

export default function ComponentsTestPage() {
  const [progress, setProgress] = useState(33)
  const [selectedValue, setSelectedValue] = useState('')

  const handleToastTest = () => {
    toast.success('Test notification', {
      description: 'This is a test toast notification using Sonner'
    })
  }

  const handleErrorToast = () => {
    toast.error('Error notification', {
      description: 'This simulates an error message'
    })
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Settings className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">shadcn/ui Components Test</h1>
                <p className="text-sm text-muted-foreground">Testing various UI components</p>
              </div>
            </div>

            <Link href="/">
              <Button variant="outline" size="sm">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
            </Link>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Buttons Section */}
        <Card>
          <CardHeader>
            <CardTitle>Buttons & Actions</CardTitle>
            <CardDescription>Various button variants and states</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              <Button>Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="link">Link</Button>
              <Button variant="destructive">Destructive</Button>
              <Button disabled>Disabled</Button>
              <Button size="sm">
                <Plus className="w-4 h-4 mr-2" />
                Small
              </Button>
              <Button size="lg">Large Button</Button>
            </div>
          </CardContent>
        </Card>

        {/* Forms Section */}
        <Card>
          <CardHeader>
            <CardTitle>Forms & Inputs</CardTitle>
            <CardDescription>Input fields and form controls</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-w-md">
              <div>
                <label className="text-sm font-medium">Email</label>
                <Input type="email" placeholder="Enter your email" className="mt-1" />
              </div>

              <div>
                <label className="text-sm font-medium">Search</label>
                <div className="relative mt-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input placeholder="Search..." className="pl-10" />
                </div>
              </div>

              <div>
                <label className="text-sm font-medium">Category</label>
                <Select value={selectedValue} onValueChange={setSelectedValue}>
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="marketing">Marketing</SelectItem>
                    <SelectItem value="sales">Sales</SelectItem>
                    <SelectItem value="development">Development</SelectItem>
                    <SelectItem value="design">Design</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Badges & Progress */}
        <Card>
          <CardHeader>
            <CardTitle>Status Indicators</CardTitle>
            <CardDescription>Badges, progress bars and status indicators</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-medium mb-3">Badges</h3>
                <div className="flex flex-wrap gap-2">
                  <Badge>Default</Badge>
                  <Badge variant="secondary">Secondary</Badge>
                  <Badge variant="outline">Outline</Badge>
                  <Badge variant="destructive">Error</Badge>
                  <Badge className="bg-green-100 text-green-800 hover:bg-green-200">Success</Badge>
                  <Badge className="bg-yellow-100 text-yellow-800 hover:bg-yellow-200">Warning</Badge>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium mb-3">Progress</h3>
                <div className="space-y-2">
                  <div className="flex items-center space-x-4">
                    <Progress value={progress} className="flex-1" />
                    <span className="text-sm text-muted-foreground">{progress}%</span>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => setProgress(Math.max(0, progress - 10))}>
                      Decrease
                    </Button>
                    <Button size="sm" onClick={() => setProgress(Math.min(100, progress + 10))}>
                      Increase
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Notifications & Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Notifications & Alerts</CardTitle>
            <CardDescription>Toast notifications and alert messages</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium mb-3">Toast Notifications</h3>
                <div className="flex gap-2">
                  <Button onClick={handleToastTest} variant="outline">
                    <Bell className="w-4 h-4 mr-2" />
                    Success Toast
                  </Button>
                  <Button onClick={handleErrorToast} variant="outline">
                    Error Toast
                  </Button>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium mb-3">Alert Messages</h3>
                <div className="space-y-3">
                  <Alert>
                    <AlertDescription>
                      This is a default alert message with some important information.
                    </AlertDescription>
                  </Alert>

                  <Alert className="border-destructive/50 text-destructive dark:border-destructive">
                    <AlertDescription>
                      This is an error alert showing a critical issue that needs attention.
                    </AlertDescription>
                  </Alert>

                  <Alert className="border-yellow-200 bg-yellow-50 text-yellow-800">
                    <AlertDescription>
                      This is a warning alert indicating something that might need your attention.
                    </AlertDescription>
                  </Alert>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Dialog Modal */}
        <Card>
          <CardHeader>
            <CardTitle>Modal Dialogs</CardTitle>
            <CardDescription>Dialog windows and modals</CardDescription>
          </CardHeader>
          <CardContent>
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="outline">
                  <Settings className="w-4 h-4 mr-2" />
                  Open Dialog
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Test Dialog</DialogTitle>
                  <DialogDescription>
                    This is a test dialog to demonstrate the modal functionality.
                    You can add forms, content, or any other components here.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Name</label>
                    <Input placeholder="Enter name" className="mt-1" />
                  </div>
                  <div className="flex justify-end space-x-2">
                    <Button variant="outline">Cancel</Button>
                    <Button>Save</Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>

        {/* Grid Layout Test */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Card {i}</CardTitle>
                  <Badge variant="outline">Active</Badge>
                </div>
                <CardDescription>
                  This is card number {i} in the grid layout test
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span>{Math.floor(Math.random() * 100)}%</span>
                  </div>
                  <Progress value={Math.floor(Math.random() * 100)} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Responsive Design Test */}
        <Card>
          <CardHeader>
            <CardTitle>Responsive Layout</CardTitle>
            <CardDescription>Testing responsive breakpoints and layouts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-primary/10 p-4 rounded-lg text-center">
                <User className="w-8 h-8 mx-auto mb-2 text-primary" />
                <p className="text-sm font-medium">Users</p>
                <p className="text-2xl font-bold">1,234</p>
              </div>
              <div className="bg-green-100 p-4 rounded-lg text-center">
                <Bell className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <p className="text-sm font-medium">Notifications</p>
                <p className="text-2xl font-bold">56</p>
              </div>
              <div className="bg-blue-100 p-4 rounded-lg text-center">
                <Settings className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <p className="text-sm font-medium">Settings</p>
                <p className="text-2xl font-bold">8</p>
              </div>
              <div className="bg-purple-100 p-4 rounded-lg text-center">
                <Filter className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                <p className="text-sm font-medium">Filters</p>
                <p className="text-2xl font-bold">12</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}