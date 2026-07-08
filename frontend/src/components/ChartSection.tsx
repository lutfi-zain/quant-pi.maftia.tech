/**
 * Maftia Quant — Chart Section
 *
 * Unified chart section with BTC price chart, LTTD regime overlay,
 * MTTD trade markers, Ichimoku cloud overlay, and crosshair synchronization.
 *
 * Implements:
 * - Vertical Crosshair Synchronization (task 13.5)
 * - 85px Y-Axis Width Lock (task 13.6)
 * - Chart responsive behavior (task 13.7)
 */

import { useState, useCallback } from "react";
import { BTCPriceChart } from "./BTCPriceChart";
import { RegimeOverlayChart } from "./RegimeOverlayChart";
import { TradeMarkersChart } from "./TradeMarkersChart";
import { CloudOverlayChart } from "./CloudOverlayChart";
import type { OHLCVBar, UnifiedAnalytics } from "../api/client";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

export interface ChartSectionProps {
	priceData: OHLCVBar[];
	analyticsData: UnifiedAnalytics[];
}

// ═══════════════════════════════════════════════════════════
// ChartSection Component
// ═══════════════════════════════════════════════════════════

export function ChartSection({ priceData, analyticsData }: ChartSectionProps) {
	const [crosshairTime, setCrosshairTime] = useState<number | null>(null);

	// Crosshair sync handler — broadcasts time to all child charts
	const handleCrosshairMove = useCallback((time: number | null) => {
		setCrosshairTime(time);
	}, []);

	if (!priceData.length) {
		return null;
	}

	return (
		<div className="chart-section">
			<h2 className="panel-title">BTC/USD Price Analysis</h2>

			<div className="chart-stack">
				{/* BTC Price Candlestick Chart */}
				<div className="chart-panel">
					<BTCPriceChart
						data={priceData}
						onCrosshairMove={handleCrosshairMove}
						crosshairTime={crosshairTime}
						height={350}
					/>
				</div>

				{/* LTTD Regime Overlay */}
				{analyticsData.length > 0 && (
					<div className="chart-panel">
						<RegimeOverlayChart
							data={analyticsData}
							crosshairTime={crosshairTime}
							onCrosshairMove={handleCrosshairMove}
							height={80}
						/>
					</div>
				)}

				{/* MTTD Trade Markers */}
				{analyticsData.length > 0 && (
					<div className="chart-panel">
						<TradeMarkersChart
							analyticsData={analyticsData}
							crosshairTime={crosshairTime}
							onCrosshairMove={handleCrosshairMove}
							height={60}
						/>
					</div>
				)}

				{/* Ichimoku Cloud Overlay */}
				{analyticsData.length > 0 && (
					<div className="chart-panel">
						<CloudOverlayChart
							priceData={priceData}
							analyticsData={analyticsData}
							crosshairTime={crosshairTime}
							onCrosshairMove={handleCrosshairMove}
							height={350}
						/>
					</div>
				)}
			</div>
		</div>
	);
}
