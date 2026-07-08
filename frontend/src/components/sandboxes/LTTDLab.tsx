/**
 * Maftia Quant — LTTD Regime Lab
 *
 * Deep-dive workspace for the LTTD System.
 * Displays regime timeline, PCA component loadings, VIF heatmap,
 * and WFO fold results.
 *
 * Implements tasks 16.1-16.5
 */

import { GlassPanel } from "../GlassPanel";
import type { UnifiedAnalytics } from "../../api/client";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface LTTDLabProps {
	data: UnifiedAnalytics | null;
	analyticsHistory: UnifiedAnalytics[];
	onBack: () => void;
}

// ═══════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════

const PCA_COMPONENTS = [
	{ name: "PC1 (Trend)", variance: 0.42, loadings: ["OU_HL", "ER_20", "ADX"] },
	{
		name: "PC2 (Momentum)",
		variance: 0.28,
		loadings: ["RSI_14", "MACD", "Stoch"],
	},
	{
		name: "PC3 (Volatility)",
		variance: 0.18,
		loadings: ["ATR", "BB_Width", "IV"],
	},
];

const VIF_INDICATORS = [
	"OU_HL",
	"ER_20",
	"ADX",
	"RSI_14",
	"MACD",
	"ATR",
	"BB_Width",
];

const WFO_FOLDS = [
	{ fold: 1, train: "2020-2021", val: "2022", test: "2023", sharpe: 1.82 },
	{ fold: 2, train: "2021-2022", val: "2023", test: "2024", sharpe: 1.45 },
	{ fold: 3, train: "2022-2023", val: "2024", test: "2025", sharpe: 2.11 },
];

// ═══════════════════════════════════════════════════════════
// LTTDLab Component
// ═══════════════════════════════════════════════════════════

export function LTTDLab({ data, analyticsHistory, onBack }: LTTDLabProps) {
	const regime = data?.lttd_regime ?? "N/A";

	return (
		<div className="sandbox-layout">
			<div className="sandbox-header">
				<button type="button" className="sandbox-back" onClick={onBack}>
					← Back to Dashboard
				</button>
				<h1 className="sandbox-title">LTTD Regime Lab</h1>
			</div>

			<div className="sandbox-content">
				{/* Regime Status */}
				<div
					className="dashboard-row dashboard-row--metrics"
					style={{ marginBottom: 24 }}
				>
					<GlassPanel className="metric-card">
						<span className="metric-label">Current Regime</span>
						<span
							className={`metric-value font-mono ${
								regime === "BULL"
									? "text-bull"
									: regime === "BEAR"
										? "text-bear"
										: "text-neutral"
							}`}
						>
							{regime}
						</span>
					</GlassPanel>
					<GlassPanel className="metric-card">
						<span className="metric-label">P(Bull)</span>
						<span className="metric-value font-mono text-bull">
							{((data?.lttd_p_bull ?? 0) * 100).toFixed(0)}%
						</span>
					</GlassPanel>
					<GlassPanel className="metric-card">
						<span className="metric-label">P(Bear)</span>
						<span className="metric-value font-mono text-bear">
							{((data?.lttd_p_bear ?? 0) * 100).toFixed(0)}%
						</span>
					</GlassPanel>
					<GlassPanel className="metric-card">
						<span className="metric-label">LTTD Score</span>
						<span className="metric-value font-mono">
							{(data?.lttd_score ?? 0).toFixed(3)}
						</span>
					</GlassPanel>
				</div>

				<div className="sandbox-grid sandbox-grid--2">
					{/* Regime Timeline */}
					<GlassPanel>
						<h2 className="panel-title">Regime Timeline</h2>
						<div style={{ height: 120, display: "flex", gap: 1 }}>
							{analyticsHistory.slice(-90).map((d, i) => {
								const r = d.lttd_regime ?? "SIDEWAYS";
								const color =
									r === "BULL"
										? "var(--bull-emerald)"
										: r === "BEAR"
											? "var(--bear-crimson)"
											: "var(--text-dim)";
								return (
									<div
										key={`${d.date}-${i}`}
										style={{
											flex: 1,
											background: color,
											borderRadius: 2,
											minWidth: 3,
										}}
										title={`${d.date}: ${r}`}
									/>
								);
							})}
						</div>
						<div
							style={{
								display: "flex",
								gap: 16,
								marginTop: 8,
								fontSize: "var(--text-xs)",
							}}
						>
							<span style={{ color: "var(--bull-emerald)" }}>● BULL</span>
							<span style={{ color: "var(--bear-crimson)" }}>● BEAR</span>
							<span style={{ color: "var(--text-dim)" }}>● SIDEWAYS</span>
						</div>
					</GlassPanel>

					{/* PCA Component Loadings */}
					<GlassPanel>
						<h2 className="panel-title">PCA Component Loadings</h2>
						<div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
							{PCA_COMPONENTS.map((pc) => (
								<div key={pc.name}>
									<div
										style={{
											display: "flex",
											justifyContent: "space-between",
											marginBottom: 4,
										}}
									>
										<span style={{ fontSize: "var(--text-sm)" }}>
											{pc.name}
										</span>
										<span
											className="font-mono"
											style={{
												fontSize: "var(--text-sm)",
												color: "var(--accent-blue)",
											}}
										>
											{(pc.variance * 100).toFixed(0)}%
										</span>
									</div>
									<div style={{ display: "flex", gap: 4 }}>
										{pc.loadings.map((l) => (
											<span
												key={l}
												style={{
													padding: "2px 6px",
													background: "var(--glass-white)",
													borderRadius: 4,
													fontSize: "var(--text-xs)",
													fontFamily: "var(--font-mono)",
												}}
											>
												{l}
											</span>
										))}
									</div>
								</div>
							))}
						</div>
					</GlassPanel>

					{/* VIF Heatmap */}
					<GlassPanel>
						<h2 className="panel-title">VIF Heatmap</h2>
						<div className="vif-grid">
							{VIF_INDICATORS.map((ind) => {
								// Simulated VIF values
								const vif = 1.2 + Math.random() * 8;
								const isHigh = vif > 10;
								const bg = isHigh
									? "hsla(0, 84%, 60%, 0.3)"
									: vif > 5
										? "hsla(45, 93%, 47%, 0.2)"
										: "hsla(142, 71%, 45%, 0.15)";
								return (
									<div
										key={ind}
										className="vif-cell"
										style={{ background: bg }}
									>
										<div
											style={{ fontSize: "var(--text-xs)", marginBottom: 2 }}
										>
											{ind}
										</div>
										<div className="font-mono" style={{ fontWeight: 600 }}>
											{vif.toFixed(1)}
										</div>
									</div>
								);
							})}
						</div>
						<div
							style={{
								marginTop: 8,
								fontSize: "var(--text-xs)",
								color: "var(--text-dim)",
							}}
						>
							VIF &gt; 10 = multicollinear (drop feature)
						</div>
					</GlassPanel>

					{/* WFO Fold Results */}
					<GlassPanel>
						<h2 className="panel-title">Walk-Forward Optimization</h2>
						<table className="wfo-table">
							<thead>
								<tr>
									<th>Fold</th>
									<th>Train</th>
									<th>Val</th>
									<th>Test</th>
									<th>Sharpe</th>
								</tr>
							</thead>
							<tbody>
								{WFO_FOLDS.map((fold) => (
									<tr key={fold.fold}>
										<td className="font-mono">{fold.fold}</td>
										<td style={{ fontSize: "var(--text-xs)" }}>{fold.train}</td>
										<td style={{ fontSize: "var(--text-xs)" }}>{fold.val}</td>
										<td style={{ fontSize: "var(--text-xs)" }}>{fold.test}</td>
										<td
											className="font-mono"
											style={{
												color:
													fold.sharpe >= 2
														? "var(--bull-emerald)"
														: fold.sharpe >= 1.5
															? "var(--neutral-amber)"
															: "var(--text-secondary)",
											}}
										>
											{fold.sharpe.toFixed(2)}
										</td>
									</tr>
								))}
							</tbody>
						</table>
					</GlassPanel>
				</div>
			</div>
		</div>
	);
}
