"""
Maftia Quant — Daily Analytics Runner

Computes daily analytics for all 4 systems and writes to unified_daily_analytics.
Implements interlocking safeguards (Circuit Breaker + Regime Override).

Usage:
    from src.pipelines.daily_analytics import DailyAnalyticsRunner
    
    runner = DailyAnalyticsRunner()
    result = runner.run("2026-07-08")
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db import get_db, execute_query, execute_insert


@dataclass
class SystemScores:
    """Container for all system scores for a single date."""
    date: str
    
    # Valuation
    mvo_score: float = 0.0
    mvo_pillar_fundamental: float = 0.0
    mvo_pillar_technical: float = 0.0
    mvo_pillar_sentiment: float = 0.0
    
    # LTTD
    lttd_score: float = 0.0
    lttd_regime: str = "SIDEWAYS"
    lttd_p_bull: float = 0.33
    lttd_p_bear: float = 0.33
    lttd_p_sideways: float = 0.34
    lttd_exposure: float = 0.0
    lttd_circuit_breaker: int = 0
    
    # MTTD
    mttd_imo: float = 0.0
    mttd_position: float = 0.0
    mttd_er: float = 0.0
    mttd_entropy: float = 0.0
    
    # Ichimoku
    ichi_imo: float = 0.0
    ichi_position: float = 0.0
    ichi_s_tk: float = 0.0
    ichi_s_cloud: float = 0.0
    ichi_s_future: float = 0.0
    ichi_s_chikou: float = 0.0
    
    # Consensus
    consensus_score: float = 0.0
    consensus_exposure: float = 0.0


class InterlockingSafeguards:
    """
    Implements the interlocking safeguards matrix.
    
    Tier 1: Circuit Breaker (MVO ≥ +1.50 → ALL systems forced to 0.0)
    Tier 2: Regime Override (BEAR/SIDEWAYS → MTTD + Ichimoku forced to 0.0)
    Tier 3: Gate blocks (ER < 0.20, Entropy > 2.30 → individual system 0.0)
    """
    
    # Thresholds
    CIRCUIT_BREAKER_THRESHOLD = 1.50
    CIRCUIT_BREAKER_COOL_OFF = 0.80
    ER_THRESHOLD = 0.20
    ENTROPY_THRESHOLD = 2.30
    
    @classmethod
    def apply_circuit_breaker(cls, scores: SystemScores) -> SystemScores:
        """
        Apply Circuit Breaker (Tier 1).
        
        When MVO ≥ +1.50, ALL systems forced to 0.0 exposure.
        """
        if scores.mvo_score >= cls.CIRCUIT_BREAKER_THRESHOLD:
            scores.lttd_exposure = 0.0
            scores.mttd_position = 0.0
            scores.ichi_position = 0.0
            scores.lttd_circuit_breaker = 1
        return scores
    
    @classmethod
    def apply_regime_override(cls, scores: SystemScores) -> SystemScores:
        """
        Apply Regime Override (Tier 2).
        
        When LTTD Regime = BEAR or SIDEWAYS, MTTD + Ichimoku forced to 0.0.
        """
        if scores.lttd_regime in ("BEAR", "SIDEWAYS"):
            scores.mttd_position = 0.0
            scores.ichi_position = 0.0
        return scores
    
    @classmethod
    def apply_gate_blocks(cls, scores: SystemScores) -> SystemScores:
        """
        Apply Gate Blocks (Tier 3).
        
        ER < 0.20 → MTTD blocked
        Entropy > 2.30 → MTTD blocked
        """
        if scores.mttd_er < cls.ER_THRESHOLD:
            scores.mttd_position = 0.0
        if scores.mttd_entropy > cls.ENTROPY_THRESHOLD:
            scores.mttd_position = 0.0
        return scores
    
    @classmethod
    def compute_consensus(cls, scores: SystemScores) -> SystemScores:
        """
        Compute consensus exposure from all system positions.
        
        Final exposure is the intersection of all system constraints.
        Any system can veto to 0.0, but NO system can override to 1.0 alone.
        """
        # Apply safeguards in order
        scores = cls.apply_circuit_breaker(scores)
        scores = cls.apply_regime_override(scores)
        scores = cls.apply_gate_blocks(scores)
        
        # Consensus is minimum of all positions
        positions = [scores.lttd_exposure, scores.mttd_position, scores.ichi_position]
        scores.consensus_exposure = min(positions) if positions else 0.0
        
        # Consensus score is average of all scores
        score_list = [scores.lttd_score, scores.mttd_imo, scores.ichi_imo]
        scores.consensus_score = sum(score_list) / len(score_list) if score_list else 0.0
        
        return scores


class DailyAnalyticsRunner:
    """
    Runs daily analytics computation for all systems.
    """
    
    def __init__(self):
        """Initialize the runner."""
        self.safeguards = InterlockingSafeguards()
    
    def fetch_latest_data(self, date: str) -> dict[str, Any]:
        """
        Fetch latest data from all tables for computation.
        
        Args:
            date: Date to compute analytics for (YYYY-MM-DD)
            
        Returns:
            Dictionary with all required data
        """
        # This is a placeholder - in production, this would fetch from
        # the actual computation results or raw data tables
        return {
            "date": date,
            "mvo_score": 0.0,
            "lttd_score": 0.0,
            "lttd_regime": "SIDEWAYS",
            "mttd_imo": 0.0,
            "mttd_er": 0.5,
            "mttd_entropy": 1.5,
            "ichi_imo": 0.0,
        }
    
    def compute_analytics(self, data: dict[str, Any]) -> SystemScores:
        """
        Compute analytics from raw data.
        
        Args:
            data: Raw data dictionary
            
        Returns:
            SystemScores with all computed values
        """
        scores = SystemScores(date=data["date"])
        
        # Valuation scores
        scores.mvo_score = data.get("mvo_score", 0.0)
        
        # LTTD scores
        scores.lttd_score = data.get("lttd_score", 0.0)
        scores.lttd_regime = data.get("lttd_regime", "SIDEWAYS")
        scores.lttd_exposure = 1.0 if scores.lttd_score > 0.5 else 0.0
        
        # MTTD scores
        scores.mttd_imo = data.get("mttd_imo", 0.0)
        scores.mttd_er = data.get("mttd_er", 0.0)
        scores.mttd_entropy = data.get("mttd_entropy", 0.0)
        scores.mttd_position = 1.0 if scores.mttd_imo > 0.25 else 0.0
        
        # Ichimoku scores
        scores.ichi_imo = data.get("ichi_imo", 0.0)
        scores.ichi_position = 1.0 if scores.ichi_imo > 0.25 else 0.0
        
        return scores
    
    def store_analytics(self, scores: SystemScores) -> None:
        """
        Store computed analytics in database.
        
        Args:
            scores: Computed system scores
        """
        data = {
            "date": scores.date,
            "mvo_score": scores.mvo_score,
            "lttd_score": scores.lttd_score,
            "lttd_regime": scores.lttd_regime,
            "lttd_exposure": scores.lttd_exposure,
            "lttd_circuit_breaker": scores.lttd_circuit_breaker,
            "mttd_imo": scores.mttd_imo,
            "mttd_position": scores.mttd_position,
            "mttd_er": scores.mttd_er,
            "mttd_entropy": scores.mttd_entropy,
            "ichi_imo": scores.ichi_imo,
            "ichi_position": scores.ichi_position,
            "consensus_score": scores.consensus_score,
            "consensus_exposure": scores.consensus_exposure,
        }
        execute_insert("unified_daily_analytics", data)
    
    def run(self, date: Optional[str] = None) -> dict[str, Any]:
        """
        Run the full daily analytics pipeline.
        
        Args:
            date: Date to compute (default: today)
            
        Returns:
            Execution summary
        """
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        print(f"🔄 Computing daily analytics for {date}...")
        
        # Fetch data
        data = self.fetch_latest_data(date)
        
        # Compute analytics
        scores = self.compute_analytics(data)
        
        # Apply interlocking safeguards
        scores = self.safeguards.compute_consensus(scores)
        
        # Store results
        self.store_analytics(scores)
        
        print(f"   ✓ MVO: {scores.mvo_score:.2f}")
        print(f"   ✓ Regime: {scores.lttd_regime}")
        print(f"   ✓ Circuit Breaker: {'ACTIVE' if scores.lttd_circuit_breaker else 'INACTIVE'}")
        print(f"   ✓ Consensus Exposure: {scores.consensus_exposure:.1f}")
        
        return {
            "date": date,
            "mvo_score": scores.mvo_score,
            "regime": scores.lttd_regime,
            "circuit_breaker": bool(scores.lttd_circuit_breaker),
            "consensus_exposure": scores.consensus_exposure,
        }


if __name__ == "__main__":
    runner = DailyAnalyticsRunner()
    result = runner.run()
    print(f"\n✅ Daily analytics complete: {result}")
