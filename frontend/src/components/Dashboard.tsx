/**
 * Maftia Quant — Dashboard Component
 *
 * Executive Dashboard with Bento grid layout.
 * Displays cross-system consensus and key metrics.
 */

import type { UnifiedAnalytics } from "../api/client";
import { GlassPanel } from "./GlassPanel";
import { ConfluenceGauge } from "./ConfluenceGauge";
import { ActionBanner } from "./ActionBanner";
import { SummaryTable } from "./SummaryTable";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface DashboardProps {
	data: UnifiedAnalytics | null;
}

// ═══════════════════════════════════════════════════════════
// Dashboard Component
// ═══════════════════════════════════════════════════════════

export function Dashboard({ data }: DashboardProps) {
	if (!data) {
		return (
			<div className="dashboard-empty">
				<GlassPanel>
					<p className="text-secondary">No analytics data available</p>
					<p className="text-dim text-sm">
						Run the daily analytics pipeline to generate data
					</p>
				</GlassPanel>
			</div>
		);
	}

	return (
		<div className="dashboard">
			{/* Row 1: Action Banner (full width) */}
			<div className="dashboard-row dashboard-row--banner">
				<ActionBanner data={data} />
			</div>

			{/* Row 2: Key Metrics (4 columns) */}
			<div className="dashboard-row dashboard-row--metrics">
				<GlassPanel className="metric-card">
					<span className="metric-label">MVO Score</span>
					<span
						className={`metric-value font-mono ${
							(data.mvo_score ?? 0) >= 0 ? "text-bull" : "text-bear"
						}`}
					>
						{(data.mvo_score ?? 0).toFixed(2)}
					</span>
					<span className="metric-range text-dim text-xs">[-2, +2]</span>
				</GlassPanel>

				<GlassPanel className="metric-card">
					<span className="metric-label">LTTD Regime</span>
					<span
						className={`metric-value font-mono ${
							data.lttd_regime === "BULL"
								? "text-bull"
								: data.lttd_regime === "BEAR"
									? "text-bear"
									: "text-neutral"
						}`}
					>
						{data.lttd_regime ?? "N/A"}
					</span>
					<span className="metric-range text-dim text-xs">
						P(bull): {((data.lttd_p_bull ?? 0) * 100).toFixed(0)}%
					</span>
				</GlassPanel>

				<GlassPanel className="metric-card">
					<span className="metric-label">MTTD Position</span>
					<span
						className={`metric-value font-mono ${
							(data.mttd_position ?? 0) > 0.5 ? "text-bull" : "text-dim"
						}`}
					>
						{(data.mttd_position ?? 0) > 0.5 ? "LONG" : "FLAT"}
					</span>
					<span className="metric-range text-dim text-xs">
						IMO: {(data.mttd_imo ?? 0).toFixed(2)}
					</span>
				</GlassPanel>

				<GlassPanel className="metric-card">
					<span className="metric-label">Ichimoku</span>
					<span
						className={`metric-value font-mono ${
							(data.ichi_position ?? 0) > 0.5 ? "text-bull" : "text-dim"
						}`}
					>
						{(data.ichi_position ?? 0) > 0.5 ? "LONG" : "FLAT"}
					</span>
					<span className="metric-range text-dim text-xs">
						IMO: {(data.ichi_imo ?? 0).toFixed(2)}
					</span>
				</GlassPanel>
			</div>

			{/* Row 3: Confluence Gauge + Summary Table */}
			<div className="dashboard-row dashboard-row--main">
				<div className="dashboard-col dashboard-col--gauge">
					<GlassPanel>
						<h2 className="panel-title">Cross-System Confluence</h2>
						<ConfluenceGauge data={data} />
					</GlassPanel>
				</div>

				<div className="dashboard-col dashboard-col--table">
					<GlassPanel>
						<h2 className="panel-title">System Status</h2>
						<SummaryTable data={data} />
					</GlassPanel>
				</div>
			</div>

			{/* Row 4: Safeguard Status */}
			<div className="dashboard-row dashboard-row--safeguards">
				<GlassPanel className="safeguard-panel">
					<h2 className="panel-title">Interlocking Safeguards</h2>
					<div className="safeguard-grid">
						<div className="safeguard-item">
							<span className="safeguard-label">Circuit Breaker</span>
							<span
								className={`safeguard-status ${
									data.lttd_circuit_breaker ? "active" : "inactive"
								}`}
							>
								{data.lttd_circuit_breaker ? "🔴 ACTIVE" : "🟢 INACTIVE"}
							</span>
						</div>
						<div className="safeguard-item">
							<span className="safeguard-label">Regime Override</span>
							<span
								className={`safeguard-status ${
									data.lttd_regime !== "BULL" ? "active" : "inactive"
								}`}
							>
								{data.lttd_regime !== "BULL"
									? `🔴 ${data.lttd_regime}`
									: "🟢 BULL"}
							</span>
						</div>
						<div className="safeguard-item">
							<span className="safeguard-label">Consensus Exposure</span>
							<span
								className={`safeguard-status ${
									(data.consensus_exposure ?? 0) > 0 ? "active" : "inactive"
								}`}
							>
								{(data.consensus_exposure ?? 0) > 0 ? "🟢 LONG" : "⚪ FLAT"}
							</span>
						</div>
					</div>
				</GlassPanel>
			</div>
		</div>
	);
}
