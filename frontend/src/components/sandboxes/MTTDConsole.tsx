/**
 * Maftia Quant — MTTD Console
 *
 * Deep-dive workspace for the MTTD System.
 * Displays IMO time-series with gate annotations,
 * trade markers, and gate blocker heatmap.
 *
 * Implements tasks 17.1-17.4
 */

import { GlassPanel } from "../GlassPanel";
import type { UnifiedAnalytics } from "../../api/client";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface MTTDConsoleProps {
	data: UnifiedAnalytics | null;
	analyticsHistory: UnifiedAnalytics[];
	onBack: () => void;
}

// ═══════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════

const GATE_HISTORY = [
	{
		date: "2025-06-15",
		gate: "ER Gate",
		blocked: true,
		reason: "ER=0.18 < 0.20",
	},
	{
		date: "2025-06-10",
		gate: "Entropy Gate",
		blocked: true,
		reason: "Entropy=2.45 > 2.30",
	},
	{
		date: "2025-05-28",
		gate: "Regime Override",
		blocked: true,
		reason: "LTTD=BEAR",
	},
	{
		date: "2025-05-15",
		gate: "None",
		blocked: false,
		reason: "All gates passed",
	},
	{
		date: "2025-05-01",
		gate: "ER Gate",
		blocked: true,
		reason: "ER=0.15 < 0.20",
	},
];

// ═══════════════════════════════════════════════════════════
// MTTDConsole Component
// ═══════════════════════════════════════════════════════════

export function MTTDConsole({
	data,
	analyticsHistory,
	onBack,
}: MTTDConsoleProps) {
	const position = (data?.mttd_position ?? 0) > 0.5 ? "LONG" : "FLAT";
	const imo = data?.mttd_imo ?? 0;
	const er = data?.mttd_er ?? 0;
	const entropy = data?.mttd_entropy ?? 0;

	return (
		<div className="sandbox-layout">
			<div className="sandbox-header">
				<button type="button" className="sandbox-back" onClick={onBack}>
					← Back to Dashboard
				</button>
				<h1 className="sandbox-title">MTTD Console</h1>
			</div>

			<div className="sandbox-content">
				{/* MTTD Status */}
				<div
					className="dashboard-row dashboard-row--metrics"
					style={{ marginBottom: 24 }}
				>
					<GlassPanel className="metric-card">
						<span className="metric-label">Position</span>
						<span
							className={`metric-value font-mono ${position === "LONG" ? "text-bull" : "text-dim"}`}
						>
							{position}
						</span>
					</GlassPanel>
					<GlassPanel className="metric-card">
						<span className="metric-label">IMO Score</span>
						<span
							className={`metric-value font-mono ${imo > 0 ? "text-bull" : imo < 0 ? "text-bear" : "text-dim"}`}
						>
							{imo.toFixed(2)}
						</span>
						<span className="metric-range text-dim text-xs">[-1, +1]</span>
					</GlassPanel>
					<GlassPanel className="metric-card">
						<span className="metric-label">Efficiency Ratio</span>
						<span
							className={`metric-value font-mono ${er >= 0.2 ? "text-bull" : "text-bear"}`}
						>
							{er.toFixed(2)}
						</span>
						<span className="metric-range text-dim text-xs">Gate: ≥ 0.20</span>
					</GlassPanel>
					<GlassPanel className="metric-card">
						<span className="metric-label">Entropy</span>
						<span
							className={`metric-value font-mono ${entropy <= 2.3 ? "text-bull" : "text-bear"}`}
						>
							{entropy.toFixed(2)}
						</span>
						<span className="metric-range text-dim text-xs">Gate: ≤ 2.30</span>
					</GlassPanel>
				</div>

				<div className="sandbox-grid sandbox-grid--2">
					{/* IMO Time Series */}
					<GlassPanel>
						<h2 className="panel-title">IMO Score History</h2>
						<div
							style={{
								height: 200,
								display: "flex",
								alignItems: "center",
								gap: 1,
							}}
						>
							{analyticsHistory.slice(-60).map((d, i) => {
								const score = d.mttd_imo ?? 0;
								const height = Math.abs(score) * 80;
								const color =
									score > 0 ? "var(--bull-emerald)" : "var(--bear-crimson)";
								return (
									<div
										key={`${d.date}-${i}`}
										style={{
											flex: 1,
											display: "flex",
											flexDirection: "column",
											justifyContent: score > 0 ? "flex-end" : "flex-start",
											height: "100%",
										}}
									>
										<div
											style={{
												height: `${height}px`,
												background: color,
												borderRadius: 2,
												opacity: 0.7,
												minWidth: 3,
											}}
											title={`${d.date}: ${score.toFixed(3)}`}
										/>
									</div>
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
							<span>60 days ago</span>
							<span>Today</span>
						</div>
					</GlassPanel>

					{/* Gate Blocker Heatmap */}
					<GlassPanel>
						<h2 className="panel-title">Gate Blockers</h2>
						<div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
							{GATE_HISTORY.map((entry) => (
								<div
									key={entry.date}
									style={{
										display: "flex",
										justifyContent: "space-between",
										alignItems: "center",
										padding: "8px 12px",
										background: entry.blocked
											? "hsla(0, 84%, 60%, 0.1)"
											: "hsla(142, 71%, 45%, 0.1)",
										borderRadius: 4,
										borderLeft: `3px solid ${entry.blocked ? "var(--bear-crimson)" : "var(--bull-emerald)"}`,
									}}
								>
									<div>
										<div
											style={{ fontSize: "var(--text-sm)", fontWeight: 600 }}
										>
											{entry.date}
										</div>
										<div
											style={{
												fontSize: "var(--text-xs)",
												color: "var(--text-secondary)",
											}}
										>
											{entry.reason}
										</div>
									</div>
									<span
										style={{
											fontSize: "var(--text-sm)",
											fontWeight: 600,
											color: entry.blocked
												? "var(--bear-crimson)"
												: "var(--bull-emerald)",
										}}
									>
										{entry.blocked ? "BLOCKED" : "PASSED"}
									</span>
								</div>
							))}
						</div>
					</GlassPanel>
				</div>

				{/* Trade Markers on Price */}
				<GlassPanel className="mt-16">
					<h2 className="panel-title">Recent Trade Signals</h2>
					<div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
						{analyticsHistory.slice(-30).map((d, i) => {
							const pos = (d.mttd_position ?? 0) > 0.5;
							const prevPos =
								i > 0
									? (analyticsHistory[analyticsHistory.length - 30 + i - 1]
											?.mttd_position ?? 0) > 0.5
									: false;
							const isEntry = !prevPos && pos;
							const isExit = prevPos && !pos;
							if (!isEntry && !isExit) return null;
							return (
								<div
									key={d.date}
									style={{
										padding: "4px 8px",
										background: isEntry
											? "hsla(142, 71%, 45%, 0.15)"
											: "hsla(0, 84%, 60%, 0.15)",
										borderRadius: 4,
										fontSize: "var(--text-xs)",
										fontFamily: "var(--font-mono)",
									}}
								>
									{isEntry ? "▲ ENTRY" : "▼ EXIT"} {d.date}
								</div>
							);
						})}
						{analyticsHistory.slice(-30).every((d, i) => {
							const pos = (d.mttd_position ?? 0) > 0.5;
							const prevPos =
								i > 0
									? (analyticsHistory[analyticsHistory.length - 30 + i - 1]
											?.mttd_position ?? 0) > 0.5
									: false;
							return !((!prevPos && pos) || (prevPos && !pos));
						}) && (
							<span className="text-dim" style={{ fontSize: "var(--text-sm)" }}>
								No recent trade signals
							</span>
						)}
					</div>
				</GlassPanel>
			</div>
		</div>
	);
}
