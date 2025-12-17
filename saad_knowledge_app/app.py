#!/usr/bin/env python3
"""
SAAD KNOWLEDGE BASE - Interactive Q&A
Built from 125 YouTube videos by Saad Belcaid

Features:
- Multiple quotes per video
- Saad's tone of voice
- Approximate timestamps
- User's own API key
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from collections import defaultdict

try:
    import streamlit as st
    from openai import OpenAI
except ImportError:
    print("ERROR: Install dependencies: pip install streamlit openai numpy")
    sys.exit(1)

# Page config
st.set_page_config(
    page_title="Saad Knowledge Base",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .video-section {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .quote-box {
        background-color: #ffffff;
        border-left: 3px solid #ffa500;
        padding: 1rem;
        margin: 0.75rem 0;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .timestamp-link {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        text-decoration: none;
        font-size: 0.9rem;
        margin-right: 0.5rem;
    }
    .relevance-badge {
        display: inline-block;
        background-color: #4caf50;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-size: 0.85rem;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
    }
    .api-key-section {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
@st.cache_data
def load_vectors():
    """Load vectors from JSON file"""
    vectors_file = Path(__file__).parent / "saad_vectors.json"

    if not vectors_file.exists():
        st.error("""
        ⚠️ Vector database not found!

        Please ensure `saad_vectors.json` is in the same folder as this app.
        """)
        st.stop()

    with open(vectors_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity"""
    a_np = np.array(a)
    b_np = np.array(b)
    return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))

def format_timestamp(seconds: int) -> str:
    """Convert seconds to MM:SS format"""
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins}:{secs:02d}"

def calculate_approximate_timestamp(chunk_index: int, video_chunks: List[Dict]) -> int:
    """
    Calculate approximate timestamp based on chunk position
    Returns seconds
    """
    if not video_chunks:
        return 0

    total_chunks = len(video_chunks)
    position_ratio = chunk_index / max(total_chunks, 1)

    # Assume average video is 10 minutes (600 seconds)
    # This is a rough estimate - ideally we'd have exact duration
    estimated_duration = 600

    return int(position_ratio * estimated_duration)

def add_timestamp_to_url(url: str, seconds: int) -> str:
    """Add timestamp parameter to YouTube URL"""
    if "?" in url:
        return f"{url}&t={seconds}s"
    else:
        return f"{url}?t={seconds}s"

def search_and_group_by_video(
    question_embedding: List[float],
    vectors_data: Dict,
    top_k: int = 15
) -> Dict[str, List[Dict]]:
    """
    Find top-K chunks and group by video
    Returns: {video_title: [chunks...]}
    """
    similarities = []

    for idx, vector in enumerate(vectors_data["vectors"]):
        similarity = cosine_similarity(question_embedding, vector["embedding"])
        similarities.append({
            "idx": idx,
            "similarity": similarity,
            "text": vector["text"],
            "video_title": vector["video_title"],
            "video_url": vector["video_url"],
            "chunk_index": vector.get("chunk_index", 0)
        })

    # Sort by similarity
    similarities.sort(key=lambda x: x["similarity"], reverse=True)

    # Take top-K
    top_chunks = similarities[:top_k]

    # Group by video
    grouped = defaultdict(list)
    for chunk in top_chunks:
        grouped[chunk["video_title"]].append(chunk)

    return dict(grouped)

def generate_saad_style_answer(
    question: str,
    grouped_chunks: Dict[str, List[Dict]],
    client: OpenAI
) -> str:
    """Generate answer in Saad's tone of voice"""

    # Build context with multiple quotes per video
    context_parts = []

    for video_title, chunks in grouped_chunks.items():
        context_parts.append(f"\n=== From: {video_title} ===")
        for idx, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Quote {idx}] (Relevance: {chunk['similarity']:.1%})\n{chunk['text']}\n"
            )

    context = "\n".join(context_parts)

    system_prompt = """You are Saad Belcaid - a direct, no-BS sales systems expert who has built a $100K+/month agency.

YOUR PERSONALITY & TONE:
- Direct and straightforward (zero fluff)
- Use specific numbers ("$10K/month", "in 3 weeks", "105K this month")
- Give numbered action steps
- Reference real examples from your videos
- Confident but relatable
- Call out BS and common mistakes

HOW YOU SPEAK:
- "Look, here's the deal..."
- "Stop doing X. Do Y instead."
- "I made $15K from this one campaign..."
- "Here's exactly what you need to do: 1... 2... 3..."
- "Most people mess this up because..."

STRUCTURE YOUR ANSWER:
1. **Direct Answer** (1-2 sentences, straight to the point)
2. **Key Points with Quotes** (use actual quotes from context with "...")
3. **Summary in Your Voice** (brief, actionable, Saad-style)
4. **Action Steps** (numbered list if applicable)

IMPORTANT:
- Include DIRECT QUOTES from the context using quotation marks
- After quotes, add your own commentary in Saad's voice
- Be specific with numbers and timeframes
- Keep it actionable and practical

Context from your videos:
---
{context}
---"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt.format(context=context)},
                {"role": "user", "content": question}
            ],
            temperature=0.8,
            max_tokens=2000
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating answer: {str(e)}"

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []

if "vectors_data" not in st.session_state:
    with st.spinner("Loading Saad's knowledge base..."):
        st.session_state.vectors_data = load_vectors()

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    # API Key input
    st.markdown("""
    <div class="api-key-section">
        <strong>🔑 Your OpenAI API Key Required</strong>
        <p style="font-size: 0.9rem; margin-top: 0.5rem;">
        Your key is stored only in your browser session.<br>
        Get your key: <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="sk-proj-...",
        help="Your OpenAI API key (not saved anywhere)",
        key="api_key_input"
    )

    st.markdown("---")

    top_k = st.slider(
        "Number of sources",
        min_value=5,
        max_value=20,
        value=12,
        help="More sources = more comprehensive answer (but slower)"
    )

    st.markdown("---")

    # Stats
    metadata = st.session_state.vectors_data["metadata"]
    st.markdown("### 📊 Database Stats")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{metadata['total_videos']}</h2>
            <p>Videos</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="stat-box">
            <h2>{metadata['total_chunks']}</h2>
            <p>Chunks</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    - **Model:** {metadata['embedding_model']}
    - **Chunk size:** {metadata['chunk_size']} tokens
    - **Created:** {metadata['created_at'][:10]}
    """)

    st.markdown("---")

    if st.button("🗑️ Clear history"):
        st.session_state.history = []
        st.rerun()

# Main content
st.markdown('<h1 class="main-header">🎯 Saad Knowledge Base</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Get insights from 125 Saad Belcaid videos on sales systems, automation & AI freelancing</p>', unsafe_allow_html=True)

# Example questions
with st.expander("💡 Example Questions"):
    st.markdown("""
    - What are the best niches for sales systems agencies?
    - How can I get my first client in 2 weeks?
    - What cold email strategies does Saad use?
    - How to price automation services?
    - What's the connector business model?
    - How did Saad build a $100K/month business?
    """)

# Question input
question = st.text_area(
    "Your question:",
    placeholder="Example: What are the best niches for sales systems agencies in 2025?",
    height=100,
    key="question_input"
)

col1, col2 = st.columns([1, 5])
with col1:
    ask_button = st.button("🚀 Ask Saad", type="primary", use_container_width=True)

# Process question
if ask_button and question:
    if not api_key:
        st.error("⚠️ Please enter your OpenAI API key in the sidebar")
        st.stop()

    if not api_key.startswith("sk-"):
        st.error("⚠️ Invalid API key format. Should start with 'sk-'")
        st.stop()

    with st.spinner("Searching Saad's videos..."):
        try:
            # Initialize OpenAI with user's key
            client = OpenAI(api_key=api_key)

            # Create embedding
            question_response = client.embeddings.create(
                model="text-embedding-3-small",
                input=question
            )
            question_embedding = question_response.data[0].embedding

            # Search and group by video
            grouped_chunks = search_and_group_by_video(
                question_embedding,
                st.session_state.vectors_data,
                top_k=top_k
            )

            # Generate answer in Saad's voice
            with st.spinner("Generating answer in Saad's style..."):
                answer = generate_saad_style_answer(question, grouped_chunks, client)

            # Save to history
            st.session_state.history.insert(0, {
                "question": question,
                "answer": answer,
                "grouped_chunks": grouped_chunks,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        except Exception as e:
            st.error(f"Error: {str(e)}")
            if "invalid_api_key" in str(e).lower():
                st.error("Your API key is invalid. Please check it and try again.")
            st.stop()

# Display results
if st.session_state.history:
    latest = st.session_state.history[0]

    st.markdown("---")

    # Question
    st.markdown(f"### ❓ Question")
    st.markdown(f"*{latest['question']}*")

    # Answer (in Saad's voice)
    st.markdown("### 💡 Answer from Saad")
    st.markdown(latest['answer'])

    st.markdown("---")

    # Sources grouped by video
    st.markdown(f"### 📚 Sources ({len(latest['grouped_chunks'])} videos)")

    for video_idx, (video_title, chunks) in enumerate(latest['grouped_chunks'].items(), 1):
        st.markdown(f"""
        <div class="video-section">
            <h4>🎬 Video {video_idx}: {video_title}</h4>
        </div>
        """, unsafe_allow_html=True)

        # Get all chunks for this video to calculate timestamps
        video_url = chunks[0]['video_url']

        for chunk_idx, chunk in enumerate(chunks, 1):
            # Calculate approximate timestamp
            approx_seconds = calculate_approximate_timestamp(
                chunk['chunk_index'],
                chunks
            )
            timestamp_url = add_timestamp_to_url(video_url, approx_seconds)
            timestamp_str = format_timestamp(approx_seconds)

            # Display quote with timestamp
            st.markdown(f"""
            <div class="quote-box">
                <div style="margin-bottom: 0.5rem;">
                    <a href="{timestamp_url}" target="_blank" class="timestamp-link">
                        ⏱️ ~{timestamp_str}
                    </a>
                    <span class="relevance-badge">{chunk['similarity']:.1%} match</span>
                </div>
                <p style="margin: 0; font-style: italic;">
                    "{chunk['text'][:400]}{'...' if len(chunk['text']) > 400 else ''}"
                </p>
            </div>
            """, unsafe_allow_html=True)

    # History
    if len(st.session_state.history) > 1:
        st.markdown("---")
        st.markdown("### 📜 Previous Questions")

        for idx, item in enumerate(st.session_state.history[1:], 1):
            with st.expander(f"{item['timestamp']} - {item['question'][:80]}..."):
                st.markdown("**Answer:**")
                st.markdown(item['answer'])
                st.markdown(f"**Sources:** {len(item['grouped_chunks'])} videos")

else:
    # Welcome message
    st.info("""
    👋 **Welcome to Saad's Knowledge Base!**

    This database contains insights from **125 YouTube videos** by Saad Belcaid covering:
    - 💼 Sales Systems & Automation
    - 🎯 Client Acquisition Strategies
    - 💰 Pricing & Business Models
    - 📧 Cold Email & Outreach
    - 🚀 Scaling Your Agency

    **To get started:**
    1. Enter your OpenAI API key in the sidebar (get one at platform.openai.com)
    2. Ask any question about Saad's content
    3. Get answers with direct quotes and approximate timestamps

    **Cost:** ~$0.0003 per question (less than a penny!)
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <small>
        Powered by OpenAI Embeddings + GPT-4o-mini<br>
        Database: 125 videos from @SaadBelcaid<br>
        <a href="https://github.com/yourusername/saad-knowledge-base" target="_blank">GitHub</a> |
        <a href="https://www.youtube.com/@SaadBelcaid" target="_blank">Saad's Channel</a>
    </small>
</div>
""", unsafe_allow_html=True)
