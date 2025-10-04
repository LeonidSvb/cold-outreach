#!/usr/bin/env python3
"""
=== INSTANTLY UNIVERSAL DATA COLLECTOR ===
Version: 1.0.0 | Created: 2025-09-21

PURPOSE:
Универсальный сборщик всех данных Instantly по конфигу для dashboard

FEATURES:
- Конфигурируемые даты и параметры
- Полный сбор всех доступных данных
- Анализ качества ответов (real vs fake)
- Подготовка данных для dashboard
- Автоматические расчеты метрик

USAGE:
1. Настройте CONFIG секцию ниже
2. Run: python instantly_universal_collector.py
3. Результат в dashboard_data_{timestamp}.json

IMPROVEMENTS:
v1.0.0 - Универсальный сборщик с конфигом
"""

import subprocess
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIG SECTION - НАСТРОЙТЕ ЗДЕСЬ
# ============================================================================

CONFIG = {
    # БАЗОВЫЕ НАСТРОЙКИ
    "API_KEY": "YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0Om94cnhsVkhYQ3p3Rg==",
    "BASE_URL": "https://api.instantly.ai/api/v2",

    # ВРЕМЕННЫЕ РАМКИ
    "DATE_RANGE": {
        "start_date": "2024-01-01",  # Начальная дата или "auto" для авто-расчета
        "end_date": "2025-12-31",    # Конечная дата или "today" для сегодня
        "auto_days_back": 90         # Автоматически брать последние N дней
    },

    # ЧТО СОБИРАТЬ
    "COLLECT": {
        "campaigns_overview": True,
        "campaigns_detailed": True,
        "daily_analytics": True,
        "steps_analytics": True,
        "accounts_data": True,
        "emails_sample": True,      # Образец писем для анализа
        "warmup_data": False        # Пока не работает
    },

    # АНАЛИЗ ДАННЫХ
    "ANALYSIS": {
        "calculate_real_metrics": True,
        "estimate_ooo_percentage": 0.4,  # 40% ответов = out-of-office
        "estimate_auto_percentage": 0.2,  # 20% ответов = автоответы
        "opportunity_threshold": 1       # Минимум для учета как конверсия
    },

    # ВЫВОД
    "OUTPUT": {
        "save_raw_data": True,
        "save_dashboard_json": True,
        "save_summary_report": True,
        "results_dir": "results"
    }
}

# ============================================================================
# MAIN COLLECTOR CLASS
# ============================================================================

class InstantlyUniversalCollector:
    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent / self.config["OUTPUT"]["results_dir"]
        self.results_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.collected_data = {}

    def collect_all_data(self):
        """Главная функция сбора всех данных"""
        print(f"🚀 Starting Instantly Universal Data Collection")
        print(f"⏰ Timestamp: {self.timestamp}")
        print(f"📁 Results will be saved to: {self.results_dir}")
        print()

        # Подготовка дат
        start_date, end_date = self._prepare_dates()
        print(f"📅 Date range: {start_date} to {end_date}")
        print()

        # Сбор данных по конфигу
        if self.config["COLLECT"]["campaigns_overview"]:
            self._collect_campaigns_overview()

        if self.config["COLLECT"]["campaigns_detailed"]:
            self._collect_campaigns_detailed()

        if self.config["COLLECT"]["daily_analytics"]:
            self._collect_daily_analytics(start_date, end_date)

        if self.config["COLLECT"]["steps_analytics"]:
            self._collect_steps_analytics()

        if self.config["COLLECT"]["accounts_data"]:
            self._collect_accounts_data()

        if self.config["COLLECT"]["emails_sample"]:
            self._collect_emails_sample()

        # Анализ и обработка
        if self.config["ANALYSIS"]["calculate_real_metrics"]:
            self._calculate_real_metrics()

        # Сохранение результатов
        self._save_all_results()

        print(f"\n✅ Collection completed!")
        print(f"📊 Dashboard data ready: dashboard_data_{self.timestamp}.json")

        return self.collected_data

    def _prepare_dates(self):
        """Подготовка дат по конфигу"""
        end_date = self.config["DATE_RANGE"]["end_date"]
        start_date = self.config["DATE_RANGE"]["start_date"]

        if end_date == "today":
            end_date = datetime.now().strftime("%Y-%m-%d")

        if start_date == "auto":
            days_back = self.config["DATE_RANGE"]["auto_days_back"]
            start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        return start_date, end_date

    def _curl_request(self, endpoint, data=None):
        """Выполнение curl запроса"""
        url = f"{self.config['BASE_URL']}/{endpoint}"
        headers = f"Authorization: Bearer {self.config['API_KEY']}"

        if data:
            # POST request
            cmd = [
                "curl", "-X", "POST",
                "-H", headers,
                "-H", "Content-Type: application/json",
                "-d", json.dumps(data),
                url
            ]
        else:
            # GET request
            cmd = ["curl", "-H", headers, url]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"❌ Error in curl request: {result.stderr}")
                return None
        except Exception as e:
            print(f"❌ Exception in curl request: {e}")
            return None

    def _collect_campaigns_overview(self):
        """Сбор общего обзора кампаний"""
        print("📋 Collecting campaigns overview...")

        data = self._curl_request("campaigns/analytics")
        if data:
            self.collected_data['campaigns_overview'] = data
            count = len(data) if isinstance(data, list) else 1
            print(f"   ✅ Collected {count} campaigns")
        else:
            print("   ❌ Failed to collect campaigns overview")

    def _collect_campaigns_detailed(self):
        """Сбор детальных данных по каждой кампании"""
        if 'campaigns_overview' not in self.collected_data:
            return

        print("🔍 Collecting detailed campaign data...")
        campaigns = self.collected_data['campaigns_overview']

        detailed_campaigns = []
        for campaign in campaigns:
            campaign_id = campaign.get('campaign_id')
            if campaign_id:
                print(f"   📊 Getting details for: {campaign.get('campaign_name', 'Unknown')}")

                # Детальная аналитика
                detail = self._curl_request(f"campaigns/analytics?id={campaign_id}")
                if detail and len(detail) > 0:
                    detailed_campaigns.append(detail[0])

        self.collected_data['campaigns_detailed'] = detailed_campaigns
        print(f"   ✅ Collected detailed data for {len(detailed_campaigns)} campaigns")

    def _collect_daily_analytics(self, start_date, end_date):
        """Сбор ежедневной аналитики"""
        print("📅 Collecting daily analytics...")

        # Общая ежедневная аналитика
        endpoint = f"campaigns/analytics/daily?start_date={start_date}&end_date={end_date}"
        data = self._curl_request(endpoint)

        if data:
            self.collected_data['daily_analytics_all'] = data
            print(f"   ✅ Collected daily data for {len(data)} days")

        # По каждой кампании отдельно
        if 'campaigns_overview' in self.collected_data:
            daily_by_campaign = {}
            for campaign in self.collected_data['campaigns_overview']:
                campaign_id = campaign.get('campaign_id')
                campaign_name = campaign.get('campaign_name', 'Unknown')

                endpoint = f"campaigns/analytics/daily?campaign_id={campaign_id}&start_date={start_date}&end_date={end_date}"
                data = self._curl_request(endpoint)

                if data:
                    daily_by_campaign[campaign_id] = {
                        'name': campaign_name,
                        'data': data
                    }

            self.collected_data['daily_analytics_by_campaign'] = daily_by_campaign
            print(f"   ✅ Collected daily data for {len(daily_by_campaign)} individual campaigns")

    def _collect_steps_analytics(self):
        """Сбор аналитики по этапам"""
        if 'campaigns_overview' not in self.collected_data:
            return

        print("🔢 Collecting steps analytics...")
        steps_by_campaign = {}

        for campaign in self.collected_data['campaigns_overview']:
            campaign_id = campaign.get('campaign_id')
            campaign_name = campaign.get('campaign_name', 'Unknown')

            data = self._curl_request(f"campaigns/analytics/steps?campaign_id={campaign_id}")
            if data:
                steps_by_campaign[campaign_id] = {
                    'name': campaign_name,
                    'steps': data
                }

        self.collected_data['steps_analytics'] = steps_by_campaign
        print(f"   ✅ Collected steps data for {len(steps_by_campaign)} campaigns")

    def _collect_accounts_data(self):
        """Сбор данных по email аккаунтам"""
        print("📧 Collecting accounts data...")

        data = self._curl_request("accounts")
        if data:
            self.collected_data['accounts'] = data

            # Анализ аккаунтов
            items = data.get('items', [])
            active_accounts = [acc for acc in items if acc.get('status') == 1]
            inactive_accounts = [acc for acc in items if acc.get('status') == -1]

            print(f"   ✅ Total accounts: {len(items)}")
            print(f"   ✅ Active: {len(active_accounts)}")
            print(f"   ❌ Inactive: {len(inactive_accounts)}")
        else:
            print("   ❌ Failed to collect accounts data")

    def _collect_emails_sample(self):
        """Сбор образца писем для анализа"""
        print("📨 Collecting email samples...")

        data = self._curl_request("emails?limit=50")
        if data:
            self.collected_data['emails_sample'] = data
            items = data.get('items', [])
            print(f"   ✅ Collected {len(items)} email samples")
        else:
            print("   ❌ Failed to collect email samples")

    def _calculate_real_metrics(self):
        """Расчет реальных метрик с учетом OOO и автоответов"""
        print("🧮 Calculating real metrics...")

        if 'campaigns_detailed' not in self.collected_data:
            return

        ooo_rate = self.config["ANALYSIS"]["estimate_ooo_percentage"]
        auto_rate = self.config["ANALYSIS"]["estimate_auto_percentage"]

        enhanced_campaigns = []

        for campaign in self.collected_data['campaigns_detailed']:
            enhanced = campaign.copy()

            # Базовые метрики
            sent = campaign.get('emails_sent_count', 0)
            replies = campaign.get('reply_count', 0)
            opportunities = campaign.get('total_opportunities', 0)

            # Расчет реальных метрик
            estimated_ooo = int(replies * ooo_rate)
            estimated_auto = int(replies * auto_rate)
            estimated_real_replies = max(0, replies - estimated_ooo - estimated_auto)
            estimated_positive_replies = opportunities if opportunities > 0 else max(0, int(estimated_real_replies * 0.3))

            # Добавление расчетных метрик
            enhanced['analytics_enhanced'] = {
                'formal_reply_rate': round(replies / sent * 100, 2) if sent > 0 else 0,
                'estimated_ooo_replies': estimated_ooo,
                'estimated_auto_replies': estimated_auto,
                'estimated_real_replies': estimated_real_replies,
                'estimated_positive_replies': estimated_positive_replies,
                'real_reply_rate': round(estimated_real_replies / sent * 100, 2) if sent > 0 else 0,
                'positive_reply_rate': round(estimated_positive_replies / sent * 100, 2) if sent > 0 else 0,
                'bounce_rate': round(campaign.get('bounced_count', 0) / sent * 100, 2) if sent > 0 else 0,
                'opportunity_rate': round(opportunities / sent * 100, 2) if sent > 0 else 0
            }

            enhanced_campaigns.append(enhanced)

        self.collected_data['campaigns_with_real_metrics'] = enhanced_campaigns
        print(f"   ✅ Enhanced {len(enhanced_campaigns)} campaigns with real metrics")

    def _save_all_results(self):
        """Сохранение всех результатов"""
        print("\n💾 Saving results...")

        # Сырые данные
        if self.config["OUTPUT"]["save_raw_data"]:
            raw_file = self.results_dir / f"raw_data_{self.timestamp}.json"
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(self.collected_data, f, indent=2, ensure_ascii=False)
            print(f"   📄 Raw data: {raw_file.name}")

        # Dashboard JSON
        if self.config["OUTPUT"]["save_dashboard_json"]:
            dashboard_data = self._prepare_dashboard_data()
            dashboard_file = self.results_dir / f"dashboard_data_{self.timestamp}.json"
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            print(f"   📊 Dashboard data: {dashboard_file.name}")

        # Summary отчет
        if self.config["OUTPUT"]["save_summary_report"]:
            summary = self._generate_summary()
            summary_file = self.results_dir / f"summary_{self.timestamp}.md"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"   📋 Summary report: {summary_file.name}")

    def _prepare_dashboard_data(self):
        """Подготовка данных для dashboard"""
        dashboard = {
            "metadata": {
                "timestamp": self.timestamp,
                "collection_date": datetime.now().isoformat(),
                "config_used": self.config,
                "data_types": list(self.collected_data.keys())
            },
            "summary": {},
            "campaigns": [],
            "accounts": {},
            "daily_trends": [],
            "performance_metrics": {}
        }

        # Заполнение данных...
        if 'campaigns_with_real_metrics' in self.collected_data:
            dashboard["campaigns"] = self.collected_data['campaigns_with_real_metrics']

        if 'accounts' in self.collected_data:
            dashboard["accounts"] = self.collected_data['accounts']

        if 'daily_analytics_all' in self.collected_data:
            dashboard["daily_trends"] = self.collected_data['daily_analytics_all']

        return dashboard

    def _generate_summary(self):
        """Генерация summary отчета"""
        summary = f"""# INSTANTLY DATA COLLECTION SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Timestamp: {self.timestamp}

## Data Collected:
"""
        for key, value in self.collected_data.items():
            if isinstance(value, list):
                summary += f"- {key}: {len(value)} items\n"
            elif isinstance(value, dict):
                summary += f"- {key}: {len(value)} entries\n"
            else:
                summary += f"- {key}: collected\n"

        return summary

def main():
    logger.info("Instantly Universal Collector started")
    try:
        collector = InstantlyUniversalCollector()
        collector.collect_all_data()
        logger.info("Data collection completed successfully")
    except Exception as e:
        logger.error("Data collection failed", error=e)
        raise

if __name__ == "__main__":
    main()