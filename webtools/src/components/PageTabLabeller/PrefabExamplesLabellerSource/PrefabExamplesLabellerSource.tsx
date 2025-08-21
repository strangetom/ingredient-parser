// {{EXTERNAL}}

import {
	ActionIcon,
	Avatar,
	Box,
	Center,
	Flex,
	Group,
	Image,
	Loader,
	Paper,
	ScrollArea,
	Stack,
	Text,
} from "@mantine/core";
// {{ASSETS}}
import { IconArrowRight } from "@tabler/icons-react";
import { useShallow } from "zustand/react/shallow";
// {{INTERNAL}}
import {
	collectionPublisherSources,
	useTabLabellerStore,
} from "../../../domain";

export function PrefabExamplesLabellerSource({
	onClick,
}: {
	onClick: (abbr: string) => void;
}) {
	const { availablePublisherSources, fetchingAvailablePublisherSources } =
		useTabLabellerStore(
			useShallow((state) => ({
				availablePublisherSources: state.availablePublisherSources,
				fetchingAvailablePublisherSources:
					state.fetchingAvailablePublisherSources,
			})),
		);

	const optionsPublisherSources = availablePublisherSources.map((source) => {
		const match = collectionPublisherSources.find(
			({ abbr }) => abbr === source,
		);
		return match ? match : { abbr: source, name: source, logo: null };
	});

	return (
		<Box style={{ borderRadius: "var(--xsmall-spacing)", overflow: "hidden" }}>
			{fetchingAvailablePublisherSources ? (
				<Flex
					w={350}
					h={150}
					bg="color-mix(in srgb,var(--fg), transparent 90%)"
				>
					<Loader color="var(--fg)" size={16} />
				</Flex>
			) : (
				<ScrollArea.Autosize w={350} mah={150} type="always">
					<Stack gap={1}>
						{optionsPublisherSources.map(({ abbr, logo, name }) => (
							<Group
								key={`publisher-source-${abbr}`}
								bg="color-mix(in srgb,var(--fg), transparent 90%)"
								pr="var(--medium-spacing)"
								pl="var(--xsmall-spacing)"
								py="var(--xsmall-spacing)"
								justify="space-between"
								wrap="nowrap"
							>
								<Group wrap="nowrap">
									{logo ? (
										<Image h={36} w={36} src={logo} radius="sm" />
									) : (
										<Paper h={36} w={36} radius="sm" bg="var(--fg)">
											<Center style={{ width: "100%", height: "100%" }}>
												<Avatar
													variant="transparent"
													color="var(--bg-4)"
													name={name}
												/>
											</Center>
										</Paper>
									)}
									<Text variant="light" lh={1}>
										{name}
									</Text>
								</Group>
								<ActionIcon variant="dark" onClick={() => onClick?.(abbr)}>
									<IconArrowRight size={16} />
								</ActionIcon>
							</Group>
						))}
					</Stack>
				</ScrollArea.Autosize>
			)}
		</Box>
	);
}
