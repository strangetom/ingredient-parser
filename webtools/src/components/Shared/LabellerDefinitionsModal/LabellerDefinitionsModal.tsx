import { Divider, Drawer, Group, Text } from "@mantine/core";
import { Fragment } from "react";
import { useShallow } from "zustand/react/shallow";
import { collectionsLabelDefinitions, useAppShellStore } from "../../../domain";
import { Labeller, type LabellerProps } from "../Labeller/Labeller";

function SmallLabelDefinitionRow({
	labellerProps,
	definitions,
}: {
	labellerProps: LabellerProps;
	definitions: string[];
}) {
	return (
		<Group gap="md" pt="xl" pb="xs" px="xs" wrap="nowrap">
			<div style={{ minWidth: 75 }}>
				<Labeller size="small" {...labellerProps} />
			</div>
			<div>
				{definitions.map((definition) => (
					<Text key={`definnition-${definition}`} size="sm">
						{definition}
					</Text>
				))}
			</div>
		</Group>
	);
}

export function LabellerDefinitionsModal() {
	const { labelDefsModalOpen, setLabelDefsModalOpen } = useAppShellStore(
		useShallow((state) => ({
			labelDefsModalOpen: state.labelDefsModalOpen,
			setLabelDefsModalOpen: state.setLabelDefsModalOpen,
		})),
	);

	return (
		<Drawer
			title="Label definitions"
			position="right"
			styles={{ body: { padding: 0, height: "100%" } }}
			opened={labelDefsModalOpen}
			onClose={() => setLabelDefsModalOpen(false)}
			size="xl"
		>
			{collectionsLabelDefinitions.map(({ token, definitions }, ix) => (
				<Fragment key={`label-definnition-${token[1]}`}>
					<SmallLabelDefinitionRow
						labellerProps={{ size: "small", token: token }}
						definitions={definitions}
					/>
					{ix + 1 < collectionsLabelDefinitions.length && <Divider />}
				</Fragment>
			))}
		</Drawer>
	);
}
