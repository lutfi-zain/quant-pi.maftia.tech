#!/usr/bin/env python3
"""
Maftia Quant — OHLCV Pipeline Runner

CLI runner for the unified OHLCV pipeline.

Usage:
    python run_ohlcv_pipeline.py [--symbol BTCUSDT] [--limit 1000] [--start-date 2024-01-01]
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from pipelines.ohlcv import OHLCVPipeline
from db import init_db


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run the unified OHLCV pipeline"
    )
    parser.add_argument(
        "--symbol",
        default="BTCUSDT",
        help="Trading pair symbol (default: BTCUSDT)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Number of bars to fetch (default: 1000)"
    )
    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database before running pipeline"
    )
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        print("🔧 Initializing database...")
        init_db()
        print()
    
    # Run pipeline
    pipeline = OHLCVPipeline(symbol=args.symbol)
    result = pipeline.run(limit=args.limit, start_date=args.start_date)
    
    print("\n" + "=" * 50)
    print("📊 Pipeline Summary")
    print("=" * 50)
    print(f"Symbol:  {result['symbol']}")
    print(f"Fetched: {result['fetched']} bars")
    print(f"Valid:   {result['valid']} bars")
    print(f"Stored:  {result['stored']} bars")
    print(f"Time:    {result['timestamp']}")
    print("=" * 50)
    
    return 0 if result["stored"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
