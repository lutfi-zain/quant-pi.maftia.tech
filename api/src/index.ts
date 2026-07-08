/**
 * Maftia Quant — Unified API Gateway
 *
 * Hono v4 on Bun runtime serving all system endpoints.
 *
 * Usage:
 *   bun run dev     # Development with hot reload
 *   bun run start   # Production
 */

import { Hono } from "hono";
import { cors } from "hono/cors";
import { logger } from "hono/logger";
import { createNodeWebSocket } from "@hono/node-ws";
import { serve } from "@hono/node-server";
import Database from "better-sqlite3";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface OHLCVBar {
	date: string;
	open: number;
	high: number;
	low: number;
	close: number;
	volume: number;
	source: string;
}

interface OnchainMetrics {
	date: string;
	sth_mvrv: number | null;
	sth_nupl: number | null;
	sth_sopr_24h: number | null;
	sth_supply_in_profit: number | null;
}

interface UnifiedAnalytics {
	date: string;
	btc_price: number | null;
	valuation_composite: number | null;
	lttd_regime: string | null;
	lttd_score: number | null;
	lttd_prob_bull: number | null;
	lttd_prob_bear: number | null;
	lttd_prob_sideways: number | null;
	mttd_imo: number | null;
	mttd_er: number | null;
	mttd_entropy: number | null;
	mttd_position: number | null;
	mttd_immunity_active: number | null;
	ichimoku_imo: number | null;
	ichimoku_regime: string | null;
	ichimoku_position: number | null;
}

// ═══════════════════════════════════════════════════════════
// Database Connection
// ═══════════════════════════════════════════════════════════

const DB_PATH = "../data/maftia_quant.db";

function getDb(): Database.Database {
	const db = new Database(DB_PATH, { readonly: true });
	db.pragma("journal_mode = WAL");
	return db;
}

// ═══════════════════════════════════════════════════════════
// App Setup with WebSocket
// ═══════════════════════════════════════════════════════════

const app = new Hono();
const { injectWebSocket, upgradeWebSocket } = createNodeWebSocket({ app });

// Middleware
app.use("*", logger());
app.use(
	"*",
	cors({
		origin: ["http://localhost:5173", "http://0.0.0.0:5173"],
		allowMethods: ["GET"],
	}),
);

// ═══════════════════════════════════════════════════════════
// Health Check
// ═══════════════════════════════════════════════════════════

app.get("/api/v1/ping", (c) => {
	return c.json({
		status: "ok",
		timestamp: new Date().toISOString(),
		version: "1.0.0",
	});
});

// ═══════════════════════════════════════════════════════════
// Market Endpoints
// ═══════════════════════════════════════════════════════════

app.get("/api/v1/market/ohlc", (c) => {
	const { from, to, limit } = c.req.query();

	const db = getDb();
	try {
		let query = "SELECT * FROM master_ohlcv";
		const params: string[] = [];

		if (from && to) {
			query += " WHERE date BETWEEN ? AND ?";
			params.push(from, to);
		} else if (from) {
			query += " WHERE date >= ?";
			params.push(from);
		} else if (to) {
			query += " WHERE date <= ?";
			params.push(to);
		}

		query += " ORDER BY date DESC";

		if (limit) {
			query += ` LIMIT ${parseInt(limit)}`;
		}

		const rows = db.prepare(query).all(...params) as OHLCVBar[];
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

app.get("/api/v1/market/onchain", (c) => {
	const { from, to } = c.req.query();

	const db = getDb();
	try {
		let query = "SELECT * FROM onchain_metrics";
		const params: string[] = [];

		if (from && to) {
			query += " WHERE date BETWEEN ? AND ?";
			params.push(from, to);
		}

		query += " ORDER BY date DESC";

		const rows = db.prepare(query).all(...params) as OnchainMetrics[];
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

// ═══════════════════════════════════════════════════════════
// Valuation Endpoints
// ═══════════════════════════════════════════════════════════

app.get("/api/v1/valuation/composite", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, valuation_composite as mvo_score FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all() as { date: string; mvo_score: number | null }[];
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

app.get("/api/v1/valuation/pillars", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, valuation_composite FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

// ═══════════════════════════════════════════════════════════
// LTTD Endpoints
// ═══════════════════════════════════════════════════════════

app.get("/api/v1/lttd/regime", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, lttd_regime, lttd_prob_bull, lttd_prob_bear, lttd_prob_sideways FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

app.get("/api/v1/lttd/score", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, lttd_score FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

app.get("/api/v1/lttd/exposure", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, lttd_score, lttd_regime FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

// ═══════════════════════════════════════════════════════════
// MTTD Endpoints
// ═══════════════════════════════════════════════════════════

app.get("/api/v1/mttd/imo", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, mttd_imo, mttd_position FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

app.get("/api/v1/mttd/position", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, mttd_position, mttd_immunity_active FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

app.get("/api/v1/mttd/gates", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, mttd_er, mttd_entropy, mttd_imo FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

// ═══════════════════════════════════════════════════════════
// Ichimoku Endpoints
// ═══════════════════════════════════════════════════════════

app.get("/api/v1/ichimoku/imo", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, ichimoku_imo as ichi_imo, ichimoku_position as ichi_position FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

app.get("/api/v1/ichimoku/position", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, ichimoku_position as ichi_position, ichimoku_regime FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

app.get("/api/v1/ichimoku/components", (c) => {
	const db = getDb();
	try {
		const rows = db
			.prepare(
				"SELECT date, ichimoku_imo, ichimoku_regime, ichimoku_position FROM unified_daily_analytics ORDER BY date DESC",
			)
			.all();
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

// ═══════════════════════════════════════════════════════════
// Consensus Endpoint
// ═══════════════════════════════════════════════════════════

app.get("/api/v1/consensus", (c) => {
	const db = getDb();
	try {
		const latest = db
			.prepare(
				"SELECT * FROM unified_daily_analytics ORDER BY date DESC LIMIT 1",
			)
			.get() as UnifiedAnalytics | null;

		if (!latest) {
			return c.json({ data: null, message: "No data available" });
		}

		return c.json({ data: latest });
	} finally {
		db.close();
	}
});

// ═══════════════════════════════════════════════════════════
// Analytics Daily Endpoint
// ═══════════════════════════════════════════════════════════

app.get("/api/v1/analytics/daily", (c) => {
	const { from, to } = c.req.query();

	const db = getDb();
	try {
		let query = "SELECT * FROM unified_daily_analytics";
		const params: string[] = [];

		if (from && to) {
			query += " WHERE date BETWEEN ? AND ?";
			params.push(from, to);
		}

		query += " ORDER BY date ASC";

		const rows = db.prepare(query).all(...params);
		return c.json({ data: rows });
	} finally {
		db.close();
	}
});

// ═══════════════════════════════════════════════════════════
// WebSocket Server
// ═══════════════════════════════════════════════════════════

// Track connected clients
const wsClients = new Set<{
	send: (data: string) => void;
	readyState: number;
}>();

// Broadcast to all connected clients
function broadcast(data: Record<string, unknown>): void {
	const message = JSON.stringify(data);
	for (const client of wsClients) {
		if (client.readyState === 1) {
			client.send(message);
		}
	}
}

// WebSocket endpoint for real-time analytics streaming
app.get(
	"/ws/v1/stream",
	upgradeWebSocket((c) => ({
		onOpen(_event, ws) {
			wsClients.add(
				ws as unknown as { send: (data: string) => void; readyState: number },
			);
			console.log(`🔌 WebSocket client connected (total: ${wsClients.size})`);

			// Send initial state on connect
			const db = getDb();
			try {
				const latest = db
					.prepare(
						"SELECT * FROM unified_daily_analytics ORDER BY date DESC LIMIT 1",
					)
					.get();

				ws.send(
					JSON.stringify({
						type: "init",
						data: latest,
						timestamp: new Date().toISOString(),
					}),
				);
			} finally {
				db.close();
			}
		},

		onMessage(event, ws) {
			try {
				const message = JSON.parse(String(event.data));

				if (message.type === "ping") {
					ws.send(
						JSON.stringify({
							type: "pong",
							timestamp: new Date().toISOString(),
						}),
					);
				} else if (message.type === "subscribe") {
					// Client can subscribe to specific channels
					ws.send(
						JSON.stringify({
							type: "subscribed",
							channel: message.channel,
							timestamp: new Date().toISOString(),
						}),
					);
				}
			} catch (e) {
				console.error("WebSocket message error:", e);
			}
		},

		onClose(_event, _ws) {
			wsClients.delete(
				_ws as unknown as { send: (data: string) => void; readyState: number },
			);
			console.log(
				`🔌 WebSocket client disconnected (total: ${wsClients.size})`,
			);
		},

		onError(event, ws) {
			console.error("WebSocket error:", event);
			wsClients.delete(
				ws as unknown as { send: (data: string) => void; readyState: number },
			);
		},
	})),
);

// ═══════════════════════════════════════════════════════════
// Start Server
// ═══════════════════════════════════════════════════════════

const port = 3000;
const server = serve({
	fetch: app.fetch,
	port,
	hostname: "0.0.0.0",
});

// Inject WebSocket upgrade handler
injectWebSocket(server);

console.log(`🚀 Maftia Quant API running on http://0.0.0.0:${port}`);
console.log(`📡 WebSocket available at ws://0.0.0.0:${port}/ws/v1/stream`);
