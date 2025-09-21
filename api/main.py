#!/usr/bin/env python3
"""
FastAPI Backend for Script Runner
"""

import asyncio
import json
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from script_runner import get_available_scripts, run_openai_processor_with_monitoring

app = FastAPI(title="Script Runner API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job storage (in production, use a database)
jobs: Dict[str, Dict[str, Any]] = {}

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    status: str
    progress: int
    message: str
    logs: List[str]
    results: Optional[Any] = None
    error: Optional[str] = None

class ScriptConfig(BaseModel):
    name: str
    description: str
    config: List[Dict[str, Any]]
    requiresFile: bool

def parse_script_config(script_path: str) -> Optional[Dict[str, Any]]:
    """Extract CONFIG from Python script"""
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find CONFIG = { ... } block
        config_match = re.search(r'CONFIG\s*=\s*{.*?^}', content, re.MULTILINE | re.DOTALL)
        if not config_match:
            return None

        config_text = config_match.group(0)

        # Simple config extraction - get sections
        sections = []

        # Extract OPENAI_API section
        if '"OPENAI_API"' in config_text:
            sections.append({
                "name": "OpenAI API Settings",
                "fields": [
                    {
                        "key": "openai_api_key",
                        "label": "OpenAI API Key",
                        "type": "text",
                        "defaultValue": "",
                        "description": "Your OpenAI API key"
                    },
                    {
                        "key": "openai_model",
                        "label": "Model",
                        "type": "select",
                        "defaultValue": "gpt-4o-mini",
                        "options": ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4"]
                    },
                    {
                        "key": "max_tokens",
                        "label": "Max Tokens",
                        "type": "number",
                        "defaultValue": 4000
                    }
                ]
            })

        # Extract PROCESSING section
        if '"PROCESSING"' in config_text:
            sections.append({
                "name": "Processing Settings",
                "fields": [
                    {
                        "key": "concurrency",
                        "label": "Parallel Requests",
                        "type": "number",
                        "defaultValue": 10,
                        "description": "Number of parallel API requests"
                    },
                    {
                        "key": "batch_size",
                        "label": "Batch Size",
                        "type": "number",
                        "defaultValue": 100
                    },
                    {
                        "key": "cost_limit",
                        "label": "Cost Limit (USD)",
                        "type": "number",
                        "defaultValue": 10.0
                    }
                ]
            })

        return {
            "config": sections,
            "requiresFile": True
        }

    except Exception as e:
        print(f"Error parsing script config: {e}")
        return None

@app.get("/api/scripts", response_model=List[ScriptConfig])
async def get_scripts():
    """Get available scripts"""
    scripts_data = get_available_scripts()

    return [
        ScriptConfig(
            name=script["name"],
            description=script["description"],
            config=script["config"],
            requiresFile=script["requiresFile"]
        )
        for script in scripts_data
    ]

@app.post("/api/run-script", response_model=JobResponse)
async def run_script(
    script_name: str = Form(...),
    config: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """Start script execution"""
    job_id = str(uuid.uuid4())

    try:
        config_data = json.loads(config)

        # Save uploaded file if provided
        file_path = None
        if file:
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)
            file_path = upload_dir / f"{job_id}_{file.filename}"

            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

        # Initialize job
        jobs[job_id] = {
            "status": "running",
            "progress": 0,
            "message": "Starting script execution...",
            "logs": [],
            "script_name": script_name,
            "config": config_data,
            "file_path": str(file_path) if file_path else None,
            "started_at": datetime.now()
        }

        # Start script execution in background
        asyncio.create_task(execute_script(job_id))

        return JobResponse(
            job_id=job_id,
            status="running",
            message="Script execution started"
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job execution status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatus(
        status=job["status"],
        progress=job["progress"],
        message=job["message"],
        logs=job["logs"],
        results=job.get("results"),
        error=job.get("error")
    )

async def execute_script(job_id: str):
    """Execute script in background"""
    job = jobs[job_id]

    try:
        script_name = job["script_name"]
        config_data = job["config"]
        file_path = job["file_path"]

        # Update job status
        job["progress"] = 10
        job["message"] = "Preparing script execution..."
        job["logs"].append(f"Starting {script_name} execution")

        if script_name == "openai_mass_processor":
            await execute_openai_processor(job_id, config_data, file_path)
        else:
            raise Exception(f"Unknown script: {script_name}")

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        job["logs"].append(f"Error: {str(e)}")

async def execute_openai_processor(job_id: str, config: Dict, file_path: Optional[str]):
    """Execute OpenAI mass processor script"""
    job = jobs[job_id]

    async def update_progress(progress: int, message: str):
        job["progress"] = progress
        job["message"] = message
        job["logs"].append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    try:
        script_path = "../modules/openai/openai_mass_processor.py"

        # Run the actual script with monitoring
        results = await run_openai_processor_with_monitoring(
            script_path=script_path,
            config=config,
            csv_file_path=file_path,
            progress_callback=update_progress
        )

        # Complete the job
        job["status"] = "completed"
        job["results"] = results

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
        job["logs"].append(f"Execution failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)