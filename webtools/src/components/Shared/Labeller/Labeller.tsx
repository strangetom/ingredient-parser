// {{{EXTERNAL}}}

import {
	Badge,
	Box,
	type BoxProps,
	Combobox,
	Flex,
	Menu,
	Tooltip,
	type TooltipProps,
	useCombobox,
} from "@mantine/core";
import type { UseListStateHandlers } from "@mantine/hooks";
// {{{ASSETS}}}
import { IconSelector } from "@tabler/icons-react";
import cx from "clsx";
import { useCallback, useRef, useState } from "react";
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
	const [search, setSearch] = useState("");
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

	const combobox = useCombobox({
		onDropdownClose: () => {
			combobox.resetSelectedOption();
			combobox.focusTarget();
			setSearch("");
		},

		onDropdownOpen: () => {
			combobox.focusSearchInput();
		},
	});

	if (editMode) {
		const menuItems = labellers
			.filter((item) =>
				item.toLowerCase().includes(search.toLowerCase().trim()),
			)
			.map((labeller) => (
				<Combobox.Option
					key={`labeller-${labeller}`}
					value={labeller}
					style={{ padding: "calc(var(--small-spacing) / 3)" }}
				>
					<Badge variant={labeller}>{labeller}</Badge>
				</Combobox.Option>
			));

		return (
			<Combobox
				store={combobox}
				width={250}
				position="bottom-start"
				onOptionSubmit={(val) => {
					if (!val) return;
					onEditHandler(val as LabellerCategory);
					combobox.closeDropdown();
				}}
				keepMounted={false}
			>
				<Combobox.Target>
					<Box
						component="button"
						className={cx(classes.labeller, classes.editable)}
						data-labeller={editable}
						data-size={size}
						data-position={position}
						onClick={() => combobox.toggleDropdown()}
						{...others}
					>
						<span>{txt}</span>
						<IconSelector size={16} />
					</Box>
				</Combobox.Target>

				<Combobox.Dropdown>
					<Combobox.Search
						value={search}
						onChange={(event) => {
							setSearch(event.currentTarget.value);
						}}
					/>
					<Combobox.Options mah={200} style={{ overflowY: "auto" }}>
						{menuItems.length > 0 ? (
							menuItems
						) : (
							<Combobox.Empty c="var(--fg-4)">
								Type a correct label
							</Combobox.Empty>
						)}
					</Combobox.Options>
				</Combobox.Dropdown>
			</Combobox>
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
