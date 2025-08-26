// {{{EXTERNAL}}}
import {
	Badge,
	Breadcrumbs,
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
	return (
		<Table.Tr {...others}>
			<Table.Td width={100} fw="bold">
				<Text variant="light">{title}</Text>
			</Table.Td>
			<Table.Td>
				<Breadcrumbs
					separator=" , "
					separatorMargin="xs"
					styles={{
						breadcrumb: { marginTop: 2, marginBottom: 2 },
						separator: { color: "var(--fg)" },
					}}
					fz="md"
				>
					{items.map(
						({
							text,
							confidence,
							APPROXIMATE,
							SINGULAR,
							PREPARED_INGREDIENT,
						}) => (
							<span key={`table-row-${text}`}>
								{text}
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
							</span>
						),
					)}
				</Breadcrumbs>
			</Table.Td>
		</Table.Tr>
	);
}
