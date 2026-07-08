/**
 * Maftia Quant — Action Banner Component
 *
 * Displays the current recommended action based on interlocking safeguards.
 * Shows circuit breaker status, regime override, and consensus exposure.
 */

import type { UnifiedAnalytics } from "../api/client";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface ActionBannerProps {
	data: UnifiedAnalytics;
}

interface ActionState {
	action: string;
	reason: string;
	severity: "info" | "warning" | "critical";
}

// ═══════════════════════════════════════════════════════════
// Helper Functions
// ═══════════════════════════════════════════════════════════

function getActionState(data: UnifiedAnalytics): ActionState {
	// Tier 1: Circuit Breaker
	if (data.lttd_circuit_breaker) {
		return {
			action: "HOLD — Circuit Breaker Active",
			reason: `MVO at ${(data.mvo_score ?? 0).toFixed(2)} exceeded +1.50 threshold`,
			severity: "critical",
		};
	}

	// Tier 2: Regime Override
	if (data.lttd_regime === "BEAR" || data.lttd_regime === "SIDEWAYS") {
		return {
			action: `REDUCE — Regime Override (${data.lttd_regime})`,
			reason: "MTTD and Ichimoku systems forced to 0.0 exposure",
			severity: "warning",
		};
	}

	// Tier 3: No position
	if ((data.consensus_exposure ?? 0) === 0) {
		return {
			action: "FLAT — No Confluence",
			reason: "Systems not aligned for entry",
			severity: "info",
		};
	}

	// Active position
	return {
		action: "LONG — All Systems Aligned",
		reason: "Consensus exposure active with safeguards clear",
		severity: "info",
	};
}

// ═══════════════════════════════════════════════════════════
// ActionBanner Component
// ═══════════════════════════════════════════════════════════

export function ActionBanner({ data }: ActionBannerProps) {
	const state = getActionState(data);

	return (
		<div className={`action-banner action-banner--${state.severity}`}>
			<div className="action-banner-content">
				<span className="action-banner-icon">
					{state.severity === "critical"
						? "🔴"
						: state.severity === "warning"
							? "🟡"
							: "🟢"}
				</span>
				<div className="action-banner-text">
					<span className="action-banner-action font-mono">{state.action}</span>
					<span className="action-banner-reason text-secondary">
						{state.reason}
					</span>
				</div>
			</div>
			<div className="action-banner-meta text-dim text-xs">
				<span>Last Updated: {data.date}</span>
				<span>•</span>
				<span>Consensus: {(data.consensus_score ?? 0).toFixed(3)}</span>
			</div>
		</div>
	);
}
