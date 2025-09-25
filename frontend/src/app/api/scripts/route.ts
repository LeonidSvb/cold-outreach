import { NextRequest, NextResponse } from 'next/server'

export async function GET() {
  try {
    // Список доступных скриптов
    const scripts = [
      {
        name: "csv_column_transformer",
        description: "AI-powered CSV column transformation with customizable prompts",
        requiresFile: true,
        config: [
          {
            name: "Transformation Settings",
            fields: [
              {
                key: "new_column_name",
                label: "New Column Name",
                type: "text",
                defaultValue: "transformed_column",
                description: "Name for the new transformed column"
              },
              {
                key: "max_rows",
                label: "Max Rows to Process",
                type: "number",
                defaultValue: 100,
                description: "Limit processing for cost control"
              },
              {
                key: "prompt_type",
                label: "Transformation Type",
                type: "select",
                defaultValue: "COMPANY_NAME_NORMALIZER",
                options: ["COMPANY_NAME_NORMALIZER", "CITY_NORMALIZER"],
                description: "Select transformation prompt"
              }
            ]
          }
        ]
      },
      {
        name: "openai_mass_processor",
        description: "Generate personalized icebreakers using OpenAI",
        requiresFile: true,
        config: [
          {
            name: "OpenAI API Settings",
            fields: [
              {
                key: "openai_api_key",
                label: "OpenAI API Key",
                type: "text",
                defaultValue: process.env.OPENAI_API_KEY || "",
                description: "Your OpenAI API key"
              },
              {
                key: "openai_model",
                label: "Model",
                type: "select",
                defaultValue: "gpt-4o-mini",
                options: ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4"]
              },
              {
                key: "max_tokens",
                label: "Max Tokens",
                type: "number",
                defaultValue: 4000
              }
            ]
          },
          {
            name: "Processing Settings",
            fields: [
              {
                key: "concurrency",
                label: "Parallel Requests",
                type: "number",
                defaultValue: 10,
                description: "Number of concurrent API requests"
              },
              {
                key: "batch_size",
                label: "Batch Size",
                type: "number",
                defaultValue: 100
              },
              {
                key: "cost_limit",
                label: "Cost Limit (USD)",
                type: "number",
                defaultValue: 10.0
              }
            ]
          }
        ]
      }
    ]

    return NextResponse.json(scripts)
  } catch (error) {
    console.error('Error fetching scripts:', error)
    return NextResponse.json({ error: 'Failed to fetch scripts' }, { status: 500 })
  }
}