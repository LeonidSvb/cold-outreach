#!/usr/bin/env python3
"""
Pipeline status component for sidebar
"""

import streamlit as st
from typing import Optional


def render_pipeline_status():
    """
    Render pipeline status in sidebar showing data flow between tabs.
    Uses st.session_state to track progress.
    """
    st.sidebar.header("🔄 Pipeline Status")

    # Step 1: Scraping
    if 'scraped_data' in st.session_state and st.session_state['scraped_data'] is not None:
        df = st.session_state['scraped_data']
        st.sidebar.success(f"✅ Scraped: {len(df)} rows")

        # Show preview stats
        if 'email' in df.columns:
            with_email = len(df[df['email'].notna()])
            st.sidebar.caption(f"   └─ {with_email} with emails")
    else:
        st.sidebar.info("⏸️ No scraped data")

    # Step 2: Validation
    if 'validated_data' in st.session_state and st.session_state['validated_data'] is not None:
        df = st.session_state['validated_data']

        if 'verification_result' in df.columns:
            deliverable = len(df[df['verification_result'] == 'deliverable'])
            st.sidebar.success(f"✅ Validated: {deliverable} deliverable")

            # Show breakdown
            total = len(df)
            st.sidebar.caption(f"   └─ {deliverable}/{total} ({deliverable/total*100:.1f}%)")
        else:
            st.sidebar.success(f"✅ Validated: {len(df)} rows")
    else:
        st.sidebar.info("⏸️ No validated data")

    # Step 3: AI Processing
    if 'ai_processed_data' in st.session_state and st.session_state['ai_processed_data'] is not None:
        df = st.session_state['ai_processed_data']
        st.sidebar.success(f"✅ AI Processed: {len(df)} rows")

        # Show what was added
        if 'icebreaker' in df.columns:
            with_icebreaker = len(df[df['icebreaker'].notna()])
            st.sidebar.caption(f"   └─ {with_icebreaker} with icebreakers")
    else:
        st.sidebar.info("⏸️ No AI processed data")

    # Separator
    st.sidebar.markdown("---")

    # Quick actions
    st.sidebar.subheader("⚡ Quick Actions")

    # Clear all data
    if st.sidebar.button("🗑️ Clear All Data"):
        keys_to_clear = ['scraped_data', 'validated_data', 'ai_processed_data']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    # Download final results
    if 'ai_processed_data' in st.session_state and st.session_state['ai_processed_data'] is not None:
        df = st.session_state['ai_processed_data']
        csv = df.to_csv(index=False)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"final_results_{timestamp}.csv"

        st.sidebar.download_button(
            label="📥 Download Final CSV",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )

    elif 'validated_data' in st.session_state and st.session_state['validated_data'] is not None:
        df = st.session_state['validated_data']
        csv = df.to_csv(index=False)

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validated_results_{timestamp}.csv"

        st.sidebar.download_button(
            label="📥 Download Validated CSV",
            data=csv,
            file_name=filename,
            mime="text/csv"
        )
