/**
 * Maftia Quant — Chart Color Constants
 *
 * Lightweight Charts doesn't support CSS variables.
 * These are the resolved color values from tokens.css.
 */

export const CHART_COLORS = {
	// Backgrounds
	transparent: "transparent",
	obsidianBorder: "rgba(255, 255, 255, 0.08)",

	// Text
	textSecondary: "rgba(255, 255, 255, 0.5)",

	// Semantic
	bullEmerald: "#22c55e",
	bearCrimson: "#ef4444",
	neutralAmber: "#eab308",
	accentBlue: "#3b82f6",
	textDim: "rgba(255, 255, 255, 0.3)",

	// Font
	fontMono: "'JetBrains Mono', monospace",
} as const;
