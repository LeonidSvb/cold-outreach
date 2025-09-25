#!/usr/bin/env python3
"""
=== CSV COLUMN TRANSFORMER ===
Version: 1.0.0 | Created: 2025-09-25

PURPOSE:
Interactive CSV transformation tool with AI-powered column generation using custom prompts

FEATURES:
- Automatic CSV column detection and analysis
- Interactive prompt selection from markdown library
- OpenAI-powered column transformations
- New column generation with AI insights
- Backup creation and results tracking
- Batch processing with progress monitoring

USAGE:
1. Place CSV file in current directory or provide full path
2. Run: python csv_column_transformer.py
3. Select columns to analyze from detected CSV structure
4. Choose transformation prompt from library
5. Configure new column name and parameters
6. Review results in generated CSV file

IMPROVEMENTS:
v1.0.0 - Initial version with interactive column transformation
"""

import os
import sys
import json
import time
import pandas as pd
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add parent directories to path for shared modules
sys.path.append(str(Path(__file__).parent.parent))
from shared.logger import auto_log

# OpenAI integration
try:
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: OpenAI not installed. Install with: pip install openai")

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # OPENAI API SETTINGS
    "OPENAI_API": {
        "API_KEY": os.getenv("OPENAI_API_KEY", "your_openai_api_key_here"),
        "DEFAULT_MODEL": "gpt-4o-mini",
        "BACKUP_MODEL": "gpt-3.5-turbo",
        "MAX_TOKENS": 4000,
        "TEMPERATURE": 0.3,
        "MAX_RETRIES": 3,
        "RETRY_DELAY": 1.0
    },

    # PROCESSING SETTINGS
    "PROCESSING": {
        "BATCH_SIZE": 50,               # Rows per batch
        "MAX_ROWS_PREVIEW": 5,          # Rows to show in preview
        "CONCURRENCY": 10,              # Parallel requests
        "RATE_LIMIT_DELAY": 0.1,        # Delay between requests
        "MAX_COST_USD": 10.0            # Cost limit per transformation
    },

    # FILE HANDLING
    "FILES": {
        "RESULTS_DIR": "results",
        "BACKUP_DIR": "backups",
        "SUPPORTED_FORMATS": [".csv", ".xlsx", ".xls"],
        "OUTPUT_FORMAT": "csv",
        "CREATE_BACKUP": True
    },

    # PROMPTS
    "PROMPTS": {
        "PROMPTS_FILE": "prompts.md",
        "DEFAULT_SECTION": "Company Analysis Prompts"
    }
}

# ============================================================================
# SCRIPT STATISTICS - AUTO-UPDATED
# ============================================================================

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "last_run": None,
    "total_rows_processed": 0,
    "total_transformations": 0,
    "success_rate": 0.0,
    "avg_processing_time": 0.0,
    "total_api_cost": 0.0
}

# ============================================================================
# PROMPT MANAGER
# ============================================================================

class PromptManager:
    """Manages loading and parsing prompts from markdown file"""

    def __init__(self, prompts_file: str = None):
        self.prompts_file = prompts_file or CONFIG["PROMPTS"]["PROMPTS_FILE"]
        self.prompts = {}
        self.load_prompts()

    def load_prompts(self):
        """Load prompts from markdown file"""

        prompts_path = Path(__file__).parent / self.prompts_file

        if not prompts_path.exists():
            print(f"Prompts file not found: {prompts_path}")
            return

        with open(prompts_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse markdown sections
        sections = re.split(r'^## (.+?)$', content, flags=re.MULTILINE)
        current_section = None

        for i, section in enumerate(sections):
            if i % 2 == 1:  # Section headers
                current_section = section.strip()
                self.prompts[current_section] = {}
            elif current_section and section.strip():
                # Parse individual prompts
                prompts_in_section = re.split(r'^### (.+?)$', section, flags=re.MULTILINE)

                for j, prompt_content in enumerate(prompts_in_section):
                    if j % 2 == 1:  # Prompt names
                        prompt_name = prompt_content.strip()
                    elif j % 2 == 0 and j > 0:  # Prompt content
                        # Extract prompt details
                        lines = prompt_content.strip().split('\n')

                        prompt_data = {
                            "name": prompt_name,
                            "section": current_section,
                            "purpose": "",
                            "input_columns": [],
                            "output": "",
                            "prompt": ""
                        }

                        # Parse prompt metadata and content
                        in_prompt = False
                        prompt_lines = []

                        for line in lines:
                            if line.startswith("**Purpose:**"):
                                prompt_data["purpose"] = line.replace("**Purpose:**", "").strip()
                            elif line.startswith("**Input Columns:**"):
                                cols_text = line.replace("**Input Columns:**", "").strip()
                                prompt_data["input_columns"] = [col.strip() for col in cols_text.split(',')]
                            elif line.startswith("**Output:**"):
                                prompt_data["output"] = line.replace("**Output:**", "").strip()
                            elif line.startswith("```") and not in_prompt:
                                in_prompt = True
                            elif line.startswith("```") and in_prompt:
                                break
                            elif in_prompt:
                                prompt_lines.append(line)

                        prompt_data["prompt"] = '\n'.join(prompt_lines).strip()

                        if prompt_data["prompt"]:
                            self.prompts[current_section][prompt_name] = prompt_data

        print(f"Loaded {sum(len(section) for section in self.prompts.values())} prompts from {len(self.prompts)} sections")

    def get_all_prompts(self) -> Dict[str, Dict[str, Dict]]:
        """Get all loaded prompts organized by section"""
        return self.prompts

    def get_prompt(self, section: str, name: str) -> Optional[Dict]:
        """Get specific prompt by section and name"""
        return self.prompts.get(section, {}).get(name)

    def list_prompts(self) -> List[Tuple[str, str, str]]:
        """Get list of all prompts as (section, name, purpose) tuples"""
        all_prompts = []
        for section, prompts in self.prompts.items():
            for name, data in prompts.items():
                all_prompts.append((section, name, data.get("purpose", "")))
        return all_prompts

# ============================================================================
# CSV ANALYZER
# ============================================================================

class CSVAnalyzer:
    """Analyzes CSV files and provides column information"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.df = None
        self.column_info = {}
        self.load_csv()

    def load_csv(self):
        """Load CSV file and analyze structure"""

        try:
            if self.file_path.suffix.lower() == '.csv':
                self.df = pd.read_csv(self.file_path)
            elif self.file_path.suffix.lower() in ['.xlsx', '.xls']:
                self.df = pd.read_excel(self.file_path)
            else:
                raise ValueError(f"Unsupported file format: {self.file_path.suffix}")

            print(f"Loaded CSV: {len(self.df)} rows, {len(self.df.columns)} columns")
            self.analyze_columns()

        except Exception as e:
            print(f"Error loading CSV: {e}")
            sys.exit(1)

    def analyze_columns(self):
        """Analyze each column's data type and content"""

        for col in self.df.columns:
            # Basic statistics
            non_null_count = self.df[col].notna().sum()
            null_count = len(self.df) - non_null_count

            # Data type detection
            dtype = str(self.df[col].dtype)

            # Sample values (first 3 non-null values)
            sample_values = self.df[col].dropna().head(3).tolist()

            # Content analysis
            if dtype == 'object':
                avg_length = self.df[col].astype(str).str.len().mean()
                max_length = self.df[col].astype(str).str.len().max()
                content_type = self._detect_content_type(self.df[col])
            else:
                avg_length = None
                max_length = None
                content_type = dtype

            self.column_info[col] = {
                "dtype": dtype,
                "non_null_count": non_null_count,
                "null_count": null_count,
                "null_percentage": (null_count / len(self.df)) * 100,
                "sample_values": sample_values,
                "avg_length": avg_length,
                "max_length": max_length,
                "content_type": content_type
            }

    def _detect_content_type(self, series: pd.Series) -> str:
        """Detect the type of content in a text column"""

        # Sample some values for analysis
        sample = series.dropna().astype(str).head(20)

        if sample.empty:
            return "empty"

        # Check for common patterns
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        url_pattern = r'^https?://'
        phone_pattern = r'[\+\-\s\(\)0-9]{10,}'

        email_count = sum(1 for val in sample if re.match(email_pattern, val.strip()))
        url_count = sum(1 for val in sample if re.match(url_pattern, val.strip()))
        phone_count = sum(1 for val in sample if re.match(phone_pattern, val.strip()))

        # Classification
        total_sample = len(sample)
        if email_count / total_sample > 0.8:
            return "email"
        elif url_count / total_sample > 0.8:
            return "url"
        elif phone_count / total_sample > 0.8:
            return "phone"
        else:
            # Check average length for other classifications
            avg_len = series.astype(str).str.len().mean()
            if avg_len < 50:
                return "short_text"
            elif avg_len < 200:
                return "medium_text"
            else:
                return "long_text"

    def display_column_info(self):
        """Display formatted column information"""

        print("\n" + "="*80)
        print("CSV COLUMN ANALYSIS")
        print("="*80)

        for i, (col, info) in enumerate(self.column_info.items(), 1):
            print(f"\n{i}. {col}")
            print(f"   Type: {info['content_type']} ({info['dtype']})")
            print(f"   Data: {info['non_null_count']:,} values, {info['null_percentage']:.1f}% missing")

            if info['avg_length']:
                print(f"   Length: avg {info['avg_length']:.0f}, max {info['max_length']} chars")

            if info['sample_values']:
                sample_str = ', '.join([str(val)[:50] + ('...' if len(str(val)) > 50 else '')
                                      for val in info['sample_values']])
                print(f"   Sample: {sample_str}")

    def get_preview_data(self, max_rows: int = 5) -> pd.DataFrame:
        """Get preview of the data"""
        return self.df.head(max_rows)

    def get_column_names(self) -> List[str]:
        """Get list of column names"""
        return list(self.df.columns)

    def validate_columns(self, required_columns: List[str]) -> Tuple[bool, List[str]]:
        """Validate that required columns exist in the CSV"""

        missing_columns = []
        for col in required_columns:
            if col not in self.df.columns:
                missing_columns.append(col)

        return len(missing_columns) == 0, missing_columns

# ============================================================================
# COLUMN TRANSFORMER
# ============================================================================

class ColumnTransformer:
    """Handles AI-powered column transformations"""

    def __init__(self):
        self.results_dir = Path(__file__).parent / CONFIG["FILES"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)

        self.backup_dir = Path(__file__).parent / CONFIG["FILES"]["BACKUP_DIR"]
        self.backup_dir.mkdir(exist_ok=True)

        self.total_cost = 0.0
        self.processed_rows = 0

    @auto_log("csv_transformer")
    def transform_column(self,
                        df: pd.DataFrame,
                        prompt_data: Dict,
                        new_column_name: str,
                        input_columns: List[str] = None) -> pd.DataFrame:
        """Main transformation function"""

        print(f"\nStarting column transformation...")
        print(f"Prompt: {prompt_data['name']}")
        print(f"New column: {new_column_name}")
        print(f"Processing {len(df)} rows")

        if not HAS_OPENAI:
            print("Error: OpenAI not available. Cannot perform transformation.")
            return df

        start_time = time.time()

        # Validate input columns
        if input_columns:
            required_columns = input_columns
        else:
            required_columns = prompt_data.get('input_columns', [])

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return df

        # Create backup if enabled
        if CONFIG["FILES"]["CREATE_BACKUP"]:
            self._create_backup(df)

        # Process in batches
        batch_size = CONFIG["PROCESSING"]["BATCH_SIZE"]
        results = []

        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]

            print(f"Processing batch {i//batch_size + 1}/{(len(df) + batch_size - 1)//batch_size}...")

            batch_results = self._process_batch(batch_df, prompt_data, required_columns)
            results.extend(batch_results)

            # Cost check
            if self.total_cost > CONFIG["PROCESSING"]["MAX_COST_USD"]:
                print(f"Cost limit reached: ${self.total_cost:.3f}")
                break

            # Rate limiting
            time.sleep(CONFIG["PROCESSING"]["RATE_LIMIT_DELAY"])

        # Add new column to dataframe
        df_copy = df.copy()

        # Ensure we have results for all rows
        while len(results) < len(df):
            results.append("Processing incomplete due to limits")

        df_copy[new_column_name] = results[:len(df)]

        processing_time = time.time() - start_time

        print(f"\nTransformation completed!")
        print(f"Processing time: {processing_time:.1f} seconds")
        print(f"Rows processed: {len(results):,}")
        print(f"API cost: ${self.total_cost:.3f}")

        # Save results
        output_path = self._save_results(df_copy, new_column_name, prompt_data)
        print(f"Results saved to: {output_path}")

        return df_copy

    def _process_batch(self, batch_df: pd.DataFrame, prompt_data: Dict, input_columns: List[str]) -> List[str]:
        """Process a batch of rows with AI transformation"""

        results = []

        for _, row in batch_df.iterrows():
            try:
                # Prepare prompt with row data
                formatted_prompt = self._format_prompt(prompt_data["prompt"], row, input_columns)

                # Call OpenAI API
                response = self._call_openai_api(formatted_prompt)

                if response:
                    results.append(response)
                    self.processed_rows += 1
                else:
                    results.append("Error: No response from API")

            except Exception as e:
                print(f"Error processing row: {e}")
                results.append(f"Error: {str(e)}")

        return results

    def _format_prompt(self, prompt_template: str, row: pd.Series, input_columns: List[str]) -> str:
        """Format prompt template with row data"""

        formatted_prompt = prompt_template

        # Replace placeholders with row data
        for col in input_columns:
            placeholder = "{" + col + "}"
            value = str(row.get(col, "")).strip()

            # Handle missing values
            if not value or value.lower() in ['nan', 'null', 'none']:
                value = "Not provided"

            formatted_prompt = formatted_prompt.replace(placeholder, value)

        return formatted_prompt

    def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API with retry logic"""

        for attempt in range(CONFIG["OPENAI_API"]["MAX_RETRIES"]):
            try:
                response = openai.ChatCompletion.create(
                    model=CONFIG["OPENAI_API"]["DEFAULT_MODEL"],
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=CONFIG["OPENAI_API"]["MAX_TOKENS"],
                    temperature=CONFIG["OPENAI_API"]["TEMPERATURE"]
                )

                # Calculate cost (approximate)
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens

                # Pricing for gpt-4o-mini (approximate)
                cost = (prompt_tokens * 0.00015 + completion_tokens * 0.0006) / 1000
                self.total_cost += cost

                return response.choices[0].message.content.strip()

            except Exception as e:
                print(f"API call attempt {attempt + 1} failed: {e}")
                if attempt < CONFIG["OPENAI_API"]["MAX_RETRIES"] - 1:
                    time.sleep(CONFIG["OPENAI_API"]["RETRY_DELAY"] * (attempt + 1))

        return None

    def _create_backup(self, df: pd.DataFrame):
        """Create backup of original data"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.csv"
        backup_path = self.backup_dir / backup_filename

        df.to_csv(backup_path, index=False)
        print(f"Backup created: {backup_filename}")

    def _save_results(self, df: pd.DataFrame, new_column_name: str, prompt_data: Dict) -> Path:
        """Save transformed dataframe to results directory"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transformed_{new_column_name}_{timestamp}.csv"
        output_path = self.results_dir / filename

        # Save CSV
        df.to_csv(output_path, index=False)

        # Save metadata
        metadata = {
            "timestamp": timestamp,
            "new_column": new_column_name,
            "prompt_used": prompt_data["name"],
            "prompt_section": prompt_data["section"],
            "rows_processed": len(df),
            "total_columns": len(df.columns),
            "api_cost": round(self.total_cost, 4),
            "processing_stats": {
                "successful_rows": self.processed_rows,
                "error_rows": len(df) - self.processed_rows,
                "success_rate": (self.processed_rows / len(df)) * 100 if len(df) > 0 else 0
            }
        }

        metadata_path = self.results_dir / f"metadata_{new_column_name}_{timestamp}.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return output_path

# ============================================================================
# INTERACTIVE INTERFACE
# ============================================================================

class InteractiveInterface:
    """Handles user interaction and workflow orchestration"""

    def __init__(self):
        self.prompt_manager = PromptManager()
        self.csv_analyzer = None
        self.transformer = ColumnTransformer()

    def run(self):
        """Main interactive workflow"""

        print("="*80)
        print("CSV COLUMN TRANSFORMER v1.0.0")
        print("AI-Powered Column Generation Tool")
        print("="*80)

        # Step 1: Load CSV file
        csv_file = self._get_csv_file()
        if not csv_file:
            return

        self.csv_analyzer = CSVAnalyzer(csv_file)

        # Step 2: Show CSV analysis
        self.csv_analyzer.display_column_info()

        # Step 3: Preview data
        print("\n" + "="*80)
        print("DATA PREVIEW")
        print("="*80)
        preview_df = self.csv_analyzer.get_preview_data()
        print(preview_df.to_string())

        # Step 4: Select transformation prompt
        selected_prompt = self._select_prompt()
        if not selected_prompt:
            return

        # Step 5: Configure transformation
        config = self._configure_transformation(selected_prompt)
        if not config:
            return

        # Step 6: Confirm and execute
        if self._confirm_transformation(selected_prompt, config):
            result_df = self.transformer.transform_column(
                self.csv_analyzer.df,
                selected_prompt,
                config["new_column_name"],
                config["input_columns"]
            )

            print(f"\nTransformation completed successfully!")
            print(f"New CSV saved with column: {config['new_column_name']}")

    def _get_csv_file(self) -> Optional[str]:
        """Get CSV file path from user"""

        print("\nCSV FILE SELECTION")
        print("-" * 20)

        # Look for CSV files in current directory
        csv_files = []
        for ext in CONFIG["FILES"]["SUPPORTED_FORMATS"]:
            csv_files.extend(Path().glob(f"*{ext}"))

        if csv_files:
            print(f"Found {len(csv_files)} CSV/Excel file(s) in current directory:")
            for i, file in enumerate(csv_files, 1):
                size = file.stat().st_size
                size_mb = size / (1024*1024)
                print(f"{i}. {file.name} ({size_mb:.1f} MB)")

            print(f"{len(csv_files) + 1}. Enter custom file path")

            while True:
                try:
                    choice = input(f"\nSelect file (1-{len(csv_files) + 1}): ").strip()

                    if choice.isdigit():
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(csv_files):
                            return str(csv_files[choice_num - 1])
                        elif choice_num == len(csv_files) + 1:
                            break

                    print("Invalid choice. Please try again.")

                except ValueError:
                    print("Invalid input. Please enter a number.")

        # Get custom file path
        while True:
            file_path = input("Enter CSV file path: ").strip()

            if not file_path:
                print("No file specified. Exiting.")
                return None

            path = Path(file_path)
            if path.exists():
                if path.suffix.lower() in CONFIG["FILES"]["SUPPORTED_FORMATS"]:
                    return str(path)
                else:
                    print(f"Unsupported file format. Supported: {CONFIG['FILES']['SUPPORTED_FORMATS']}")
            else:
                print("File not found. Please check the path.")

    def _select_prompt(self) -> Optional[Dict]:
        """Interactive prompt selection"""

        print("\n" + "="*80)
        print("PROMPT SELECTION")
        print("="*80)

        all_prompts = self.prompt_manager.list_prompts()

        if not all_prompts:
            print("No prompts found in prompts.md file.")
            return None

        # Group prompts by section
        sections = {}
        for section, name, purpose in all_prompts:
            if section not in sections:
                sections[section] = []
            sections[section].append((name, purpose))

        # Display prompts by section
        prompt_index = 1
        prompt_map = {}

        for section, prompts in sections.items():
            print(f"\n{section}:")
            print("-" * len(section))

            for name, purpose in prompts:
                print(f"{prompt_index}. {name}")
                print(f"   Purpose: {purpose}")
                prompt_map[prompt_index] = (section, name)
                prompt_index += 1

        # Get user selection
        while True:
            try:
                choice = input(f"\nSelect prompt (1-{len(all_prompts)}): ").strip()

                if choice.isdigit():
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(all_prompts):
                        section, name = prompt_map[choice_num]
                        return self.prompt_manager.get_prompt(section, name)

                print("Invalid choice. Please try again.")

            except ValueError:
                print("Invalid input. Please enter a number.")

    def _configure_transformation(self, prompt_data: Dict) -> Optional[Dict]:
        """Configure transformation parameters"""

        print("\n" + "="*80)
        print("TRANSFORMATION CONFIGURATION")
        print("="*80)

        print(f"\nSelected prompt: {prompt_data['name']}")
        print(f"Purpose: {prompt_data['purpose']}")

        # Show required input columns
        required_columns = prompt_data.get('input_columns', [])
        available_columns = self.csv_analyzer.get_column_names()

        print(f"\nRequired input columns: {', '.join(required_columns)}")
        print(f"Available CSV columns: {', '.join(available_columns)}")

        # Validate column availability
        valid_columns, missing_columns = self.csv_analyzer.validate_columns(required_columns)

        if missing_columns:
            print(f"\nWarning: Some required columns are missing: {missing_columns}")

            # Let user select alternative columns
            print("\nColumn Mapping:")
            column_mapping = {}

            for req_col in required_columns:
                if req_col not in available_columns:
                    print(f"\nRequired column '{req_col}' not found.")
                    print("Available columns:")
                    for i, col in enumerate(available_columns, 1):
                        print(f"{i}. {col}")

                    while True:
                        try:
                            choice = input(f"Select column to use for '{req_col}' (1-{len(available_columns)}, or 'skip'): ").strip()

                            if choice.lower() == 'skip':
                                column_mapping[req_col] = None
                                break
                            elif choice.isdigit():
                                choice_num = int(choice)
                                if 1 <= choice_num <= len(available_columns):
                                    column_mapping[req_col] = available_columns[choice_num - 1]
                                    break

                            print("Invalid choice. Please try again.")

                        except ValueError:
                            print("Invalid input.")
                else:
                    column_mapping[req_col] = req_col

            # Update input columns based on mapping
            mapped_columns = [col for col in column_mapping.values() if col is not None]
        else:
            mapped_columns = required_columns

        # Get new column name
        while True:
            new_column_name = input("\nEnter name for new column: ").strip()

            if not new_column_name:
                print("Column name cannot be empty.")
                continue

            if new_column_name in available_columns:
                overwrite = input(f"Column '{new_column_name}' already exists. Overwrite? (y/n): ").strip().lower()
                if overwrite != 'y':
                    continue

            break

        # Estimate cost and processing time
        row_count = len(self.csv_analyzer.df)
        estimated_cost = self._estimate_cost(row_count)
        estimated_time = row_count * 0.5  # seconds

        print(f"\nEstimated processing:")
        print(f"Rows to process: {row_count:,}")
        print(f"Estimated cost: ${estimated_cost:.3f}")
        print(f"Estimated time: {estimated_time/60:.1f} minutes")

        return {
            "new_column_name": new_column_name,
            "input_columns": mapped_columns,
            "estimated_cost": estimated_cost,
            "estimated_time": estimated_time
        }

    def _confirm_transformation(self, prompt_data: Dict, config: Dict) -> bool:
        """Get user confirmation before processing"""

        print("\n" + "="*80)
        print("CONFIRM TRANSFORMATION")
        print("="*80)

        print(f"Prompt: {prompt_data['name']}")
        print(f"New column: {config['new_column_name']}")
        print(f"Input columns: {', '.join(config['input_columns'])}")
        print(f"Estimated cost: ${config['estimated_cost']:.3f}")
        print(f"Estimated time: {config['estimated_time']/60:.1f} minutes")

        while True:
            confirm = input("\nProceed with transformation? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                return True
            elif confirm in ['n', 'no']:
                print("Transformation cancelled.")
                return False
            else:
                print("Please enter 'y' or 'n'.")

    def _estimate_cost(self, row_count: int) -> float:
        """Estimate API cost for transformation"""

        # Rough estimation based on typical prompt/response sizes
        avg_prompt_tokens = 500
        avg_response_tokens = 200

        # GPT-4o-mini pricing (approximate)
        cost_per_1k_input = 0.00015
        cost_per_1k_output = 0.0006

        total_input_tokens = row_count * avg_prompt_tokens
        total_output_tokens = row_count * avg_response_tokens

        total_cost = (total_input_tokens * cost_per_1k_input + total_output_tokens * cost_per_1k_output) / 1000

        return total_cost

# ============================================================================
# EXECUTION
# ============================================================================

def update_script_stats(processing_time: float, rows_processed: int, api_cost: float):
    """Update script statistics"""
    global SCRIPT_STATS

    SCRIPT_STATS["total_runs"] += 1
    SCRIPT_STATS["last_run"] = datetime.now().isoformat()
    SCRIPT_STATS["total_rows_processed"] += rows_processed
    SCRIPT_STATS["total_transformations"] += 1
    SCRIPT_STATS["avg_processing_time"] = processing_time
    SCRIPT_STATS["total_api_cost"] += api_cost
    SCRIPT_STATS["success_rate"] = 100.0  # Will be calculated based on actual results

def main():
    """Main execution function"""

    # Check OpenAI availability
    if not HAS_OPENAI or not CONFIG["OPENAI_API"]["API_KEY"] or CONFIG["OPENAI_API"]["API_KEY"] == "your_openai_api_key_here":
        print("Error: OpenAI API key not configured.")
        print("Please set OPENAI_API_KEY environment variable.")
        return

    start_time = time.time()
    interface = InteractiveInterface()

    try:
        interface.run()

        # Update stats
        processing_time = time.time() - start_time
        rows_processed = interface.transformer.processed_rows
        api_cost = interface.transformer.total_cost

        update_script_stats(processing_time, rows_processed, api_cost)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()