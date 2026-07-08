/**
 * Maftia Quant — Interactive Summary Table Component
 *
 * Displays all system scores and positions in a sortable table.
 */

import { useState, useMemo } from "react";
import type { UnifiedAnalytics } from "../api/client";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface SummaryTableProps {
	data: UnifiedAnalytics;
}

type SortField = "system" | "score" | "position" | "regime" | "circuit_breaker";
type SortDirection = "asc" | "desc";

interface SystemRow {
	system: string;
	score: number;
	position: number;
	regime: string;
	circuit_breaker: number;
	impliedExposure: number;
}

// ═══════════════════════════════════════════════════════════
// SummaryTable Component
// ═══════════════════════════════════════════════════════════

export function SummaryTable({ data }: SummaryTableProps) {
	const [sortField, setSortField] = useState<SortField>("system");
	const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

	// Convert data to table rows
	const rows: SystemRow[] = useMemo(
		() => [
			{
				system: "Valuation",
				score: data.mvo_score ?? 0,
				position: (data.mvo_score ?? 0) >= 1.5 ? 0 : 1, // Circuit breaker check
				regime: (data.mvo_score ?? 0) >= 1.5 ? "CIRCUIT_BREAKER" : "N/A",
				circuit_breaker: (data.mvo_score ?? 0) >= 1.5 ? 1 : 0,
				impliedExposure: (data.mvo_score ?? 0) >= 1.5 ? 0 : 1,
			},
			{
				system: "LTTD",
				score: data.lttd_score ?? 0,
				position: data.lttd_exposure ?? 0,
				regime: data.lttd_regime ?? "N/A",
				circuit_breaker: data.lttd_circuit_breaker ?? 0,
				impliedExposure: data.lttd_exposure ?? 0,
			},
			{
				system: "MTTD",
				score: data.mttd_imo ?? 0,
				position: data.mttd_position ?? 0,
				regime: "N/A",
				circuit_breaker: 0,
				impliedExposure: data.mttd_position ?? 0,
			},
			{
				system: "Ichimoku",
				score: data.ichi_imo ?? 0,
				position: data.ichi_position ?? 0,
				regime: "N/A",
				circuit_breaker: 0,
				impliedExposure: data.ichi_position ?? 0,
			},
		],
		[data],
	);

	// Sort rows
	const sortedRows = useMemo(() => {
		return [...rows].sort((a, b) => {
			let comparison = 0;

			switch (sortField) {
				case "system":
					comparison = a.system.localeCompare(b.system);
					break;
				case "score":
					comparison = a.score - b.score;
					break;
				case "position":
					comparison = a.position - b.position;
					break;
				case "regime":
					comparison = a.regime.localeCompare(b.regime);
					break;
				case "circuit_breaker":
					comparison = a.circuit_breaker - b.circuit_breaker;
					break;
				default:
					comparison = 0;
			}

			return sortDirection === "asc" ? comparison : -comparison;
		});
	}, [rows, sortField, sortDirection]);

	const handleSort = (field: SortField) => {
		if (sortField === field) {
			setSortDirection(sortDirection === "asc" ? "desc" : "asc");
		} else {
			setSortField(field);
			setSortDirection("asc");
		}
	};

	const getSortIndicator = (field: SortField) => {
		if (sortField !== field) return "";
		return sortDirection === "asc" ? " ↑" : " ↓";
	};

	return (
		<div className="summary-table">
			<table>
				<thead>
					<tr>
						<th onClick={() => handleSort("system")} className="sortable">
							System{getSortIndicator("system")}
						</th>
						<th onClick={() => handleSort("score")} className="sortable">
							Score{getSortIndicator("score")}
						</th>
						<th onClick={() => handleSort("position")} className="sortable">
							Position{getSortIndicator("position")}
						</th>
						<th onClick={() => handleSort("regime")} className="sortable">
							Regime{getSortIndicator("regime")}
						</th>
						<th
							onClick={() => handleSort("circuit_breaker")}
							className="sortable"
						>
							CB{getSortIndicator("circuit_breaker")}
						</th>
					</tr>
				</thead>
				<tbody>
					{sortedRows.map((row) => (
						<tr key={row.system}>
							<td className="font-mono">{row.system}</td>
							<td
								className={`font-mono ${
									row.score >= 0 ? "text-bull" : "text-bear"
								}`}
							>
								{row.score.toFixed(3)}
							</td>
							<td
								className={`font-mono ${
									row.position > 0.5 ? "text-bull" : "text-dim"
								}`}
							>
								{row.position > 0.5 ? "1.0" : "0.0"}
							</td>
							<td
								className={`font-mono ${
									row.regime === "BULL"
										? "text-bull"
										: row.regime === "BEAR"
											? "text-bear"
											: "text-neutral"
								}`}
							>
								{row.regime}
							</td>
							<td
								className={`font-mono ${
									row.circuit_breaker ? "text-bear" : "text-dim"
								}`}
							>
								{row.circuit_breaker ? "ON" : "OFF"}
							</td>
						</tr>
					))}
				</tbody>
			</table>
		</div>
	);
}
