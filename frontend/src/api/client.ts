/**
 * Maftia Quant — API Client
 *
 * TypeScript client for the Maftia Quant API.
 */

// ═══════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════

const API_BASE_PATH = "/api/v1";

// Allowlisted API endpoints
const ALLOWED_ENDPOINTS = [
	"/market/ohlc",
	"/market/onchain",
	"/valuation/composite",
	"/valuation/pillars",
	"/lttd/regime",
	"/lttd/score",
	"/lttd/exposure",
	"/mttd/imo",
	"/mttd/position",
	"/mttd/gates",
	"/ichimoku/imo",
	"/ichimoku/position",
	"/ichimoku/components",
	"/consensus",
	"/analytics/daily",
	"/ping",
] as const;

type AllowedEndpoint = (typeof ALLOWED_ENDPOINTS)[number];

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

export interface OHLCVBar {
	date: string;
	open: number;
	high: number;
	low: number;
	close: number;
	volume: number;
	source: string;
}

export interface OnchainMetrics {
	date: string;
	sth_mvrv: number | null;
	sth_nupl: number | null;
	sth_sopr_24h: number | null;
	sth_supply_in_profit: number | null;
}

export interface UnifiedAnalytics {
	date: string;
	mvo_score: number | null;
	lttd_score: number | null;
	lttd_regime: string | null;
	lttd_p_bull: number | null;
	lttd_p_bear: number | null;
	lttd_p_sideways: number | null;
	lttd_exposure: number | null;
	lttd_circuit_breaker: number | null;
	mttd_imo: number | null;
	mttd_position: number | null;
	mttd_er: number | null;
	mttd_entropy: number | null;
	ichi_imo: number | null;
	ichi_position: number | null;
	ichi_s_tk: number | null;
	ichi_s_cloud: number | null;
	ichi_s_future: number | null;
	ichi_s_chikou: number | null;
	consensus_score: number | null;
	consensus_exposure: number | null;
}

export interface ApiResponse<T> {
	data: T;
	message?: string;
}

// ═══════════════════════════════════════════════════════════
// API Client
// ═══════════════════════════════════════════════════════════

function validateEndpoint(endpoint: string): endpoint is AllowedEndpoint {
	return ALLOWED_ENDPOINTS.includes(endpoint as AllowedEndpoint);
}

function buildUrl(endpoint: string, params?: Record<string, string>): string {
	if (!validateEndpoint(endpoint)) {
		throw new Error(`Invalid endpoint: ${endpoint}`);
	}

	const url = new URL(`${API_BASE_PATH}${endpoint}`, window.location.origin);

	if (params) {
		Object.entries(params).forEach(([key, value]) => {
			if (value) {
				url.searchParams.append(key, value);
			}
		});
	}

	return url.toString();
}

async function fetchApi<T>(
	endpoint: string,
	params?: Record<string, string>,
): Promise<T> {
	const url = buildUrl(endpoint, params);

	const response = await fetch(url);

	if (!response.ok) {
		throw new Error(`API error: ${response.status} ${response.statusText}`);
	}

	return response.json();
}

// ═══════════════════════════════════════════════════════════
// Market API
// ═══════════════════════════════════════════════════════════

export async function fetchOHLCV(params?: {
	from?: string;
	to?: string;
	limit?: number;
}): Promise<OHLCVBar[]> {
	const response = await fetchApi<ApiResponse<OHLCVBar[]>>(
		"/market/ohlc",
		params as Record<string, string>,
	);
	return response.data;
}

export async function fetchOnchainMetrics(params?: {
	from?: string;
	to?: string;
}): Promise<OnchainMetrics[]> {
	const response = await fetchApi<ApiResponse<OnchainMetrics[]>>(
		"/market/onchain",
		params as Record<string, string>,
	);
	return response.data;
}

// ═══════════════════════════════════════════════════════════
// Valuation API
// ═══════════════════════════════════════════════════════════

export async function fetchValuationComposite(): Promise<
	{ date: string; mvo_score: number | null }[]
> {
	const response = await fetchApi<
		ApiResponse<{ date: string; mvo_score: number | null }[]>
	>("/valuation/composite");
	return response.data;
}

// ═══════════════════════════════════════════════════════════
// LTTD API
// ═══════════════════════════════════════════════════════════

export async function fetchLTTDRegime(): Promise<
	{
		date: string;
		lttd_regime: string | null;
		lttd_p_bull: number | null;
		lttd_p_bear: number | null;
		lttd_p_sideways: number | null;
	}[]
> {
	const response =
		await fetchApi<
			ApiResponse<
				{
					date: string;
					lttd_regime: string | null;
					lttd_p_bull: number | null;
					lttd_p_bear: number | null;
					lttd_p_sideways: number | null;
				}[]
			>
		>("/lttd/regime");
	return response.data;
}

// ═══════════════════════════════════════════════════════════
// MTTD API
// ═══════════════════════════════════════════════════════════

export async function fetchMTTDIMO(): Promise<
	{ date: string; mttd_imo: number | null }[]
> {
	const response =
		await fetchApi<ApiResponse<{ date: string; mttd_imo: number | null }[]>>(
			"/mttd/imo",
		);
	return response.data;
}

// ═══════════════════════════════════════════════════════════
// Ichimoku API
// ═══════════════════════════════════════════════════════════

export async function fetchIchimokuIMO(): Promise<
	{ date: string; ichi_imo: number | null }[]
> {
	const response =
		await fetchApi<ApiResponse<{ date: string; ichi_imo: number | null }[]>>(
			"/ichimoku/imo",
		);
	return response.data;
}

// ═══════════════════════════════════════════════════════════
// Consensus API
// ═══════════════════════════════════════════════════════════

export async function fetchConsensus(): Promise<UnifiedAnalytics | null> {
	const response =
		await fetchApi<ApiResponse<UnifiedAnalytics | null>>("/consensus");
	return response.data;
}

// ═══════════════════════════════════════════════════════════
// Analytics API
// ═══════════════════════════════════════════════════════════

export async function fetchDailyAnalytics(params?: {
	from?: string;
	to?: string;
}): Promise<UnifiedAnalytics[]> {
	const response = await fetchApi<ApiResponse<UnifiedAnalytics[]>>(
		"/analytics/daily",
		params as Record<string, string>,
	);
	return response.data;
}

// ═══════════════════════════════════════════════════════════
// Health Check
// ═══════════════════════════════════════════════════════════

export async function ping(): Promise<{
	status: string;
	timestamp: string;
	version: string;
}> {
	return fetchApi<{ status: string; timestamp: string; version: string }>(
		"/ping",
	);
}
