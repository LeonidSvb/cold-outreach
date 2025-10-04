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
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from script_runner import get_available_scripts, run_openai_processor_with_monitoring

# Import CSV transformer
sys.path.append(str(Path(__file__).parent.parent / "modules" / "csv_transformer"))
from api_wrapper import csv_transformer_api

# Import enhanced column detector
from lib.column_detector import detect_all_columns

# Import CSV to Supabase service
from services.csv_to_supabase import upload_csv_to_supabase

# Import routers
from routers import instantly, csv_upload

app = FastAPI(title="Script Runner API", version="1.0.0")

# Register routers
app.include_router(instantly.router)
app.include_router(csv_upload.router)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:3004"],
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

# CSV Transformer Models
class ColumnInfo(BaseModel):
    type: str
    dtype: str
    non_null_count: int
    null_percentage: float
    sample_values: List[str]
    avg_length: Optional[float] = None
    max_length: Optional[int] = None

class PromptInfo(BaseModel):
    id: str
    section: str
    name: str
    purpose: str
    input_columns: List[str]
    output: str

class CSVAnalysisResponse(BaseModel):
    success: bool
    file_info: Optional[Dict[str, Any]] = None
    column_details: Dict[str, ColumnInfo] = {}
    preview_data: List[Dict[str, Any]] = []
    available_prompts: List[PromptInfo] = []
    error: Optional[str] = None

class TransformRequest(BaseModel):
    file_id: str
    selected_columns: List[str]
    prompt_id: str
    new_column_name: str
    max_rows: Optional[int] = None

class TransformResponse(BaseModel):
    success: bool
    summary: Optional[Dict[str, Any]] = None
    sample_results: List[Dict[str, Any]] = []
    output_file: Optional[str] = None
    error: Optional[str] = None

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
    """
    DEPRECATED: Old keyword-only detection function
    Use detect_column_types_enhanced() instead for better accuracy
    """
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


def detect_column_types_enhanced(
    columns: List[str],
    sample_data: Dict[str, List[Any]],
    sample_size: int = 10
) -> Dict[str, Dict[str, Any]]:
    """
    Enhanced column detection using hybrid approach (keyword + regex validation)

    Args:
        columns: List of column names
        sample_data: Dict mapping column names to sample values
        sample_size: Number of samples to analyze per column

    Returns:
        Dict mapping column names to detection results with confidence scores
    """
    return detect_all_columns(columns, sample_data, sample_size)

def analyze_csv_file_enhanced(file_path: str) -> Dict[str, Any]:
    """Analyze CSV file and extract metadata with enhanced column detection"""
    try:
        import pandas as pd

        # Read CSV with pandas for better handling
        df = pd.read_csv(file_path)
        columns = df.columns.tolist()
        rows = len(df)

        # Prepare sample data for enhanced detection
        sample_size = 10
        sample_data = {}
        for col in columns:
            sample_data[col] = df[col].head(sample_size).tolist()

        # Enhanced column detection
        detected_columns = detect_column_types_enhanced(
            columns=columns,
            sample_data=sample_data,
            sample_size=sample_size
        )

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

# CSV Transformer Endpoints
@app.post("/api/csv/analyze/{file_id}", response_model=CSVAnalysisResponse)
async def analyze_csv_file(file_id: str):
    """Analyze uploaded CSV file for transformation"""
    upload_dir = Path("uploads")
    metadata_file = upload_dir / f"{file_id}_metadata.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Load metadata
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        # Get actual file path
        csv_file = upload_dir / metadata["filename"]
        if not csv_file.exists():
            raise HTTPException(status_code=404, detail="CSV file not found")

        # Analyze with our CSV transformer
        analysis = csv_transformer_api.analyze_csv_file(str(csv_file))

        if not analysis["success"]:
            return CSVAnalysisResponse(
                success=False,
                error=analysis["error"]
            )

        # Convert to response format
        column_details = {}
        for col, info in analysis["column_details"].items():
            column_details[col] = ColumnInfo(**info)

        prompts = [PromptInfo(**prompt) for prompt in analysis["available_prompts"]]

        return CSVAnalysisResponse(
            success=True,
            file_info=analysis["file_info"],
            column_details=column_details,
            preview_data=analysis["preview_data"],
            available_prompts=prompts
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/csv/transform", response_model=TransformResponse)
async def transform_csv_file(request: TransformRequest):
    """Transform CSV file with selected columns and prompt"""
    upload_dir = Path("uploads")
    metadata_file = upload_dir / f"{request.file_id}_metadata.json"

    if not metadata_file.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Load metadata
        with open(metadata_file, "r") as f:
            metadata = json.load(f)

        # Get actual file path
        csv_file = upload_dir / metadata["filename"]
        if not csv_file.exists():
            raise HTTPException(status_code=404, detail="CSV file not found")

        # Perform transformation
        result = await csv_transformer_api.transform_csv(
            file_path=str(csv_file),
            selected_columns=request.selected_columns,
            prompt_id=request.prompt_id,
            new_column_name=request.new_column_name,
            max_rows=request.max_rows
        )

        if not result["success"]:
            return TransformResponse(
                success=False,
                error=result["error"]
            )

        return TransformResponse(
            success=True,
            summary=result["summary"],
            sample_results=result["sample_results"],
            output_file=result["output_file"]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transformation failed: {str(e)}")

@app.get("/api/csv/prompts")
async def get_available_prompts():
    """Get all available transformation prompts"""
    try:
        # Use a dummy file path to get prompts (we only need the prompt manager)
        analysis = csv_transformer_api.analyze_csv_file("dummy")
        return {
            "prompts": analysis["available_prompts"]
        }
    except Exception as e:
        return {
            "prompts": []
        }

# Pydantic models for Supabase upload
class SupabaseUploadRequest(BaseModel):
    file_id: str
    user_id: Optional[str] = 'ce8ac78e-1bb6-4a89-83ee-3cbac618ad25'
    batch_size: Optional[int] = 500

class SupabaseUploadResponse(BaseModel):
    success: bool
    import_id: Optional[str]
    total_rows: int
    companies_created: int
    companies_merged: int
    leads_created: int
    leads_updated: int
    errors: List[str]
    message: str

@app.post("/api/supabase/upload-csv", response_model=SupabaseUploadResponse)
async def upload_csv_to_supabase_endpoint(request: SupabaseUploadRequest):
    """
    Upload CSV file to Supabase with normalization and deduplication

    Process:
    1. Read CSV file from uploads/
    2. Detect column types (TASK-002)
    3. Normalize to companies + leads
    4. Deduplicate companies by domain
    5. Upsert leads with UPDATE strategy
    6. Save raw CSV to csv_imports_raw

    Returns upload statistics and any errors
    """
    try:
        upload_dir = Path("uploads")
        file_path = upload_dir / request.file_id

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {request.file_id}")

        # Read CSV for column detection
        import pandas as pd
        df = pd.read_csv(file_path)

        # Detect columns using TASK-002 system
        sample_data = {}
        for col in df.columns:
            sample_data[col] = df[col].head(10).tolist()

        detected_columns = detect_all_columns(
            columns=df.columns.tolist(),
            sample_data=sample_data,
            sample_size=10
        )

        # Upload to Supabase
        results = upload_csv_to_supabase(
            file_path=str(file_path),
            detected_columns=detected_columns,
            user_id=request.user_id,
            batch_size=request.batch_size
        )

        # Prepare response
        message = "Upload completed successfully"
        if results['errors']:
            message = f"Upload completed with {len(results['errors'])} errors"

        return SupabaseUploadResponse(
            success=results['success'],
            import_id=results['import_id'],
            total_rows=results['total_rows'],
            companies_created=results['companies_created'],
            companies_merged=results['companies_merged'],
            leads_created=results['leads_created'],
            leads_updated=results['leads_updated'],
            errors=results['errors'][:10],  # Limit to first 10 errors
            message=message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)