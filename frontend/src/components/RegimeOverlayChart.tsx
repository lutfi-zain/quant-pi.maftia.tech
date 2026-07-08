/**
 * Maftia Quant — Regime Overlay Chart
 *
 * Horizontal bar chart showing LTTD regime states (BULL/BEAR/SIDEWAYS)
 * as colored bands. Synchronized with BTC price chart crosshair.
 *
 * Implements task 13.2: Add LTTD regime overlay (colored bands)
 */

import { useEffect, useRef } from "react";
import {
	createChart,
	ColorType,
	CrosshairMode,
	type IChartApi,
	type ISeriesApi,
	type Time,
} from "lightweight-charts";
import type { UnifiedAnalytics } from "../api/client";
import { CHART_COLORS } from "../styles/chart-colors";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface RegimeOverlayChartProps {
	data: UnifiedAnalytics[];
	crosshairTime: number | null;
	onCrosshairMove?: (time: number | null) => void;
	height?: number;
}

// ═══════════════════════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════════════════════

const REGIME_COLORS: Record<string, string> = {
	BULL: CHART_COLORS.bullEmerald,
	BEAR: CHART_COLORS.bearCrimson,
	SIDEWAYS: CHART_COLORS.textDim,
};

// ═══════════════════════════════════════════════════════════
// RegimeOverlayChart Component
// ═══════════════════════════════════════════════════════════

export function RegimeOverlayChart({
	data,
	crosshairTime,
	onCrosshairMove,
	height = 80,
}: RegimeOverlayChartProps) {
	const chartContainerRef = useRef<HTMLDivElement>(null);
	const chartRef = useRef<IChartApi | null>(null);
	const seriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);

	// Initialize chart
	useEffect(() => {
		if (!chartContainerRef.current) return;

		const chart = createChart(chartContainerRef.current, {
			layout: {
				background: { type: ColorType.Solid, color: "transparent" },
				textColor: CHART_COLORS.textSecondary,
				fontFamily: CHART_COLORS.fontMono,
				fontSize: 10,
			},
			grid: {
				vertLines: { color: CHART_COLORS.obsidianBorder },
				horzLines: { visible: false },
			},
			crosshair: {
				mode: CrosshairMode.Normal,
				vertLine: {
					color: CHART_COLORS.accentBlue,
					width: 1,
					style: 2,
					labelBackgroundColor: CHART_COLORS.accentBlue,
				},
				horzLine: { visible: false },
			},
			rightPriceScale: {
				borderColor: CHART_COLORS.obsidianBorder,
				scaleMargins: { top: 0.1, bottom: 0.1 },
			},
			timeScale: {
				borderColor: CHART_COLORS.obsidianBorder,
				timeVisible: false,
				rightOffset: 5,
				barSpacing: 8,
			},
			width: chartContainerRef.current.clientWidth,
			height,
		});

		const histogramSeries = chart.addHistogramSeries({
			color: CHART_COLORS.textDim,
			priceFormat: { type: "price", precision: 0, minMove: 1 },
			priceScaleId: "regime",
		});

		chart.priceScale("regime").applyOptions({
			scaleMargins: { top: 0.1, bottom: 0.1 },
		});

		chartRef.current = chart;
		seriesRef.current = histogramSeries;

		// Crosshair sync
		chart.subscribeCrosshairMove((param) => {
			if (onCrosshairMove) {
				const time = param.time as number | undefined;
				onCrosshairMove(time ?? null);
			}
		});

		// Resize observer
		const resizeObserver = new ResizeObserver((entries) => {
			for (const entry of entries) {
				chart.applyOptions({ width: entry.contentRect.width });
			}
		});
		resizeObserver.observe(chartContainerRef.current);

		return () => {
			resizeObserver.disconnect();
			chart.remove();
			chartRef.current = null;
			seriesRef.current = null;
		};
	}, [height, onCrosshairMove]);

	// Update data
	useEffect(() => {
		if (!seriesRef.current || !data.length) return;

		const regimeData = data
			.filter((d) => d.lttd_regime && d.date)
			.map((d) => {
				const time = Math.floor(new Date(d.date).getTime() / 1000) as Time;
				const regime = d.lttd_regime ?? "SIDEWAYS";
				const color = REGIME_COLORS[regime] ?? CHART_COLORS.textDim;
				// Map regime to numeric value for histogram height
				const value = regime === "BULL" ? 1 : regime === "BEAR" ? -1 : 0;
				return { time, value, color };
			})
			.sort((a, b) => (a.time as number) - (b.time as number));

		seriesRef.current.setData(regimeData);
	}, [data]);

	// External crosshair sync
	useEffect(() => {
		if (!chartRef.current || crosshairTime === null || !seriesRef.current)
			return;

		const seriesData = seriesRef.current.data();
		const lastBar = seriesData[seriesData.length - 1];
		if (lastBar && "close" in lastBar) {
			chartRef.current.setCrosshairPosition(
				lastBar.close as number,
				crosshairTime as Time,
				seriesRef.current,
			);
		}
	}, [crosshairTime]);

	return (
		<div className="regime-overlay-chart">
			<span className="chart-label text-dim text-xs">LTTD REGIME</span>
			<div
				ref={chartContainerRef}
				style={{ width: "100%", height: `${height}px` }}
			/>
		</div>
	);
}
