// {{{EXTERNAL}}}
import { Box, type BoxProps } from "@mantine/core";
import cx from "clsx";
// {{{STYLES}}}
import { default as classes } from "./Sectionable.module.css";

export function Sectionable({
	children,
	...others
}: {
	children?: React.ReactNode;
} & BoxProps) {
	return (
		<Box className={classes.root} {...others}>
			{children}
		</Box>
	);
}

export interface SectionableSectionProps extends BoxProps {
	mounted?: boolean;
	children: React.ReactNode;
	grow?: boolean;
	padded?: boolean;
	full?: boolean;
	bordered?: boolean;
	border?: "top" | "bottom" | "left" | "right";
	overflowHidden?: boolean;
}

export function SectionableSection({
	mounted = true,
	grow = false,
	padded = false,
	bordered = false,
	full = false,
	overflowHidden = false,
	border,
	children,
	...others
}: SectionableSectionProps) {
	const wrappable = padded ? (
		<Box
			className={cx(classes.sectionPadded, {
				[classes.sectionFull]: full,
				[classes.sectionOverflowHidden]: overflowHidden,
			})}
		>
			{children}
		</Box>
	) : (
		children
	);

	return mounted ? (
		<Box
			className={cx(classes.section, {
				[classes.sectionGrow]: grow,
				[classes.sectionBordered]: bordered,
				[classes.sectionFull]: full,
				[classes.sectionOverflowHidden]: overflowHidden,
			})}
			data-bordered={(bordered && border) || undefined}
			{...others}
		>
			{wrappable}
		</Box>
	) : null;
}

Sectionable.Section = SectionableSection;

interface SectionableActionBarProps {
	mounted?: boolean;
	position?: "top" | "bottom";
	children?: React.ReactNode;
	grow?: boolean;
}

function SectionableActionBar({
	mounted = true,
	position = "top",
	children,
	grow = false,
	...others
}: SectionableActionBarProps) {
	return mounted ? (
		<Box
			className={cx(classes.bar, { [classes.barGrow]: grow })}
			data-position={position}
			{...others}
		>
			<Box className={classes.barGroupings}>{children}</Box>
		</Box>
	) : null;
}

interface ActionBarSubGroupingProps {
	children?: React.ReactNode;
}

Sectionable.ActionBar = SectionableActionBar;

function SectionableActionBarSubGrouping({
	children,
	...others
}: ActionBarSubGroupingProps) {
	return (
		<Box className={classes.barSubGroupings} {...others}>
			{children}
		</Box>
	);
}

Sectionable.ActionBarSubGrouping = SectionableActionBarSubGrouping;
