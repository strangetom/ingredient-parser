// {{{EXTERNAL}}}
import { Box } from "@mantine/core";
import cx from "clsx";
import type React from "react";
// {{{STYLES}}}
import { default as classes } from "./ActionBar.module.css";

export interface ActionBarProps {
	position?: "top" | "bottom";
	children?: React.ReactNode;
	grow?: boolean;
}

export function ActionBar(props: ActionBarProps) {
	const { position = "top", children, grow = false, ...others } = props;

	return (
		<Box
			className={cx(classes.root, { [classes.grow]: grow })}
			data-position={position}
			{...others}
		>
			<Box className={classes.groupings}>{children}</Box>
		</Box>
	);
}

export interface ActionBarSubGroupingProps {
	children?: React.ReactNode;
}

function ActionBarSubGrouping({
	children,
	...others
}: ActionBarSubGroupingProps) {
	return (
		<Box className={classes.subgroupings} {...others}>
			{children}
		</Box>
	);
}

ActionBar.SubGrouping = ActionBarSubGrouping;
