#!/usr/bin/env python3
"""
Web Scraper + AI Tab - Scrape websites and analyze with AI for personalized outreach
"""

import sys
from pathlib import Path
import streamlit as st
import pandas as pd
from datetime import datetime
import subprocess
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.ui.components import (
    render_file_uploader,
    render_results_viewer
)


# Default AI analysis prompt template
DEFAULT_AI_PROMPT = """Analyze this company's website and extract information for personalized cold outreach.

Extract the following:

1. ICP (Ideal Customer Profile): Who is their target customer? Be specific about industry, company size, and role.
2. Business Summary: What does this company do? (1-2 sentences, concise and clear)
3. Recent Achievements: Any recent wins, awards, milestones, product launches, or news?
4. Personalization Angle: What unique hook can we use for cold outreach based on their business?

Return ONLY valid JSON in this exact format:
{{
  "icp": "Example: B2B SaaS companies with 50-200 employees in the fintech sector",
  "business_summary": "Example: Digital marketing agency specializing in SEO and content strategy for healthcare startups",
  "recent_achievements": "Example: Won 2024 Best Agency Award, expanded to 3 new markets, launched AI-powered content platform",
  "personalization_angle": "Example: Their recent expansion into AI tools shows they value innovation - our solution can help automate their customer outreach while maintaining personal touch"
}}

WEBSITE CONTENT:
{content}

IMPORTANT: Return ONLY the JSON object, no additional text or explanation.
"""


def render_web_scraper_ai_tab():
    """
    Web Scraper + AI tab - main rendering function
    """
    st.header("Web Scraper + AI")
    st.markdown("Scrape websites and analyze with AI for personalized outreach insights")

    # File upload
    df = render_file_uploader(
        label="Upload CSV with websites",
        with_results_browser=True,
        results_dir="modules/ui/results/web_scraper_ai",
        key_prefix="web_scraper_ai_upload"
    )

    if df is not None:
        # Configuration
        st.subheader("Configuration")

        col1, col2 = st.columns(2)

        with col1:
            # Auto-detect website column
            website_col_candidates = [
                col for col in df.columns
                if 'website' in col.lower() or 'url' in col.lower() or 'domain' in col.lower()
            ]
            default_website = website_col_candidates[0] if website_col_candidates else None

            website_column = st.selectbox(
                "Website column",
                options=df.columns.tolist(),
                index=df.columns.tolist().index(default_website) if default_website else 0,
                help="Column containing website URLs"
            )

        with col2:
            # Auto-detect name column
            name_col_candidates = [
                col for col in df.columns
                if 'name' in col.lower() or 'company' in col.lower()
            ]
            default_name = name_col_candidates[0] if name_col_candidates else None

            name_column = st.selectbox(
                "Name column (optional)",
                options=["-- Auto-generate --"] + df.columns.tolist(),
                index=df.columns.tolist().index(default_name) + 1 if default_name else 0,
                help="Column with company names (auto-generated from URL if not selected)"
            )

        # Test Mode
        st.markdown("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            test_mode = st.checkbox(
                "Test mode",
                value=True,
                help="Process only a subset of rows for testing before running on full dataset"
            )

        with col2:
            if test_mode:
                test_options = ["5 rows", "10 rows", "20 rows", "50 rows", "100 rows", "All rows"]
                test_limit_str = st.selectbox(
                    "Test with",
                    options=test_options,
                    index=0,
                    help="Number of rows to process in test mode"
                )
                # Extract number from string
                if "All" in test_limit_str:
                    limit = 0
                else:
                    limit = int(test_limit_str.split()[0])
            else:
                limit = 0
                st.info(f"Will process all {len(df)} rows")

        # AI Model Selection
        st.markdown("---")
        st.subheader("AI Model & Cost")

        col1, col2 = st.columns([1, 1])

        with col1:
            ai_model = st.selectbox(
                "OpenAI Model",
                options=["gpt-4o-mini (Recommended)", "gpt-4o (Higher Quality)"],
                index=0,
                help="Choose model based on budget vs quality needs"
            )

            # Clean model name
            ai_model_clean = "gpt-4o-mini" if "mini" in ai_model else "gpt-4o"

        with col2:
            # Cost info
            if "mini" in ai_model:
                st.metric("Cost per lead", "~$0.015", help="gpt-4o-mini: Best value")
                cost_per_lead = 0.015
            else:
                st.metric("Cost per lead", "~$0.10", help="gpt-4o: Higher quality but 7x more expensive")
                cost_per_lead = 0.10

        # AI Prompt Configuration
        st.subheader("AI Analysis Prompt")
        st.caption("Customize what AI should extract from each website. Use {content} placeholder for website text.")

        ai_prompt = st.text_area(
            "AI Prompt Template",
            value=DEFAULT_AI_PROMPT,
            height=350,
            help="Edit this prompt to customize AI analysis. Use {content} for website content."
        )

        # Advanced options
        with st.expander("Advanced Options"):
            col1, col2, col3 = st.columns(3)

            with col1:
                workers = st.number_input(
                    "Parallel workers",
                    min_value=1,
                    max_value=50,
                    value=20,
                    help="Number of parallel scraping workers (higher = faster but more load)"
                )

                scraping_mode = st.selectbox(
                    "Scraping mode",
                    options=["multi_page", "homepage_only"],
                    index=0,
                    help="multi_page: scrapes 3-5 important pages (about, contact, team). homepage_only: faster but less data."
                )

            with col2:
                max_pages = st.number_input(
                    "Max pages per site",
                    min_value=1,
                    max_value=10,
                    value=5,
                    disabled=(scraping_mode == "homepage_only"),
                    help="Maximum additional pages to scrape (only applies to multi_page mode)"
                )

                ai_workers = st.number_input(
                    "AI parallel requests",
                    min_value=1,
                    max_value=15,
                    value=5,
                    help="Number of parallel OpenAI API requests (max 15 to avoid rate limits)"
                )

            with col3:
                ai_model = st.selectbox(
                    "OpenAI Model",
                    options=["gpt-4o-mini", "gpt-4o"],
                    index=0,
                    help="gpt-4o-mini: cheaper (~$0.015/lead). gpt-4o: higher quality (~$0.10/lead)"
                )

                limit = st.number_input(
                    "Limit rows (0 = all)",
                    min_value=0,
                    value=0,
                    help="Process only first N rows (useful for testing)"
                )

        # API Key check
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            st.warning("OpenAI API key not found in .env file")
            api_key = st.text_input(
                "Enter OpenAI API Key",
                type="password",
                help="Get your API key from https://platform.openai.com/api-keys"
            )

        # Cost estimate
        if api_key:
            rows_to_process = limit if limit > 0 else len(df)
            cost_per_lead = 0.015 if ai_model == "gpt-4o-mini" else 0.10
            estimated_cost = rows_to_process * cost_per_lead

            st.info(f"Estimated cost: ${estimated_cost:.2f} ({rows_to_process} leads × ${cost_per_lead})")

        # Start button
        if api_key and st.button("Start Scraping + AI Analysis", type="primary"):
            # Save temp files
            temp_dir = Path("temp")
            temp_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_input = temp_dir / f"temp_web_ai_{timestamp}.csv"
            temp_prompt = temp_dir / f"temp_prompt_{timestamp}.txt"

            df.to_csv(temp_input, index=False)

            # Save prompt to file
            with open(temp_prompt, 'w', encoding='utf-8') as f:
                f.write(ai_prompt)

            # Build command
            cmd = [
                "python",
                "modules/scraping/web_scraper_ai/scraper_with_ai.py",
                "--input", str(temp_input),
                "--website-column", website_column,
                "--prompt-file", str(temp_prompt),
                "--workers", str(workers),
                "--ai-workers", str(ai_workers),
                "--ai-model", ai_model,
                "--scraping-mode", scraping_mode,
                "--max-pages", str(max_pages)
            ]

            if name_column != "-- Auto-generate --":
                cmd.extend(["--name-column", name_column])

            if limit > 0:
                cmd.extend(["--limit", str(limit)])

            # Set API key as env var
            env = os.environ.copy()
            env['OPENAI_API_KEY'] = api_key

            # Run scraper
            rows_to_process = limit if limit > 0 else len(df)
            with st.spinner(f"Processing {rows_to_process} websites... This may take 10-20 minutes."):
                try:
                    process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        env=env
                    )

                    # Wait for completion
                    stdout, stderr = process.communicate()
                    result_code = process.returncode

                    if result_code == 0:
                        st.success("Processing completed!")

                        # Parse output for results directory
                        output_lines = stdout.split('\n')
                        results_dir = None

                        for line in output_lines:
                            if "Results saved to:" in line:
                                results_dir = line.split("Results saved to:")[-1].strip()
                                break

                        if results_dir:
                            success_file = Path(results_dir) / "success.csv"

                            if success_file.exists():
                                success_df = pd.read_csv(success_file)

                                # Save to session state
                                st.session_state['web_scraper_ai_data'] = success_df

                                # Show results
                                render_results_viewer(
                                    success_df,
                                    title=f"Success Results ({len(success_df)} rows)",
                                    download_filename="web_scraper_ai_results.csv"
                                )

                                # Show analytics
                                analytics_file = Path(results_dir) / "analytics.json"
                                if analytics_file.exists():
                                    import json
                                    with open(analytics_file, 'r') as f:
                                        analytics = json.load(f)

                                    st.markdown("---")
                                    st.subheader("Analytics")

                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("Total Processed", analytics['summary']['total'])
                                    with col2:
                                        st.metric("Successful", analytics['summary']['success'])
                                    with col3:
                                        st.metric("Failed", analytics['summary']['failed'])
                                    with col4:
                                        st.metric("Total Cost", f"${analytics['summary']['total_cost']:.2f}")

                            else:
                                st.warning("Success file not found")
                        else:
                            st.warning("Could not parse results directory from output")

                    else:
                        st.error(f"Processing failed: {stderr}")

                except Exception as e:
                    st.error(f"Error running scraper: {e}")

    # Show data from session state if available
    elif 'web_scraper_ai_data' in st.session_state and st.session_state['web_scraper_ai_data'] is not None:
        st.info("Showing previously processed data from session")

        render_results_viewer(
            st.session_state['web_scraper_ai_data'],
            title="Web Scraper + AI Results",
            download_filename="web_scraper_ai_results.csv"
        )
