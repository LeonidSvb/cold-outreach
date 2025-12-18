"""
Connector Email Generator - Streamlit UI
Interactive interface for generating connector-style cold emails
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from prompts import PROMPT_LIBRARY, ROTATION_OPENERS, FOLLOW_UPS
from scripts.generator import ConnectorEmailGenerator, SCRIPT_STATS

st.set_page_config(
    page_title="Connector Email Generator",
    page_icon="📧",
    layout="wide"
)

def main():
    st.title("📧 Connector Email Generator")
    st.markdown("Generate high-status connector-style cold emails with AI")

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    # File upload
    st.sidebar.subheader("1. Upload CSV")
    uploaded_file = st.sidebar.file_uploader(
        "Upload leads CSV",
        type=["csv"],
        help="CSV file with lead data (FirstName, Company, Title, etc.)"
    )

    # Prompt selection
    st.sidebar.subheader("2. Select Prompt")
    prompt_options = {
        f"{pid}: {p['name']}": pid
        for pid, p in PROMPT_LIBRARY.items()
    }
    selected_prompt_str = st.sidebar.selectbox(
        "Prompt template",
        options=list(prompt_options.keys()),
        help="Choose email style from SSM SOP"
    )
    selected_prompt_id = prompt_options[selected_prompt_str]

    # Show prompt description
    prompt_info = PROMPT_LIBRARY[selected_prompt_id]
    st.sidebar.info(f"**Description:** {prompt_info['description']}")

    # Rotation opener (if applicable)
    rotation_key = None
    if prompt_info.get("supports_rotation"):
        st.sidebar.subheader("3. Rotation Opener (Optional)")
        rotation_options = {"Default (No rotation)": None}
        rotation_options.update({
            f"{key.replace('_', ' ').title()}": key
            for key in ROTATION_OPENERS.keys()
        })
        selected_rotation = st.sidebar.selectbox(
            "Opener variation",
            options=list(rotation_options.keys()),
            help="Rotate opener to avoid market fatigue"
        )
        rotation_key = rotation_options[selected_rotation]

        if rotation_key:
            st.sidebar.success(f"Opener: {ROTATION_OPENERS[rotation_key]}")

    # Email structure
    st.sidebar.subheader("4. Email Structure")
    email_prefix = st.sidebar.text_area(
        "Prefix (before AI output)",
        value="Hey {first_name}—\n\n",
        height=80,
        help="Use {first_name} as placeholder"
    )

    use_ai_output = st.sidebar.checkbox(
        "Include AI icebreaker",
        value=True,
        help="Insert AI-generated icebreaker in email"
    )

    email_suffix = st.sidebar.text_area(
        "Suffix (after AI output)",
        value="\n\nWorth intro'eing you?\n\nBest,",
        height=80
    )

    # Processing options
    st.sidebar.subheader("5. Processing Options")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        skip_rows = st.number_input("Skip rows", min_value=0, value=0, step=1)
    with col2:
        limit_rows = st.number_input("Limit rows", min_value=0, value=0, step=1, help="0 = process all")

    extract_variables = st.sidebar.checkbox(
        "Extract variables",
        value=True,
        help="Extract dreamICP, painTheySolve, etc. to separate columns"
    )

    check_corporate_speak = st.sidebar.checkbox(
        "Validate corporate speak",
        value=True,
        help="Flag outputs with forbidden words"
    )

    generate_followups = st.sidebar.checkbox(
        "Generate follow-ups",
        value=True,
        help="Add Follow-Up #1 and #2 columns"
    )

    dry_run = st.sidebar.checkbox(
        "Dry run (no API calls)",
        value=False,
        help="Test without calling OpenAI API"
    )

    # Advanced settings
    with st.sidebar.expander("🔧 Advanced Settings"):
        openai_model = st.selectbox(
            "OpenAI Model",
            options=["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            index=0
        )
        temperature = st.slider("Temperature", 0.0, 2.0, 1.0, 0.1)
        max_tokens = st.number_input("Max tokens", 100, 5000, 3000, 100)
        batch_size = st.number_input("Batch size", 1, 20, 5, 1)
        retry_attempts = st.number_input("Retry attempts", 1, 5, 3, 1)

    # Main content area
    if uploaded_file is None:
        st.info("👈 Upload a CSV file to get started")

        # Show example structure
        st.subheader("📋 Expected CSV Structure")
        example_df = pd.DataFrame({
            "FirstName": ["John", "Sarah"],
            "Company": ["Acme Corp", "TechStart Inc"],
            "Title": ["CEO", "VP Operations"],
            "Industry": ["Manufacturing", "SaaS"],
            "Company Size": ["50-200", "10-50"],
            "Revenue": ["$5M-$10M", "$1M-$5M"],
            "Description": ["Leading manufacturer...", "B2B SaaS platform..."]
        })
        st.dataframe(example_df, width='stretch')

        st.markdown("""
        **Column names are auto-detected.** Supported variations:
        - FirstName, First Name, first_name, fname
        - Company, CompanyName, company, Organization
        - Title, Job Title, Position, Role
        - Description, Company Description, About
        - Industry, Vertical, Sector
        - Company Size, Employees, Size
        - Revenue, Annual Revenue, ARR
        """)

        # Show prompt examples
        st.subheader("📝 Prompt Examples")
        for pid, prompt in PROMPT_LIBRARY.items():
            with st.expander(f"Prompt {pid}: {prompt['name']}"):
                st.markdown(f"**Description:** {prompt['description']}")
                st.code(prompt['system_prompt'], language="text")

        return

    # Load uploaded CSV
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")

        # Show preview
        st.subheader("📊 Data Preview")
        st.dataframe(df.head(10), width='stretch')

        # Field mapping preview
        st.subheader("🔗 Field Mapping Preview")

        from scripts.generator import ConnectorEmailGenerator

        temp_config = {
            "FIELD_MAPPING": {
                "first_name": ["FirstName", "First Name", "first_name", "fname"],
                "company_name": ["Company", "CompanyName", "company"],
                "title": ["Title", "Job Title", "Position"],
                "description": ["Description", "Company Description", "About"],
                "industry": ["Industry", "Vertical", "Sector"],
                "company_size": ["Company Size", "Employees", "Size"],
                "revenue": ["Revenue", "Annual Revenue", "ARR"],
            },
            "PROMPT_ID": 1,
            "ROTATION_KEY": None,
        }

        temp_gen = ConnectorEmailGenerator(temp_config)
        field_map = temp_gen.auto_detect_fields(df)

        mapping_df = pd.DataFrame([
            {"Internal Field": k, "CSV Column": v if v else "❌ Not found"}
            for k, v in field_map.items()
        ])
        st.dataframe(mapping_df, width='stretch', hide_index=True)

        missing_fields = [k for k, v in field_map.items() if v is None]
        if missing_fields:
            st.warning(f"⚠️ Missing fields will be empty: {', '.join(missing_fields)}")

    except Exception as e:
        st.error(f"Error loading CSV: {e}")
        return

    # Generate button
    st.divider()

    if st.button("🚀 Generate Emails", type="primary", width='stretch'):
        if "OPENAI_API_KEY" not in os.environ and not dry_run:
            st.error("❌ OPENAI_API_KEY not found in environment variables")
            st.info("Add to .env file: `OPENAI_API_KEY=sk-...`")
            return

        # Build config
        config = {
            "INPUT_CSV": "temp_upload.csv",
            "OUTPUT_FOLDER": "results/",
            "FIELD_MAPPING": temp_config["FIELD_MAPPING"],
            "PROMPT_ID": selected_prompt_id,
            "ROTATION_KEY": rotation_key,
            "EMAIL_STRUCTURE": {
                "prefix": email_prefix,
                "use_ai_output": use_ai_output,
                "suffix": email_suffix,
            },
            "EXTRACT_VARIABLES": extract_variables,
            "VALIDATION": {
                "check_corporate_speak": check_corporate_speak,
                "forbidden_words": ["optimize", "solution", "solutions", "leverage", "streamline", "platform", "synergy"],
            },
            "OPENAI_MODEL": openai_model,
            "TEMPERATURE": temperature,
            "MAX_TOKENS": max_tokens,
            "BATCH_SIZE": batch_size,
            "RETRY_ATTEMPTS": retry_attempts,
            "RETRY_DELAY": 2,
            "SKIP_ROWS": skip_rows,
            "LIMIT_ROWS": limit_rows if limit_rows > 0 else None,
            "DRY_RUN": dry_run,
            "GENERATE_FOLLOWUPS": generate_followups,
        }

        # Save temp CSV
        temp_path = Path(__file__).parent / "data" / "input" / "temp_upload.csv"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(temp_path, index=False)

        # Generate output path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_name = PROMPT_LIBRARY[selected_prompt_id]["name"].replace(" ", "_").lower()
        output_filename = f"connector_emails_{prompt_name}_{timestamp}.csv"
        output_path = Path(__file__).parent / config["OUTPUT_FOLDER"] / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Process
        with st.spinner("🔄 Generating emails..."):
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                generator = ConnectorEmailGenerator(config)

                # Process CSV
                status_text.text("Processing rows...")
                generator.process_csv(str(temp_path), str(output_path))

                progress_bar.progress(100)
                status_text.text("✅ Complete!")

                # Show results
                st.success(f"🎉 Generated {SCRIPT_STATS['successful']} emails successfully!")

                # Stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Processed", SCRIPT_STATS['total_processed'])
                with col2:
                    st.metric("Successful", SCRIPT_STATS['successful'])
                with col3:
                    st.metric("Failed", SCRIPT_STATS['failed'])
                with col4:
                    st.metric("Insufficient Data", SCRIPT_STATS['insufficient_data'])

                if SCRIPT_STATS['corporate_speak_detected'] > 0:
                    st.warning(f"⚠️ Corporate speak detected in {SCRIPT_STATS['corporate_speak_detected']} outputs")

                # Load and display results
                result_df = pd.read_csv(output_path)
                st.subheader("📧 Generated Emails")
                st.dataframe(result_df, width='stretch')

                # Download button
                csv_data = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Results CSV",
                    data=csv_data,
                    file_name=output_filename,
                    mime="text/csv",
                    width='stretch'
                )

            except Exception as e:
                st.error(f"❌ Error during generation: {e}")
                import traceback
                st.code(traceback.format_exc())


if __name__ == "__main__":
    main()
