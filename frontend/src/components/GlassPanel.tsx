/**
 * Maftia Quant — GlassPanel Component
 *
 * Glassmorphism panel with blur effect and subtle border.
 */

import type { ReactNode } from "react";

// ═══════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════

interface GlassPanelProps {
	children: ReactNode;
	className?: string;
	onClick?: () => void;
}

// ═══════════════════════════════════════════════════════════
// GlassPanel Component
// ═══════════════════════════════════════════════════════════

export function GlassPanel({
	children,
	className = "",
	onClick,
}: GlassPanelProps) {
	const baseClasses = "glass-panel";
	const combinedClassName = `${baseClasses} ${className}`.trim();

	return (
		<div
			className={combinedClassName}
			onClick={onClick}
			onKeyDown={
				onClick
					? (e) => {
							if (e.key === "Enter" || e.key === " ") {
								onClick();
							}
						}
					: undefined
			}
			role={onClick ? "button" : undefined}
			tabIndex={onClick ? 0 : undefined}
		>
			{children}
		</div>
	);
}
