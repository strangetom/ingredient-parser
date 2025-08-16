// {{{EXTERNAL}}}

import {
	Badge,
	Box,
	type BoxProps,
	Flex,
	Menu,
	Tooltip,
	type TooltipProps,
} from "@mantine/core";
import type { UseListStateHandlers } from "@mantine/hooks";
// {{{ASSETS}}}
import { IconSelector } from "@tabler/icons-react";
import cx from "clsx";
import { useCallback, useState } from "react";
// {{{INTERNAL}}}
import {
	type LabellerCategory,
	labellers,
	type ParsedSentenceEditable,
	type Token,
} from "../../../domain/types";
// {{{STYLES}}}
import { default as classes } from "./Labeller.module.css";

const sortedMarginalsList = [
	"B_NAME_TOK",
	"INAME_TOK",
	"NAME_VAR",
	"NAME_MOD",
	"NAME_SEP",
	"QTY",
	"UNIT",
	"PREP",
	"PURPOSE",
	"COMMENT",
	"SIZE",
	"PUNC",
];

export interface LabellerProps extends BoxProps {
	identifier?: number | string;
	editMode?: boolean;
	marginalsMode?: boolean;
	tooltipProps?: TooltipProps;
	token: Token;
	size?: "small" | "medium" | "large";
	handler?: Omit<UseListStateHandlers<ParsedSentenceEditable>, "setState"> & {
		set: (items: ParsedSentenceEditable[]) => void;
	};
	position?: "top" | "bottom";
}

export function Labeller({
	identifier,
	editMode = false,
	marginalsMode = false,
	tooltipProps = { label: undefined },
	token,
	size = "medium",
	position = "top",
	handler,
	...others
}: LabellerProps) {
	const [txt, lbl, marginals] = token;
	const [editable, setEditable] = useState(lbl);

	const onEditHandler = useCallback(
		(labellerCat: LabellerCategory) => {
			setEditable(labellerCat);
			if (handler && identifier) {
				handler.applyWhere(
					(item) => item.id === identifier,
					(item) => ({
						...item,
						edited: true,
						tokens: item.tokens.map((tkn: Token) => {
							if (tkn[0] === txt) return [txt, labellerCat];
							else return tkn;
						}),
					}),
				);
			}
		},
		[handler, identifier, txt],
	);

	if (editMode) {
		const menuItems = labellers.map((labeller) => (
			<>
				<Menu.Item
					component="button"
					className={classes.menuItem}
					onClick={() => onEditHandler(labeller)}
				>
					<Badge variant={labeller}>{labeller}</Badge>
				</Menu.Item>
			</>
		));

		return (
			<Menu position="bottom-start" keepMounted={false}>
				<Menu.Target>
					<Box
						component="button"
						className={cx(classes.labeller, classes.editable)}
						data-labeller={editable}
						data-size={size}
						data-position={position}
						{...others}
					>
						<span>{txt}</span>
						<IconSelector size={16} />
					</Box>
				</Menu.Target>

				<Menu.Dropdown>{menuItems}</Menu.Dropdown>
			</Menu>
		);
	}

	if (marginalsMode && marginals) {
		const marginalRows = Object.keys(marginals)
			.sort(
				(a, b) =>
					sortedMarginalsList.indexOf(a) - sortedMarginalsList.indexOf(b),
			)
			.map((category) => (
				<Flex
					key={`marignal-row-${category}`}
					justify="space-between"
					gap="var(--small-spacing)"
				>
					<div>{category}</div>
					<div>
						{(marginals[category as LabellerCategory] * 100).toFixed(2)}%
					</div>
				</Flex>
			));

		return (
			<Tooltip {...tooltipProps} label={marginalRows}>
				<Box
					{...others}
					component="span"
					className={cx(classes.labeller, classes.marginable)}
					data-labeller={lbl}
					data-size={size}
					data-position={position}
				>
					{txt}
				</Box>
			</Tooltip>
		);
	}

	return (
		<Box
			{...others}
			component="span"
			className={cx(classes.labeller)}
			data-labeller={lbl}
			data-size={size}
			data-position={position}
		>
			{txt}
		</Box>
	);
}
