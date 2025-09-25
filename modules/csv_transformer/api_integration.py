#!/usr/bin/env python3
"""
API Integration Layer for CSV Column Transformer
Adapts the core CSV transformer module for web interface usage
"""

import os
import sys
import json
import tempfile
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the core CSV transformer
from csv_column_transformer import (
    ColumnTransformer,
    PromptManager,
    CONFIG as DEFAULT_CONFIG,
    SCRIPT_STATS
)
from shared.logger import auto_log

class CsvTransformerApiIntegration:
    """Web API integration layer for CSV Column Transformer"""

    def __init__(self):
        self.prompt_manager = PromptManager()

    @auto_log("csv_transformer_api")
    def analyze_csv_structure(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Analyze CSV structure for web interface preview

        Args:
            file_content: Raw CSV file content
            filename: Original filename

        Returns:
            Analysis results for web interface
        """

        try:
            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name

            # Load and analyze CSV
            df = pd.read_csv(temp_path)

            # Detect column types
            column_types = self._detect_column_types(df)

            # Get sample data (last 5 rows)
            sample_rows = df.tail(5).to_dict('records')

            # Clean up temp file
            os.unlink(temp_path)

            return {
                'filename': filename,
                'total_rows': len(df),
                'columns': df.columns.tolist(),
                'column_types': column_types,
                'sample_data': sample_rows,
                'detected_key_columns': [col for col, type_info in column_types.items()
                                       if type_info['type'] in ['company', 'website', 'email', 'phone', 'name', 'title']],
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': f"Failed to analyze CSV: {str(e)}",
                'filename': filename
            }

    def _detect_column_types(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Detect column types based on content and headers"""

        column_types = {}

        for col in df.columns:
            col_lower = col.lower()
            sample_values = df[col].dropna().head(3).tolist()

            # Determine type based on column name and content
            if 'company' in col_lower or 'business' in col_lower:
                type_info = {'type': 'company', 'icon': '🏢', 'color': 'blue'}
            elif 'website' in col_lower or 'url' in col_lower or 'site' in col_lower:
                type_info = {'type': 'website', 'icon': '🌐', 'color': 'green'}
            elif 'email' in col_lower or 'mail' in col_lower:
                type_info = {'type': 'email', 'icon': '📧', 'color': 'purple'}
            elif 'phone' in col_lower or 'tel' in col_lower or 'mobile' in col_lower:
                type_info = {'type': 'phone', 'icon': '📞', 'color': 'orange'}
            elif ('name' in col_lower and 'company' not in col_lower) or 'contact' in col_lower:
                type_info = {'type': 'name', 'icon': '👤', 'color': 'yellow'}
            elif 'title' in col_lower or 'position' in col_lower or 'job' in col_lower:
                type_info = {'type': 'title', 'icon': '💼', 'color': 'indigo'}
            elif 'city' in col_lower or 'location' in col_lower or 'address' in col_lower:
                type_info = {'type': 'location', 'icon': '📍', 'color': 'red'}
            elif 'industry' in col_lower or 'sector' in col_lower:
                type_info = {'type': 'industry', 'icon': '🏭', 'color': 'gray'}
            else:
                type_info = {'type': 'text', 'icon': '📄', 'color': 'gray'}

            # Add sample values and confidence
            type_info.update({
                'sample_values': sample_values,
                'non_null_count': int(df[col].notna().sum()),
                'null_count': int(df[col].isna().sum())
            })

            column_types[col] = type_info

        return column_types

    @auto_log("csv_transformer_api")
    def get_available_prompts(self) -> Dict[str, List[Dict[str, str]]]:
        """Get available transformation prompts from the prompt manager"""

        try:
            available_prompts = {}

            for section_name, section_prompts in self.prompt_manager.prompts.items():
                available_prompts[section_name] = []

                for prompt_name, prompt_data in section_prompts.items():
                    available_prompts[section_name].append({
                        'name': prompt_name,
                        'description': prompt_data.get('description', 'No description available'),
                        'example_input': prompt_data.get('example_input', ''),
                        'example_output': prompt_data.get('example_output', '')
                    })

            return available_prompts

        except Exception as e:
            return {'error': f"Failed to load prompts: {str(e)}"}

    @auto_log("csv_transformer_api")
    def transform_csv_column(self,
                           file_content: bytes,
                           web_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform CSV column using web configuration

        Args:
            file_content: Raw CSV file content
            web_config: Configuration from web interface

        Returns:
            Transformation results for web interface
        """

        try:
            # Convert web config to internal config
            internal_config = self._convert_web_config(web_config)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name

            # Initialize transformer with config
            transformer = ColumnTransformer()
            transformer.config.update(internal_config)

            # Process the transformation
            result = transformer.process_csv_file(temp_path, web_config)

            # Clean up temp file
            os.unlink(temp_path)

            # Format result for web interface
            web_result = self._format_result_for_web(result, web_config)

            # Log session data for dashboard
            self._log_session_data(web_result)

            return web_result

        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self._log_session_data(error_result)
            return error_result

    def _convert_web_config(self, web_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert web interface config to internal module config"""

        internal_config = DEFAULT_CONFIG.copy()

        # Map web config to internal structure
        if 'max_rows' in web_config:
            internal_config['PROCESSING']['MAX_ROWS'] = web_config['max_rows']

        if 'prompt_type' in web_config:
            internal_config['PROMPTS']['SELECTED_PROMPT'] = web_config['prompt_type']

        if 'new_column_name' in web_config:
            internal_config['OUTPUT']['NEW_COLUMN_NAME'] = web_config['new_column_name']

        if 'openai_model' in web_config:
            internal_config['OPENAI_API']['DEFAULT_MODEL'] = web_config['openai_model']

        if 'cost_limit' in web_config:
            internal_config['PROCESSING']['MAX_COST_USD'] = web_config['cost_limit']

        return internal_config

    def _format_result_for_web(self, result: Dict[str, Any], web_config: Dict[str, Any]) -> Dict[str, Any]:
        """Format transformation result for web interface"""

        return {
            'success': result.get('success', False),
            'processed_rows': result.get('processed_rows', 0),
            'new_column_name': web_config.get('new_column_name', 'transformed_column'),
            'transformation_type': web_config.get('prompt_type', 'unknown'),
            'processing_time': result.get('processing_time', 0),
            'api_cost': result.get('total_cost', 0.0),
            'output_preview': result.get('preview_data', []),
            'output_file': result.get('output_file', ''),
            'statistics': {
                'successful_transformations': result.get('success_count', 0),
                'failed_transformations': result.get('error_count', 0),
                'processing_rate': result.get('processing_rate', 0)
            },
            'timestamp': datetime.now().isoformat(),
            'session_id': result.get('session_id', '')
        }

    def _log_session_data(self, result: Dict[str, Any]):
        """Log session data for dashboard integration"""

        try:
            session_data = {
                'module': 'csv_transformer',
                'timestamp': datetime.now().isoformat(),
                'success': result.get('success', False),
                'processed_rows': result.get('processed_rows', 0),
                'processing_time': result.get('processing_time', 0),
                'api_cost': result.get('api_cost', 0.0),
                'transformation_type': result.get('transformation_type', 'unknown')
            }

            # Update script stats
            SCRIPT_STATS['total_runs'] += 1
            SCRIPT_STATS['last_run'] = session_data['timestamp']
            if result.get('success'):
                SCRIPT_STATS['total_rows_processed'] += result.get('processed_rows', 0)
                SCRIPT_STATS['total_transformations'] += 1
                SCRIPT_STATS['total_api_cost'] += result.get('api_cost', 0.0)

            # Calculate success rate
            if SCRIPT_STATS['total_runs'] > 0:
                SCRIPT_STATS['success_rate'] = (SCRIPT_STATS['total_transformations'] /
                                               SCRIPT_STATS['total_runs']) * 100

        except Exception as e:
            print(f"Warning: Failed to log session data: {e}")

    def get_module_info(self) -> Dict[str, Any]:
        """Get module information for web interface"""

        return {
            'name': 'CSV Column Transformer',
            'version': SCRIPT_STATS['version'],
            'description': 'AI-powered CSV column transformation with customizable prompts',
            'statistics': SCRIPT_STATS.copy(),
            'available_prompts': len(self.prompt_manager.prompts),
            'supported_formats': DEFAULT_CONFIG['FILES']['SUPPORTED_FORMATS'],
            'max_cost_limit': DEFAULT_CONFIG['PROCESSING']['MAX_COST_USD']
        }

# Global instance for web API
csv_transformer_api = CsvTransformerApiIntegration()