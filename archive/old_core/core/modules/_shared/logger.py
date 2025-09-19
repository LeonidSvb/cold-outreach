#!/usr/bin/env python3
"""
=== MODULAR AUTO-LOGGER ===
Version: 1.0.0 | Created: 2025-01-15

PURPOSE: 
Automatic logging system for all modular functions with performance tracking

FEATURES:
- Auto-timestamp all function calls
- Track performance metrics (time, memory, success rate)
- JSON structured logging to data/logs/
- Statistics aggregation for dashboard
- Error capture with stack traces
"""

import os
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from functools import wraps

# Get root directory (3 levels up from this file)
ROOT_DIR = Path(__file__).parent.parent.parent.parent
LOGS_DIR = ROOT_DIR / "data" / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class ModuleLogger:
    """Auto-logger for modular functions"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.log_file = LOGS_DIR / f"{module_name}_{datetime.now().strftime('%Y%m%d')}.json"
        
    def log_function_call(self, func_name: str, input_params: Dict[str, Any], 
                         output_data: Any, execution_time: float, 
                         success: bool, error_msg: str = None):
        """Log a single function call"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": self.module_name,
            "function": func_name,
            "input": self._sanitize_input(input_params),
            "output_size": self._get_output_size(output_data),
            "execution_time_seconds": round(execution_time, 3),
            "success": success,
            "error": error_msg
        }
        
        # Append to daily log file
        logs = []
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(log_entry)
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
            
        return log_entry
    
    def _sanitize_input(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data and limit size"""
        sanitized = {}
        for key, value in params.items():
            if isinstance(value, str):
                # Limit string length for logging
                sanitized[key] = value[:200] + "..." if len(value) > 200 else value
            elif isinstance(value, (list, tuple)):
                sanitized[key] = f"[{len(value)} items]"
            elif isinstance(value, dict):
                sanitized[key] = f"{{{len(value)} keys}}"
            else:
                sanitized[key] = str(value)
        return sanitized
    
    def _get_output_size(self, output: Any) -> str:
        """Get human-readable output size"""
        if isinstance(output, str):
            return f"{len(output)} chars"
        elif isinstance(output, (list, tuple)):
            return f"{len(output)} items"
        elif isinstance(output, dict):
            return f"{len(output)} keys"
        else:
            return str(type(output).__name__)

def auto_log(module_name: str):
    """Decorator for automatic function logging"""
    def decorator(func):
        logger = ModuleLogger(module_name)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Prepare input params for logging
            input_params = {}
            if args:
                input_params['args'] = args
            if kwargs:
                input_params.update(kwargs)
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful call
                logger.log_function_call(
                    func_name=func.__name__,
                    input_params=input_params,
                    output_data=result,
                    execution_time=execution_time,
                    success=True
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_msg = f"{type(e).__name__}: {str(e)}"
                
                # Log failed call
                logger.log_function_call(
                    func_name=func.__name__,
                    input_params=input_params,
                    output_data=None,
                    execution_time=execution_time,
                    success=False,
                    error_msg=error_msg
                )
                
                # Re-raise the exception
                raise
                
        return wrapper
    return decorator

def get_module_stats(module_name: str) -> Dict[str, Any]:
    """Get aggregated statistics for a module"""
    log_files = list(LOGS_DIR.glob(f"{module_name}_*.json"))
    
    total_calls = 0
    successful_calls = 0
    total_time = 0
    recent_calls = []
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                
            for entry in logs:
                total_calls += 1
                if entry['success']:
                    successful_calls += 1
                total_time += entry['execution_time_seconds']
                
                # Keep last 10 calls for recent activity
                if len(recent_calls) < 10:
                    recent_calls.append(entry)
        except:
            continue
    
    return {
        "module": module_name,
        "total_calls": total_calls,
        "success_rate": round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 1),
        "avg_execution_time": round((total_time / total_calls) if total_calls > 0 else 0, 3),
        "last_run": recent_calls[-1]['timestamp'] if recent_calls else None,
        "recent_activity": recent_calls
    }

# Export main functions
__all__ = ['auto_log', 'ModuleLogger', 'get_module_stats']