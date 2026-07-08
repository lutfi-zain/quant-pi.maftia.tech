/**
 * Maftia Quant — Executive Dashboard
 *
 * Main application entry point with routing.
 */

import { useState, useEffect, useCallback } from "react";
import { Dashboard } from "./components/Dashboard";
import { ValuationStudio } from "./components/sandboxes/ValuationStudio";
import { LTTDLab } from "./components/sandboxes/LTTDLab";
import { MTTDConsole } from "./components/sandboxes/MTTDConsole";
import { IchimokuTerminal } from "./components/sandboxes/IchimokuTerminal";
import {
	fetchConsensus,
	fetchOHLCV,
	fetchDailyAnalytics,
	ping,
} from "./api/client";
import type { OHLCVBar, UnifiedAnalytics } from "./api/client";
import "./styles/tokens.css";
import "./styles/components.css";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface AppState {
	connected: boolean;
	loading: boolean;
	error: string | null;
	data: UnifiedAnalytics | null;
	priceData: OHLCVBar[];
	analyticsHistory: UnifiedAnalytics[];
}

type Page = "dashboard" | "valuation" | "lttd" | "mttd" | "ichimoku";

// ═══════════════════════════════════════════════════════════
// App Component
// ═══════════════════════════════════════════════════════════

export default function App() {
	const [state, setState] = useState<AppState>({
		connected: false,
		loading: true,
		error: null,
		data: null,
		priceData: [],
		analyticsHistory: [],
	});

	const [currentPage, setCurrentPage] = useState<Page>("dashboard");

	const handleNavigate = useCallback((page: string) => {
		setCurrentPage(page as Page);
		window.scrollTo(0, 0);
	}, []);

	// Check API connection on mount
	useEffect(() => {
		async function checkConnection() {
			try {
				await ping();
				setState((prev) => ({ ...prev, connected: true }));

				// Fetch initial data
				const [consensus, priceData, analyticsHistory] = await Promise.all([
					fetchConsensus(),
					fetchOHLCV({}),
					fetchDailyAnalytics({}),
				]);

				setState((prev) => ({
					...prev,
					loading: false,
					data: consensus,
					priceData,
					analyticsHistory,
				}));
			} catch (err) {
				setState((prev) => ({
					...prev,
					connected: false,
					loading: false,
					error: "Unable to connect to API server",
				}));
			}
		}

		checkConnection();

		// Poll for updates every 30 seconds
		const interval = setInterval(async () => {
			try {
				const consensus = await fetchConsensus();
				setState((prev) => ({ ...prev, data: consensus, connected: true }));
			} catch {
				setState((prev) => ({ ...prev, connected: false }));
			}
		}, 30000);

		return () => clearInterval(interval);
	}, []);

	// WebSocket connection for real-time updates
	useEffect(() => {
		if (!state.connected) return;

		const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
		const wsUrl = `${wsProtocol}//${window.location.host}/ws/v1/stream`;

		const ws = new WebSocket(wsUrl);

		ws.onmessage = (event) => {
			try {
				const message = JSON.parse(String(event.data));
				if (message.type === "init" || message.type === "update") {
					setState((prev) => ({
						...prev,
						data: message.data ?? prev.data,
					}));
				}
			} catch (e) {
				console.error("WebSocket message error:", e);
			}
		};

		ws.onerror = () => {
			console.warn("WebSocket connection error");
		};

		ws.onclose = () => {
			console.log("WebSocket disconnected");
		};

		return () => {
			ws.close();
		};
	}, [state.connected]);

	if (state.loading) {
		return (
			<div className="loading-screen">
				<div className="loading-spinner" />
				<p>Loading Maftia Quant...</p>
			</div>
		);
	}

	if (state.error) {
		return (
			<div className="error-screen">
				<h1>⚠️ Connection Error</h1>
				<p>{state.error}</p>
				<button
					type="button"
					onClick={() => window.location.reload()}
					className="retry-button"
				>
					Retry
				</button>
			</div>
		);
	}

	const renderPage = () => {
		switch (currentPage) {
			case "valuation":
				return (
					<ValuationStudio
						data={state.data}
						analyticsHistory={state.analyticsHistory}
						onBack={() => handleNavigate("dashboard")}
					/>
				);
			case "lttd":
				return (
					<LTTDLab
						data={state.data}
						analyticsHistory={state.analyticsHistory}
						onBack={() => handleNavigate("dashboard")}
					/>
				);
			case "mttd":
				return (
					<MTTDConsole
						data={state.data}
						analyticsHistory={state.analyticsHistory}
						onBack={() => handleNavigate("dashboard")}
					/>
				);
			case "ichimoku":
				return (
					<IchimokuTerminal
						data={state.data}
						analyticsHistory={state.analyticsHistory}
						onBack={() => handleNavigate("dashboard")}
					/>
				);
			default:
				return (
					<Dashboard
						data={state.data}
						priceData={state.priceData}
						analyticsHistory={state.analyticsHistory}
						onNavigate={handleNavigate}
					/>
				);
		}
	};

	return (
		<div className="app">
			<header className="app-header">
				<div className="app-title">
					<h1>Maftia Quant</h1>
					<span className="app-subtitle">Unified Bitcoin Intelligence</span>
				</div>
				<div className="connection-status">
					<span
						className={`status-dot ${state.connected ? "connected" : "disconnected"}`}
					/>
					<span className="status-text">
						{state.connected ? "Live" : "Offline"}
					</span>
				</div>
			</header>

			<main className="app-main">{renderPage()}</main>

			<footer className="app-footer">
				<span className="footer-text">
					Maftia Quant v1.0.0 • Interlocking Safeguards Active
				</span>
			</footer>
		</div>
	);
}
