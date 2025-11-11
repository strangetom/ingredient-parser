// {{{EXTERNAL}}}
import {
	Anchor,
	Badge,
	Box,
	Breadcrumbs,
	type BreadcrumbsProps,
	Flex,
	type FlexProps,
	Table,
	type TableTrProps,
	Text,
	Tooltip,
	type TooltipProps,
} from "@mantine/core";
// {{{INTERNAL}}}
import type {
	Amount,
	Confidence,
	FoundationFood,
	LabellerCategory,
} from "../../../../../domain";

function TableRowTooltip({ children, label, ...others }: TooltipProps) {
	return (
		<Tooltip
			p="xs"
			withArrow
			maw={200}
			position="top"
			bg="var(--bg-2)"
			label={
				<Text variant="light" size="xs">
					{label}
				</Text>
			}
			{...others}
		>
			{children}
		</Tooltip>
	);
}

interface TableRowLineItemProps extends FlexProps {
	isCompositeIngredient: boolean;
	badgeCategory: LabellerCategory;
	lineItem: Confidence | FoundationFood | Amount;
}

function TableRowLineItem({
	isCompositeIngredient,
	badgeCategory,
	lineItem,
	...others
}: TableRowLineItemProps) {
	const { text, confidence, APPROXIMATE, SINGULAR, PREPARED_INGREDIENT } =
		lineItem;

	return (
		<Flex justify="flex-start" align="center" fz="md" {...others}>
			<Box>{text}</Box>
			{isCompositeIngredient && (
				<TableRowTooltip label="Composite Ingredient">
					<Badge style={{ cursor: "help" }} ml={6}>
						C
					</Badge>
				</TableRowTooltip>
			)}
			{APPROXIMATE && (
				<TableRowTooltip label="Approximate">
					<Badge style={{ cursor: "help" }} ml={6}>
						~
					</Badge>
				</TableRowTooltip>
			)}
			{SINGULAR && (
				<TableRowTooltip label="Singular">
					<Badge style={{ cursor: "help" }} ml={6}>
						1
					</Badge>
				</TableRowTooltip>
			)}
			{PREPARED_INGREDIENT && (
				<TableRowTooltip label="Prepared Ingredient">
					<Badge style={{ cursor: "help" }} ml={6}>
						P
					</Badge>
				</TableRowTooltip>
			)}
			{confidence !== 0 && (
				<Badge ml={6} variant={badgeCategory}>
					{(confidence * 100).toFixed(2)}%
				</Badge>
			)}
		</Flex>
	);
}

interface TableRowLineFoundationItemProps extends FlexProps {
	badgeCategory: LabellerCategory;
	lineItem: FoundationFood;
}

function TableRowLineFoundationItem({
	badgeCategory,
	lineItem,
}: TableRowLineFoundationItemProps) {
	const { text, confidence, fdc_id } = lineItem;

	return (
		<Flex justify="flex-start" align="center" fz="md">
			<Anchor
				href={`https://fdc.nal.usda.gov/food-details/${fdc_id}/nutrients`}
				target="_blank"
				fw="normal"
			>
				{text}
			</Anchor>
			{confidence !== 0 && (
				<Badge ml={6} variant={badgeCategory}>
					{(confidence * 100).toFixed(2)}%
				</Badge>
			)}
		</Flex>
	);
}

interface TableRowProps extends TableTrProps {
	title: string;
	badgeCategory: LabellerCategory;
	items: Confidence[] | FoundationFood[] | Amount[] | Amount[][];
}

export function TableRow({
	title,
	badgeCategory,
	items,
	...others
}: TableRowProps) {
	const breadcrumbDefaultProps = {
		separator: " , ",
		separatorMargin: "xs",
		styles: {
			breadcrumb: { marginTop: 2, marginBottom: 2 },
			separator: { color: "var(--fg)" },
		},
		fz: "md",
	} as BreadcrumbsProps;

	const isNestedAmount = items.some((_i) => Array.isArray(_i));

	if (isNestedAmount) {
		const itemsBreadcrumbs = items.map((item) =>
			Array.isArray(item) ? (
				item.map((itemsSub) => (
					<TableRowLineItem
						key={`table-row-${itemsSub.text}`}
						isCompositeIngredient={true}
						lineItem={itemsSub}
						badgeCategory={badgeCategory}
					/>
				))
			) : (
				<TableRowLineItem
					key={`table-row-${item.text}`}
					isCompositeIngredient={false}
					lineItem={item}
					badgeCategory={badgeCategory}
				/>
			),
		);

		return (
			<Table.Tr {...others}>
				<Table.Td width={100} fw="bold">
					<Text variant="light">{title}</Text>
				</Table.Td>
				<Table.Td>
					<Breadcrumbs {...breadcrumbDefaultProps}>
						{itemsBreadcrumbs}
					</Breadcrumbs>
				</Table.Td>
			</Table.Tr>
		);
	}

	const itemsBreadcrumbs = items.map((item) =>
		item?.fdc_id ? (
			<TableRowLineFoundationItem
				key={`table-row-${item.text}`}
				lineItem={item}
				badgeCategory={badgeCategory}
			/>
		) : (
			<TableRowLineItem
				key={`table-row-${item.text}`}
				isCompositeIngredient={false}
				lineItem={item}
				badgeCategory={badgeCategory}
			/>
		),
	);

	return (
		<Table.Tr {...others}>
			<Table.Td width={100} fw="bold">
				<Text variant="light">{title}</Text>
			</Table.Td>
			<Table.Td>
				<Breadcrumbs {...breadcrumbDefaultProps}>
					{itemsBreadcrumbs}
				</Breadcrumbs>
			</Table.Td>
		</Table.Tr>
	);
}
