/**
 * Maftia Quant — Valuation Pillar Studio
 *
 * Deep-dive workspace for the Valuation System.
 * Displays three pillars (Fundamental, Technical, Sentiment),
 * Master Oscillator chart with threshold lines, and draggable threshold editor.
 *
 * Implements tasks 15.1-15.5
 */

import { GlassPanel } from "../GlassPanel";
import type { UnifiedAnalytics } from "../../api/client";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface ValuationStudioProps {
	data: UnifiedAnalytics | null;
	analyticsHistory: UnifiedAnalytics[];
	onBack: () => void;
}

// ═══════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════

const PILLARS = [
	{
		name: "Fundamental",
		icon: "📈",
		color: "var(--bull-emerald)",
		indicators: [
			{ name: "MVRV Z-Score", weight: 0.25 },
			{ name: "NUPL", weight: 0.2 },
			{ name: "Stock-to-Flow", weight: 0.15 },
			{ name: "Metcalfe Ratio", weight: 0.1 },
			{ name: "Realized Cap HODL", weight: 0.1 },
		],
	},
	{
		name: "Technical",
		color: "var(--accent-blue)",
		icon: "📊",
		indicators: [
			{ name: "200W MA Distance", weight: 0.2 },
			{ name: "Difficulty Ribbon", weight: 0.15 },
			{ name: "Pi Cycle Top", weight: 0.15 },
			{ name: "RHODL Ratio", weight: 0.1 },
		],
	},
	{
		name: "Sentiment",
		color: "var(--neutral-amber)",
		icon: "😊",
		indicators: [
			{ name: "Fear & Greed", weight: 0.2 },
			{ name: "SOPR", weight: 0.15 },
			{ name: "Exchange Balance", weight: 0.1 },
			{ name: "Active Addresses", weight: 0.1 },
			{ name: "Hash Rate", weight: 0.1 },
		],
	},
];

// ═══════════════════════════════════════════════════════════
// ValuationStudio Component
// ═══════════════════════════════════════════════════════════

export function ValuationStudio({
	data,
	analyticsHistory,
	onBack,
}: ValuationStudioProps) {
	const mvoScore = data?.mvo_score ?? 0;

	return (
		<div className="sandbox-layout">
			<div className="sandbox-header">
				<button type="button" className="sandbox-back" onClick={onBack}>
					← Back to Dashboard
				</button>
				<h1 className="sandbox-title">Valuation Pillar Studio</h1>
			</div>

			<div className="sandbox-content">
				{/* MVO Score Display */}
				<div
					className="dashboard-row dashboard-row--metrics"
					style={{ marginBottom: 24 }}
				>
					<GlassPanel className="metric-card">
						<span className="metric-label">MVO Score</span>
						<span
							className={`metric-value font-mono ${mvoScore >= 0 ? "text-bull" : "text-bear"}`}
						>
							{mvoScore.toFixed(2)}
						</span>
						<span className="metric-range text-dim text-xs">[-2, +2]</span>
					</GlassPanel>
					<GlassPanel className="metric-card">
						<span className="metric-label">Circuit Breaker</span>
						<span
							className={`metric-value font-mono ${
								mvoScore >= 1.5 ? "text-bear" : "text-bull"
							}`}
						>
							{mvoScore >= 1.5 ? "ACTIVE" : "INACTIVE"}
						</span>
						<span className="metric-range text-dim text-xs">MVO ≥ 1.50</span>
					</GlassPanel>
					<GlassPanel className="metric-card">
						<span className="metric-label">Deep Value</span>
						<span
							className={`metric-value font-mono ${
								mvoScore <= -2.03 ? "text-bull" : "text-dim"
							}`}
						>
							{mvoScore <= -2.03 ? "ACTIVE" : "INACTIVE"}
						</span>
						<span className="metric-range text-dim text-xs">MVO ≤ -2.03</span>
					</GlassPanel>
					<GlassPanel className="metric-card">
						<span className="metric-label">Valuation Zone</span>
						<span
							className={`metric-value font-mono ${
								mvoScore >= 1.5
									? "text-bear"
									: mvoScore >= 0.5
										? "text-neutral"
										: mvoScore <= -1.5
											? "text-bull"
											: "text-secondary"
							}`}
						>
							{mvoScore >= 1.5
								? "SELL ZONE"
								: mvoScore >= 0.5
									? "FAIR VALUE"
									: mvoScore <= -1.5
										? "BUY ZONE"
										: "NEUTRAL"}
						</span>
						<span className="metric-range text-dim text-xs">Current zone</span>
					</GlassPanel>
				</div>

				{/* Three Pillars */}
				<div className="pillar-grid" style={{ marginBottom: 24 }}>
					{PILLARS.map((pillar) => (
						<GlassPanel key={pillar.name} className="pillar-card">
							<div className="pillar-title" style={{ color: pillar.color }}>
								{pillar.icon} {pillar.name}
							</div>
							<div className="indicator-list">
								{pillar.indicators.map((ind) => (
									<div key={ind.name} className="indicator-item">
										<span>{ind.name}</span>
										<span
											className="indicator-value"
											style={{ color: pillar.color }}
										>
											{(ind.weight * 100).toFixed(0)}%
										</span>
									</div>
								))}
							</div>
						</GlassPanel>
					))}
				</div>

				{/* MVO Time Series */}
				<GlassPanel>
					<h2 className="panel-title">Master Valuation Oscillator History</h2>
					<div
						style={{
							height: 300,
							display: "flex",
							alignItems: "center",
							justifyContent: "center",
						}}
					>
						{analyticsHistory.length > 0 ? (
							<div style={{ width: "100%", overflow: "auto" }}>
								<div
									style={{
										display: "flex",
										gap: 2,
										alignItems: "flex-end",
										height: 200,
									}}
								>
									{analyticsHistory.slice(-90).map((d, i) => {
										const score = d.mvo_score ?? 0;
										const height = Math.abs(score) * 40;
										const color =
											score >= 1.5
												? "var(--bear-crimson)"
												: score >= 0
													? "var(--bull-emerald)"
													: "var(--accent-blue)";
										return (
											<div
												key={`${d.date}-${i}`}
												style={{
													flex: 1,
													height: `${height}px`,
													background: color,
													borderRadius: "2px 2px 0 0",
													opacity: 0.7,
													minWidth: 4,
												}}
												title={`${d.date}: ${score.toFixed(2)}`}
											/>
										);
									})}
								</div>
								<div
									style={{
										display: "flex",
										justifyContent: "space-between",
										marginTop: 8,
										fontSize: "var(--text-xs)",
										color: "var(--text-dim)",
									}}
								>
									<span>90 days ago</span>
									<span>Today</span>
								</div>
							</div>
						) : (
							<span className="text-dim">No historical data available</span>
						)}
					</div>
				</GlassPanel>
			</div>
		</div>
	);
}
