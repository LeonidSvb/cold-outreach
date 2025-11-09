#!/usr/bin/env python3
"""
Statistics Tracker для мониторинга производительности scraping
Собирает метрики и показывает бенчмарки
"""

import time
from typing import Dict, List
from collections import defaultdict


class StatsTracker:
    """
    Отслеживание статистики выполнения scraping

    Метрики:
    - Общее время выполнения
    - Скорость обработки (items/sec)
    - Success rate
    - Распределение ошибок по типам
    - Средние времена отклика

    Использование:
        tracker = StatsTracker(total=1000, workers=25)

        for item in items:
            start = time.time()
            result = process(item)
            tracker.record(result['status'], time.time() - start)

        tracker.print_summary()
    """

    def __init__(self, total: int = 0, workers: int = 1):
        """
        Args:
            total: Общее количество элементов для обработки
            workers: Количество параллельных workers
        """
        self.total = total
        self.workers = workers

        self.start_time = time.time()
        self.end_time = None

        # Счётчики
        self.completed = 0
        self.success = 0
        self.failed = 0

        # Детализация по типам
        self.results_by_status = defaultdict(int)

        # Времена обработки
        self.processing_times = []

    def record(self, status: str, processing_time: float = 0):
        """
        Записать результат обработки одного элемента

        Args:
            status: Статус обработки ('success', 'timeout', 'error', etc)
            processing_time: Время обработки этого элемента (секунды)
        """
        self.completed += 1
        self.results_by_status[status] += 1

        if status == 'success':
            self.success += 1
        else:
            self.failed += 1

        if processing_time > 0:
            self.processing_times.append(processing_time)

    def get_progress_string(self) -> str:
        """
        Получить строку прогресса для вывода в консоль

        Returns:
            "[650/1000] 65.0% | ETA: 5.2min | Speed: 12.5 items/sec"
        """
        if self.total == 0:
            return f"[{self.completed}] processed"

        elapsed = time.time() - self.start_time
        progress_pct = (self.completed / self.total * 100)

        # Расчёт ETA
        if self.completed > 0:
            avg_time_per_item = elapsed / self.completed
            remaining = self.total - self.completed
            eta_seconds = avg_time_per_item * remaining
            eta_str = f"{eta_seconds/60:.1f}min" if eta_seconds > 60 else f"{eta_seconds:.0f}s"
        else:
            eta_str = "calculating..."

        # Скорость обработки
        speed = self.completed / elapsed if elapsed > 0 else 0

        return f"[{self.completed}/{self.total}] {progress_pct:.1f}% | ETA: {eta_str} | Speed: {speed:.1f} items/sec"

    def finalize(self) -> Dict:
        """
        Завершить сбор статистики и вернуть summary

        Returns:
            Словарь с полной статистикой
        """
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        # Базовые метрики
        success_rate = (self.success / self.total * 100) if self.total > 0 else 0
        failure_rate = (self.failed / self.total * 100) if self.total > 0 else 0

        # Времена обработки
        if self.processing_times:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            min_time = min(self.processing_times)
            max_time = max(self.processing_times)
        else:
            avg_time = min_time = max_time = 0

        # Скорость
        items_per_second = self.completed / duration if duration > 0 else 0

        return {
            # Основные метрики
            'total': self.total,
            'completed': self.completed,
            'success': self.success,
            'failed': self.failed,
            'success_rate_pct': round(success_rate, 2),
            'failure_rate_pct': round(failure_rate, 2),

            # Производительность
            'duration_seconds': round(duration, 2),
            'duration_minutes': round(duration / 60, 2),
            'items_per_second': round(items_per_second, 2),
            'workers': self.workers,

            # Времена обработки
            'avg_processing_time': round(avg_time, 3),
            'min_processing_time': round(min_time, 3),
            'max_processing_time': round(max_time, 3),

            # Детализация
            'results_by_status': dict(self.results_by_status),

            # Timestamps
            'started_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time)),
            'finished_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.end_time))
        }

    def print_summary(self):
        """
        Вывести красивый summary в консоль
        """
        stats = self.finalize()

        print(f"\n{'='*80}")
        print(f"EXECUTION SUMMARY")
        print(f"{'='*80}")
        print(f"Total items:           {stats['total']}")
        print(f"Completed:             {stats['completed']}")
        print(f"Success:               {stats['success']} ({stats['success_rate_pct']}%)")
        print(f"Failed:                {stats['failed']} ({stats['failure_rate_pct']}%)")
        print(f"")
        print(f"Duration:              {stats['duration_minutes']:.1f} min ({stats['duration_seconds']:.1f} sec)")
        print(f"Speed:                 {stats['items_per_second']:.2f} items/sec")
        print(f"Parallel workers:      {stats['workers']}")
        print(f"")
        print(f"Processing times:")
        print(f"  Average:             {stats['avg_processing_time']:.3f} sec")
        print(f"  Min:                 {stats['min_processing_time']:.3f} sec")
        print(f"  Max:                 {stats['max_processing_time']:.3f} sec")

        # Детализация по статусам
        if stats['results_by_status']:
            print(f"")
            print(f"Results by status:")
            for status, count in sorted(stats['results_by_status'].items(), key=lambda x: -x[1]):
                pct = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"  {status:<20} {count:>6} ({pct:>5.1f}%)")

        print(f"{'='*80}\n")

        # Рекомендации по оптимизации
        self._print_recommendations(stats)

    def _print_recommendations(self, stats: Dict):
        """
        Вывести рекомендации по оптимизации на основе статистики
        """
        recommendations = []

        # Если много timeout'ов - увеличить timeout
        timeout_count = stats['results_by_status'].get('timeout', 0)
        if timeout_count > stats['total'] * 0.1:  # >10% timeouts
            recommendations.append(
                f"HIGH TIMEOUTS ({timeout_count}): Consider increasing --timeout parameter"
            )

        # Если много dynamic sites - использовать Firecrawl
        dynamic_count = stats['results_by_status'].get('dynamic', 0)
        if dynamic_count > stats['total'] * 0.15:  # >15% dynamic
            recommendations.append(
                f"MANY DYNAMIC SITES ({dynamic_count}): Consider using --use-firecrawl for better coverage"
            )

        # Если низкая скорость - увеличить workers
        if stats['items_per_second'] < 5 and stats['workers'] < 50:
            recommendations.append(
                f"LOW SPEED ({stats['items_per_second']:.1f} items/sec): Consider increasing --workers (current: {stats['workers']})"
            )

        # Если высокая скорость но много ошибок - уменьшить workers
        if stats['failure_rate_pct'] > 30 and stats['workers'] > 25:
            recommendations.append(
                f"HIGH FAILURE RATE ({stats['failure_rate_pct']:.1f}%): Consider reducing --workers to avoid rate limiting"
            )

        if recommendations:
            print(f"OPTIMIZATION RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
            print()


def estimate_time(items: int, mode: str, workers: int = 25) -> dict:
    """
    Оценка времени выполнения на основе benchmarks

    Args:
        items: Количество элементов для обработки
        mode: Режим работы ('quick', 'standard', 'full')
        workers: Количество параллельных workers

    Returns:
        {
            'estimated_seconds': 120,
            'estimated_minutes': 2.0,
            'estimated_hours': 0.03,
            'mode': 'standard',
            'items': 1000,
            'workers': 25
        }
    """
    # Benchmarks (секунд на 1 элемент)
    # Основаны на реальных тестах с 25 workers
    benchmarks = {
        'quick': 0.05,      # Только detection static/dynamic (0.05 сек/item)
        'standard': 0.5,    # Scraping + email extraction (0.5 сек/item)
        'full': 3.0         # Scraping + AI analysis (3.0 сек/item)
    }

    # Поправка на количество workers (больше workers = быстрее)
    worker_multiplier = 25 / workers  # Baseline: 25 workers

    base_time = benchmarks.get(mode, benchmarks['standard'])
    adjusted_time = base_time * worker_multiplier

    total_seconds = items * adjusted_time

    return {
        'estimated_seconds': round(total_seconds, 1),
        'estimated_minutes': round(total_seconds / 60, 1),
        'estimated_hours': round(total_seconds / 3600, 2),
        'mode': mode,
        'items': items,
        'workers': workers,
        'time_per_item_sec': round(adjusted_time, 3)
    }
