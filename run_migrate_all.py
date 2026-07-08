"""
Maftia Quant — Migration Orchestrator

Runs all system migrations in sequence:
1. LTTD system (lttd.db → unified)
2. Valuation system (metrics.db → unified)
3. MTTD system (JSON/CSV → unified)
4. Ichimoku system (cache/API → unified)

Usage:
    python run_migrate_all.py --lttd-db /path/to/lttd.db --metrics-db /path/to/metrics.db
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
import argparse

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from pipelines.lttd_migration import LTTDMigrationPipeline  # noqa: E402
from pipelines.valuation_migration import ValuationMigrationPipeline  # noqa: E402
from pipelines.mttd_sync import MTTDSyncPipeline  # noqa: E402
from pipelines.ichimoku_sync import IchimokuSyncPipeline  # noqa: E402


class MigrationOrchestrator:
    """
    Orchestrates all system migrations in sequence.
    
    Execution order:
    1. LTTD (no dependencies)
    2. Valuation (no dependencies)
    3. MTTD (no dependencies)
    4. Ichimoku (no dependencies)
    
    All systems write to the same unified_daily_analytics table,
    with INSERT OR REPLACE handling any date conflicts.
    """
    
    def __init__(
        self,
        lttd_db_path: str | Path = "lttd.db",
        metrics_db_path: str | Path = "metrics.db",
        mttd_data_dir: str | Path = ".",
        ichimoku_cache_dir: str | Path = ".",
        ichimoku_api_url: Optional[str] = None,
        target_db_path: Optional[str | Path] = None,
    ):
        """
        Initialize the orchestrator.
        
        Args:
            lttd_db_path: Path to legacy lttd.db
            metrics_db_path: Path to legacy metrics.db
            mttd_data_dir: Directory with MTTD data files
            ichimoku_cache_dir: Directory with yfinance cache
            ichimoku_api_url: Optional Ichimoku FastAPI URL
            target_db_path: Optional target database path
        """
        self.lttd_pipeline = LTTDMigrationPipeline(
            lttd_db_path=lttd_db_path,
            target_db_path=target_db_path,
        )
        self.valuation_pipeline = ValuationMigrationPipeline(
            metrics_db_path=metrics_db_path,
            target_db_path=target_db_path,
        )
        self.mttd_pipeline = MTTDSyncPipeline(
            data_dir=mttd_data_dir,
            target_db_path=target_db_path,
        )
        self.ichimoku_pipeline = IchimokuSyncPipeline(
            cache_dir=ichimoku_cache_dir,
            api_url=ichimoku_api_url,
            target_db_path=target_db_path,
        )
    
    def run_all(self) -> dict[str, Any]:
        """
        Run all migrations in sequence.
        
        Returns:
            Combined migration summary
        """
        results: dict[str, Any] = {}
        start_time = datetime.utcnow()
        
        print("╔" + "═" * 58 + "╗")
        print("║" + " Maftia Quant — Full System Migration ".center(58) + "║")
        print("╚" + "═" * 58 + "╝")
        print()
        
        # 1. LTTD Migration
        print("━" * 60)
        print("Phase 1/4: LTTD System")
        print("━" * 60)
        try:
            results["lttd"] = self.lttd_pipeline.run()
        except FileNotFoundError as e:
            print(f"⚠️  Skipping LTTD: {e}")
            results["lttd"] = {"migrated": 0, "skipped": 0, "error": str(e)}
        except Exception as e:
            print(f"✗ LTTD migration failed: {e}")
            results["lttd"] = {"migrated": 0, "skipped": 0, "error": str(e)}
        
        print()
        
        # 2. Valuation Migration
        print("━" * 60)
        print("Phase 2/4: Valuation System")
        print("━" * 60)
        try:
            results["valuation"] = self.valuation_pipeline.run()
        except FileNotFoundError as e:
            print(f"⚠️  Skipping Valuation: {e}")
            results["valuation"] = {"migrated": 0, "skipped": 0, "error": str(e)}
        except Exception as e:
            print(f"✗ Valuation migration failed: {e}")
            results["valuation"] = {"migrated": 0, "skipped": 0, "error": str(e)}
        
        print()
        
        # 3. MTTD Sync
        print("━" * 60)
        print("Phase 3/4: MTTD System")
        print("━" * 60)
        try:
            results["mttd"] = self.mttd_pipeline.run()
        except Exception as e:
            print(f"✗ MTTD sync failed: {e}")
            results["mttd"] = {"synced": 0, "skipped": 0, "error": str(e)}
        
        print()
        
        # 4. Ichimoku Sync
        print("━" * 60)
        print("Phase 4/4: Ichimoku System")
        print("━" * 60)
        try:
            results["ichimoku"] = self.ichimoku_pipeline.run()
        except Exception as e:
            print(f"✗ Ichimoku sync failed: {e}")
            results["ichimoku"] = {"synced": 0, "skipped": 0, "error": str(e)}
        
        # Summary
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        total_migrated = sum(
            r.get("migrated", r.get("synced", 0))
            for r in results.values()
            if isinstance(r, dict)
        )
        
        print()
        print("╔" + "═" * 58 + "╗")
        print("║" + " Migration Complete ".center(58) + "║")
        print("╚" + "═" * 58 + "╝")
        print()
        print(f"Duration: {duration:.1f}s")
        print(f"Total records migrated: {total_migrated}")
        print()
        print("Per-system results:")
        for system, result in results.items():
            if isinstance(result, dict):
                migrated = result.get("migrated", result.get("synced", 0))
                error = result.get("error")
                if error:
                    print(f"  {system}: ⚠️  {error}")
                else:
                    print(f"  {system}: ✓ {migrated} records")
        
        return {
            "duration_seconds": duration,
            "total_migrated": total_migrated,
            "systems": results,
            "timestamp": end_time.isoformat(),
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate all systems to unified database"
    )
    parser.add_argument(
        "--lttd-db",
        default="lttd.db",
        help="Path to legacy lttd.db (default: lttd.db)",
    )
    parser.add_argument(
        "--metrics-db",
        default="metrics.db",
        help="Path to legacy metrics.db (default: metrics.db)",
    )
    parser.add_argument(
        "--mttd-dir",
        default=".",
        help="Directory with MTTD data files (default: current dir)",
    )
    parser.add_argument(
        "--ichimoku-cache",
        default=".",
        help="Directory with yfinance cache (default: current dir)",
    )
    parser.add_argument(
        "--ichimoku-api",
        default=None,
        help="Ichimoku FastAPI URL (optional)",
    )
    parser.add_argument(
        "--target-db",
        default=None,
        help="Target database path (default: unified db)",
    )
    
    args = parser.parse_args()
    
    orchestrator = MigrationOrchestrator(
        lttd_db_path=args.lttd_db,
        metrics_db_path=args.metrics_db,
        mttd_data_dir=args.mttd_dir,
        ichimoku_cache_dir=args.ichimoku_cache,
        ichimoku_api_url=args.ichimoku_api,
        target_db_path=args.target_db,
    )
    
    result = orchestrator.run_all()
    
    # Exit with error if any system failed
    has_errors = any(
        "error" in r
        for r in result["systems"].values()
        if isinstance(r, dict)
    )
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
