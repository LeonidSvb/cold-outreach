#!/usr/bin/env python3
"""
Prompts Router
Handles AI prompts management with version history
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from lib.supabase_client import get_supabase

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


# Response Models
class Prompt(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    prompt_text: str
    version: int
    parent_id: Optional[str]
    change_comment: Optional[str]
    created_at: str


class PromptsListResponse(BaseModel):
    success: bool
    prompts: List[Prompt]
    total: int


class PromptCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_text: str
    parent_id: Optional[str] = None
    change_comment: Optional[str] = None


class PromptCreateResponse(BaseModel):
    success: bool
    prompt: Prompt
    message: str


class PromptHistoryResponse(BaseModel):
    success: bool
    versions: List[Prompt]
    total_versions: int


@router.get("/", response_model=PromptsListResponse)
async def get_prompts(name: Optional[str] = None):
    """
    Get all prompts or filter by name
    Returns latest version of each prompt by default
    """
    try:
        supabase = get_supabase()

        if name:
            # Get all versions of specific prompt
            result = supabase.table('prompts').select('*').eq('name', name).order('version', desc=True).execute()
        else:
            # Get latest version of each unique prompt name
            # Using a subquery approach
            all_prompts = supabase.table('prompts').select('*').order('created_at', desc=True).execute()

            # Group by name and keep only latest version
            seen_names = set()
            latest_prompts = []
            for prompt in all_prompts.data:
                if prompt['name'] not in seen_names:
                    latest_prompts.append(prompt)
                    seen_names.add(prompt['name'])

            return PromptsListResponse(
                success=True,
                prompts=latest_prompts,
                total=len(latest_prompts)
            )

        return PromptsListResponse(
            success=True,
            prompts=result.data,
            total=len(result.data)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PromptCreateResponse)
async def create_prompt(request: PromptCreateRequest):
    """
    Create new prompt or new version of existing prompt

    If parent_id is provided, creates new version (increments version number)
    Otherwise creates new prompt with version 1
    """
    try:
        supabase = get_supabase()

        # Determine version number
        if request.parent_id:
            # Get parent prompt to increment version
            parent = supabase.table('prompts').select('version, name').eq('id', request.parent_id).execute()

            if not parent.data:
                raise HTTPException(status_code=404, detail="Parent prompt not found")

            version = parent.data[0]['version'] + 1
            name = parent.data[0]['name']  # Keep same name for versioning
        else:
            # Check if prompt with this name exists
            existing = supabase.table('prompts').select('version').eq('name', request.name).order('version', desc=True).limit(1).execute()

            if existing.data:
                # Create new version
                version = existing.data[0]['version'] + 1
            else:
                # Brand new prompt
                version = 1

            name = request.name

        # Create new prompt
        new_prompt = {
            'name': name,
            'description': request.description,
            'prompt_text': request.prompt_text,
            'version': version,
            'parent_id': request.parent_id,
            'change_comment': request.change_comment
        }

        result = supabase.table('prompts').insert(new_prompt).execute()

        return PromptCreateResponse(
            success=True,
            prompt=result.data[0],
            message=f"Prompt '{name}' v{version} created successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prompt_id}/history", response_model=PromptHistoryResponse)
async def get_prompt_history(prompt_id: str):
    """
    Get version history for a prompt
    Returns all versions in chronological order
    """
    try:
        supabase = get_supabase()

        # Get the prompt to find its name
        prompt = supabase.table('prompts').select('name').eq('id', prompt_id).execute()

        if not prompt.data:
            raise HTTPException(status_code=404, detail="Prompt not found")

        prompt_name = prompt.data[0]['name']

        # Get all versions of this prompt
        versions = supabase.table('prompts').select('*').eq('name', prompt_name).order('version', desc=True).execute()

        return PromptHistoryResponse(
            success=True,
            versions=versions.data,
            total_versions=len(versions.data)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prompt_id}", response_model=Prompt)
async def get_prompt_by_id(prompt_id: str):
    """
    Get specific prompt by ID
    """
    try:
        supabase = get_supabase()

        result = supabase.table('prompts').select('*').eq('id', prompt_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Prompt not found")

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
