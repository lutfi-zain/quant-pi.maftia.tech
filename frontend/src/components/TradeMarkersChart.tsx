/**
 * Maftia Quant — Trade Markers Chart
 *
 * Line chart showing MTTD position with entry/exit markers.
 * Synchronized with BTC price chart crosshair.
 *
 * Implements task 13.3: Add MTTD trade markers (entry/exit)
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

interface TradeMarkersChartProps {
	analyticsData: UnifiedAnalytics[];
	crosshairTime: number | null;
	onCrosshairMove?: (time: number | null) => void;
	height?: number;
}

// ═══════════════════════════════════════════════════════════
// TradeMarkersChart Component
// ═══════════════════════════════════════════════════════════

export function TradeMarkersChart({
	analyticsData,
	crosshairTime,
	onCrosshairMove,
	height = 60,
}: TradeMarkersChartProps) {
	const chartContainerRef = useRef<HTMLDivElement>(null);
	const chartRef = useRef<IChartApi | null>(null);
	const positionSeriesRef = useRef<ISeriesApi<"Line"> | null>(null);

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
				horzLines: { color: CHART_COLORS.obsidianBorder },
			},
			crosshair: {
				mode: CrosshairMode.Normal,
				vertLine: {
					color: CHART_COLORS.accentBlue,
					width: 1,
					style: 2,
					labelBackgroundColor: CHART_COLORS.accentBlue,
				},
				horzLine: {
					color: CHART_COLORS.accentBlue,
					width: 1,
					style: 2,
					labelBackgroundColor: CHART_COLORS.accentBlue,
				},
			},
			rightPriceScale: {
				borderColor: CHART_COLORS.obsidianBorder,
				scaleMargins: { top: 0.2, bottom: 0.2 },
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

		const positionSeries = chart.addLineSeries({
			color: CHART_COLORS.accentBlue,
			lineWidth: 2,
			priceFormat: { type: "price", precision: 1, minMove: 0.1 },
			priceScaleId: "position",
		});

		chart.priceScale("position").applyOptions({
			scaleMargins: { top: 0.2, bottom: 0.2 },
		});

		chartRef.current = chart;
		positionSeriesRef.current = positionSeries;

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
			positionSeriesRef.current = null;
		};
	}, [height, onCrosshairMove]);

	// Update data with trade markers
	useEffect(() => {
		if (!positionSeriesRef.current || !analyticsData.length) return;

		const positionData = analyticsData
			.filter((d) => d.date)
			.map((d) => {
				const time = Math.floor(new Date(d.date).getTime() / 1000) as Time;
				const position = d.mttd_position ?? 0;
				return { time, value: position };
			})
			.sort((a, b) => (a.time as number) - (b.time as number));

		positionSeriesRef.current.setData(positionData);

		// Add trade markers (entry/exit transitions)
		const markers: Array<{
			time: Time;
			position: "aboveBar" | "belowBar";
			color: string;
			shape: "arrowUp" | "arrowDown";
			text: string;
		}> = [];

		for (let i = 1; i < positionData.length; i++) {
			const prev = positionData[i - 1].value;
			const curr = positionData[i].value;

			// Entry: FLAT -> LONG
			if (prev <= 0.5 && curr > 0.5) {
				markers.push({
					time: positionData[i].time,
					position: "belowBar",
					color: CHART_COLORS.bullEmerald,
					shape: "arrowUp",
					text: "ENTRY",
				});
			}
			// Exit: LONG -> FLAT
			else if (prev > 0.5 && curr <= 0.5) {
				markers.push({
					time: positionData[i].time,
					position: "aboveBar",
					color: CHART_COLORS.bearCrimson,
					shape: "arrowDown",
					text: "EXIT",
				});
			}
		}

		if (markers.length > 0) {
			positionSeriesRef.current.setMarkers(markers);
		}
	}, [analyticsData]);

	// External crosshair sync
	useEffect(() => {
		if (
			!chartRef.current ||
			crosshairTime === null ||
			!positionSeriesRef.current
		)
			return;

		const seriesData = positionSeriesRef.current.data();
		const lastBar = seriesData[seriesData.length - 1];
		if (lastBar && "close" in lastBar) {
			chartRef.current.setCrosshairPosition(
				lastBar.close as number,
				crosshairTime as Time,
				positionSeriesRef.current,
			);
		}
	}, [crosshairTime]);

	return (
		<div className="trade-markers-chart">
			<span className="chart-label text-dim text-xs">MTTD POSITION</span>
			<div
				ref={chartContainerRef}
				style={{ width: "100%", height: `${height}px` }}
			/>
		</div>
	);
}
