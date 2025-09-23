#!/usr/bin/env python3
"""
=== CONTENT PROCESSOR ===
Version: 1.0.0 | Created: 2025-09-21

PURPOSE:
AI-powered content processing for extracted website data.
Generates personalized insights and summaries for cold outreach.

FEATURES:
- OpenAI GPT-4 content summarization
- Personalization insights extraction
- Contact information discovery
- Company analysis and profiling
- Batch processing with token optimization

USAGE:
from content_processor import ContentProcessor
processor = ContentProcessor()
results = await processor.process_domains_batch(extracted_data)

IMPROVEMENTS:
v1.0.0 - Initial implementation with OpenAI integration
"""

import os
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI not installed. AI processing will be disabled.")

class ContentProcessor:
    """AI-powered content processing and summarization"""

    def __init__(self):
        self.config = {
            "model": "gpt-3.5-turbo",
            "max_tokens_per_request": 4000,
            "temperature": 0.3,
            "batch_size": 5,
            "max_text_length": 8000,  # Max text to send to AI
            "retry_attempts": 3,
            "rate_limit_delay": 1.0
        }

        # Initialize OpenAI client
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = OpenAI(api_key=api_key)
                self.ai_enabled = True
            else:
                print("Warning: OPENAI_API_KEY not found. AI processing disabled.")
                self.ai_enabled = False
        else:
            self.ai_enabled = False

        self.processing_stats = {
            "domains_processed": 0,
            "ai_requests_made": 0,
            "total_tokens_used": 0,
            "total_cost": 0.0,
            "errors": 0
        }

    async def process_domains_batch(self, extracted_data: Dict[str, Any], batch_size: int = None) -> Dict[str, Any]:
        """
        Process multiple domains with AI summarization

        Args:
            extracted_data: Dictionary of domain -> extraction results
            batch_size: Number of domains to process in each batch

        Returns:
            Dictionary of domain -> AI analysis results
        """

        if not self.ai_enabled:
            print("AI processing disabled - returning empty results")
            return {}

        batch_size = batch_size or self.config["batch_size"]
        print(f"Starting AI content processing: {len(extracted_data)} domains, batch size {batch_size}")

        # Filter domains with sufficient content
        valid_domains = {
            domain: data for domain, data in extracted_data.items()
            if data.get("success", False) and data.get("total_text_length", 0) > 200
        }

        if not valid_domains:
            print("No domains with sufficient content for AI processing")
            return {}

        print(f"Processing {len(valid_domains)} domains with AI...")

        # Process in batches
        all_results = {}
        domains_list = list(valid_domains.keys())

        for i in range(0, len(domains_list), batch_size):
            batch_domains = domains_list[i:i + batch_size]
            batch_data = {domain: valid_domains[domain] for domain in batch_domains}

            print(f"Processing batch {i//batch_size + 1}: {len(batch_domains)} domains")

            try:
                batch_results = await self._process_batch(batch_data)
                all_results.update(batch_results)

                # Rate limiting
                if i + batch_size < len(domains_list):
                    await asyncio.sleep(self.config["rate_limit_delay"])

            except Exception as e:
                print(f"Batch processing error: {e}")
                self.processing_stats["errors"] += 1

        self._print_processing_summary()
        return all_results

    async def _process_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single batch of domains"""

        batch_results = {}

        for domain, data in batch_data.items():
            try:
                # Prepare content for AI
                content_text = self._prepare_content_for_ai(data)

                if not content_text:
                    continue

                # Generate AI analysis
                ai_result = await self._generate_ai_analysis(domain, content_text)

                if ai_result:
                    batch_results[domain] = ai_result
                    self.processing_stats["domains_processed"] += 1

            except Exception as e:
                print(f"Error processing {domain}: {e}")
                self.processing_stats["errors"] += 1

        return batch_results

    def _prepare_content_for_ai(self, extraction_data: Dict[str, Any]) -> str:
        """Prepare extracted content for AI analysis"""

        pages = extraction_data.get("pages", [])
        if not pages:
            return ""

        # Combine text from all pages
        all_text = []
        for page in pages:
            text = page.get("text", "").strip()
            if text:
                # Add page URL context
                url = page.get("url", "")
                page_header = f"\n--- Content from {url} ---\n"
                all_text.append(page_header + text)

        combined_text = "\n".join(all_text)

        # Truncate if too long
        if len(combined_text) > self.config["max_text_length"]:
            combined_text = combined_text[:self.config["max_text_length"]] + "\n[Content truncated...]"

        return combined_text

    async def _generate_ai_analysis(self, domain: str, content_text: str) -> Optional[Dict[str, Any]]:
        """Generate AI analysis for domain content"""

        prompt = self._build_analysis_prompt(domain, content_text)

        try:
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=self.config["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert business analyst specializing in website analysis for B2B sales and outreach. Provide structured, actionable insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.config["max_tokens_per_request"],
                temperature=self.config["temperature"]
            )

            # Track usage
            usage = response.usage
            self.processing_stats["ai_requests_made"] += 1
            self.processing_stats["total_tokens_used"] += usage.total_tokens

            # Estimate cost (GPT-3.5-turbo pricing)
            cost = (usage.prompt_tokens * 0.0005 + usage.completion_tokens * 0.0015) / 1000
            self.processing_stats["total_cost"] += cost

            # Parse response
            content = response.choices[0].message.content

            # Try to parse as JSON, fallback to text
            try:
                analysis_result = json.loads(content)
            except json.JSONDecodeError:
                analysis_result = {"raw_analysis": content}

            # Add metadata
            analysis_result.update({
                "processing_time": time.time() - start_time,
                "tokens_used": usage.total_tokens,
                "cost": cost,
                "model": self.config["model"],
                "timestamp": datetime.now().isoformat()
            })

            return analysis_result

        except Exception as e:
            print(f"AI analysis error for {domain}: {e}")
            return None

    def _build_analysis_prompt(self, domain: str, content_text: str) -> str:
        """Build AI analysis prompt"""

        prompt = f"""
Analyze the following website content for B2B sales outreach insights.

WEBSITE: {domain}

CONTENT:
{content_text}

Please provide a JSON response with the following structure:

{{
    "company_overview": {{
        "name": "Company name if found",
        "industry": "Primary industry/sector",
        "size_estimate": "startup/small/medium/large/enterprise",
        "business_model": "B2B/B2C/marketplace/etc",
        "description": "Brief company description"
    }},
    "personalization_insights": [
        {{
            "type": "recent_news/achievement/hiring/product_launch/expansion",
            "insight": "Specific insight for personalization",
            "confidence": "high/medium/low",
            "source_context": "Where this was found on the site"
        }}
    ],
    "contact_information": {{
        "emails": ["found emails"],
        "phones": ["found phone numbers"],
        "addresses": ["found addresses"],
        "social_media": ["found social profiles"]
    }},
    "technologies": [
        "List of technologies/tools they use or mention"
    ],
    "outreach_recommendations": {{
        "best_approach": "email/phone/linkedin/etc",
        "key_pain_points": ["identified pain points"],
        "value_propositions": ["what might interest them"],
        "conversation_starters": ["personalized conversation starters"]
    }},
    "confidence_score": 85,
    "analysis_notes": "Any additional observations or red flags"
}}

Focus on actionable insights for personalized B2B outreach. If information is not available, use null or empty arrays.
"""

        return prompt

    def _print_processing_summary(self):
        """Print AI processing summary"""

        stats = self.processing_stats

        print(f"\n=== AI CONTENT PROCESSING COMPLETE ===")
        print(f"Domains Processed: {stats['domains_processed']}")
        print(f"AI Requests: {stats['ai_requests_made']}")
        print(f"Total Tokens: {stats['total_tokens_used']:,}")
        print(f"Estimated Cost: ${stats['total_cost']:.4f}")
        print(f"Errors: {stats['errors']}")

        if stats['domains_processed'] > 0:
            print(f"Avg Cost per Domain: ${stats['total_cost']/stats['domains_processed']:.4f}")
            print(f"Avg Tokens per Domain: {stats['total_tokens_used']/stats['domains_processed']:.0f}")

    async def process_single_domain(self, domain: str, extraction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single domain (convenience method)"""

        if not self.ai_enabled:
            return None

        content_text = self._prepare_content_for_ai(extraction_data)
        if not content_text:
            return None

        return await self._generate_ai_analysis(domain, content_text)

# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

async def main():
    """Test the content processor"""

    # Mock extraction data for testing
    test_data = {
        "example.com": {
            "success": True,
            "total_text_length": 1500,
            "pages": [
                {
                    "url": "https://example.com",
                    "text": "Example Domain. This domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission."
                }
            ]
        }
    }

    processor = ContentProcessor()

    if processor.ai_enabled:
        print("Testing Content Processor with AI...")
        print("=" * 50)

        results = await processor.process_domains_batch(test_data)

        for domain, analysis in results.items():
            print(f"\nDomain: {domain}")
            print(f"Analysis: {json.dumps(analysis, indent=2)}")
    else:
        print("AI processing not available - check OPENAI_API_KEY")

if __name__ == "__main__":
    asyncio.run(main())