#!/usr/bin/env python3
"""
FastAPI Backend for Script Runner
"""

import asyncio
import json
import os
import subprocess
import uuid
import csv
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

class UploadedFile(BaseModel):
    id: str
    filename: str
    original_name: str
    upload_date: str
    rows: int
    columns: List[str]
    size: int
    detected_columns: Dict[str, str]  # detected column types

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    rows: int
    columns: List[str]
    detected_columns: Dict[str, str]
    message: str

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

def detect_column_types(columns: List[str]) -> Dict[str, str]:
    """Detect column types based on column names"""
    detected = {}

    for col in columns:
        col_lower = col.lower()

        # Company name detection
        if any(word in col_lower for word in ['company', 'organization', 'business', 'firm']):
            detected['company_name'] = col

        # Website detection
        elif any(word in col_lower for word in ['website', 'url', 'domain', 'site']):
            detected['website'] = col

        # Email detection
        elif any(word in col_lower for word in ['email', 'mail', '@']):
            detected['email'] = col

        # Phone detection
        elif any(word in col_lower for word in ['phone', 'tel', 'mobile', 'number']):
            detected['phone'] = col

        # Name detection
        elif any(word in col_lower for word in ['name', 'first', 'last', 'full']):
            if 'first' in col_lower:
                detected['first_name'] = col
            elif 'last' in col_lower:
                detected['last_name'] = col
            elif 'full' in col_lower:
                detected['full_name'] = col

        # Title detection
        elif any(word in col_lower for word in ['title', 'position', 'role', 'job']):
            detected['title'] = col

    return detected

def analyze_csv_file(file_path: str) -> Dict[str, Any]:
    """Analyze CSV file and extract metadata"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)

            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            reader = csv.reader(f, delimiter=delimiter)
            columns = next(reader)  # First row as headers

            # Count rows
            rows = sum(1 for row in reader)

            # Detect column types
            detected_columns = detect_column_types(columns)

            return {
                'columns': columns,
                'rows': rows,
                'detected_columns': detected_columns
            }

    except Exception as e:
        print(f"Error analyzing CSV: {e}")
        return {
            'columns': [],
            'rows': 0,
            'detected_columns': {}
        }

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

@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and analyze CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    try:
        # Create uploads directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_path = upload_dir / f"{file_id}_{file.filename}"

        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Analyze file
        analysis = analyze_csv_file(str(file_path))

        # Save metadata
        metadata = {
            "id": file_id,
            "filename": file_path.name,
            "original_name": file.filename,
            "upload_date": datetime.now().isoformat(),
            "rows": analysis['rows'],
            "columns": analysis['columns'],
            "size": len(content),
            "detected_columns": analysis['detected_columns']
        }

        metadata_file = upload_dir / f"{file_id}_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            rows=analysis['rows'],
            columns=analysis['columns'],
            detected_columns=analysis['detected_columns'],
            message="File uploaded and analyzed successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/uploaded-files", response_model=List[UploadedFile])
async def get_uploaded_files():
    """Get list of uploaded files"""
    upload_dir = Path("uploads")
    if not upload_dir.exists():
        return []

    files = []
    for metadata_file in upload_dir.glob("*_metadata.json"):
        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                files.append(UploadedFile(**metadata))
        except Exception as e:
            print(f"Error reading metadata file {metadata_file}: {e}")

    # Sort by upload date (newest first)
    files.sort(key=lambda x: x.upload_date, reverse=True)
    return files

@app.get("/api/files/{file_id}/preview")
async def get_file_preview(file_id: str, limit: int = 15):
    """Get preview of CSV file (last N rows)"""
    upload_dir = Path("uploads")
    metadata_file = upload_dir / f"{file_id}_metadata.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Load metadata
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        # Find the actual CSV file
        csv_file = upload_dir / metadata["filename"]
        if not csv_file.exists():
            raise HTTPException(status_code=404, detail="CSV file not found")

        # Read last N rows
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Get headers and last N rows
        headers = lines[0].strip().split(',') if lines else []
        data_lines = lines[1:] if len(lines) > 1 else []
        preview_lines = data_lines[-limit:] if len(data_lines) > limit else data_lines

        preview_data = []
        for line in preview_lines:
            row = [cell.strip('"') for cell in line.strip().split(',')]
            preview_data.append(dict(zip(headers, row)))

        return {
            "metadata": metadata,
            "headers": headers,
            "preview": preview_data,
            "total_rows": len(data_lines),
            "showing": len(preview_data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

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
    uvicorn.run(app, host="0.0.0.0", port=8002)