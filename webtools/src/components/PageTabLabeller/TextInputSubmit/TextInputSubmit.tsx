// {{{EXTERNAL}}}

import {
	ActionIcon,
	ActionIconGroup,
	type ActionIconProps,
	Box,
	Checkbox,
	Code,
	Divider,
	Flex,
	Group,
	Kbd,
	Loader,
	Menu,
	MultiSelect,
	Popover,
	Stack,
	Text,
	TextInput,
	type TextInputProps,
	Title,
	Transition,
} from "@mantine/core";
import { getHotkeyHandler, useDisclosure } from "@mantine/hooks";
// {{{ASSETS}}}
import {
	IconFilter,
	IconFilterFilled,
	IconQuestionMark,
	IconX,
} from "@tabler/icons-react";
import { type ReactNode, useState } from "react";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import {
	type LabellerCategory,
	labellers,
	useTabLabellerStore,
} from "../../../domain";

interface ReservedChars {
	chars: {
		value: string;
		label: string;
	}[];
	description: ReactNode;
}

const reservedCharacters: ReservedChars[] = [
	{
		chars: [
			{ value: "**", label: "(double asterick)" },
			{ value: "~~", label: "(double tilde)" },
		],
		description: (
			<span>
				Reserved for wildcard searches. Use this to search the ingredient
				database without a keyword. For example, input only <Code>**</Code>.
			</span>
		),
	},
	{
		chars: [
			{ value: "== n,n+1", label: "(double equals, comma separated numbers)" },
		],
		description: (
			<span>
				Reserved for ID matched searches. Use this to directly query the
				ingredient database row IDs. Supports double dot notation for ID ranges.
				For example the input <Code>== 1,2,10..14</Code> would be interpreted as{" "}
				<Code>== 1,2,10,11,12,13,14</Code>.
			</span>
		),
	},
];

function ReservedCharDescriptor({
	reservedChars,
}: {
	reservedChars: ReservedChars;
}) {
	const { chars, description } = reservedChars;

	return (
		<Stack gap="xs" px="xs" py="sm">
			<Stack gap="xs">
				{chars.map(({ label, value }) => (
					<Group key={`rchar-${label}`} gap={3}>
						<Kbd>{value}</Kbd>
						<Text variant="light" size="xs">
							{label}
						</Text>
					</Group>
				))}
			</Stack>
			<Text variant="light" size="sm">
				{description}
			</Text>
		</Stack>
	);
}

function ActionIconQuestion(props: ActionIconProps) {
	const [opened, { close, open }] = useDisclosure(false);

	return (
		<Popover
			opened={opened}
			shadow="md"
			keepMounted={false}
			position="bottom-end"
			width={350}
			offset={8}
		>
			<Popover.Target>
				<ActionIcon
					onMouseEnter={open}
					onMouseLeave={close}
					variant="dark"
					style={{ cursor: "help", width: 36, height: 36 }}
					{...props}
				>
					<IconQuestionMark strokeWidth={1} />
				</ActionIcon>
			</Popover.Target>

			<Popover.Dropdown p={0}>
				<Box px="xs" py="md">
					<Title order={4} lh={1}>
						Search Operators
					</Title>
				</Box>
				<Divider />
				{reservedCharacters.map((reservedChar, i) => (
					<>
						<ReservedCharDescriptor
							key={`rchar-descriptor-${reservedChar.description}`}
							reservedChars={reservedChar}
						/>
						{i + 1 !== reservedCharacters.length && <Divider />}
					</>
				))}
			</Popover.Dropdown>
		</Popover>
	);
}

function ActionIconClear(props: ActionIconProps) {
	const { sentence } = useTabLabellerStore(
		useShallow((state) => ({
			sentence: state.input.sentence,
		})),
	);

	const onClearHandler = () => {
		const { hasUnsavedChanges, setUnsavedChangesModalOpen } =
			useTabLabellerStore.getState();
		const fnCallback = () => {
			const { updateInput, setParsed, setActivePage } =
				useTabLabellerStore.getState();
			updateInput({ sentence: "" });
			setParsed(null);
			setActivePage(1);
		};
		if (hasUnsavedChanges()) {
			const { setUnsavedChangesFnCallback } = useTabLabellerStore.getState();
			setUnsavedChangesFnCallback(fnCallback);
			setUnsavedChangesModalOpen(true);
		} else {
			fnCallback();
		}
	};

	return (
		<Transition mounted={sentence.length !== 0}>
			{(styles) => (
				<ActionIcon
					variant="transparent-light"
					style={{ width: 36, height: 36, ...styles }}
					onClick={onClearHandler}
					{...props}
				>
					<IconX strokeWidth={1} />
				</ActionIcon>
			)}
		</Transition>
	);
}

function ActionIconFilter(props: ActionIconProps) {
	const {
		availablePublisherSources,
		fetchingAvailablePublisherSources,
		input,
		updateInputSettings,
	} = useTabLabellerStore(
		useShallow((state) => ({
			availablePublisherSources: state.availablePublisherSources,
			fetchingAvailablePublisherSources:
				state.fetchingAvailablePublisherSources,
			input: state.input,
			updateInputSettings: state.updateInputSettings,
		})),
	);

	const [opened, setOpened] = useState(false);

	const labelFilters = (
		<MultiSelect
			data={labellers}
			value={input.settings.labels}
			onChange={(values) => {
				if (values.length === 0) return;
				updateInputSettings({ labels: [...values] as LabellerCategory[] });
			}}
			comboboxProps={{ withinPortal: false, width: 200, position: "top-start" }}
		/>
	);

	const labelSources = fetchingAvailablePublisherSources ? (
		<Flex style={{ width: "100%" }}>
			<Loader color="var(--fg)" size={16} />
		</Flex>
	) : (
		<MultiSelect
			data={availablePublisherSources}
			value={input.settings.sources}
			onChange={(values) => {
				if (values.length === 0) return;
				updateInputSettings({ sources: [...values] });
			}}
			comboboxProps={{ withinPortal: false, width: 200, position: "top-start" }}
		/>
	);

	return (
		<Menu
			shadow="md"
			keepMounted={false}
			position="bottom-end"
			width={350}
			closeOnItemClick={false}
			offset={8}
			opened={opened}
			onChange={setOpened}
			trigger="click"
		>
			<Menu.Target>
				<ActionIcon style={{ width: 36, height: 36 }} variant="dark" {...props}>
					{opened ? <IconFilterFilled size={16} /> : <IconFilter size={16} />}
				</ActionIcon>
			</Menu.Target>

			<Menu.Dropdown>
				<Menu.Label>Keyword (options)</Menu.Label>
				<Box py="xs" px="sm">
					<Checkbox
						defaultChecked
						checked={input.settings.wholeWord}
						label="Whole word"
						name="WHOLE_WORD"
						onChange={(event) =>
							updateInputSettings({ wholeWord: event.currentTarget.checked })
						}
						styles={{
							root: { width: "100%" },
							labelWrapper: { width: "100%" },
						}}
					/>
				</Box>
				<Box py="xs" px="sm">
					<Checkbox
						defaultChecked
						checked={input.settings.caseSensitive}
						label="Case sensitve"
						name="CASE_SENSITIVE"
						onChange={(event) =>
							updateInputSettings({
								caseSensitive: event.currentTarget.checked,
							})
						}
						styles={{
							root: { width: "100%" },
							labelWrapper: { width: "100%" },
						}}
					/>
				</Box>
				<Menu.Divider />
				<Menu.Label>Labels (to search against)</Menu.Label>
				<Box py="xs" px="sm">
					{labelFilters}
				</Box>
				<Menu.Divider />
				<Menu.Label>Sources (to search against)</Menu.Label>
				<Box py="xs" px="sm">
					{labelSources}
				</Box>
			</Menu.Dropdown>
		</Menu>
	);
}

export function TextInputSubmit(props: TextInputProps) {
	const { sentence, updateInput, setActivePage, getLabellerSearchApi } =
		useTabLabellerStore(
			useShallow((state) => ({
				sentence: state.input.sentence,
				updateInput: state.updateInput,
				setActivePage: state.setActivePage,
				getLabellerSearchApi: state.getLabellerSearchApi,
			})),
		);

	const onEnterWrapperHandler = () => {
		getLabellerSearchApi();
		setActivePage(1);
	};

	return (
		<TextInput
			styles={{ input: { height: 50 }, root: { height: 50 } }}
			placeholder="Keyword to search, e.g. tomato"
			value={sentence}
			onChange={(event) => {
				updateInput({ sentence: event.target.value });
			}}
			onKeyDown={getHotkeyHandler([
				["mod+Enter", () => onEnterWrapperHandler()],
				["Enter", () => onEnterWrapperHandler()],
			])}
			rightSection={
				<Group gap="var(--xxsmall-spacing)" mr="var(--xsmall-spacing)">
					<ActionIconClear />
					<ActionIconGroup>
						<ActionIconFilter />
						<ActionIconQuestion />
					</ActionIconGroup>
				</Group>
			}
			rightSectionProps={{ style: { backgroundColor: "var(--bg-2)" } }}
			rightSectionWidth="auto"
			{...props}
		/>
	);
}
