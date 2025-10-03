#!/usr/bin/env python3
"""
Supabase Client Library
Centralized Supabase connection and operations for all backend services
"""

import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_client: Optional[Client] = None

def get_supabase() -> Client:
    """
    Get singleton Supabase client instance

    Returns:
        Client: Supabase client

    Raises:
        ValueError: If credentials not found in environment
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not found in environment")

    _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client

def upsert_rows(table: str, rows: List[Dict[str, Any]],
                on_conflict: str = "id") -> Dict[str, Any]:
    """
    Upsert rows to Supabase table (insert or update on conflict)

    Args:
        table: Table name
        rows: List of row dictionaries to upsert
        on_conflict: Column name for conflict resolution (default: "id")

    Returns:
        Dict with success status and data

    Example:
        result = upsert_rows('campaigns', [
            {'campaign_id': '123', 'name': 'Test'}
        ], on_conflict='campaign_id')
    """
    try:
        supabase = get_supabase()
        response = supabase.table(table).upsert(rows, on_conflict=on_conflict).execute()

        return {
            "success": True,
            "upserted": len(rows),
            "data": response.data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def query_table(table: str, filters: Optional[Dict] = None,
                limit: int = 100) -> Dict[str, Any]:
    """
    Query rows from Supabase table

    Args:
        table: Table name
        filters: Optional dict of column: value filters
        limit: Maximum rows to return (default: 100)

    Returns:
        Dict with success status and data

    Example:
        result = query_table('users', filters={'status': 'active'}, limit=10)
    """
    try:
        supabase = get_supabase()
        query = supabase.table(table).select("*")

        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)

        response = query.limit(limit).execute()

        return {
            "success": True,
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Test function
if __name__ == "__main__":
    # Test connection
    try:
        client = get_supabase()
        print(f"Successfully connected to Supabase: {client.supabase_url}")

        # Test query (assuming 'users' table exists)
        result = query_table('users', limit=1)
        print(f"Query test: {result}")

    except Exception as e:
        print(f"Connection test failed: {e}")
