/**
 * Maftia Quant — Cross-System Confluence Gauge
 *
 * Visual gauge showing the alignment of all 4 systems.
 * Displays consensus score and exposure state.
 */

import type { UnifiedAnalytics } from "../api/client";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface ConfluenceGaugeProps {
	data: UnifiedAnalytics;
}

// ═══════════════════════════════════════════════════════════
// Helper Functions
// ═══════════════════════════════════════════════════════════

function getConfluenceLevel(data: UnifiedAnalytics): {
	level: string;
	color: string;
	percentage: number;
} {
	const positions = [
		data.lttd_exposure ?? 0,
		data.mttd_position ?? 0,
		data.ichi_position ?? 0,
	];

	const activeCount = positions.filter((p) => p > 0.5).length;
	const percentage = (activeCount / 3) * 100;

	if (activeCount === 3) {
		return {
			level: "STRONG CONFLUENCE",
			color: "var(--bull-emerald)",
			percentage,
		};
	}
	if (activeCount === 2) {
		return {
			level: "PARTIAL CONFLUENCE",
			color: "var(--neutral-amber)",
			percentage,
		};
	}
	if (activeCount === 1) {
		return { level: "WEAK SIGNAL", color: "var(--text-secondary)", percentage };
	}
	return { level: "NO CONFLUENCE", color: "var(--bear-crimson)", percentage };
}

// ═══════════════════════════════════════════════════════════
// ConfluenceGauge Component
// ═══════════════════════════════════════════════════════════

export function ConfluenceGauge({ data }: ConfluenceGaugeProps) {
	const confluence = getConfluenceLevel(data);
	const consensusScore = data.consensus_score ?? 0;
	const consensusExposure = data.consensus_exposure ?? 0;

	return (
		<div className="confluence-gauge">
			{/* Circular Gauge */}
			<div className="gauge-visual">
				<svg viewBox="0 0 120 120" className="gauge-svg">
					{/* Background circle */}
					<circle
						cx="60"
						cy="60"
						r="54"
						fill="none"
						stroke="var(--obsidian-border)"
						strokeWidth="8"
					/>
					{/* Progress arc */}
					<circle
						cx="60"
						cy="60"
						r="54"
						fill="none"
						stroke={confluence.color}
						strokeWidth="8"
						strokeDasharray={`${(confluence.percentage / 100) * 339.292} 339.292`}
						strokeLinecap="round"
						transform="rotate(-90 60 60)"
						style={{ transition: "stroke-dasharray 0.5s ease-out" }}
					/>
				</svg>
				<div className="gauge-center">
					<span
						className="gauge-value font-mono"
						style={{ color: confluence.color }}
					>
						{consensusExposure > 0.5 ? "1.0" : "0.0"}
					</span>
					<span className="gauge-label text-dim text-xs">EXPOSURE</span>
				</div>
			</div>

			{/* Confluence Level */}
			<div className="confluence-info">
				<span className="confluence-level" style={{ color: confluence.color }}>
					{confluence.level}
				</span>
				<span className="confluence-score font-mono text-secondary">
					Score: {consensusScore.toFixed(3)}
				</span>
			</div>

			{/* System Alignment */}
			<div className="system-alignment">
				<div className="alignment-item">
					<span className="alignment-label">Valuation</span>
					<span
						className={`alignment-status ${
							(data.mvo_score ?? 0) >= 0 ? "text-bull" : "text-bear"
						}`}
					>
						{(data.mvo_score ?? 0).toFixed(2)}
					</span>
				</div>
				<div className="alignment-item">
					<span className="alignment-label">LTTD</span>
					<span
						className={`alignment-status ${
							(data.lttd_exposure ?? 0) > 0.5 ? "text-bull" : "text-dim"
						}`}
					>
						{(data.lttd_exposure ?? 0) > 0.5 ? "ON" : "OFF"}
					</span>
				</div>
				<div className="alignment-item">
					<span className="alignment-label">MTTD</span>
					<span
						className={`alignment-status ${
							(data.mttd_position ?? 0) > 0.5 ? "text-bull" : "text-dim"
						}`}
					>
						{(data.mttd_position ?? 0) > 0.5 ? "ON" : "OFF"}
					</span>
				</div>
				<div className="alignment-item">
					<span className="alignment-label">Ichimoku</span>
					<span
						className={`alignment-status ${
							(data.ichi_position ?? 0) > 0.5 ? "text-bull" : "text-dim"
						}`}
					>
						{(data.ichi_position ?? 0) > 0.5 ? "ON" : "OFF"}
					</span>
				</div>
			</div>
		</div>
	);
}
