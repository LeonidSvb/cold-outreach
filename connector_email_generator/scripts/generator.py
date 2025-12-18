#!/usr/bin/env python3
"""
=== CONNECTOR EMAIL GENERATOR ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Generate personalized connector-style cold emails using OpenAI GPT-4o
Based on SSM SOP with rotation framework

FEATURES:
- Auto-detect CSV fields with fallback mapping
- 4 deduplicated prompts + rotation openers
- Variable extraction (dreamICP, painTheySolve, etc.)
- Batch processing with retry logic
- Email assembly (prefix + AI + suffix)
- Follow-up generation

USAGE:
1. Configure CONFIG section below
2. Place CSV in data/input/
3. Run: python scripts/generator.py
4. Results saved to results/

IMPROVEMENTS:
v1.0.0 - Initial version with rotation framework
"""

import sys
import os
import re
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
from prompts import PROMPT_LIBRARY, get_prompt_with_rotation, FOLLOW_UPS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

CONFIG = {
    # ========== INPUT/OUTPUT ==========
    "INPUT_CSV": "data/input/leads.csv",
    "OUTPUT_FOLDER": "results/",

    # ========== CSV FIELD MAPPING ==========
    # Auto-detect with fallback patterns (case-insensitive)
    "FIELD_MAPPING": {
        "first_name": ["FirstName", "First Name", "first_name", "fname", "First", "Name"],
        "company_name": ["Company", "CompanyName", "company", "company_name", "Organization"],
        "title": ["Title", "Job Title", "Position", "JobTitle", "Role"],
        "description": ["Description", "Company Description", "About", "company_description"],
        "industry": ["Industry", "Vertical", "Sector", "industry"],
        "company_size": ["Company Size", "Employees", "Size", "company_size", "EmployeeCount"],
        "revenue": ["Revenue", "Annual Revenue", "ARR", "company_annual_revenue_clean", "AnnualRevenue"],
    },

    # ========== PROMPT SELECTION ==========
    "PROMPT_ID": 3,  # 1-4 from PROMPT_LIBRARY
    "ROTATION_KEY": None,  # Options: "been_mapping", "saw_movement", "name_came_up", "curating_matches", "got_signal"
                            # Only works with PROMPT_ID=3

    # ========== EMAIL ASSEMBLY ==========
    "EMAIL_STRUCTURE": {
        "prefix": "Hey {first_name}—\n\n",
        "use_ai_output": True,
        "suffix": "\n\nWorth intro'eing you?\n\nBest,",
    },

    # ========== VARIABLE EXTRACTION ==========
    # Creates separate columns for these variables from AI output
    "EXTRACT_VARIABLES": True,
    "VALIDATION": {
        "check_corporate_speak": True,
        "forbidden_words": ["optimize", "solution", "solutions", "leverage", "streamline", "platform", "synergy"],
    },

    # ========== OPENAI SETTINGS ==========
    "OPENAI_MODEL": "gpt-4o",
    "TEMPERATURE": 1.0,
    "MAX_TOKENS": 3000,
    "BATCH_SIZE": 5,
    "RETRY_ATTEMPTS": 3,
    "RETRY_DELAY": 2,

    # ========== PROCESSING OPTIONS ==========
    "SKIP_ROWS": 0,
    "LIMIT_ROWS": None,
    "DRY_RUN": False,
    "GENERATE_FOLLOWUPS": True,
}

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_processed": 0,
    "successful": 0,
    "failed": 0,
    "insufficient_data": 0,
    "corporate_speak_detected": 0,
    "start_time": None,
    "end_time": None
}


class ConnectorEmailGenerator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt = get_prompt_with_rotation(
            config["PROMPT_ID"],
            config.get("ROTATION_KEY")
        )
        logger.info(f"Initialized with prompt: {self.prompt['name']}")
        if config.get("ROTATION_KEY"):
            logger.info(f"Rotation applied: {config['ROTATION_KEY']}")

    def auto_detect_fields(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Auto-detect CSV column names based on FIELD_MAPPING patterns

        Returns dict: {internal_field: csv_column_name}
        """
        detected = {}
        csv_columns_lower = {col.lower(): col for col in df.columns}

        for field, patterns in self.config["FIELD_MAPPING"].items():
            for pattern in patterns:
                if pattern.lower() in csv_columns_lower:
                    detected[field] = csv_columns_lower[pattern.lower()]
                    logger.info(f"Detected '{field}' -> '{csv_columns_lower[pattern.lower()]}'")
                    break

            if field not in detected:
                logger.warning(f"Field '{field}' not found in CSV. Will use empty string.")
                detected[field] = None

        return detected

    def extract_variables_from_output(self, text: str) -> Dict[str, str]:
        """
        Extract variables from AI output using regex patterns
        """
        variables = {}

        # Extract dreamICP
        dreamicp_pattern = r"I'm around (.*?) daily"
        match = re.search(dreamicp_pattern, text)
        if match:
            variables["dreamICP"] = match.group(1).strip()

        # Alternative pattern for "I talk to a lot of"
        dreamicp_alt = r"I talk to a lot of (.*?) and they"
        match_alt = re.search(dreamicp_alt, text)
        if match_alt and "dreamICP" not in variables:
            variables["dreamICP"] = match_alt.group(1).strip()

        # Extract painTheySolve
        pain_pattern = r"they keep saying they (.*?)(?:\.|$)"
        match = re.search(pain_pattern, text)
        if match:
            variables["painTheySolve"] = match.group(1).strip()

        # Extract clean_company_name
        company_pattern = r"Noticed (.*?) helps"
        match = re.search(company_pattern, text)
        if match:
            variables["clean_company_name"] = match.group(1).strip()

        # Extract job_titles
        titles_pattern = r"helps (.*?) at"
        match = re.search(titles_pattern, text)
        if match:
            variables["job_titles"] = match.group(1).strip()

        # Extract company_type
        type_pattern = r"at (.*?) —"
        match = re.search(type_pattern, text)
        if match:
            variables["company_type"] = match.group(1).strip()

        # Extract pain_description
        pain_desc_pattern = r"I know a few who (.*?)(?:\.|$)"
        match = re.search(pain_desc_pattern, text)
        if match:
            variables["pain_description"] = match.group(1).strip()

        return variables

    def validate_output(self, text: str) -> tuple[bool, List[str]]:
        """
        Validate AI output for corporate speak and other issues

        Returns: (is_valid, list_of_issues)
        """
        issues = []

        if self.config["VALIDATION"]["check_corporate_speak"]:
            forbidden = self.config["VALIDATION"]["forbidden_words"]
            text_lower = text.lower()
            found_words = [word for word in forbidden if word in text_lower]
            if found_words:
                issues.append(f"Corporate speak detected: {', '.join(found_words)}")

        if text.strip() == "INSUFFICIENT_DATA":
            issues.append("Insufficient data in input")

        return len(issues) == 0, issues

    def generate_icebreaker(self, row_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate single icebreaker using OpenAI
        """
        user_prompt = self.prompt["user_prompt_template"].format(**row_data)

        for attempt in range(self.config["RETRY_ATTEMPTS"]):
            try:
                response = self.client.chat.completions.create(
                    model=self.config["OPENAI_MODEL"],
                    messages=[
                        {"role": "system", "content": self.prompt["system_prompt"]},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.config["TEMPERATURE"],
                    max_tokens=self.config["MAX_TOKENS"]
                )

                output = response.choices[0].message.content.strip()
                is_valid, issues = self.validate_output(output)

                result = {
                    "ai_output": output,
                    "is_valid": is_valid,
                    "issues": issues,
                    "tokens_used": response.usage.total_tokens,
                }

                if self.config["EXTRACT_VARIABLES"]:
                    result["variables"] = self.extract_variables_from_output(output)

                return result

            except Exception as e:
                logger.error(f"API call failed (attempt {attempt + 1}): {e}")
                if attempt < self.config["RETRY_ATTEMPTS"] - 1:
                    time.sleep(self.config["RETRY_DELAY"] * (attempt + 1))
                else:
                    return {
                        "ai_output": "",
                        "is_valid": False,
                        "issues": [f"API Error: {str(e)}"],
                        "tokens_used": 0,
                        "variables": {}
                    }

    def assemble_email(self, first_name: str, ai_output: str) -> str:
        """
        Assemble final email: prefix + AI output + suffix
        """
        email_parts = []

        if self.config["EMAIL_STRUCTURE"]["prefix"]:
            email_parts.append(self.config["EMAIL_STRUCTURE"]["prefix"].format(first_name=first_name))

        if self.config["EMAIL_STRUCTURE"]["use_ai_output"]:
            email_parts.append(ai_output)

        if self.config["EMAIL_STRUCTURE"]["suffix"]:
            email_parts.append(self.config["EMAIL_STRUCTURE"]["suffix"])

        return "".join(email_parts)

    def process_csv(self, input_path: str, output_path: str):
        """
        Main processing pipeline
        """
        SCRIPT_STATS["start_time"] = datetime.now()

        logger.info(f"Reading CSV: {input_path}")
        df = pd.read_csv(input_path)

        # Auto-detect fields
        field_map = self.auto_detect_fields(df)

        # Apply skip/limit
        start_idx = self.config["SKIP_ROWS"]
        end_idx = start_idx + self.config["LIMIT_ROWS"] if self.config["LIMIT_ROWS"] else len(df)
        df_subset = df.iloc[start_idx:end_idx].copy()

        logger.info(f"Processing {len(df_subset)} rows (skipped {start_idx})")

        # Prepare results columns
        df_subset["AI_Icebreaker"] = ""
        df_subset["Final_Email"] = ""
        df_subset["Is_Valid"] = True
        df_subset["Issues"] = ""
        df_subset["Tokens_Used"] = 0

        if self.config["GENERATE_FOLLOWUPS"]:
            df_subset["FollowUp_1"] = ""
            df_subset["FollowUp_2"] = ""

        # Add variable columns
        if self.config["EXTRACT_VARIABLES"]:
            for var in self.prompt.get("variables", []):
                df_subset[var] = ""

        # Process rows
        for idx, row in df_subset.iterrows():
            try:
                # Extract row data
                row_data = {}
                for field, csv_col in field_map.items():
                    if csv_col and csv_col in df.columns:
                        row_data[field] = str(row[csv_col]) if pd.notna(row[csv_col]) else ""
                    else:
                        row_data[field] = ""

                first_name = row_data.get("first_name", "there")

                logger.info(f"Processing row {idx + 1}/{len(df_subset)}: {first_name} @ {row_data.get('company_name', 'Unknown')}")

                # DRY RUN
                if self.config["DRY_RUN"]:
                    df_subset.at[idx, "AI_Icebreaker"] = "[DRY RUN - No API call made]"
                    df_subset.at[idx, "Final_Email"] = self.assemble_email(first_name, "[DRY RUN]")
                    continue

                # Generate icebreaker
                result = self.generate_icebreaker(row_data)

                df_subset.at[idx, "AI_Icebreaker"] = result["ai_output"]
                df_subset.at[idx, "Is_Valid"] = result["is_valid"]
                df_subset.at[idx, "Issues"] = "; ".join(result["issues"])
                df_subset.at[idx, "Tokens_Used"] = result["tokens_used"]

                # Extract variables
                if self.config["EXTRACT_VARIABLES"] and "variables" in result:
                    for var, value in result["variables"].items():
                        if var in df_subset.columns:
                            df_subset.at[idx, var] = value

                # Assemble final email
                df_subset.at[idx, "Final_Email"] = self.assemble_email(first_name, result["ai_output"])

                # Generate follow-ups
                if self.config["GENERATE_FOLLOWUPS"]:
                    df_subset.at[idx, "FollowUp_1"] = FOLLOW_UPS[1].format(first_name=first_name)
                    df_subset.at[idx, "FollowUp_2"] = FOLLOW_UPS[2].format(first_name=first_name)

                # Update stats
                SCRIPT_STATS["total_processed"] += 1
                if result["is_valid"]:
                    SCRIPT_STATS["successful"] += 1
                else:
                    if "Insufficient data" in result["issues"]:
                        SCRIPT_STATS["insufficient_data"] += 1
                    if "Corporate speak" in str(result["issues"]):
                        SCRIPT_STATS["corporate_speak_detected"] += 1
                    SCRIPT_STATS["failed"] += 1

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Failed to process row {idx}: {e}")
                df_subset.at[idx, "Issues"] = f"Processing error: {str(e)}"
                SCRIPT_STATS["failed"] += 1

        # Save results
        logger.info(f"Saving results to: {output_path}")
        df_subset.to_csv(output_path, index=False)

        SCRIPT_STATS["end_time"] = datetime.now()

        # Print stats
        duration = (SCRIPT_STATS["end_time"] - SCRIPT_STATS["start_time"]).total_seconds()
        logger.info("=== PROCESSING COMPLETE ===")
        logger.info(f"Total processed: {SCRIPT_STATS['total_processed']}")
        logger.info(f"Successful: {SCRIPT_STATS['successful']}")
        logger.info(f"Failed: {SCRIPT_STATS['failed']}")
        logger.info(f"Insufficient data: {SCRIPT_STATS['insufficient_data']}")
        logger.info(f"Corporate speak detected: {SCRIPT_STATS['corporate_speak_detected']}")
        logger.info(f"Duration: {duration:.2f}s")


def main():
    logger.info("=== CONNECTOR EMAIL GENERATOR STARTED ===")
    logger.info(f"Version: {SCRIPT_STATS['version']}")
    logger.info(f"Prompt ID: {CONFIG['PROMPT_ID']}")
    logger.info(f"Rotation: {CONFIG.get('ROTATION_KEY', 'None')}")

    # Resolve paths
    script_dir = Path(__file__).parent.parent
    input_path = script_dir / CONFIG["INPUT_CSV"]

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("Please place your CSV file in: data/input/leads.csv")
        return

    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prompt_name = PROMPT_LIBRARY[CONFIG["PROMPT_ID"]]["name"].replace(" ", "_").lower()
    output_filename = f"connector_emails_{prompt_name}_{timestamp}.csv"
    output_path = script_dir / CONFIG["OUTPUT_FOLDER"] / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate
    generator = ConnectorEmailGenerator(CONFIG)
    generator.process_csv(str(input_path), str(output_path))

    logger.info(f"Results saved to: {output_path}")
    logger.info("=== DONE ===")


if __name__ == "__main__":
    main()
