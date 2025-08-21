// {{{EXTERNAL}}}
import { Box, Tooltip, type TooltipProps } from "@mantine/core";
import { type HotkeyItem, useHotkeys } from "@mantine/hooks";

export function TooltipExtended({ children, label, ...others }: TooltipProps) {
	const defaultTooltipProps: Partial<TooltipProps> = {
		position: "bottom",
		p: "var(--xxsmall-spacing) var(--xsmall-spacing)",
		fz: ".75rem",
		withArrow: false,
		zIndex: 99999,
		events: { hover: true, focus: true, touch: false },
	};

	return (
		<Tooltip label={label} {...defaultTooltipProps} {...others}>
			{children}
		</Tooltip>
	);
}

export function TooltipExtendedWithShortcut({
	children,
	label,
	withShift = true,
	shortcut,
	hotkeyItems,
	...others
}: TooltipProps & {
	withShift?: boolean;
	shortcut: typeof label;
	hotkeyItems: HotkeyItem[];
}) {
	// Defaults
	const defaultTooltipProps: Partial<TooltipProps> = {
		position: "bottom",
		bg: "var(--mantine-color-blankdish-dark-5)",
		px: "xs",
		py: "calc(var(--mantine-spacing-xs) / 2)",
		c: "var(--mantine-color-blankdish-light-0)",
		fz: "xs",
		withArrow: false,
		zIndex: 99999,
		events: { hover: true, focus: true, touch: false },
	};

	// Handlers
	useHotkeys(hotkeyItems);

	const ShortcutLabel = (
		<div>
			<Box fw={800}>{label}</Box>
			<Box fw={400}>
				Shortcut: {withShift && "⇧"} {shortcut}
			</Box>
		</div>
	);

	return (
		<Tooltip label={ShortcutLabel} {...defaultTooltipProps} {...others}>
			{children}
		</Tooltip>
	);
}
