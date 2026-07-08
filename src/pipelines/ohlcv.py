"""
Maftia Quant — Unified OHLCV Pipeline

Fetches BTC/USD daily OHLCV from Binance, validates using CausalFilter,
and stores in maftia_quant.db.

Usage:
    from src.pipelines.ohlcv import OHLCVPipeline
    
    pipeline = OHLCVPipeline()
    pipeline.run()
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class OHLCVBar:
    """Represents a single OHLCV bar."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "binance"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            "date": self.date,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "source": self.source,
        }


class BinanceClient:
    """
    Binance API client for OHLCV data.
    
    Note: In production, use the official binance-connector library.
    This is a simplified client for demonstration.
    """
    
    BASE_URL = "https://api.binance.com"
    
    def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1d",
        limit: int = 1000,
        start_time: Optional[int] = None,
    ) -> list[list[Any]]:
        """
        Fetch klines (OHLCV) from Binance API.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval (1m, 5m, 1h, 1d, etc.)
            limit: Number of klines to fetch
            start_time: Start time in milliseconds
            
        Returns:
            List of kline arrays
        """
        import urllib.request
        import json
        
        params = f"symbol={symbol}&interval={interval}&limit={limit}"
        if start_time:
            params += f"&startTime={start_time}"
        
        url = f"{self.BASE_URL}/api/v3/klines?{params}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                return data
        except Exception as e:
            print(f"Error fetching from Binance: {e}")
            return []
    
    def parse_klines(self, klines: list[list[Any]]) -> list[OHLCVBar]:
        """
        Parse raw klines into OHLCVBar objects.
        
        Args:
            klines: Raw kline data from Binance API
            
        Returns:
            List of OHLCVBar objects
        """
        bars = []
        for kline in klines:
            try:
                # Binance kline format:
                # [open_time, open, high, low, close, volume, close_time, ...]
                date = datetime.fromtimestamp(kline[0] / 1000).strftime("%Y-%m-%d")
                bar = OHLCVBar(
                    date=date,
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                )
                bars.append(bar)
            except (ValueError, IndexError, TypeError) as e:
                print(f"Warning: Skipping invalid kline: {e}")
                continue
        return bars


class CausalFilter:
    """
    Ensures zero lookahead bias.
    
    Only confirmed (closed) bars are stored.
    No future data leakage.
    """
    
    @staticmethod
    def filter_confirmed_bars(bars: list[OHLCVBar]) -> list[OHLCVBar]:
        """
        Filter to only include confirmed bars.
        
        For daily bars, a bar is confirmed if its date is before today.
        
        Args:
            bars: List of OHLCV bars
            
        Returns:
            List of confirmed bars only
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return [bar for bar in bars if bar.date < today]
    
    @staticmethod
    def validate_ohlcv(bar: OHLCVBar) -> bool:
        """
        Validate OHLCV bar integrity.
        
        Args:
            bar: OHLCV bar to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check for null values
        if any(v is None for v in [bar.open, bar.high, bar.low, bar.close, bar.volume]):
            return False
        
        # Check OHLCV relationships
        if bar.high < bar.low:
            return False
        if bar.open < bar.low or bar.open > bar.high:
            return False
        if bar.close < bar.low or bar.close > bar.high:
            return False
        
        # Check for positive values
        if any(v <= 0 for v in [bar.open, bar.high, bar.low, bar.close]):
            return False
        
        return True


class OHLCVPipeline:
    """
    Unified OHLCV pipeline for BTC/USD daily data.
    
    Fetches from Binance, applies CausalFilter, and stores in database.
    """
    
    def __init__(self, symbol: str = "BTCUSDT"):
        """
        Initialize the pipeline.
        
        Args:
            symbol: Trading pair symbol (default: BTCUSDT)
        """
        self.symbol = symbol
        self.client = BinanceClient()
        self.causal_filter = CausalFilter()
    
    def fetch(
        self,
        limit: int = 1000,
        start_date: Optional[str] = None,
    ) -> list[OHLCVBar]:
        """
        Fetch OHLCV data from Binance.
        
        Args:
            limit: Number of bars to fetch
            start_date: Optional start date (YYYY-MM-DD)
            
        Returns:
            List of OHLCV bars
        """
        start_time = None
        if start_date:
            try:
                start_time = int(
                    datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000
                )
            except ValueError as e:
                print(f"Warning: Invalid start_date format: {e}")
        
        raw_klines = self.client.get_klines(
            symbol=self.symbol,
            interval="1d",
            limit=limit,
            start_time=start_time,
        )
        
        return self.client.parse_klines(raw_klines)
    
    def validate(self, bars: list[OHLCVBar]) -> list[OHLCVBar]:
        """
        Validate and filter bars using CausalFilter.
        
        Args:
            bars: Raw OHLCV bars
            
        Returns:
            Validated and filtered bars
        """
        # Apply causal filter (no lookahead)
        confirmed = self.causal_filter.filter_confirmed_bars(bars)
        
        # Validate OHLCV integrity
        valid = [bar for bar in confirmed if self.causal_filter.validate_ohlcv(bar)]
        
        return valid
    
    def store(self, bars: list[OHLCVBar]) -> int:
        """
        Store validated bars in database.
        
        Args:
            bars: Validated OHLCV bars
            
        Returns:
            Number of bars stored
        """
        if not bars:
            return 0
        
        from db import execute_many_insert
        
        rows = [bar.to_dict() for bar in bars]
        execute_many_insert("master_ohlcv", rows)
        
        return len(rows)
    
    def run(
        self,
        limit: int = 1000,
        start_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run the full pipeline: fetch → validate → store.
        
        Args:
            limit: Number of bars to fetch
            start_date: Optional start date (YYYY-MM-DD)
            
        Returns:
            Pipeline execution summary
        """
        print(f"🔄 Fetching {self.symbol} OHLCV data...")
        bars = self.fetch(limit, start_date)
        print(f"   Fetched {len(bars)} bars")
        
        print("🔍 Applying CausalFilter...")
        valid_bars = self.validate(bars)
        print(f"   {len(valid_bars)} bars passed validation")
        
        print("💾 Storing in database...")
        stored = self.store(valid_bars)
        print(f"   Stored {stored} bars")
        
        return {
            "symbol": self.symbol,
            "fetched": len(bars),
            "valid": len(valid_bars),
            "stored": stored,
            "timestamp": datetime.utcnow().isoformat(),
        }


if __name__ == "__main__":
    # Run pipeline
    pipeline = OHLCVPipeline()
    result = pipeline.run()
    print(f"\n✅ Pipeline complete: {result}")
