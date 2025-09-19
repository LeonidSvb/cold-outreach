#!/usr/bin/env python3
"""
=== OPENAI CONTENT ANALYZER ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Advanced content analysis using OpenAI for lead qualification and personalization

FEATURES:
- Website content analysis and insights extraction
- Lead qualification scoring based on content
- Personalization hook generation
- Industry and company size detection
- Pain point identification
- Decision maker analysis

USAGE:
1. Set OpenAI API key in CONFIG
2. Configure analysis parameters
3. Run: python openai_content_analyzer.py

IMPROVEMENTS:
v1.0.0 - Initial version
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys

sys.path.append(str(Path(__file__).parent.parent))
from shared.logger import auto_log

CONFIG = {
    "OPENAI_API": {
        "API_KEY": os.getenv("OPENAI_API_KEY", "your_key_here"),
        "BASE_URL": "https://api.openai.com/v1",
        "MODEL": "gpt-4o-mini"
    },
    "PROCESSING": {
        "CONCURRENCY": 30,
        "BATCH_SIZE": 50
    },
    "OUTPUT": {
        "SAVE_JSON": True,
        "RESULTS_DIR": "results"
    }
}

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "items_analyzed": 0,
    "success_rate": 0.0
}

class OpenAIContentAnalyzer:
    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)

    @auto_log("openai_content_analyzer")
    async def analyze_content(self, content_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        print(f"Analyzing {len(content_data)} content items")

        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            self.session = session
            results = await self._process_content_parallel(content_data)

        await self._save_results(results, start_time)
        return results

    async def _process_content_parallel(self, content_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        semaphore = asyncio.Semaphore(self.config["PROCESSING"]["CONCURRENCY"])

        async def process_with_semaphore(item):
            async with semaphore:
                return await self._analyze_single_item(item)

        tasks = [process_with_semaphore(item) for item in content_data]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def _analyze_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        Analyze this company/website content and provide insights:

        Company: {item.get('company_name', 'Unknown')}
        Website: {item.get('website', 'Unknown')}
        Content: {item.get('content', 'No content')}

        Provide analysis in JSON format:
        {{
            "pain_points": ["list of likely business challenges"],
            "industry": "detected industry",
            "company_size": "small/medium/large",
            "decision_makers": ["likely decision maker titles"],
            "personalization_hooks": ["specific hooks for outreach"],
            "priority_score": 1-10
        }}
        """

        try:
            url = f"{self.config['OPENAI_API']['BASE_URL']}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.config['OPENAI_API']['API_KEY']}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.config["OPENAI_API"]["MODEL"],
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.3
            }

            async with self.session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    analysis = data["choices"][0]["message"]["content"]

                    result = item.copy()
                    result["openai_analysis"] = analysis
                    result["analyzed_at"] = datetime.now().isoformat()
                    return result

        except Exception as e:
            print(f"Analysis failed: {e}")

        return item

    async def _save_results(self, results: List[Dict[str, Any]], start_time: float):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "processing_time": time.time() - start_time,
                "total_items": len(results)
            },
            "results": results
        }

        filename = f"content_analysis_{timestamp}.json"
        filepath = self.results_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"Analysis saved: {filename}")

async def main():
    analyzer = OpenAIContentAnalyzer()

    sample_data = [
        {
            "company_name": "Tech Corp",
            "website": "techcorp.com",
            "content": "We provide software solutions for enterprises"
        }
    ]

    await analyzer.analyze_content(sample_data)

if __name__ == "__main__":
    asyncio.run(main())