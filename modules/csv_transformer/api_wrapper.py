#!/usr/bin/env python3
"""
API Wrapper for CSV Column Transformer
Provides endpoints for FastAPI integration
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add module paths
sys.path.append(str(Path(__file__).parent.parent.parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / '.env')

# Import OpenAI
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import our modules
from csv_column_transformer import CSVAnalyzer, PromptManager, ColumnTransformer

class CSVTransformerAPI:
    """API wrapper for CSV Column Transformer"""

    def __init__(self):
        self.prompt_manager = PromptManager()

    def analyze_csv_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze CSV file and return structure info"""
        try:
            analyzer = CSVAnalyzer(file_path)

            # Get column info
            column_details = {}
            for col, info in analyzer.column_info.items():
                column_details[col] = {
                    "type": info["content_type"],
                    "dtype": info["dtype"],
                    "non_null_count": info["non_null_count"],
                    "null_percentage": round(info["null_percentage"], 1),
                    "sample_values": info["sample_values"][:3],  # First 3 samples
                    "avg_length": info.get("avg_length"),
                    "max_length": info.get("max_length")
                }

            # Get preview data
            preview_df = analyzer.get_preview_data(5)
            preview_data = preview_df.to_dict('records') if not preview_df.empty else []

            # Get available prompts
            available_prompts = []
            for section, prompts in self.prompt_manager.prompts.items():
                for prompt_name, prompt_data in prompts.items():
                    available_prompts.append({
                        "id": f"{section}_{prompt_name}",
                        "section": section,
                        "name": prompt_name,
                        "purpose": prompt_data.get("purpose", ""),
                        "input_columns": prompt_data.get("input_columns", []),
                        "output": prompt_data.get("output", "")
                    })

            return {
                "success": True,
                "file_info": {
                    "rows": len(analyzer.df),
                    "columns": len(analyzer.df.columns),
                    "column_names": analyzer.get_column_names()
                },
                "column_details": column_details,
                "preview_data": preview_data,
                "available_prompts": available_prompts
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_info": None,
                "column_details": {},
                "preview_data": [],
                "available_prompts": []
            }

    async def transform_csv(self,
                          file_path: str,
                          selected_columns: List[str],
                          prompt_id: str,
                          new_column_name: str,
                          max_rows: Optional[int] = None) -> Dict[str, Any]:
        """Transform CSV with selected prompt and columns"""
        try:
            # Parse prompt ID
            section, prompt_name = prompt_id.split("_", 1)
            prompt_data = self.prompt_manager.get_prompt(section, prompt_name)

            if not prompt_data:
                return {"success": False, "error": f"Prompt {prompt_id} not found"}

            # Load CSV
            analyzer = CSVAnalyzer(file_path)
            df = analyzer.df

            # Limit rows if specified
            if max_rows and len(df) > max_rows:
                df = df.head(max_rows)

            # Validate columns exist
            missing_columns = [col for col in selected_columns if col not in df.columns]
            if missing_columns:
                return {
                    "success": False,
                    "error": f"Missing columns: {missing_columns}"
                }

            # Initialize transformer
            transformer = ColumnTransformer()

            # Process transformation
            result_df = await self._process_transformation(
                df, prompt_data, new_column_name, selected_columns, transformer
            )

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"results/api_transform_{new_column_name}_{timestamp}.csv"
            output_path = Path(__file__).parent / output_file
            output_path.parent.mkdir(exist_ok=True)

            result_df.to_csv(output_path, index=False)

            # Create summary
            summary = {
                "original_rows": len(analyzer.df),
                "processed_rows": len(df),
                "new_column": new_column_name,
                "prompt_used": prompt_data["name"],
                "input_columns": selected_columns,
                "success_count": transformer.processed_rows,
                "api_cost": transformer.total_cost,
                "output_file": str(output_path)
            }

            # Get sample results for preview
            sample_results = []
            for i, row in result_df.head(5).iterrows():
                original_data = {col: row[col] for col in selected_columns}
                sample_results.append({
                    "original": original_data,
                    "transformed": row[new_column_name]
                })

            return {
                "success": True,
                "summary": summary,
                "sample_results": sample_results,
                "output_file": str(output_path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": None,
                "sample_results": [],
                "output_file": None
            }

    async def _process_transformation(self,
                                    df: pd.DataFrame,
                                    prompt_data: Dict,
                                    new_column_name: str,
                                    input_columns: List[str],
                                    transformer: ColumnTransformer) -> pd.DataFrame:
        """Process the actual AI transformation"""

        results = []

        for i, row in df.iterrows():
            try:
                # Format prompt with row data
                formatted_prompt = prompt_data["prompt"]

                # Replace placeholders with actual data
                for col in input_columns:
                    placeholder = "{" + col + "}"
                    value = str(row.get(col, "")).strip()
                    if not value or value.lower() in ['nan', 'null', 'none']:
                        value = "Not provided"
                    formatted_prompt = formatted_prompt.replace(placeholder, value)

                # Call OpenAI API
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": formatted_prompt}],
                    max_tokens=200,
                    temperature=0.1
                )

                result = response.choices[0].message.content.strip()
                results.append(result)
                transformer.processed_rows += 1

                # Calculate approximate cost
                transformer.total_cost += 0.001  # Rough estimate

            except Exception as e:
                print(f"Error processing row {i}: {e}")
                results.append(f"Error: {str(e)}")

        # Add results as new column
        df_copy = df.copy()
        df_copy[new_column_name] = results

        return df_copy

# Global instance
csv_transformer_api = CSVTransformerAPI()