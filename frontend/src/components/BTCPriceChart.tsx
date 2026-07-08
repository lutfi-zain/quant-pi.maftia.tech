/**
 * Maftia Quant — BTC Price Chart
 *
 * Candlestick chart using TradingView Lightweight Charts.
 * Base chart with crosshair sync support and Y-axis width lock.
 */

import { useEffect, useRef } from "react";
import {
	createChart,
	ColorType,
	CrosshairMode,
	type IChartApi,
	type ISeriesApi,
	type MouseEventParams,
	type Time,
} from "lightweight-charts";
import type { OHLCVBar } from "../api/client";
import { CHART_COLORS } from "../styles/chart-colors";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

export interface BTCPriceChartProps {
	data: OHLCVBar[];
	onCrosshairMove?: (time: number | null) => void;
	crosshairTime?: number | null;
	height?: number;
}

// ═══════════════════════════════════════════════════════════
// BTCPriceChart Component
// ═══════════════════════════════════════════════════════════

export function BTCPriceChart({
	data,
	onCrosshairMove,
	crosshairTime,
	height = 400,
}: BTCPriceChartProps) {
	const chartContainerRef = useRef<HTMLDivElement>(null);
	const chartRef = useRef<IChartApi | null>(null);
	const candlestickRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

	// Initialize chart
	useEffect(() => {
		if (!chartContainerRef.current) return;

		const chart = createChart(chartContainerRef.current, {
			layout: {
				background: { type: ColorType.Solid, color: "transparent" },
				textColor: CHART_COLORS.textSecondary,
				fontFamily: CHART_COLORS.fontMono,
				fontSize: 11,
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
				scaleMargins: {
					top: 0.1,
					bottom: 0.1,
				},
				autoScale: true,
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

		const candlestickSeries = chart.addCandlestickSeries({
			upColor: CHART_COLORS.bullEmerald,
			downColor: CHART_COLORS.bearCrimson,
			borderUpColor: CHART_COLORS.bullEmerald,
			borderDownColor: CHART_COLORS.bearCrimson,
			wickUpColor: CHART_COLORS.bullEmerald,
			wickDownColor: CHART_COLORS.bearCrimson,
		});

		chartRef.current = chart;
		candlestickRef.current = candlestickSeries;

		// Crosshair move handler for sync
		chart.subscribeCrosshairMove((param: MouseEventParams) => {
			if (onCrosshairMove) {
				const time = param.time as number | undefined;
				onCrosshairMove(time ?? null);
			}
		});

		// Resize observer
		const resizeObserver = new ResizeObserver((entries) => {
			for (const entry of entries) {
				const { width } = entry.contentRect;
				chart.applyOptions({ width });
			}
		});
		resizeObserver.observe(chartContainerRef.current);

		return () => {
			resizeObserver.disconnect();
			chart.remove();
			chartRef.current = null;
			candlestickRef.current = null;
		};
	}, [height, onCrosshairMove]);

	// Update data
	useEffect(() => {
		if (!candlestickRef.current || !data.length) return;

		const chartData = data
			.map((bar) => ({
				time: Math.floor(new Date(bar.date).getTime() / 1000) as Time,
				open: bar.open,
				high: bar.high,
				low: bar.low,
				close: bar.close,
			}))
			.sort((a, b) => (a.time as number) - (b.time as number));

		candlestickRef.current.setData(chartData);
	}, [data]);

	// External crosshair sync
	useEffect(() => {
		if (!chartRef.current || crosshairTime === null || !candlestickRef.current)
			return;

		const seriesData = candlestickRef.current.data();
		const lastBar = seriesData[seriesData.length - 1];
		if (lastBar && "close" in lastBar) {
			chartRef.current.setCrosshairPosition(
				lastBar.close as number,
				crosshairTime as Time,
				candlestickRef.current,
			);
		}
	}, [crosshairTime]);

	return (
		<div
			ref={chartContainerRef}
			className="btc-price-chart"
			style={{ width: "100%", height: `${height}px` }}
		/>
	);
}
