/**
 * Maftia Quant — Executive Dashboard
 *
 * Main application entry point.
 */

import { useState, useEffect } from "react";
import { Dashboard } from "./components/Dashboard";
import { fetchConsensus, ping } from "./api/client";
import type { UnifiedAnalytics } from "./api/client";
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
}

// ═══════════════════════════════════════════════════════════
// App Component
// ═══════════════════════════════════════════════════════════

export default function App() {
	const [state, setState] = useState<AppState>({
		connected: false,
		loading: true,
		error: null,
		data: null,
	});

	// Check API connection on mount
	useEffect(() => {
		async function checkConnection() {
			try {
				await ping();
				setState((prev) => ({ ...prev, connected: true }));

				// Fetch initial data
				const data = await fetchConsensus();
				setState((prev) => ({
					...prev,
					loading: false,
					data,
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
				const data = await fetchConsensus();
				setState((prev) => ({ ...prev, data, connected: true }));
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

			<main className="app-main">
				<Dashboard data={state.data} />
			</main>

			<footer className="app-footer">
				<span className="footer-text">
					Maftia Quant v1.0.0 • Interlocking Safeguards Active
				</span>
			</footer>
		</div>
	);
}
