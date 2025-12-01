#!/usr/bin/env python3
"""
=== WEBSITE PERSONALIZATION ENRICHER ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Scrape accessible websites and create AI-powered personalization summaries
for cold email outreach

FEATURES:
- HTTP-only scraping (static sites)
- OpenAI summarization for personalization
- Extract: services, owner name, company info
- Parallel processing (25 concurrent)
- CSV output ready for email campaigns

КАК РАБОТАЕТ С ФРОНТЕНДОМ:
1. Frontend (WebScraperTab.tsx) отправляет FormData в API
2. API (/api/data-processor/stream/route.ts) запускает этот скрипт через spawn()
3. Параметры передаются через CLI: --input, --output, --workers, --model, --prompt
4. Скрипт парсит сайты, отправляет в OpenAI, сохраняет результат
5. Логи (print) стримятся обратно в Frontend через SSE

USAGE:
CLI (из терминала):
  python scraping_website_personalization_enricher.py \
    --input input.csv \
    --output output.csv \
    --workers 25 \
    --model gpt-4o-mini \
    --max-content-length 15000 \
    --prompt "Custom prompt with {{company_name}}"

Frontend (автоматически):
  Все параметры передаются из WebScraperTab → API → сюда
"""

import sys
import csv
import json
import re
import time
import random
import os
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from modules.shared.logging.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "INPUT_CSV": "modules/scraping/results/email_extraction_20251106_135242.csv",
    "MAX_WORKERS": 25,
    "TIMEOUT": 12,
    "MAX_CONTENT_LENGTH": 15000,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "OPENAI_MODEL": "gpt-4o-mini",
    "OPENAI_MAX_TOKENS": 500,
    "OPENAI_TEMPERATURE": 0.3
}

STATS = {
    "total": 0,
    "scraped": 0,
    "analyzed": 0,
    "failed": 0
}

def extract_clean_text(html_content: str) -> str:
    """Extract clean text from HTML"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()

        # Get text
        text = soup.get_text(separator=' ', strip=True)

        # Clean whitespace
        text = ' '.join(text.split())

        # Truncate if too long
        if len(text) > CONFIG["MAX_CONTENT_LENGTH"]:
            text = text[:CONFIG["MAX_CONTENT_LENGTH"]]

        return text
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return ""

def scrape_website_content(url: str) -> Dict:
    """Scrape website and extract clean text content"""
    result = {
        "url": url,
        "content": "",
        "title": "",
        "status": "pending"
    }

    if not url or url.strip() == '':
        result["status"] = "no_url"
        return result

    # Normalize URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    result["url"] = url

    try:
        # Add delay to be polite
        time.sleep(random.uniform(0.5, 1.2))

        response = requests.get(
            url,
            headers={'User-Agent': CONFIG["USER_AGENT"]},
            timeout=CONFIG["TIMEOUT"],
            allow_redirects=True
        )

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            if soup.title:
                result["title"] = soup.title.string.strip() if soup.title.string else ""

            # Extract clean text
            content = extract_clean_text(response.text)

            if len(content) > 200:
                result["content"] = content
                result["status"] = "success"
            else:
                result["status"] = "empty_content"
        else:
            result["status"] = f"http_{response.status_code}"

    except requests.exceptions.Timeout:
        result["status"] = "timeout"
    except requests.exceptions.ConnectionError:
        result["status"] = "connection_error"
    except Exception as e:
        result["status"] = f"error: {str(e)[:50]}"

    return result

def generate_personalization_summary(company_name: str, website: str, content: str, custom_prompt: Optional[str] = None) -> Dict:
    """
    Generate personalization summary using OpenAI

    НАЗНАЧЕНИЕ:
    Отправляет спарсенный текст сайта в OpenAI для извлечения структурированных данных

    ПАРАМЕТРЫ:
        company_name: Название компании из CSV
        website: URL сайта
        content: Спарсенный текст с сайта (HTML → clean text)
        custom_prompt: Кастомный промпт от пользователя (опционально)

    КАК РАБОТАЮТ ПРОМПТЫ:
    1. Если custom_prompt передан:
       - Заменяем плейсхолдеры {{company_name}}, {{website}}, {{content}}
       - Отправляем в OpenAI
    2. Если custom_prompt НЕ передан:
       - Используем default промпт который извлекает:
         * owner_name (имя владельца)
         * business_summary (описание бизнеса)
         * personalization_hook (фраза для персонализации)

    ПРИМЕР КАСТОМНОГО ПРОМПТА:
    "Analyze {{company_name}} ({{website}}). From {{content}}, extract JSON: {...}"

    СВЯЗЬ С ФРОНТЕНДОМ:
    Frontend → FormData('prompt') → API → args.prompt → custom_prompt
    """

    try:
        client = OpenAI()

        # === ОБРАБОТКА КАСТОМНОГО ИЛИ DEFAULT ПРОМПТА ===
        if custom_prompt:
            # Пользователь указал свой промпт - используем его
            # Заменяем плейсхолдеры на реальные значения
            prompt = custom_prompt.replace('{{company_name}}', company_name)
            prompt = prompt.replace('{{website}}', website)
            prompt = prompt.replace('{{content}}', content[:8000])
        else:
            # Используем default промпт (если пользователь не указал свой)
            prompt = f"""Analyze this company website and extract key personalization data for cold email outreach.

Company: {company_name}
Website: {website}
Content: {content[:8000]}

Extract and return ONLY valid JSON (no markdown, no code blocks):
{{
    "owner_name": "first and last name of owner/founder if found, otherwise null",
    "business_summary": "1-line casual description of what they do, include key details (max 25 words)",
    "personalization_hook": "1 casual phrase for icebreaker - their specialty, achievement, or unique vibe (max 15 words)"
}}

Examples:
{{
    "owner_name": "Mike Johnson",
    "business_summary": "HVAC services in Dallas - 24/7 emergency, 15+ years, focus on commercial buildings",
    "personalization_hook": "keeping commercial spaces cool with 24/7 emergency service"
}}

{{
    "owner_name": null,
    "business_summary": "Veteran-owned landscaping in Austin - affordable pricing, eco-friendly practices",
    "personalization_hook": "blending veteran discipline with eco-friendly lawn care"
}}

Rules:
- owner_name: extract ONLY if clearly stated (CEO, Founder, Owner). Return null if unsure.
- business_summary: casual tone, mention location/specialty/experience/values
- personalization_hook: natural phrase that fits "love how you [HOOK]" or "saw you're [HOOK]"

IMPORTANT: Return ONLY the JSON object, no other text."""

        response = client.chat.completions.create(
            model=CONFIG["OPENAI_MODEL"],
            messages=[
                {"role": "system", "content": "You are a B2B research analyst. Extract personalization data from company websites for cold outreach. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=CONFIG["OPENAI_MAX_TOKENS"],
            temperature=CONFIG["OPENAI_TEMPERATURE"]
        )

        ai_response = response.choices[0].message.content.strip()

        # Clean response - remove markdown code blocks if present
        ai_response = re.sub(r'^```json\s*', '', ai_response)
        ai_response = re.sub(r'^```\s*', '', ai_response)
        ai_response = re.sub(r'\s*```$', '', ai_response)
        ai_response = ai_response.strip()

        # Parse JSON
        analysis = json.loads(ai_response)

        return {
            "status": "success",
            "analysis": analysis,
            "tokens_used": response.usage.total_tokens
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}\nResponse: {ai_response[:200]}")
        return {
            "status": "json_error",
            "error": str(e),
            "raw_response": ai_response[:500]
        }
    except Exception as e:
        logger.error(f"OpenAI analysis failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def process_single_company(row: Dict, index: int, total: int, custom_prompt: Optional[str] = None) -> Dict:
    """Process a single company: scrape + analyze"""

    company_name = row.get('\ufeff"title"', row.get('title', 'Unknown'))
    website = row.get('website', '').strip()
    accessible = row.get('accessible', 'No')

    logger.info(f"[{index}/{total}] Processing: {company_name[:40]}")

    # Initialize enriched row
    enriched = {**row}
    enriched["scraped_content_length"] = 0
    enriched["ai_summary_status"] = "pending"
    enriched["owner_name"] = ""
    enriched["business_summary"] = ""
    enriched["personalization_hook"] = ""

    # Only process accessible sites
    if accessible != "Yes" or not website:
        enriched["ai_summary_status"] = "skipped_not_accessible"
        logger.warning(f"  Skipped (not accessible)")
        return enriched

    # Step 1: Scrape website
    logger.info(f"  Scraping website...")
    scrape_result = scrape_website_content(website)

    if scrape_result["status"] != "success":
        enriched["ai_summary_status"] = f"scrape_failed_{scrape_result['status']}"
        logger.warning(f"  Scraping failed: {scrape_result['status']}")
        STATS["failed"] += 1
        return enriched

    STATS["scraped"] += 1
    enriched["scraped_content_length"] = len(scrape_result["content"])
    logger.info(f"  Scraped {len(scrape_result['content'])} chars")

    # Step 2: Generate AI summary
    logger.info(f"  Generating AI summary...")
    ai_result = generate_personalization_summary(
        company_name,
        website,
        scrape_result["content"],
        custom_prompt
    )

    if ai_result["status"] == "success":
        analysis = ai_result["analysis"]

        enriched["ai_summary_status"] = "success"
        enriched["owner_name"] = analysis.get("owner_name") or ""
        enriched["business_summary"] = analysis.get("business_summary", "")
        enriched["personalization_hook"] = analysis.get("personalization_hook", "")

        STATS["analyzed"] += 1
        logger.info(f"  ✓ AI summary generated successfully")
    else:
        enriched["ai_summary_status"] = f"ai_failed_{ai_result['status']}"
        enriched["ai_error"] = ai_result.get("error", "")
        logger.error(f"  AI analysis failed: {ai_result['status']}")
        STATS["failed"] += 1

    return enriched

def process_csv_parallel(input_file: str, custom_prompt: Optional[str] = None, output_path: Optional[str] = None) -> List[Dict]:
    """Process CSV with parallel scraping and AI analysis"""

    logger.info(f"Reading CSV: {input_file}")

    # Read CSV
    rows = []
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Filter only accessible sites
    accessible_rows = [r for r in rows if r.get('accessible') == 'Yes']

    total = len(accessible_rows)
    STATS["total"] = total

    logger.info(f"Found {total} accessible websites to process")
    logger.info(f"Starting parallel processing with {CONFIG['MAX_WORKERS']} workers...")

    results = []

    # Process in parallel
    with ThreadPoolExecutor(max_workers=CONFIG["MAX_WORKERS"]) as executor:
        future_to_row = {
            executor.submit(process_single_company, row, i+1, total, custom_prompt): row
            for i, row in enumerate(accessible_rows)
        }

        for future in as_completed(future_to_row):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Task failed: {e}")

    # Add back non-accessible rows without processing
    non_accessible = [r for r in rows if r.get('accessible') != 'Yes']
    for row in non_accessible:
        enriched = {**row}
        enriched["ai_summary_status"] = "skipped_not_accessible"
        results.append(enriched)

    return results

def save_results(results: List[Dict], output_path: Optional[str] = None) -> str:
    """Save enriched results to CSV"""

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = Path("modules/scraping/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        output_file = results_dir / f"personalization_enriched_{timestamp}.csv"

    if not results:
        logger.warning("No results to save")
        return ""

    # Write CSV
    fieldnames = list(results[0].keys())

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Results saved to: {output_file}")
    return str(output_file)

def print_summary():
    """Print processing summary"""

    print(f"\n{'='*70}")
    print(f"WEBSITE PERSONALIZATION ENRICHMENT SUMMARY")
    print(f"{'='*70}")
    print(f"Total accessible sites:    {STATS['total']}")
    print(f"Successfully scraped:      {STATS['scraped']} ({STATS['scraped']/max(1,STATS['total'])*100:.1f}%)")
    print(f"AI summaries generated:    {STATS['analyzed']} ({STATS['analyzed']/max(1,STATS['total'])*100:.1f}%)")
    print(f"Failed:                    {STATS['failed']} ({STATS['failed']/max(1,STATS['total'])*100:.1f}%)")
    print(f"{'='*70}\n")

def parse_args():
    """
    Парсинг аргументов командной строки

    ЧТО ПРОИСХОДИТ:
    Frontend → FormData → API → spawn('py', ['script.py', '--param', 'value']) → argparse

    ПРИМЕР ВЫЗОВА ИЗ API:
    spawn('py', [
        'scraping_website_personalization_enricher.py',
        '--input', '/path/to/input.csv',
        '--output', '/path/to/output.csv',
        '--workers', '25',
        '--model', 'gpt-4o-mini',
        '--max-content-length', '15000',
        '--prompt', 'Custom prompt with {{company_name}}'
    ])

    ПАРАМЕТРЫ:
    --input: Путь к входному CSV (от API)
    --output: Путь к выходному CSV (от API)
    --workers: Количество параллельных потоков (от пользователя)
    --model: OpenAI модель (от пользователя)
    --max-content-length: Макс длина текста для AI (от пользователя)
    --prompt: Кастомный промпт (от пользователя, опционально)
    """
    parser = argparse.ArgumentParser(description='Website Personalization Enricher')
    parser.add_argument('--input', type=str, help='Input CSV file path')
    parser.add_argument('--output', type=str, help='Output CSV file path')
    parser.add_argument('--workers', type=int, help='Number of parallel workers')
    parser.add_argument('--prompt', type=str, help='Custom OpenAI prompt (use {{company_name}}, {{website}}, {{content}} placeholders)')
    parser.add_argument('--model', type=str, help='OpenAI model to use (e.g., gpt-4o-mini, gpt-4o)')
    parser.add_argument('--max-content-length', type=int, help='Maximum content length to process')
    return parser.parse_args()

def main():
    """
    Main execution

    ПОТОК ДАННЫХ:
    1. Получаем параметры из argparse (от API или CLI)
    2. Применяем параметры к CONFIG (перезаписываем defaults)
    3. Читаем CSV
    4. Обрабатываем параллельно (scrape → AI analysis)
    5. Сохраняем результат
    6. Логи выводим через print() → stdout → API стримит их в Frontend

    СВЯЗЬ С ФРОНТЕНДОМ:
    Frontend State → FormData → API → spawn() → args → CONFIG → Processing
    """

    logger.info("=== WEBSITE PERSONALIZATION ENRICHER STARTED ===")

    # === 1. ПОЛУЧАЕМ ПАРАМЕТРЫ ОТ API (или CLI) ===
    args = parse_args()

    # === 2. ПРИМЕНЯЕМ ПАРАМЕТРЫ К CONFIG ===
    # Если параметр передан через CLI/API, перезаписываем default значение

    # Input/Output пути (обязательные от API)
    input_csv = args.input if args.input else CONFIG["INPUT_CSV"]
    custom_prompt = args.prompt  # Может быть None (тогда используем default промпт)

    # Параметры обработки (от пользователя из Frontend)
    if args.workers:
        CONFIG["MAX_WORKERS"] = args.workers
        # Параллельность: сколько сайтов обрабатывать одновременно

    if args.model:
        CONFIG["OPENAI_MODEL"] = args.model
        logger.info(f"Using model: {args.model}")
        # Модель OpenAI: gpt-4o-mini (дешевая) или gpt-4o (точная)

    if args.max_content_length:
        CONFIG["MAX_CONTENT_LENGTH"] = args.max_content_length
        logger.info(f"Max content length: {args.max_content_length}")
        # Макс длина текста отправляемого в AI (меньше = дешевле)

    # Промпт (кастомный или default)
    if custom_prompt:
        logger.info("Using custom prompt from CLI")
        # Пользователь указал свой промпт в Frontend
    else:
        logger.info("Using default prompt")
        # Используем встроенный промпт

    start_time = time.time()

    # Process CSV
    results = process_csv_parallel(input_csv, custom_prompt, args.output)

    # Save results
    output_file = save_results(results, args.output)

    # Print summary
    print_summary()

    elapsed = time.time() - start_time
    logger.info(f"Processing completed in {elapsed:.1f} seconds")

    if STATS['analyzed'] > 0:
        logger.info(f"Average: {elapsed/STATS['analyzed']:.1f} sec/company")

    logger.info(f"Results saved to: {output_file}")

    # Show sample results
    successful = [r for r in results if r.get('ai_summary_status') == 'success']
    if successful:
        print(f"\n{'='*70}")
        print(f"SAMPLE PERSONALIZATION DATA (first 5)")
        print(f"{'='*70}")
        for i, result in enumerate(successful[:5], 1):
            title_field = [k for k in result.keys() if 'title' in k.lower()][0]
            print(f"\n{i}. {result[title_field]}")
            print(f"   Owner: {result.get('owner_name', 'N/A')}")
            print(f"   Summary: {result.get('business_summary', 'N/A')}")
            print(f"   Hook: {result.get('personalization_hook', 'N/A')}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
