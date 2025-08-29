// {{{EXTERNAL}}}
import {
	Anchor,
	Badge,
	Box,
	Breadcrumbs,
	type BreadcrumbsProps,
	Flex,
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

interface TableRowProps extends TableTrProps {
	title: string;
	badgeCategory: LabellerCategory;
	items: Confidence[] | FoundationFood[] | Amount[];
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

	const itemsBreadcrumbs = items.map(
		({
			text,
			confidence,
			APPROXIMATE,
			SINGULAR,
			PREPARED_INGREDIENT,
			...others
		}) =>
			others?.fdc_id ? (
				<Flex
					justify="flex-start"
					align="center"
					fz="md"
					key={`table-row-${text}`}
				>
					<Anchor
						href={`https://fdc.nal.usda.gov/food-details/${others.fdc_id}/nutrients`}
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
			) : (
				<Flex
					justify="flex-start"
					align="center"
					fz="md"
					key={`table-row-${text}`}
				>
					<Box>{text}</Box>
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
