#!/usr/bin/env python3
"""
TEXT-ONLY Website Intelligence Scraper
Ультра-быстрая версия с извлечением ТОЛЬКО текста и ссылок (без HTML)

ОПТИМИЗАЦИИ:
- Только чистый текст (без HTML тегов)
- Только ссылки (без CSS/JS)
- Минимальный размер данных
- Максимальная скорость обработки
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

TEXT_ONLY_CONFIG = {
    "max_http_workers": 50,      # Увеличиваем потоки (меньше данных)
    "max_ai_workers": 8,         # Больше AI потоков (меньше токенов)
    "batch_size_tokens": 20000,  # Больший размер батча
    "max_pages_per_domain": 15,  # Меньше страниц (только важные)
    "http_timeout": 8,           # Быстрый таймаут
    "max_text_length": 2000,     # Максимум текста на страницу
    "retry_attempts": 1,         # Меньше повторов
    "save_raw_data": True
}

class TextOnlyParser(HTMLParser):
    """Парсер для извлечения ТОЛЬКО текста и ссылок"""
    
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.links = []
        self.current_tag = None
        self.base_domain = ""
        self.ignore_tags = {'script', 'style', 'nav', 'footer', 'header', 'aside', 'meta', 'link'}
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href' and attr[1]:
                    href = attr[1].strip()
                    if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                        self.links.append(href)
                        
    def handle_endtag(self, tag):
        self.current_tag = None
        
    def handle_data(self, data):
        # Извлекаем только полезный текст
        if self.current_tag not in self.ignore_tags:
            text = data.strip()
            if len(text) > 10:  # Игнорируем короткие строки
                self.text_content.append(text)
    
    def get_clean_data(self):
        """Получить очищенные данные"""
        # Объединяем текст и очищаем
        full_text = ' '.join(self.text_content)
        
        # Убираем лишние пробелы и переносы
        clean_text = re.sub(r'\s+', ' ', full_text)
        clean_text = re.sub(r'[^\w\s\.\,\!\?\-\(\)]', ' ', clean_text)
        
        # Убираем дубликаты ссылок
        unique_links = list(set(self.links))
        
        return {
            "text": clean_text[:TEXT_ONLY_CONFIG["max_text_length"]],
            "text_length": len(clean_text),
            "links": unique_links[:20]  # Максимум 20 ссылок
        }

class TextOnlyWebsiteScraper:
    """Ультра-быстрый скрейпер только текста"""
    
    def __init__(self):
        self.session_id = f"text_only_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = time.time()
        self.phase1_results = {}
        self.phase2_results = {}
        self.progress_stats = {
            "phase1_completed": 0,
            "phase1_total": 0,
            "phase2_completed": 0,
            "phase2_total": 0,
            "errors": [],
            "total_text_extracted": 0,
            "total_links_found": 0
        }
        self.lock = threading.Lock()
        
    def log(self, message: str, level: str = "INFO"):
        """Потокобезопасное логирование"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Убираем эмодзи для Windows консоли
        clean_message = message.encode('ascii', errors='ignore').decode('ascii')
        print(f"[{timestamp}] [{level}] {clean_message}")
    
    def scrape_page_text_only(self, url: str) -> Dict:
        """Быстрое извлечение только текста и ссылок"""
        try:
            # HTTP запрос с быстрым таймаутом
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            with urllib.request.urlopen(req, timeout=TEXT_ONLY_CONFIG["http_timeout"], context=ctx) as response:
                # Читаем только первые 50KB (достаточно для текста)
                content = response.read(50000).decode('utf-8', errors='ignore')
                
                # Парсим только текст и ссылки
                parser = TextOnlyParser()
                parser.base_domain = urllib.parse.urlparse(url).netloc
                parser.feed(content)
                
                clean_data = parser.get_clean_data()
                
                return {
                    "url": url,
                    "success": True,
                    "text": clean_data["text"],
                    "text_length": clean_data["text_length"],
                    "links": clean_data["links"],
                    "links_count": len(clean_data["links"])
                }
                
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "error": str(e),
                "text": "",
                "text_length": 0,
                "links": [],
                "links_count": 0
            }
    
    def scrape_domain_text_only(self, domain: str) -> Dict:
        """Быстрое извлечение текста с домена"""
        start_time = time.time()
        
        result = {
            "domain": domain,
            "pages": [],
            "total_text_length": 0,
            "total_links": 0,
            "success": False,
            "scrape_time": 0,
            "error": None
        }
        
        try:
            # Нормализуем домен
            if not domain.startswith(('http://', 'https://')):
                domain_url = f"https://{domain}"
            else:
                domain_url = domain
            
            # Скрейпим главную страницу
            main_page = self.scrape_page_text_only(domain_url)
            pages_data = []
            
            if main_page["success"]:
                pages_data.append(main_page)
                
                # Находим важные внутренние ссылки
                base_domain = urllib.parse.urlparse(domain_url).netloc
                important_pages = []
                
                for link in main_page["links"]:
                    # Нормализуем ссылку
                    if link.startswith('/'):
                        full_link = urllib.parse.urljoin(domain_url, link)
                    elif link.startswith(('http://', 'https://')):
                        full_link = link
                    else:
                        continue
                    
                    # Проверяем, что это тот же домен
                    if urllib.parse.urlparse(full_link).netloc == base_domain:
                        # Приоритет важным страницам
                        link_lower = full_link.lower()
                        if any(keyword in link_lower for keyword in 
                              ['about', 'services', 'product', 'team', 'contact', 'case', 'work', 'portfolio']):
                            important_pages.append(full_link)
                
                # Скрейпим важные страницы параллельно (максимум 10)
                important_pages = important_pages[:TEXT_ONLY_CONFIG["max_pages_per_domain"]]
                
                if important_pages:
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        future_to_url = {executor.submit(self.scrape_page_text_only, url): url 
                                       for url in important_pages}
                        
                        for future in as_completed(future_to_url, timeout=30):
                            try:
                                page_data = future.result()
                                if page_data["success"]:
                                    pages_data.append(page_data)
                            except:
                                pass  # Пропускаем ошибки
            
            # Подсчитываем статистику
            total_text_length = sum(p["text_length"] for p in pages_data)
            total_links = sum(p["links_count"] for p in pages_data)
            
            result.update({
                "pages": pages_data,
                "total_text_length": total_text_length,
                "total_links": total_links,
                "success": len(pages_data) > 0,
                "pages_count": len(pages_data)
            })
            
            # Обновляем глобальную статистику
            with self.lock:
                self.progress_stats["total_text_extracted"] += total_text_length
                self.progress_stats["total_links_found"] += total_links
                
        except Exception as e:
            result["error"] = str(e)
        
        result["scrape_time"] = time.time() - start_time
        return result
    
    def phase1_mass_text_scraping(self, domains: List[str]):
        """ФАЗА 1: Массовое извлечение текста"""
        self.log(f"📝 ФАЗА 1: Массовое извлечение текста с {len(domains)} доменов ({TEXT_ONLY_CONFIG['max_http_workers']} потоков)")
        
        with self.lock:
            self.progress_stats["phase1_total"] = len(domains)
            self.progress_stats["phase1_completed"] = 0
        
        def progress_monitor():
            while True:
                time.sleep(10)
                with self.lock:
                    completed = self.progress_stats["phase1_completed"]
                    total = self.progress_stats["phase1_total"]
                    if completed >= total:
                        break
                    
                    elapsed = time.time() - self.start_time
                    rate = completed / (elapsed / 60) if elapsed > 0 else 0
                    eta = (total - completed) / rate if rate > 0 else 0
                    
                    self.log(f"📊 ПРОГРЕСС: {completed}/{total} ({(completed/total)*100:.1f}%) | "
                           f"Скорость: {rate:.1f} доменов/мин | ETA: {eta:.1f}мин | "
                           f"Текста: {self.progress_stats['total_text_extracted']} симв | "
                           f"Ссылок: {self.progress_stats['total_links_found']}")
        
        monitor_thread = threading.Thread(target=progress_monitor, daemon=True)
        monitor_thread.start()
        
        # Массовый скрейпинг с увеличенным количеством потоков
        with ThreadPoolExecutor(max_workers=TEXT_ONLY_CONFIG["max_http_workers"]) as executor:
            future_to_domain = {executor.submit(self.scrape_domain_text_only, domain): domain 
                              for domain in domains}
            
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    result = future.result()
                    self.phase1_results[domain] = result
                    
                    with self.lock:
                        self.progress_stats["phase1_completed"] += 1
                        if not result["success"]:
                            self.progress_stats["errors"].append(f"Текст не извлечен: {domain}")
                            
                except Exception as e:
                    with self.lock:
                        self.progress_stats["phase1_completed"] += 1
                        self.progress_stats["errors"].append(f"Ошибка {domain}: {str(e)}")
        
        successful_domains = sum(1 for r in self.phase1_results.values() if r["success"])
        total_text = sum(r["total_text_length"] for r in self.phase1_results.values())
        
        self.log(f"ФАЗА 1 ЗАВЕРШЕНА: {successful_domains}/{len(domains)} доменов, "
                f"{total_text} символов текста извлечено")
        
        # Сохраняем сырые данные
        if TEXT_ONLY_CONFIG["save_raw_data"]:
            raw_file = f"raw_text_data_{self.session_id}.json"
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(self.phase1_results, f, indent=2, ensure_ascii=False)
            self.log(f"Сырые данные сохранены: {raw_file}")
    
    def prepare_text_ai_batches(self) -> List[Dict]:
        """Подготовить оптимизированные батчи для AI (только текст)"""
        self.log("🤖 Подготовка AI батчей (только текст)...")
        
        batches = []
        current_batch = []
        current_tokens = 0
        
        for domain, result in self.phase1_results.items():
            if not result["success"]:
                continue
            
            # Подготавливаем краткие данные для AI
            domain_summary = {
                "domain": domain,
                "pages_summary": []
            }
            
            for page in result["pages"]:
                if page["success"]:
                    # Только первые 300 символов текста + URL
                    page_summary = {
                        "url": page["url"],
                        "text_preview": page["text"][:300],
                        "text_length": page["text_length"]
                    }
                    domain_summary["pages_summary"].append(page_summary)
            
            # Оцениваем токены (меньше токенов = быстрее)
            estimated_tokens = sum(len(p["text_preview"]) for p in domain_summary["pages_summary"]) // 4 + 100
            
            if current_tokens + estimated_tokens > TEXT_ONLY_CONFIG["batch_size_tokens"] and current_batch:
                batches.append({
                    "domains_data": current_batch.copy(),
                    "estimated_tokens": current_tokens
                })
                current_batch = [domain_summary]
                current_tokens = estimated_tokens
            else:
                current_batch.append(domain_summary)
                current_tokens += estimated_tokens
        
        if current_batch:
            batches.append({
                "domains_data": current_batch.copy(),
                "estimated_tokens": current_tokens
            })
        
        self.log(f"📦 Создано {len(batches)} AI батчей, среднее размер: {len(current_batch)} доменов")
        return batches
    
    def process_text_ai_batch(self, batch: Dict) -> Dict:
        """Обработать батч с текстовыми данными через AI"""
        batch_start = time.time()
        domains_data = batch["domains_data"]
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Краткий промпт для текстовых данных
            prompt = f"""Analyze these {len(domains_data)} company websites and identify the 3 most valuable pages for B2B outreach personalization.

Look for: About Us, Services, Case Studies, Team, Recent Work, Products.

Return JSON array:
[{{
  "domain": "example.com",
  "selected_pages": [
    {{"url": "page_url", "value_score": 0.9, "reason": "brief reason"}},
    ...
  ]
}}]

Data: {json.dumps(domains_data, ensure_ascii=False)}"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3000  # Меньше токенов = быстрее
            )
            
            ai_result = response.choices[0].message.content
            
            try:
                parsed_results = json.loads(ai_result)
                batch_results = {}
                
                for domain_result in parsed_results:
                    domain = domain_result.get("domain")
                    if any(d["domain"] == domain for d in domains_data):
                        batch_results[domain] = {
                            "ai_analysis": domain_result,
                            "processing_time": time.time() - batch_start,
                            "success": True
                        }
                
                return {
                    "success": True,
                    "results": batch_results,
                    "processing_time": time.time() - batch_start,
                    "domains_count": len([d["domain"] for d in domains_data]),
                    "cost": response.usage.total_tokens * 0.000002
                }
                
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"JSON parse error: {str(e)}",
                    "raw_response": ai_result[:300]
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - batch_start
            }
    
    def phase2_text_ai_processing(self):
        """ФАЗА 2: AI обработка текстовых данных"""
        batches = self.prepare_text_ai_batches()
        
        if not batches:
            self.log("❌ Нет текстовых данных для AI анализа")
            return
            
        self.log(f"🤖 ФАЗА 2: AI анализ {len(batches)} батчей текста ({TEXT_ONLY_CONFIG['max_ai_workers']} потоков)")
        
        with self.lock:
            self.progress_stats["phase2_total"] = len(batches)
            self.progress_stats["phase2_completed"] = 0
        
        total_cost = 0
        total_processed = 0
        
        with ThreadPoolExecutor(max_workers=TEXT_ONLY_CONFIG["max_ai_workers"]) as executor:
            future_to_batch = {executor.submit(self.process_text_ai_batch, batch): i 
                             for i, batch in enumerate(batches)}
            
            for future in as_completed(future_to_batch):
                batch_idx = future_to_batch[future]
                try:
                    batch_result = future.result()
                    
                    if batch_result["success"]:
                        for domain, result in batch_result["results"].items():
                            self.phase2_results[domain] = result
                        
                        total_cost += batch_result.get("cost", 0)
                        total_processed += batch_result["domains_count"]
                        
                        self.log(f"✅ AI Батч {batch_idx+1}/{len(batches)}: {batch_result['domains_count']} доменов, "
                               f"${batch_result.get('cost', 0):.4f}")
                    else:
                        self.log(f"❌ AI Батч {batch_idx+1} ошибка: {batch_result['error']}")
                        
                    with self.lock:
                        self.progress_stats["phase2_completed"] += 1
                        
                except Exception as e:
                    self.log(f"❌ AI Батч {batch_idx+1} исключение: {str(e)}")
                    with self.lock:
                        self.progress_stats["phase2_completed"] += 1
        
        self.log(f"✅ ФАЗА 2 ЗАВЕРШЕНА: {total_processed} доменов проанализировано, стоимость: ${total_cost:.4f}")
    
    def save_text_results(self, output_file: str):
        """Сохранить результаты (только текст и анализ)"""
        self.log(f"💾 Сохранение текстовых результатов...")
        
        final_data = []
        
        for domain, phase1_result in self.phase1_results.items():
            row_data = {
                "domain": domain,
                "text_extraction_success": phase1_result["success"],
                "total_text_length": phase1_result["total_text_length"],
                "total_links_found": phase1_result["total_links"],
                "pages_scraped": phase1_result.get("pages_count", 0),
                "scraping_time": phase1_result["scrape_time"],
                "scraping_error": phase1_result.get("error", "")
            }
            
            # Добавляем AI анализ если есть
            if domain in self.phase2_results:
                ai_result = self.phase2_results[domain]
                row_data.update({
                    "ai_analysis_success": ai_result["success"],
                    "ai_selected_pages": json.dumps(ai_result.get("ai_analysis", {}), ensure_ascii=False),
                    "ai_processing_time": ai_result["processing_time"]
                })
            else:
                row_data.update({
                    "ai_analysis_success": False,
                    "ai_selected_pages": "",
                    "ai_processing_time": 0
                })
            
            final_data.append(row_data)
        
        df = pd.DataFrame(final_data)
        df.to_csv(output_file, index=False)
        
        self.log(f"✅ Результаты сохранены: {len(final_data)} записей")
    
    def process_csv_text_only(self, input_file: str, limit: int = None):
        """Основная функция обработки (только текст)"""
        total_start = time.time()
        
        self.log(f"📝 TEXT-ONLY WEBSITE SCRAPER - ЗАПУСК")
        self.log(f"📁 Входной файл: {input_file}")
        self.log(f"⚙️  Конфигурация: HTTP={TEXT_ONLY_CONFIG['max_http_workers']}, AI={TEXT_ONLY_CONFIG['max_ai_workers']}")
        self.log(f"🎯 Извлечение: ТОЛЬКО текст и ссылки (без HTML)")
        
        # Читаем домены
        df = pd.read_csv(input_file)
        valid_domains = df[df['company_domain'].notna() & (df['company_domain'] != '')]
        
        if limit:
            domains = valid_domains['company_domain'].tolist()[:limit]
        else:
            domains = valid_domains['company_domain'].tolist()
        
        self.log(f"📊 К обработке: {len(domains)} доменов")
        
        # ФАЗА 1: Массовое извлечение текста
        self.phase1_mass_text_scraping(domains)
        
        # ФАЗА 2: AI анализ текста
        self.phase2_text_ai_processing()
        
        # Сохраняем результаты
        output_file = f"text_only_results_{self.session_id}.csv"
        self.save_text_results(output_file)
        
        total_time = time.time() - total_start
        
        # Финальная статистика
        successful_domains = len([d for d in self.phase1_results.values() if d["success"]])
        ai_processed = len(self.phase2_results)
        total_text = sum(r["total_text_length"] for r in self.phase1_results.values())
        total_links = sum(r["total_links"] for r in self.phase1_results.values())
        
        self.log(f"\n{'='*80}")
        self.log(f"🎉 TEXT-ONLY SCRAPER - РЕЗУЛЬТАТЫ")
        self.log(f"{'='*80}")
        self.log(f"⏱️  Общее время: {total_time:.1f}с ({total_time/60:.1f}мин)")
        self.log(f"📊 Текст извлечен: {successful_domains}/{len(domains)} доменов")
        self.log(f"📝 Всего текста: {total_text} символов")
        self.log(f"🔗 Всего ссылок: {total_links}")
        self.log(f"🤖 AI анализ: {ai_processed} доменов")
        self.log(f"🚀 Скорость: {successful_domains/(total_time/60):.1f} доменов/мин")
        self.log(f"📁 Результаты: {output_file}")
        
        # Сравнение с HTML версией
        html_time_estimate = successful_domains * 60  # 1 мин на домен с HTML
        speedup = html_time_estimate / total_time if total_time > 0 else 1
        
        self.log(f"⚡ УСКОРЕНИЕ: в {speedup:.1f}x быстрее HTML версии!")
        self.log(f"💾 ЭКОНОМИЯ: {(1 - total_text/1000000):.1f}% меньше данных")
        
        return output_file

def main():
    """Основная функция"""
    input_file = "../../leads/raw/lumid_canada_20250108.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ Файл не найден: {input_file}")
        return
    
    scraper = TextOnlyWebsiteScraper()
    
    # Тестируем на 10 доменах для демонстрации скорости
    result_file = scraper.process_csv_text_only(input_file, limit=10)
    
    print(f"\nДЛЯ ПОЛНОЙ ОБРАБОТКИ ВСЕХ ДОМЕНОВ:")
    print(f"  1. Уберите limit=10")
    print(f"  2. Ожидаемое время для 745 доменов: 10-20 минут")
    print(f"  3. Только текст + ссылки (без HTML мусора)")

if __name__ == "__main__":
    main()