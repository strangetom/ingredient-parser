// {{{EXTERNAL}}}
import {
	Avatar,
	Box,
	Center,
	Combobox,
	Flex,
	Group,
	Image,
	Input,
	InputBase,
	Loader,
	Paper,
	ScrollArea,
	SegmentedControl,
	Text,
	TextInput,
	type TextProps,
	useCombobox,
} from "@mantine/core";
import { useCallback, useMemo, useState } from "react";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import {
	type CollectionPublisherSource,
	collectionPublisherSources,
	useTabLabellerStore,
	useUploadNewLabellersStore,
} from "../../../../../domain";
// {{{STYLES}}}
import classes from "./StepThree.module.css";

function SelectOption({ name, logo }: CollectionPublisherSource) {
	return (
		<Group wrap="nowrap">
			<Box h={36} w={36}>
				{logo ? (
					<Image h={36} w={36} src={logo} radius="sm" />
				) : (
					<Paper h={36} w={36} radius="sm" bg="var(--fg)">
						<Center style={{ width: "100%", height: "100%" }}>
							<Avatar variant="transparent" color="var(--bg-4)" name={name} />
						</Center>
					</Paper>
				)}
			</Box>
			<div>
				<Text>{name}</Text>
			</div>
		</Group>
	);
}

export function SelectPublisherSource() {
	const { publisherSource, setState } = useUploadNewLabellersStore(
		useShallow((state) => ({
			publisherSource: state.publisherSource,
			setState: state.setState,
		})),
	);

	const { fetchingAvailablePublisherSources, availablePublisherSources } =
		useTabLabellerStore(
			useShallow((state) => ({
				fetchingAvailablePublisherSources:
					state.fetchingAvailablePublisherSources,
				availablePublisherSources: state.availablePublisherSources,
			})),
		);

	const coerceSourcesToComboboxOptions = useCallback(
		() =>
			availablePublisherSources.map((source) => {
				const match = collectionPublisherSources.find(
					({ abbr }) => abbr === source,
				);
				return match ? match : { abbr: source, name: source, logo: null };
			}),
		[availablePublisherSources],
	);

	const optionsPublisherSources = coerceSourcesToComboboxOptions();
	const selectedOption = optionsPublisherSources.find(
		(item) => item.abbr === publisherSource,
	);

	const combobox = useCombobox({
		onDropdownClose: () => combobox.resetSelectedOption(),
	});

	const options = optionsPublisherSources.map((item) => (
		<Combobox.Option value={item.abbr} key={`publisher-source-${item.abbr}`}>
			<SelectOption {...item} />
		</Combobox.Option>
	));

	return (
		<Combobox
			store={combobox}
			onOptionSubmit={(val: string) => {
				setState({ publisherSource: val });
				combobox.closeDropdown();
			}}
		>
			<Combobox.Target>
				<InputBase
					component="button"
					type="button"
					pointer
					rightSection={
						fetchingAvailablePublisherSources ? (
							<Loader color="var(--bg)" size={18} />
						) : (
							<Combobox.Chevron />
						)
					}
					onClick={() => combobox.toggleDropdown()}
					rightSectionPointerEvents="none"
					styles={{
						root: { width: 300, height: 60 },
						input: {
							background: "var(--fg)",
							color: "var(--bg)",
							width: 300,
							height: 60,
						},
					}}
					multiline
				>
					{selectedOption ? (
						<SelectOption {...selectedOption} />
					) : (
						<Input.Placeholder c="var(--bg)">Select one</Input.Placeholder>
					)}
				</InputBase>
			</Combobox.Target>

			<Combobox.Dropdown>
				<Combobox.Options>
					{fetchingAvailablePublisherSources ? (
						<Combobox.Empty style={{ padding: "var(--medium-spacing)" }}>
							Loading....
						</Combobox.Empty>
					) : (
						<ScrollArea.Autosize mah={200} type="scroll">
							{options}
						</ScrollArea.Autosize>
					)}
				</Combobox.Options>
			</Combobox.Dropdown>
		</Combobox>
	);
}

export function TextCount(props: TextProps) {
	const { parsedSentences } = useUploadNewLabellersStore(
		useShallow((state) => ({
			parsedSentences: state.parsedSentences,
		})),
	);

	const chosenParsedSentences = useMemo(
		() => parsedSentences.filter(({ removed }) => !removed),
		[parsedSentences],
	);

	return (
		<Text c="var(--mantine-color-gray-3)" size="sm" {...props}>
			{chosenParsedSentences.length} sentence
			{chosenParsedSentences.length === 1 ? null : "s"} selected for upload
		</Text>
	);
}

export function TextInputSpecifyNew() {
	const { setState } = useUploadNewLabellersStore(
		useShallow((state) => ({
			setState: state.setState,
		})),
	);

	const [value, setValue] = useState("");

	return (
		<Flex>
			<TextInput
				placeholder="Enter name, e.g. bonappetit"
				value={value}
				onChange={(event) => {
					setValue(event.target.value);
					setState({ publisherSource: event.target.value });
				}}
				styles={{
					input: { height: 60, width: 300 },
					root: { height: 60, width: 300 },
				}}
			/>
		</Flex>
	);
}

export function StepThree() {
	const [option, setOption] = useState("existing");

	return (
		<Center className={classes.root}>
			<Text variant="light">Assign a source</Text>
			<SegmentedControl
				value={option}
				onChange={setOption}
				data={[
					{ label: "Existing publisher", value: "existing" },
					{ label: "New publisher", value: "new" },
				]}
			/>
			{option === "existing" && <SelectPublisherSource />}
			{option === "new" && <TextInputSpecifyNew />}
			<TextCount mt="xs" />
		</Center>
	);
}
