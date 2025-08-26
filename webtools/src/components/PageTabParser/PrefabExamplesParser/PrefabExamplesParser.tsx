// {{{EXTERNAL}}}
import {
	Box,
	type BoxProps,
	CopyButton,
	Group,
	ScrollArea,
	Stack,
	Text,
} from "@mantine/core";
// {{{ASSETS}}}
import { IconCopy, IconCopyCheck } from "@tabler/icons-react";

// {{{INTERNAL}}}
import { ActionIconTooltipped } from "../../Shared";
import sentences from "./sentences";

export function PrefabExamplesParser(props: BoxProps) {
	return (
		<Box
			style={{ borderRadius: "var(--xsmall-spacing)", overflow: "hidden" }}
			{...props}
		>
			<ScrollArea.Autosize w={350} mah={150} type="always">
				<Stack gap={1}>
					{sentences.map(({ value }) => (
						<Group
							bg="color-mix(in srgb,var(--fg), transparent 90%)"
							pr="var(--medium-spacing)"
							pl="var(--xsmall-spacing)"
							py="var(--xsmall-spacing)"
							justify="space-between"
							wrap="nowrap"
						>
							<Text variant="light" fz="sm">
								{value}
							</Text>
							<CopyButton value={value}>
								{({ copied, copy }) =>
									copied ? (
										<ActionIconTooltipped
											iconography={IconCopyCheck}
											text="Copied"
										/>
									) : (
										<ActionIconTooltipped
											iconography={IconCopy}
											text="Copy"
											onClick={copy}
										/>
									)
								}
							</CopyButton>
						</Group>
					))}
				</Stack>
			</ScrollArea.Autosize>
		</Box>
	);
}
