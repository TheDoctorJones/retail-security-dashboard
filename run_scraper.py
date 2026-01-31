#!/usr/bin/env python3
"""
Main Orchestration Script for Retail Security Dashboard
Run this script to scrape data from all sources and update the database
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from backend.database import init_db, get_stats
from backend.scrapers.city_data_scraper import scrape_all_cities
from backend.scrapers.news_scraper import scrape_all_news
from backend.pipeline.processor import run_full_pipeline


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          RETAIL SECURITY DASHBOARD - DATA SCRAPER            ║
║                                                              ║
║  Collects crime & security data from:                        ║
║  • 15+ City Police Department APIs                           ║
║  • Google News RSS                                           ║
║  • Industry RSS Feeds                                        ║
║  • NewsAPI (requires API key)                                ║
╚══════════════════════════════════════════════════════════════╝
    """)


def run_full_scrape(days_back: int = 30, cities_only: bool = False, news_only: bool = False):
    """Run full data scraping pipeline"""
    print_banner()
    print(f"Starting scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Looking back {days_back} days\n")

    # Initialize database
    print("Initializing database...")
    init_db()

    results = {
        'city_data': None,
        'news_data': None,
        'pipeline': None
    }

    # Scrape city data
    if not news_only:
        print("\n" + "="*60)
        print("PHASE 1: Scraping City Police Department Data")
        print("="*60 + "\n")

        results['city_data'] = scrape_all_cities(days_back=days_back)

        print(f"\nCity Data Summary:")
        print(f"  Total fetched: {results['city_data']['total_incidents']}")
        print(f"  New incidents: {results['city_data']['total_inserted']}")
        print(f"  Duplicates skipped: {results['city_data']['total_duplicates']}")

    # Scrape news
    if not cities_only:
        print("\n" + "="*60)
        print("PHASE 2: Scraping News Sources")
        print("="*60 + "\n")

        results['news_data'] = scrape_all_news(days_back=min(days_back, 14))  # News limited to 14 days

        print(f"\nNews Data Summary:")
        print(f"  Total fetched: {results['news_data']['total_incidents']}")
        print(f"  New incidents: {results['news_data']['total_inserted']}")
        print(f"  Duplicates skipped: {results['news_data']['total_duplicates']}")

    # Run processing pipeline
    print("\n" + "="*60)
    print("PHASE 3: Processing & Aggregation Pipeline")
    print("="*60 + "\n")

    results['pipeline'] = run_full_pipeline()

    # Print final summary
    print("\n" + "="*60)
    print("SCRAPE COMPLETE - FINAL SUMMARY")
    print("="*60 + "\n")

    stats = get_stats()
    print(f"Database Statistics:")
    print(f"  Total incidents: {stats['total_incidents']:,}")
    print(f"  Last 7 days: {stats['last_7_days']:,}")
    print(f"  Last 30 days: {stats['last_30_days']:,}")
    print(f"\n  By Source:")
    for source, count in stats.get('by_source', {}).items():
        print(f"    {source}: {count:,}")
    print(f"\n  Top Incident Types:")
    for inc_type, count in list(stats.get('by_type', {}).items())[:5]:
        print(f"    {inc_type}: {count:,}")

    print(f"\nCompleted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Retail Security Dashboard - Data Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_scraper.py                    # Full scrape, 30 days
  python run_scraper.py --days 7           # Scrape last 7 days
  python run_scraper.py --cities-only      # Only scrape city data
  python run_scraper.py --news-only        # Only scrape news sources

Environment Variables:
  NEWS_API_KEY    - API key from newsapi.org (optional, enables NewsAPI)
        """
    )

    parser.add_argument(
        '--days', '-d',
        type=int,
        default=30,
        help='Number of days to look back (default: 30)'
    )

    parser.add_argument(
        '--cities-only',
        action='store_true',
        help='Only scrape city police data (skip news)'
    )

    parser.add_argument(
        '--news-only',
        action='store_true',
        help='Only scrape news sources (skip city data)'
    )

    parser.add_argument(
        '--init-only',
        action='store_true',
        help='Only initialize database (no scraping)'
    )

    args = parser.parse_args()

    if args.init_only:
        print("Initializing database only...")
        init_db()
        print("Database initialized.")
        return

    run_full_scrape(
        days_back=args.days,
        cities_only=args.cities_only,
        news_only=args.news_only
    )


if __name__ == '__main__':
    main()
