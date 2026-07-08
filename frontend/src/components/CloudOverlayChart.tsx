/**
 * Maftia Quant — Cloud Overlay Chart
 *
 * BTC price chart with tanh-normalized Ichimoku cloud overlay.
 * Synchronized with main price chart crosshair.
 *
 * Implements task 13.4: Add Ichimoku cloud overlay
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
import type { OHLCVBar, UnifiedAnalytics } from "../api/client";
import { CHART_COLORS } from "../styles/chart-colors";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface CloudOverlayChartProps {
	priceData: OHLCVBar[];
	analyticsData: UnifiedAnalytics[];
	crosshairTime: number | null;
	onCrosshairMove?: (time: number | null) => void;
	height?: number;
}

// ═══════════════════════════════════════════════════════════
// CloudOverlayChart Component
// ═══════════════════════════════════════════════════════════

export function CloudOverlayChart({
	priceData,
	analyticsData,
	crosshairTime,
	onCrosshairMove,
	height = 350,
}: CloudOverlayChartProps) {
	const chartContainerRef = useRef<HTMLDivElement>(null);
	const chartRef = useRef<IChartApi | null>(null);
	const candlestickRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
	const cloudTopRef = useRef<ISeriesApi<"Area"> | null>(null);
	const cloudBottomRef = useRef<ISeriesApi<"Area"> | null>(null);

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

		// Cloud area series (filled between top and bottom)
		const cloudTopSeries = chart.addAreaSeries({
			lineColor: "rgba(59, 130, 246, 0.5)",
			lineWidth: 1,
			topColor: "rgba(59, 130, 246, 0.15)",
			bottomColor: "rgba(59, 130, 246, 0.05)",
			priceScaleId: "price",
		});

		const cloudBottomSeries = chart.addAreaSeries({
			lineColor: "rgba(59, 130, 246, 0.3)",
			lineWidth: 1,
			topColor: "rgba(59, 130, 246, 0.05)",
			bottomColor: "rgba(59, 130, 246, 0.15)",
			priceScaleId: "price",
		});

		// Candlestick series on top
		const candlestickSeries = chart.addCandlestickSeries({
			upColor: CHART_COLORS.bullEmerald,
			downColor: CHART_COLORS.bearCrimson,
			borderUpColor: CHART_COLORS.bullEmerald,
			borderDownColor: CHART_COLORS.bearCrimson,
			wickUpColor: CHART_COLORS.bullEmerald,
			wickDownColor: CHART_COLORS.bearCrimson,
			priceScaleId: "price",
		});

		chartRef.current = chart;
		candlestickRef.current = candlestickSeries;
		cloudTopRef.current = cloudTopSeries;
		cloudBottomRef.current = cloudBottomSeries;

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
			candlestickRef.current = null;
			cloudTopRef.current = null;
			cloudBottomRef.current = null;
		};
	}, [height, onCrosshairMove]);

	// Update price data
	useEffect(() => {
		if (!candlestickRef.current || !priceData.length) return;

		const chartData = priceData
			.map((bar) => ({
				time: Math.floor(new Date(bar.date).getTime() / 1000) as Time,
				open: bar.open,
				high: bar.high,
				low: bar.low,
				close: bar.close,
			}))
			.sort((a, b) => (a.time as number) - (b.time as number));

		candlestickRef.current.setData(chartData);
	}, [priceData]);

	// Update cloud data (synthetic from Ichimoku components)
	useEffect(() => {
		if (
			!cloudTopRef.current ||
			!cloudBottomRef.current ||
			!analyticsData.length
		)
			return;

		// Generate synthetic cloud from Ichimoku component scores
		// S_Cloud represents the normalized cloud position
		const cloudData = analyticsData
			.filter((d) => d.date)
			.map((d) => {
				const time = Math.floor(new Date(d.date).getTime() / 1000) as Time;
				// Use ichi_s_cloud as basis for cloud width
				const cloudScore = d.ichi_s_cloud ?? 0;
				// Find matching price data for base price
				const matchingPrice = priceData.find(
					(p) =>
						Math.floor(new Date(p.date).getTime() / 1000) === (time as number),
				);
				const basePrice = matchingPrice?.close ?? 0;
				// Cloud width proportional to cloud score (tanh-normalized)
				const cloudWidth = basePrice * 0.05 * Math.abs(cloudScore);
				return {
					time,
					top: basePrice + cloudWidth,
					bottom: basePrice - cloudWidth,
				};
			})
			.sort((a, b) => (a.time as number) - (b.time as number));

		const topData = cloudData.map((d) => ({ time: d.time, value: d.top }));
		const bottomData = cloudData.map((d) => ({
			time: d.time,
			value: d.bottom,
		}));

		cloudTopRef.current.setData(topData);
		cloudBottomRef.current.setData(bottomData);
	}, [analyticsData, priceData]);

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
		<div className="cloud-overlay-chart">
			<span className="chart-label text-dim text-xs">ICHIMOKU CLOUD</span>
			<div
				ref={chartContainerRef}
				style={{ width: "100%", height: `${height}px` }}
			/>
		</div>
	);
}
