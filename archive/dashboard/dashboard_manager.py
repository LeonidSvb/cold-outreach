#!/usr/bin/env python3
"""
Dashboard Data Manager - Управление данными для HTML Dashboard
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any

class DashboardManager:
    """Управление данными dashboard с детализацией по давности"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
        
        # Создаем папки если их нет
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Пути к файлам данных
        self.sessions_file = os.path.join(self.data_dir, 'sessions_history.json')
        self.aggregated_file = os.path.join(self.data_dir, 'aggregated_metrics.json')
        self.current_file = os.path.join(self.data_dir, 'current_session.json')
        
        # Инициализируем файлы если их нет
        self._initialize_data_files()
    
    def _initialize_data_files(self):
        """Создание базовых файлов данных"""
        
        if not os.path.exists(self.sessions_file):
            initial_data = {
                "total_sessions": 0,
                "first_session": None,
                "last_updated": datetime.now().isoformat(),
                "sessions": []
            }
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)
        
        if not os.path.exists(self.aggregated_file):
            initial_agg = {
                "overview": {
                    "total_scripts_run": 0,
                    "total_companies_processed": 0,
                    "total_api_cost": 0.0,
                    "total_processing_time": 0,
                    "average_success_rate": 0,
                    "most_used_script": None
                },
                "by_script": {},
                "trends": {
                    "daily_activity": [],
                    "weekly_summary": [],
                    "monthly_stats": []
                },
                "last_calculated": datetime.now().isoformat()
            }
            with open(self.aggregated_file, 'w', encoding='utf-8') as f:
                json.dump(initial_agg, f, indent=2, ensure_ascii=False)
    
    def save_session(self, script_name: str, session_data: Dict[str, Any]) -> str:
        """
        Сохранение данных сессии с максимальной детализацией
        
        Args:
            script_name: Название скрипта
            session_data: Полные данные сессии
            
        Returns:
            session_id: ID сохраненной сессии
        """
        
        # Генерируем уникальный ID сессии
        timestamp = datetime.now()
        session_id = f"{script_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Подготавливаем данные сессии
        session_record = {
            "session_id": session_id,
            "script_name": script_name,
            "timestamp": timestamp.isoformat(),
            "date": timestamp.strftime('%Y-%m-%d'),
            "time": timestamp.strftime('%H:%M:%S'),
            
            # Базовые метрики (всегда сохраняем)
            "summary": {
                "duration": session_data.get('total_runtime', 0),
                "success_rate": session_data.get('success_rate', 0),
                "items_processed": session_data.get('items_processed', 0),
                "api_cost": session_data.get('total_cost', 0),
                "errors_count": len(session_data.get('errors', [])),
                "status": "completed"
            }
        }
        
        # Максимальная детализация - сохраняем ВСЕ данные
        session_record["detailed_data"] = {
            "performance_metrics": session_data.get('performance_metrics', {}),
            "processing_results": session_data.get('processing_results', []),
            "session_stats": session_data.get('session_stats', {}),
            "detailed_logs": session_data.get('detailed_logs', []),
            "error_details": session_data.get('errors', []),
            "configuration": session_data.get('configuration', {}),
            "environment_info": session_data.get('environment_info', {}),
            "api_calls_breakdown": session_data.get('api_calls', []),
            "timing_breakdown": session_data.get('timing_details', {}),
            "quality_metrics": session_data.get('quality_metrics', {}),
            "raw_output": session_data.get('raw_results', [])
        }
        
        # Загружаем текущую историю
        with open(self.sessions_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        # Добавляем новую сессию
        history_data['sessions'].insert(0, session_record)  # Новые сессии в начало
        history_data['total_sessions'] += 1
        history_data['last_updated'] = timestamp.isoformat()
        
        if history_data['first_session'] is None:
            history_data['first_session'] = timestamp.isoformat()
        
        # Сохраняем обновленную историю
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
        
        # Обновляем текущую сессию
        with open(self.current_file, 'w', encoding='utf-8') as f:
            json.dump(session_record, f, indent=2, ensure_ascii=False)
        
        # Пересчитываем агрегированные метрики
        self._update_aggregated_metrics()
        
        print(f"Сессия сохранена: {session_id}")
        return session_id
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Получение данных для dashboard с умной детализацией:
        - Последние 5 сессий: МАКСИМАЛЬНАЯ детализация
        - Сессии старше 5: Только базовые метрики
        """
        
        # Загружаем историю сессий
        with open(self.sessions_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        # Загружаем агрегированные данные
        with open(self.aggregated_file, 'r', encoding='utf-8') as f:
            agg_data = json.load(f)
        
        # Разделяем сессии на детальные и краткие
        all_sessions = history_data['sessions']
        
        # Последние 5 сессий - максимальная детализация
        recent_sessions = []
        for i, session in enumerate(all_sessions[:5]):
            detailed_session = {
                **session,
                "detail_level": "maximum",
                "position": i + 1,
                "is_recent": True
            }
            recent_sessions.append(detailed_session)
        
        # Остальные сессии - краткая информация
        older_sessions = []
        for i, session in enumerate(all_sessions[5:]):
            brief_session = {
                "session_id": session["session_id"],
                "script_name": session["script_name"],
                "timestamp": session["timestamp"],
                "date": session["date"],
                "time": session["time"],
                "summary": session["summary"],
                "detail_level": "brief",
                "position": i + 6,
                "is_recent": False
            }
            older_sessions.append(brief_session)
        
        # Подготавливаем финальные данные для dashboard
        dashboard_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_sessions": history_data['total_sessions'],
                "first_session": history_data['first_session'],
                "dashboard_version": "1.0.0"
            },
            
            "current_session": recent_sessions[0] if recent_sessions else None,
            
            "recent_sessions": {
                "count": len(recent_sessions),
                "detail_level": "maximum",
                "sessions": recent_sessions
            },
            
            "older_sessions": {
                "count": len(older_sessions),
                "detail_level": "brief", 
                "sessions": older_sessions
            },
            
            "aggregated_metrics": agg_data,
            
            "insights": self._generate_insights(all_sessions, agg_data)
        }
        
        return dashboard_data
    
    def _update_aggregated_metrics(self):
        """Пересчет агрегированных метрик"""
        
        # Загружаем все сессии
        with open(self.sessions_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        sessions = history_data['sessions']
        
        if not sessions:
            return
        
        # Считаем общие метрики
        total_scripts = len(sessions)
        total_companies = sum(s['summary'].get('items_processed', 0) for s in sessions)
        total_cost = sum(s['summary'].get('api_cost', 0) for s in sessions)
        total_time = sum(s['summary'].get('duration', 0) for s in sessions)
        avg_success = sum(s['summary'].get('success_rate', 0) for s in sessions) / len(sessions)
        
        # Статистика по скриптам
        by_script = {}
        for session in sessions:
            script = session['script_name']
            if script not in by_script:
                by_script[script] = {
                    "total_runs": 0,
                    "total_items": 0,
                    "total_cost": 0.0,
                    "total_time": 0,
                    "avg_success_rate": 0,
                    "last_run": None
                }
            
            stats = by_script[script]
            stats["total_runs"] += 1
            stats["total_items"] += session['summary'].get('items_processed', 0)
            stats["total_cost"] += session['summary'].get('api_cost', 0)
            stats["total_time"] += session['summary'].get('duration', 0)
            stats["avg_success_rate"] = (stats["avg_success_rate"] * (stats["total_runs"]-1) + session['summary'].get('success_rate', 0)) / stats["total_runs"]
            
            if stats["last_run"] is None or session['timestamp'] > stats["last_run"]:
                stats["last_run"] = session['timestamp']
        
        # Находим самый используемый скрипт
        most_used = max(by_script.items(), key=lambda x: x[1]['total_runs'])[0] if by_script else None
        
        # Тренды по дням
        daily_activity = {}
        for session in sessions:
            date = session['date']
            if date not in daily_activity:
                daily_activity[date] = {
                    "date": date,
                    "sessions_count": 0,
                    "items_processed": 0,
                    "total_cost": 0.0,
                    "scripts": set()
                }
            
            daily_activity[date]["sessions_count"] += 1
            daily_activity[date]["items_processed"] += session['summary'].get('items_processed', 0)
            daily_activity[date]["total_cost"] += session['summary'].get('api_cost', 0)
            daily_activity[date]["scripts"].add(session['script_name'])
        
        # Конвертируем в список и сортируем
        daily_list = []
        for date, data in daily_activity.items():
            data["scripts"] = list(data["scripts"])
            daily_list.append(data)
        daily_list.sort(key=lambda x: x["date"], reverse=True)
        
        # Обновляем агрегированные данные
        agg_data = {
            "overview": {
                "total_scripts_run": total_scripts,
                "total_companies_processed": total_companies,
                "total_api_cost": round(total_cost, 4),
                "total_processing_time": round(total_time, 2),
                "average_success_rate": round(avg_success, 1),
                "most_used_script": most_used
            },
            "by_script": by_script,
            "trends": {
                "daily_activity": daily_list[:30],  # Последние 30 дней
                "weekly_summary": [],  # TODO: Реализовать недельную сводку
                "monthly_stats": []    # TODO: Реализовать месячную статистику
            },
            "last_calculated": datetime.now().isoformat()
        }
        
        # Сохраняем
        with open(self.aggregated_file, 'w', encoding='utf-8') as f:
            json.dump(agg_data, f, indent=2, ensure_ascii=False)
    
    def _generate_insights(self, sessions: List[Dict], agg_data: Dict) -> Dict[str, Any]:
        """Генерация инсайтов для dashboard"""
        
        insights = {
            "performance_alerts": [],
            "recommendations": [],
            "trends_analysis": {},
            "cost_optimization": []
        }
        
        if len(sessions) >= 2:
            # Сравниваем последние 2 сессии
            latest = sessions[0]
            previous = sessions[1]
            
            # Производительность
            if latest['summary']['success_rate'] < previous['summary']['success_rate']:
                insights["performance_alerts"].append({
                    "type": "warning",
                    "message": f"Успешность снизилась с {previous['summary']['success_rate']}% до {latest['summary']['success_rate']}%",
                    "script": latest['script_name']
                })
            
            # Стоимость
            if latest['summary']['api_cost'] > previous['summary']['api_cost'] * 1.5:
                insights["cost_optimization"].append({
                    "type": "high_cost",
                    "message": f"Значительное увеличение стоимости API вызовов",
                    "current": latest['summary']['api_cost'],
                    "previous": previous['summary']['api_cost']
                })
            
            # Рекомендации
            if latest['summary']['errors_count'] > 0:
                insights["recommendations"].append({
                    "priority": "high",
                    "message": f"Обнаружены ошибки в последнем запуске: {latest['summary']['errors_count']} шт.",
                    "action": "Проверить детальные логи"
                })
        
        return insights

# Глобальный экземпляр менеджера
dashboard_manager = DashboardManager()

def save_session_data(script_name: str, session_data: Dict[str, Any]) -> str:
    """Функция для использования в скриптах"""
    return dashboard_manager.save_session(script_name, session_data)

def get_dashboard_data() -> Dict[str, Any]:
    """Функция для получения данных dashboard"""
    return dashboard_manager.get_dashboard_data()