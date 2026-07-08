/**
 * Maftia Quant — WebSocket Integration Tests
 *
 * Tests for the WebSocket server at ws://localhost:3000/ws/v1/stream
 *
 * Usage:
 *   bun test src/websocket.test.ts
 */

import { describe, it, expect, beforeAll, afterAll } from "bun:test";

// ═══════════════════════════════════════════════════════════
// Test Configuration
// ═══════════════════════════════════════════════════════════

const WS_URL = "ws://localhost:3000/ws/v1/stream";
const API_URL = "http://localhost:3000";
const TIMEOUT_MS = 5000;

// ═══════════════════════════════════════════════════════════
// Helper Functions
// ═══════════════════════════════════════════════════════════

/**
 * Wait for a WebSocket message with timeout
 */
function waitForMessage(
	ws: WebSocket,
	timeout: number = TIMEOUT_MS,
): Promise<unknown> {
	return new Promise((resolve, reject) => {
		const timer = setTimeout(() => {
			reject(new Error("WebSocket message timeout"));
		}, timeout);

		ws.onmessage = (event) => {
			clearTimeout(timer);
			resolve(JSON.parse(String(event.data)));
		};

		ws.onerror = (event) => {
			clearTimeout(timer);
			reject(event);
		};
	});
}

/**
 * Check if server is running
 */
async function isServerRunning(): Promise<boolean> {
	try {
		const response = await fetch(`${API_URL}/api/v1/ping`);
		return response.ok;
	} catch {
		return false;
	}
}

// ═══════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════

describe("WebSocket Server", () => {
	let serverRunning = false;

	beforeAll(async () => {
		serverRunning = await isServerRunning();
	});

	describe("Connection", () => {
		it("should connect to WebSocket endpoint", async () => {
			if (!serverRunning) {
				console.log("⏭️  Skipping: Server not running");
				return;
			}

			const ws = new WebSocket(WS_URL);

			await new Promise<void>((resolve, reject) => {
				ws.onopen = () => resolve();
				ws.onerror = () => reject(new Error("Connection failed"));
				setTimeout(() => reject(new Error("Connection timeout")), TIMEOUT_MS);
			});

			expect(ws.readyState).toBe(WebSocket.OPEN);
			ws.close();
		});

		it("should receive init message on connect", async () => {
			if (!serverRunning) {
				console.log("⏭️  Skipping: Server not running");
				return;
			}

			const ws = new WebSocket(WS_URL);
			const message = (await waitForMessage(ws)) as Record<string, unknown>;

			expect(message).toHaveProperty("type", "init");
			expect(message).toHaveProperty("data");
			expect(message).toHaveProperty("timestamp");

			ws.close();
		});
	});

	describe("Message Handling", () => {
		it("should respond to ping with pong", async () => {
			if (!serverRunning) {
				console.log("⏭️  Skipping: Server not running");
				return;
			}

			const ws = new WebSocket(WS_URL);

			// Wait for init message
			await waitForMessage(ws);

			// Send ping
			ws.send(JSON.stringify({ type: "ping" }));

			// Wait for pong
			const response = (await waitForMessage(ws)) as Record<string, unknown>;

			expect(response).toHaveProperty("type", "pong");
			expect(response).toHaveProperty("timestamp");

			ws.close();
		});

		it("should acknowledge subscribe message", async () => {
			if (!serverRunning) {
				console.log("⏭️  Skipping: Server not running");
				return;
			}

			const ws = new WebSocket(WS_URL);

			// Wait for init message
			await waitForMessage(ws);

			// Send subscribe
			ws.send(JSON.stringify({ type: "subscribe", channel: "analytics" }));

			// Wait for subscribed response
			const response = (await waitForMessage(ws)) as Record<string, unknown>;

			expect(response).toHaveProperty("type", "subscribed");
			expect(response).toHaveProperty("channel", "analytics");

			ws.close();
		});
	});

	describe("Connection Management", () => {
		it("should handle multiple concurrent connections", async () => {
			if (!serverRunning) {
				console.log("⏭️  Skipping: Server not running");
				return;
			}

			const connections = await Promise.all(
				Array.from({ length: 3 }, () => {
					const ws = new WebSocket(WS_URL);
					return new Promise<WebSocket>((resolve, reject) => {
						ws.onopen = () => resolve(ws);
						ws.onerror = () => reject(new Error("Connection failed"));
						setTimeout(() => reject(new Error("Timeout")), TIMEOUT_MS);
					});
				}),
			);

			// All connections should be open
			for (const ws of connections) {
				expect(ws.readyState).toBe(WebSocket.OPEN);
			}

			// Close all connections
			for (const ws of connections) {
				ws.close();
			}
		});

		it("should handle clean disconnection", async () => {
			if (!serverRunning) {
				console.log("⏭️  Skipping: Server not running");
				return;
			}

			const ws = new WebSocket(WS_URL);

			await new Promise<void>((resolve) => {
				ws.onopen = () => resolve();
			});

			// Close cleanly
			ws.close(1000, "Test complete");

			// Wait for close event
			await new Promise<void>((resolve) => {
				ws.onclose = () => resolve();
			});

			expect(ws.readyState).toBeWebSocket(CLOSED);
		});
	});

	describe("Data Format", () => {
		it("should return valid JSON with required fields", async () => {
			if (!serverRunning) {
				console.log("⏭️  Skipping: Server not running");
				return;
			}

			const ws = new WebSocket(WS_URL);
			const message = (await waitForMessage(ws)) as Record<string, unknown>;

			// Verify structure
			expect(typeof message.type).toBe("string");
			expect(typeof message.timestamp).toBe("string");

			// Verify timestamp is ISO format
			const timestamp = new Date(message.timestamp as string);
			expect(timestamp.toString()).not.toBe("Invalid Date");

			ws.close();
		});

		it("should include analytics data in init message", async () => {
			if (!serverRunning) {
				console.log("⏭️  Skipping: Server not running");
				return;
			}

			const ws = new WebSocket(WS_URL);
			const message = (await waitForMessage(ws)) as Record<string, unknown>;

			expect(message.type).toBe("init");

			// Data may be null if no analytics computed yet
			if (message.data !== null) {
				const data = message.data as Record<string, unknown>;
				expect(data).toHaveProperty("date");
			}

			ws.close();
		});
	});
});
