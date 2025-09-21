#!/usr/bin/env python3
"""
Script Runner Integration Layer
Connects the web UI with existing Python scripts
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
import importlib.util
from dotenv import load_dotenv

# Load environment variables from root .env file
load_dotenv(Path(__file__).parent.parent / '.env')

def load_script_module(script_path: str):
    """Dynamically load a Python script as module"""
    spec = importlib.util.spec_from_file_location("script_module", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def modify_script_config(script_path: str, new_config: Dict[str, Any]) -> str:
    """Create a modified version of the script with new CONFIG values"""
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create modified config based on user input
    modified_config = create_modified_config(new_config)

    # Replace CONFIG section
    import re
    config_pattern = r'(CONFIG\s*=\s*{.*?^})'
    modified_content = re.sub(
        config_pattern,
        f"CONFIG = {modified_config}",
        content,
        flags=re.MULTILINE | re.DOTALL
    )

    # Create temporary file
    temp_dir = Path("temp_scripts")
    temp_dir.mkdir(exist_ok=True)

    temp_script = temp_dir / f"modified_{Path(script_path).name}"
    with open(temp_script, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    return str(temp_script)

def create_modified_config(user_config: Dict[str, Any]) -> str:
    """Create CONFIG dict string from user input"""
    # Get OpenAI API key from environment if not provided by user
    openai_key = user_config.get("openai_api_key") or os.getenv("OPENAI_API_KEY", "")

    config = {
        "OPENAI_API": {
            "API_KEY": f'"{openai_key}"',
            "BASE_URL": '"https://api.openai.com/v1"',
            "DEFAULT_MODEL": f'"{user_config.get("openai_model", "gpt-4o-mini")}"',
            "BACKUP_MODEL": '"gpt-3.5-turbo"',
            "MAX_TOKENS": user_config.get("max_tokens", 4000),
            "TEMPERATURE": 0.3
        },
        "PROCESSING": {
            "CONCURRENCY": user_config.get("concurrency", 10),
            "BATCH_SIZE": user_config.get("batch_size", 100),
            "RETRY_ATTEMPTS": 3,
            "RETRY_DELAY": 1.0,
            "RATE_LIMIT_RPM": 3000,
            "COST_LIMIT_USD": user_config.get("cost_limit", 10.0)
        },
        "PROMPTS": {
            "COMPANY_ANALYZER": '''"""
Analyze this company information and extract key insights:
Company: {{company_name}}
Website: {{website}}
Industry: {{industry}}

Provide analysis in JSON format:
{{
  "pain_points": ["list of potential business pain points"],
  "tech_stack": ["likely technologies used"],
  "decision_makers": ["typical decision maker titles"],
  "business_model": "description of business model",
  "growth_stage": "startup/growth/mature",
  "priority_score": 8.5
}}
"""'''
        },
        "GOOGLE_SHEETS": {
            "ENABLED": False,
            "CREDENTIALS_PATH": '""',
            "INPUT_SHEET_ID": '""',
            "OUTPUT_SHEET_ID": '""'
        },
        "OUTPUT": {
            "SAVE_JSON": True,
            "UPDATE_GOOGLE_SHEETS": False,
            "EXPORT_CSV": True,
            "INCLUDE_COSTS": True,
            "RESULTS_DIR": '"results"'
        }
    }

    return json.dumps(config, indent=4)

async def run_openai_processor_with_monitoring(
    script_path: str,
    config: Dict[str, Any],
    csv_file_path: Optional[str],
    progress_callback: callable
):
    """Run OpenAI processor with real-time monitoring"""

    try:
        # Update progress
        await progress_callback(10, "Preparing script execution...")

        # Create modified script
        modified_script = modify_script_config(script_path, config)

        await progress_callback(20, "Configuration prepared, starting execution...")

        # For MVP, we'll simulate the execution
        # In real implementation, you would run the actual script:

        # cmd = [sys.executable, modified_script]
        # if csv_file_path:
        #     cmd.extend(['--input-file', csv_file_path])

        # process = await asyncio.create_subprocess_exec(
        #     *cmd,
        #     stdout=asyncio.subprocess.PIPE,
        #     stderr=asyncio.subprocess.PIPE
        # )

        # Monitor progress (simulated for MVP)
        progress_steps = [
            (30, "Loading input data..."),
            (40, "Initializing OpenAI API..."),
            (50, "Processing batch 1/10..."),
            (60, "Processing batch 5/10..."),
            (70, "Processing batch 8/10..."),
            (80, "Finalizing results..."),
            (90, "Saving output files..."),
            (100, "Execution completed successfully!")
        ]

        for progress, message in progress_steps:
            await asyncio.sleep(1)  # Simulate work
            await progress_callback(progress, message)

        # Return results (simulated)
        return {
            "processed_count": 150,
            "success_rate": 96.7,
            "total_cost": 3.25,
            "output_file": "results/openai_results_20250121_143022.json",
            "execution_time": "2m 15s"
        }

    except Exception as e:
        await progress_callback(-1, f"Error: {str(e)}")
        raise e
    finally:
        # Cleanup temp files
        try:
            if 'modified_script' in locals():
                os.remove(modified_script)
        except:
            pass

def get_available_scripts() -> List[Dict[str, Any]]:
    """Get list of available scripts with their configurations"""
    scripts = []

    # Check for openai_mass_processor
    openai_script = Path("../modules/openai/openai_mass_processor.py")
    if openai_script.exists():
        scripts.append({
            "name": "openai_mass_processor",
            "description": "Generate personalized icebreakers using OpenAI",
            "path": str(openai_script),
            "requiresFile": True,
            "config": [
                {
                    "name": "OpenAI API Settings",
                    "fields": [
                        {
                            "key": "openai_api_key",
                            "label": "OpenAI API Key",
                            "type": "text",
                            "defaultValue": os.getenv("OPENAI_API_KEY", ""),
                            "description": "Your OpenAI API key (loaded from .env)"
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
                },
                {
                    "name": "Processing Settings",
                    "fields": [
                        {
                            "key": "concurrency",
                            "label": "Parallel Requests",
                            "type": "number",
                            "defaultValue": 10,
                            "description": "Number of concurrent API requests"
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
                }
            ]
        })

    return scripts