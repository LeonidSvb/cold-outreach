#!/usr/bin/env python3
"""
=== COMPREHENSIVE LEADS ANALYTICS ===
Version: 1.0.0 | Created: 2025-01-10

PURPOSE:
Deep analytics на все Google Maps leads с DuckDB
Показывает полную картину по states, niches, quality
"""

import duckdb
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PARQUET_FILE = Path(__file__).parent.parent / "data" / "raw" / "all_leads.parquet"

def run_analytics():
    """Run comprehensive analytics"""

    logger.info(f"Loading data from: {PARQUET_FILE}")
    con = duckdb.connect()

    print("\n" + "="*100)
    print("COMPREHENSIVE LEADS ANALYTICS")
    print("="*100)

    # OVERVIEW
    print("\n[OVERVIEW]")
    overview = con.execute(f"""
        SELECT
            COUNT(*) as total_leads,
            COUNT(DISTINCT state) as states,
            COUNT(DISTINCT niche) as niches,
            COUNT(DISTINCT city) as cities,
            ROUND(AVG(rating), 2) as avg_rating,
            ROUND(AVG(reviews), 0) as avg_reviews,
            COUNT(DISTINCT place_id) as unique_businesses
        FROM '{PARQUET_FILE}'
    """).fetchone()

    print(f"  Total Leads:        {overview[0]:,}")
    print(f"  Unique Businesses:  {overview[6]:,}")
    print(f"  States:             {overview[1]}")
    print(f"  Niches:             {overview[2]}")
    print(f"  Cities:             {overview[3]}")
    print(f"  Avg Rating:         {overview[4]}")
    print(f"  Avg Reviews:        {int(overview[5]):,}")

    # BY STATE (detailed)
    print("\n[BY STATE]")
    by_state = con.execute(f"""
        SELECT
            state,
            COUNT(*) as leads,
            COUNT(DISTINCT city) as cities,
            COUNT(DISTINCT niche) as niches,
            ROUND(AVG(rating), 2) as avg_rating,
            SUM(CASE WHEN has_phone AND has_website THEN 1 ELSE 0 END) as ready_for_outreach,
            ROUND(SUM(CASE WHEN has_phone AND has_website THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as ready_pct
        FROM '{PARQUET_FILE}'
        GROUP BY state
        ORDER BY leads DESC
    """).fetchall()

    for row in by_state:
        state, leads, cities, niches, rating, ready, ready_pct = row
        print(f"  {state.upper():15} {leads:>5} leads | {cities:>3} cities | {niches} niches | Rating {rating} | Ready: {ready:>4} ({ready_pct:>4.1f}%)")

    # BY NICHE (detailed)
    print("\n[BY NICHE]")
    by_niche = con.execute(f"""
        SELECT
            niche,
            COUNT(*) as leads,
            COUNT(DISTINCT state) as states,
            ROUND(AVG(rating), 2) as avg_rating,
            ROUND(AVG(reviews), 0) as avg_reviews,
            SUM(CASE WHEN has_phone AND has_website THEN 1 ELSE 0 END) as ready_for_outreach
        FROM '{PARQUET_FILE}'
        GROUP BY niche
        ORDER BY leads DESC
    """).fetchall()

    for row in by_niche:
        niche, leads, states, rating, reviews, ready = row
        print(f"  {niche.upper():20} {leads:>5} leads | {states} states | Rating {rating} | Avg Reviews: {int(reviews):>4} | Ready: {ready:>4}")

    # TOP CITIES
    print("\n[TOP 20 CITIES]")
    top_cities = con.execute(f"""
        SELECT
            city,
            state,
            COUNT(*) as leads,
            ROUND(AVG(rating), 2) as avg_rating,
            SUM(CASE WHEN has_phone AND has_website THEN 1 ELSE 0 END) as ready
        FROM '{PARQUET_FILE}'
        GROUP BY city, state
        ORDER BY leads DESC
        LIMIT 20
    """).fetchall()

    for row in top_cities:
        city, state, leads, rating, ready = row
        print(f"  {city:30} ({state:12}) {leads:>4} leads | Rating {rating} | Ready: {ready:>3}")

    # DATA QUALITY
    print("\n[DATA QUALITY]")
    quality = con.execute(f"""
        SELECT
            SUM(CASE WHEN has_phone AND has_website THEN 1 ELSE 0 END) as perfect,
            SUM(CASE WHEN has_phone AND NOT has_website THEN 1 ELSE 0 END) as need_website,
            SUM(CASE WHEN has_website AND NOT has_phone THEN 1 ELSE 0 END) as need_phone,
            SUM(CASE WHEN NOT has_phone AND NOT has_website THEN 1 ELSE 0 END) as need_both,
            ROUND(SUM(CASE WHEN rating >= 4.5 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as high_rating_pct,
            ROUND(SUM(CASE WHEN reviews >= 50 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as established_pct
        FROM '{PARQUET_FILE}'
    """).fetchone()

    perfect, need_web, need_phone, need_both, high_rating, established = quality
    total = perfect + need_web + need_phone + need_both

    print(f"  + Perfect (phone + website):  {perfect:>4} ({perfect/total*100:.1f}%)")
    print(f"  - Need website only:          {need_web:>4} ({need_web/total*100:.1f}%)")
    print(f"  - Need phone only:            {need_phone:>4} ({need_phone/total*100:.1f}%)")
    print(f"  - Need both:                  {need_both:>4} ({need_both/total*100:.1f}%)")
    print(f"  * High rating (4.5+):         {high_rating}%")
    print(f"  * Established (50+ reviews):  {established}%")

    # RATING DISTRIBUTION
    print("\n[RATING DISTRIBUTION]")
    ratings = con.execute(f"""
        SELECT
            CASE
                WHEN rating >= 4.8 THEN '4.8-5.0'
                WHEN rating >= 4.5 THEN '4.5-4.7'
                WHEN rating >= 4.0 THEN '4.0-4.4'
                ELSE '< 4.0'
            END as rating_range,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM '{PARQUET_FILE}'), 1) as pct
        FROM '{PARQUET_FILE}'
        GROUP BY rating_range
        ORDER BY rating_range DESC
    """).fetchall()

    for range_name, count, pct in ratings:
        bar = '#' * int(pct / 2)
        print(f"  {range_name:10} {count:>5} ({pct:>5.1f}%) {bar}")

    # REVIEW DISTRIBUTION
    print("\n[REVIEW DISTRIBUTION]")
    reviews_dist = con.execute(f"""
        SELECT
            CASE
                WHEN reviews >= 200 THEN '200+'
                WHEN reviews >= 100 THEN '100-199'
                WHEN reviews >= 50 THEN '50-99'
                ELSE '< 50'
            END as review_range,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM '{PARQUET_FILE}'), 1) as pct
        FROM '{PARQUET_FILE}'
        GROUP BY review_range
        ORDER BY review_range DESC
    """).fetchall()

    for range_name, count, pct in reviews_dist:
        bar = '#' * int(pct / 2)
        print(f"  {range_name:10} {count:>5} ({pct:>5.1f}%) {bar}")

    # ENRICHMENT PIPELINE READINESS
    print("\n[ENRICHMENT PIPELINE READINESS]")
    print(f"  Ready for email scraping:      {perfect:>4} businesses")
    print(f"  Estimated scraping time:       ~{perfect * 0.5 / 60:.1f} minutes (25 workers)")
    print(f"  Need website enrichment:       {need_web:>4} businesses")
    print(f"  Total pipeline capacity:       {perfect + need_web:>4} businesses")

    # RECOMMENDATIONS
    print("\n[RECOMMENDATIONS]")
    print(f"  1. Start email scraping for {perfect} ready businesses")
    print(f"  2. Focus on top states: {', '.join([row[0] for row in by_state[:3]])}")
    print(f"  3. Priority niches: {', '.join([row[0] for row in by_niche[:3]])}")
    print(f"  4. {high_rating}% have excellent ratings (4.5+) - high quality leads")

    print("\n" + "="*100 + "\n")

    con.close()

if __name__ == "__main__":
    run_analytics()
