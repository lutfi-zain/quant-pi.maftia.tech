#!/usr/bin/env python3
"""
Maftia Quant — Daily Analytics Runner

CLI runner for the daily analytics pipeline.

Usage:
    python run_daily_analytics.py [--date 2026-07-08]
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from pipelines.daily_analytics import DailyAnalyticsRunner
from db import init_db


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run the daily analytics pipeline"
    )
    parser.add_argument(
        "--date",
        default=datetime.utcnow().strftime("%Y-%m-%d"),
        help="Date to compute (YYYY-MM-DD, default: today)"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database before running"
    )
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        print("🔧 Initializing database...")
        init_db()
        print()
    
    # Run daily analytics
    runner = DailyAnalyticsRunner()
    result = runner.run(date=args.date)
    
    print("\n" + "=" * 50)
    print("📊 Daily Analytics Summary")
    print("=" * 50)
    print(f"Date:               {result['date']}")
    print(f"MVO Score:          {result['mvo_score']:.2f}")
    print(f"Regime:             {result['regime']}")
    print(f"Circuit Breaker:    {'🔴 ACTIVE' if result['circuit_breaker'] else '🟢 INACTIVE'}")
    print(f"Consensus Exposure: {result['consensus_exposure']:.1f}")
    print("=" * 50)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
