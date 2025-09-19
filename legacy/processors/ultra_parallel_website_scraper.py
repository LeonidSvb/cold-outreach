#!/usr/bin/env python3
"""
ULTRA PARALLEL Website Intelligence Scraper
Максимально быстрая 2-фазная архитектура для обработки 2000+ сайтов

АРХИТЕКТУРА:
ФАЗА 1: Массовый HTTP скрейпинг (20-50 потоков)
ФАЗА 2: Батч AI обработка (оптимальные батчи по токенам)

ЦЕЛЬ: 2000 сайтов за 15-30 минут вместо 5+ часов
"""

import sys
import os
import time
import json
import pandas as pd
from datetime import datetime
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
from html.parser import HTMLParser
from typing import List, Dict, Set, Optional, Tuple

# Добавляем путь к .env
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from dotenv import load_dotenv
load_dotenv()

ULTRA_CONFIG = {
    "max_http_workers": 30,  # Максимум HTTP потоков
    "max_ai_workers": 5,     # Максимум AI потоков (rate limit)
    "batch_size_tokens": 15000,  # Размер AI батча по токенам
    "max_pages_per_domain": 30,  # Лимит страниц на домен
    "http_timeout": 10,      # HTTP таймаут
    "retry_attempts": 2,     # Повторные попытки
    "save_raw_data": True,   # Сохранять сырые данные
    "ai_model": "gpt-3.5-turbo"
}

class HTMLLinkExtractor(HTMLParser):
    """Быстрый парсер для извлечения ссылок"""
    
    def __init__(self):
        super().__init__()
        self.links = []
        self.base_domain = ""
        
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href' and attr[1]:
                    href = attr[1].strip()
                    if href and not href.startswith('#') and not href.startswith('javascript:'):
                        self.links.append(href)

class UltraParallelScraper:
    """Ультра-быстрый скрейпер с 2-фазной архитектурой"""
    
    def __init__(self):
        self.session_id = f"ultra_parallel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = time.time()
        self.phase1_results = {}  # Результаты HTTP скрейпинга
        self.phase2_results = {}  # Результаты AI анализа
        self.progress_stats = {
            "phase1_completed": 0,
            "phase1_total": 0,
            "phase2_completed": 0,
            "phase2_total": 0,
            "errors": []
        }
        self.lock = threading.Lock()
        
    def log(self, message: str, level: str = "INFO"):
        """Потокобезопасное логирование"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def get_progress_info(self) -> str:
        """Получить информацию о прогрессе"""
        with self.lock:
            elapsed = time.time() - self.start_time
            p1_pct = (self.progress_stats["phase1_completed"] / max(self.progress_stats["phase1_total"], 1)) * 100
            p2_pct = (self.progress_stats["phase2_completed"] / max(self.progress_stats["phase2_total"], 1)) * 100
            
            return (f"🚀 ПРОГРЕСС: Phase1 {self.progress_stats['phase1_completed']}/{self.progress_stats['phase1_total']} "
                   f"({p1_pct:.1f}%) | Phase2 {self.progress_stats['phase2_completed']}/{self.progress_stats['phase2_total']} "
                   f"({p2_pct:.1f}%) | Время: {elapsed:.0f}с | Ошибки: {len(self.progress_stats['errors'])}")

    def scrape_domain_fast(self, domain: str) -> Dict:
        """Быстрый HTTP скрейпинг одного домена"""
        result = {
            "domain": domain,
            "pages": [],
            "total_pages": 0,
            "scrape_time": 0,
            "success": False,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            # Нормализуем домен
            if not domain.startswith(('http://', 'https://')):
                domain_url = f"https://{domain}"
            else:
                domain_url = domain
                
            # Создаем HTTP context с таймаутом
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Скрейпим основную страницу
            discovered_pages = set([domain_url])
            pages_data = []
            
            def scrape_page(url: str) -> Optional[Dict]:
                try:
                    req = urllib.request.Request(url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    with urllib.request.urlopen(req, timeout=ULTRA_CONFIG["http_timeout"], context=ctx) as response:
                        content = response.read().decode('utf-8', errors='ignore')
                        
                        # Извлекаем ссылки
                        parser = HTMLLinkExtractor()
                        parser.feed(content)
                        
                        # Фильтруем ссылки
                        internal_links = []
                        base_domain = urllib.parse.urlparse(url).netloc
                        
                        for link in parser.links:
                            if link.startswith('/'):
                                full_link = urllib.parse.urljoin(url, link)
                                if urllib.parse.urlparse(full_link).netloc == base_domain:
                                    internal_links.append(full_link)
                            elif link.startswith(('http://', 'https://')):
                                if urllib.parse.urlparse(link).netloc == base_domain:
                                    internal_links.append(link)
                        
                        return {
                            "url": url,
                            "content": content[:5000],  # Первые 5KB
                            "title": self.extract_title(content),
                            "links": internal_links[:20],  # Максимум 20 ссылок
                            "content_length": len(content)
                        }
                        
                except Exception as e:
                    return {"url": url, "error": str(e)}
            
            # Скрейпим основную страницу
            main_page = scrape_page(domain_url)
            if main_page and "error" not in main_page:
                pages_data.append(main_page)
                
                # Добавляем найденные ссылки
                for link in main_page.get("links", [])[:ULTRA_CONFIG["max_pages_per_domain"]]:
                    if link not in discovered_pages:
                        discovered_pages.add(link)
                        
                # Скрейпим дополнительные страницы (ограниченно)
                additional_pages = list(discovered_pages - {domain_url})[:10]  # Максимум 10 доп страниц
                
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_url = {executor.submit(scrape_page, url): url for url in additional_pages}
                    
                    for future in as_completed(future_to_url, timeout=30):
                        try:
                            page_data = future.result()
                            if page_data and "error" not in page_data:
                                pages_data.append(page_data)
                        except Exception as e:
                            pass  # Пропускаем ошибки дополнительных страниц
            
            result["pages"] = pages_data
            result["total_pages"] = len(pages_data)
            result["success"] = len(pages_data) > 0
            
        except Exception as e:
            result["error"] = str(e)
            
        result["scrape_time"] = time.time() - start_time
        return result
    
    def extract_title(self, content: str) -> str:
        """Извлечь title из HTML"""
        try:
            match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()[:100]
        except:
            pass
        return "No title"
    
    def phase1_mass_http_scraping(self, domains: List[str]):
        """ФАЗА 1: Массовый HTTP скрейпинг"""
        self.log(f"🚀 ФАЗА 1: Массовый HTTP скрейпинг {len(domains)} доменов с {ULTRA_CONFIG['max_http_workers']} потоками")
        
        with self.lock:
            self.progress_stats["phase1_total"] = len(domains)
            self.progress_stats["phase1_completed"] = 0
        
        # Прогресс-монитор в отдельном потоке
        def progress_monitor():
            while True:
                self.log(self.get_progress_info())
                time.sleep(15)  # Каждые 15 секунд
                with self.lock:
                    if self.progress_stats["phase1_completed"] >= self.progress_stats["phase1_total"]:
                        break
        
        monitor_thread = threading.Thread(target=progress_monitor, daemon=True)
        monitor_thread.start()
        
        # Массовый скрейпинг
        with ThreadPoolExecutor(max_workers=ULTRA_CONFIG["max_http_workers"]) as executor:
            future_to_domain = {executor.submit(self.scrape_domain_fast, domain): domain for domain in domains}
            
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    result = future.result()
                    self.phase1_results[domain] = result
                    
                    with self.lock:
                        self.progress_stats["phase1_completed"] += 1
                        if not result["success"]:
                            self.progress_stats["errors"].append(f"HTTP error for {domain}: {result.get('error', 'Unknown')}")
                            
                except Exception as e:
                    with self.lock:
                        self.progress_stats["phase1_completed"] += 1
                        self.progress_stats["errors"].append(f"Exception for {domain}: {str(e)}")
        
        successful_scrapes = sum(1 for r in self.phase1_results.values() if r["success"])
        total_pages = sum(r["total_pages"] for r in self.phase1_results.values())
        
        self.log(f"✅ ФАЗА 1 ЗАВЕРШЕНА: {successful_scrapes}/{len(domains)} доменов, {total_pages} страниц")
        
        # Сохраняем сырые данные
        if ULTRA_CONFIG["save_raw_data"]:
            raw_file = f"raw_scraping_data_{self.session_id}.json"
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(self.phase1_results, f, indent=2, ensure_ascii=False)
            self.log(f"💾 Сырые данные сохранены: {raw_file}")
    
    def prepare_ai_batches(self) -> List[Dict]:
        """Подготовить оптимальные батчи для AI обработки"""
        self.log("📦 Подготовка AI батчей по токенам...")
        
        batches = []
        current_batch = []
        current_tokens = 0
        
        for domain, result in self.phase1_results.items():
            if not result["success"]:
                continue
                
            # Оцениваем токены для домена (примерно)
            domain_content = ""
            for page in result["pages"]:
                domain_content += page.get("content", "") + page.get("title", "")
            
            # Грубая оценка токенов (1 токен ≈ 4 символа)
            estimated_tokens = len(domain_content) // 4 + 200  # +200 для промпта
            
            if current_tokens + estimated_tokens > ULTRA_CONFIG["batch_size_tokens"] and current_batch:
                # Начинаем новый батч
                batches.append({
                    "domains": current_batch.copy(),
                    "estimated_tokens": current_tokens
                })
                current_batch = [domain]
                current_tokens = estimated_tokens
            else:
                current_batch.append(domain)
                current_tokens += estimated_tokens
        
        # Добавляем последний батч
        if current_batch:
            batches.append({
                "domains": current_batch.copy(),
                "estimated_tokens": current_tokens
            })
        
        self.log(f"📦 Создано {len(batches)} AI батчей, среднее размер: {len(current_batch)} доменов")
        return batches
    
    def process_ai_batch(self, batch: Dict) -> Dict:
        """Обработать один AI батч"""
        batch_start = time.time()
        domains = batch["domains"]
        
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
            # Подготавливаем данные для анализа
            batch_data = []
            for domain in domains:
                result = self.phase1_results[domain]
                if result["success"]:
                    pages_info = []
                    for page in result["pages"]:
                        pages_info.append({
                            "url": page["url"],
                            "title": page.get("title", ""),
                            "content_preview": page.get("content", "")[:500]
                        })
                    batch_data.append({
                        "domain": domain,
                        "pages": pages_info
                    })
            
            # AI промпт для батч-обработки
            prompt = f"""Analyze these {len(batch_data)} company websites and prioritize their most valuable pages for B2B outreach personalization.

For each domain, identify the 3 most valuable pages from: About, Services, Case Studies, Team, Recent News, Products.

Return JSON array with this structure:
[{{
  "domain": "example.com",
  "selected_pages": [
    {{"url": "page_url", "value_score": 0.9, "reason": "why valuable"}},
    ...
  ]
}}]

Website data: {json.dumps(batch_data, ensure_ascii=False)}"""

            # Отправляем запрос
            response = openai.ChatCompletion.create(
                model=ULTRA_CONFIG["ai_model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=4000
            )
            
            ai_result = response.choices[0].message.content
            
            # Парсим JSON ответ
            try:
                parsed_results = json.loads(ai_result)
                batch_results = {}
                
                for domain_result in parsed_results:
                    domain = domain_result.get("domain")
                    if domain in domains:
                        batch_results[domain] = {
                            "ai_analysis": domain_result,
                            "processing_time": time.time() - batch_start,
                            "success": True
                        }
                
                return {
                    "success": True,
                    "results": batch_results,
                    "processing_time": time.time() - batch_start,
                    "domains_count": len(domains),
                    "cost": response.usage.total_tokens * 0.000002  # GPT-3.5 pricing
                }
                
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"JSON parse error: {str(e)}",
                    "raw_response": ai_result[:500]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "domains_count": len(domains),
                "processing_time": time.time() - batch_start
            }
    
    def phase2_batch_ai_processing(self):
        """ФАЗА 2: Батч AI обработка"""
        batches = self.prepare_ai_batches()
        
        if not batches:
            self.log("❌ Нет данных для AI обработки")
            return
            
        self.log(f"🤖 ФАЗА 2: Батч AI обработка {len(batches)} батчей с {ULTRA_CONFIG['max_ai_workers']} потоками")
        
        with self.lock:
            self.progress_stats["phase2_total"] = len(batches)
            self.progress_stats["phase2_completed"] = 0
        
        total_cost = 0
        total_processed = 0
        
        with ThreadPoolExecutor(max_workers=ULTRA_CONFIG["max_ai_workers"]) as executor:
            future_to_batch = {executor.submit(self.process_ai_batch, batch): i for i, batch in enumerate(batches)}
            
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    batch_result = future.result()
                    
                    if batch_result["success"]:
                        # Мергим результаты
                        for domain, result in batch_result["results"].items():
                            self.phase2_results[domain] = result
                        
                        total_cost += batch_result.get("cost", 0)
                        total_processed += batch_result["domains_count"]
                        
                        self.log(f"✅ Батч {batch_idx+1}/{len(batches)}: {batch_result['domains_count']} доменов, "
                               f"${batch_result.get('cost', 0):.4f}, {batch_result['processing_time']:.1f}с")
                    else:
                        self.log(f"❌ Батч {batch_idx+1} error: {batch_result['error']}")
                        
                    with self.lock:
                        self.progress_stats["phase2_completed"] += 1
                        
                except Exception as e:
                    self.log(f"❌ Exception batch {batch_idx+1}: {str(e)}")
                    with self.lock:
                        self.progress_stats["phase2_completed"] += 1
        
        self.log(f"✅ ФАЗА 2 ЗАВЕРШЕНА: {total_processed} доменов, общая стоимость: ${total_cost:.4f}")
    
    def save_final_results(self, output_file: str):
        """Сохранить финальные результаты в CSV"""
        self.log(f"💾 Сохранение результатов в {output_file}")
        
        final_data = []
        
        for domain, phase1_result in self.phase1_results.items():
            row_data = {
                "domain": domain,
                "scraping_success": phase1_result["success"],
                "total_pages_found": phase1_result["total_pages"],
                "scraping_time": phase1_result["scrape_time"],
                "scraping_error": phase1_result.get("error", "")
            }
            
            # Добавляем AI результаты если есть
            if domain in self.phase2_results:
                ai_result = self.phase2_results[domain]
                row_data.update({
                    "ai_success": ai_result["success"],
                    "ai_analysis": json.dumps(ai_result.get("ai_analysis", {}), ensure_ascii=False),
                    "ai_processing_time": ai_result["processing_time"]
                })
            else:
                row_data.update({
                    "ai_success": False,
                    "ai_analysis": "",
                    "ai_processing_time": 0
                })
            
            final_data.append(row_data)
        
        # Сохраняем CSV
        df = pd.DataFrame(final_data)
        df.to_csv(output_file, index=False)
        
        self.log(f"✅ Результаты сохранены: {len(final_data)} записей")
    
    def process_csv_ultra_fast(self, input_file: str, limit: int = None):
        """Ультра-быстрая обработка CSV файла"""
        total_start = time.time()
        
        self.log(f"🚀 ULTRA PARALLEL SCRAPER - ЗАПУСК")
        self.log(f"📁 Входной файл: {input_file}")
        self.log(f"⚙️  Конфигурация: HTTP потоки={ULTRA_CONFIG['max_http_workers']}, AI потоки={ULTRA_CONFIG['max_ai_workers']}")
        
        # Читаем домены
        df = pd.read_csv(input_file)
        valid_domains = df[df['company_domain'].notna() & (df['company_domain'] != '')]
        
        if limit:
            domains = valid_domains['company_domain'].tolist()[:limit]
        else:
            domains = valid_domains['company_domain'].tolist()
        
        self.log(f"📊 К обработке: {len(domains)} доменов")
        
        # ФАЗА 1: Массовый HTTP скрейпинг
        self.phase1_mass_http_scraping(domains)
        
        # ФАЗА 2: Батч AI обработка
        self.phase2_batch_ai_processing()
        
        # Сохраняем результаты
        output_file = f"ultra_parallel_results_{self.session_id}.csv"
        self.save_final_results(output_file)
        
        total_time = time.time() - total_start
        
        # Финальная статистика
        successful_domains = len([d for d in self.phase1_results.values() if d["success"]])
        ai_processed = len(self.phase2_results)
        
        self.log(f"\n{'='*80}")
        self.log(f"🎉 ULTRA PARALLEL SCRAPER - РЕЗУЛЬТАТЫ")
        self.log(f"{'='*80}")
        self.log(f"⏱️  Общее время: {total_time:.1f}с ({total_time/60:.1f}мин)")
        self.log(f"📊 HTTP скрейпинг: {successful_domains}/{len(domains)} доменов")
        self.log(f"🤖 AI анализ: {ai_processed} доменов")
        self.log(f"🚀 Скорость: {successful_domains/(total_time/60):.1f} доменов/мин")
        self.log(f"📁 Результаты: {output_file}")
        self.log(f"❌ Ошибки: {len(self.progress_stats['errors'])}")
        
        if self.progress_stats['errors']:
            self.log("🔍 Первые 5 ошибок:")
            for error in self.progress_stats['errors'][:5]:
                self.log(f"  • {error}")
        
        return output_file

def main():
    """Основная функция"""
    input_file = "../../leads/raw/lumid_canada_20250108.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ Файл не найден: {input_file}")
        return
    
    scraper = UltraParallelScraper()
    
    # Тестируем на 100 доменах сначала
    result_file = scraper.process_csv_ultra_fast(input_file, limit=100)
    
    print(f"\n🎯 ДЛЯ ПОЛНОЙ ОБРАБОТКИ 2000+ ДОМЕНОВ:")
    print(f"  1. Запустите без limit parameter")
    print(f"  2. Ожидаемое время: 20-40 минут")
    print(f"  3. Настройте ULTRA_CONFIG по необходимости")

if __name__ == "__main__":
    main()