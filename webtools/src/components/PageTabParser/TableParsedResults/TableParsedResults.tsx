// {{{EXTERNAL}}}
import { Table } from "@mantine/core";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useTabParserStore } from "../../../domain";
import { Filler } from "../../Shared";
import { PrefabExamplesParser } from "../PrefabExamplesParser";
import { TableRow } from "./tablecomponents";

function TableBase() {
	const { parsed } = useTabParserStore(
		useShallow((state) => ({
			parsed: state.parsed,
		})),
	);

	if (!parsed) return null;

	return (
		<Table
			striped
			withTableBorder
			withColumnBorders
			horizontalSpacing="md"
			verticalSpacing="sm"
		>
			<Table.Tbody>
				<TableRow items={parsed.name} title="Name" badgeCategory="NAME_VAR" />
				<TableRow items={[parsed.size]} title="Size" badgeCategory="SIZE" />
				<TableRow items={parsed.amounts} title="Amount" badgeCategory="UNIT" />
				<TableRow
					items={[parsed.preparation]}
					title="Preparation"
					badgeCategory="PREP"
				/>
				<TableRow
					items={[parsed.comment]}
					title="Comment"
					badgeCategory="COMMENT"
				/>
				<TableRow
					items={[parsed.purpose]}
					title="Purpose"
					badgeCategory="PURPOSE"
				/>
				<TableRow
					items={parsed.foundation_foods}
					title="Foundation Food"
					badgeCategory="OTHER"
				/>
			</Table.Tbody>
		</Table>
	);
}

export function TableParsedResults() {
	const { parsed } = useTabParserStore(
		useShallow((state) => ({
			parsed: state.parsed,
		})),
	);

	return (
		<>
			{parsed ? (
				<TableBase />
			) : (
				<Filler
					text="Enter full ingredient sentence. View some examples below"
					illustration="bowl"
				>
					<PrefabExamplesParser mt="xs" />
				</Filler>
			)}
		</>
	);
}
