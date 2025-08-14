// {{{EXTERNAL}}}

import {
	ActionIcon,
	type ActionIconProps,
	Tooltip,
	type TooltipProps,
} from "@mantine/core";
// {{{STYLES}}}
import type { Icon, IconProps } from "@tabler/icons-react";
import type React from "react";

interface ActionIconTooltippedProps {
	tooltipProps?: Omit<TooltipProps, "children" | "label">;
	actionIconProps?: ActionIconProps;
	onClick?: () => void;
	text: string;
	iconography: React.ForwardRefExoticComponent<
		IconProps & React.RefAttributes<Icon>
	>;
}

export function ActionIconTooltipped({
	tooltipProps,
	actionIconProps,
	onClick,
	text,
	iconography,
}: ActionIconTooltippedProps) {
	const defaultTooltipProps = {
		withArrow: false,
		withinPortal: false,
		position: "left",
		style: {
			padding: "var(--xxsmall-spacing) var(--xsmall-spacing)",
			fontSize: ".75rem",
		},
		...tooltipProps,
	} as Partial<TooltipProps>;

	const defaultActionIconProps = {
		variant: "dark",
		...actionIconProps,
	};

	const Iconography = iconography;

	return (
		<Tooltip label={text} {...defaultTooltipProps}>
			<ActionIcon {...defaultActionIconProps} onClick={onClick} title={text}>
				<Iconography size={16} />
			</ActionIcon>
		</Tooltip>
	);
}
