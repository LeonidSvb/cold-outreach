'use client'

import { useState } from 'react'
import { Input } from './ui/input'
import { Button } from './ui/button'

interface ConfigField {
  key: string
  label: string
  type: 'text' | 'number' | 'boolean' | 'select'
  defaultValue: any
  description?: string
  options?: string[]
}

interface ConfigSection {
  name: string
  fields: ConfigField[]
}

interface ConfigFormProps {
  config: ConfigSection[]
  onSubmit: (config: Record<string, any>) => void
  isLoading?: boolean
}

export default function ConfigForm({ config, onSubmit, isLoading = false }: ConfigFormProps) {
  const [formData, setFormData] = useState<Record<string, any>>(() => {
    const initial: Record<string, any> = {}
    config.forEach(section => {
      section.fields.forEach(field => {
        initial[field.key] = field.defaultValue
      })
    })
    return initial
  })

  const handleChange = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  const renderField = (field: ConfigField) => {
    const value = formData[field.key]

    switch (field.type) {
      case 'text':
        return (
          <Input
            type="text"
            value={value || ''}
            onChange={(e) => handleChange(field.key, e.target.value)}
            placeholder={field.description}
          />
        )
      case 'number':
        return (
          <Input
            type="number"
            value={value || ''}
            onChange={(e) => handleChange(field.key, parseFloat(e.target.value))}
            placeholder={field.description}
          />
        )
      case 'boolean':
        return (
          <input
            type="checkbox"
            checked={value || false}
            onChange={(e) => handleChange(field.key, e.target.checked)}
            className="h-4 w-4 text-primary border-gray-300 rounded focus:ring-primary"
          />
        )
      case 'select':
        return (
          <select
            value={value || ''}
            onChange={(e) => handleChange(field.key, e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            {field.options?.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        )
      default:
        return null
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {config.map((section, sectionIndex) => (
        <div key={sectionIndex} className="space-y-4">
          <h3 className="text-lg font-medium text-gray-900">{section.name}</h3>
          <div className="grid grid-cols-1 gap-4">
            {section.fields.map((field, fieldIndex) => (
              <div key={fieldIndex} className="space-y-2">
                <label className="text-sm font-medium text-gray-700">
                  {field.label}
                </label>
                {renderField(field)}
                {field.description && (
                  <p className="text-xs text-gray-500">{field.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      <Button
        type="submit"
        disabled={isLoading}
        className="w-full"
      >
        {isLoading ? 'Processing...' : 'Start Processing'}
      </Button>
    </form>
  )
}