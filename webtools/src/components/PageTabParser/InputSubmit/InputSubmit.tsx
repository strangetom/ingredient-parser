// {{{EXTERNAL}}}
import {
	ActionIcon,
	ActionIconGroup,
	type ActionIconProps,
	Button,
	Combobox,
	type ComboboxProps,
	Flex,
	Group,
	Indicator,
	Menu,
	ScrollArea,
	Switch,
	TextInput,
	type TextInputProps,
	Transition,
	useCombobox,
} from "@mantine/core";
import { getHotkeyHandler } from "@mantine/hooks";
// {{{ASSETS}}}
import {
	IconClipboardList,
	IconClipboardListFilled,
	IconFilter,
	IconFilterFilled,
	IconTrash,
	IconX,
} from "@tabler/icons-react";
import { useCallback, useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { useTabParserStore } from "../../../domain";
// {{{INTERNAL}}}
import { PopoverQuestionMark } from "../../Shared";

function ActionIconClear(props: ActionIconProps) {
	const { sentence, updateInput, setParsed } = useTabParserStore(
		useShallow((state) => ({
			sentence: state.input.sentence,
			updateInput: state.updateInput,
			setParsed: state.setParsed,
		})),
	);

	const onClearHandler = () => {
		updateInput({ sentence: "" });
		setParsed(null);
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
	const { input, updateInput } = useTabParserStore(
		useShallow((state) => ({
			input: state.input,
			updateInput: state.updateInput,
		})),
	);

	const [opened, setOpened] = useState(false);

	const foundationFoodsInput = (
		<Switch
			defaultChecked
			checked={input.foundation_foods}
			label={
				<Flex gap="xs" justify="flex-start">
					<div>Foundation foods</div>
					<PopoverQuestionMark>
						Foundation foods are the core or fundamental part of an ingredient
						name, without any other words like descriptive adjectives or brand
						names. If enabled, the foundation foods are extracted from the
						ingredient name
					</PopoverQuestionMark>
				</Flex>
			}
			name="FOUNDATION_FOOD"
			onChange={(event) =>
				updateInput({ foundation_foods: event.target.checked })
			}
			styles={{
				root: { width: "100%" },
				labelWrapper: { width: "100%" },
			}}
		/>
	);

	const discardIsolatedStopWordsInput = (
		<Switch
			defaultChecked
			checked={input.discard_isolated_stop_words}
			label={
				<Flex gap="xs" justify="flex-start">
					<div>Discard isolated stop words</div>
					<PopoverQuestionMark>
						Discard stop words that appear in isolation within the name,
						preparation, size, purpose or comment fields. If disabled, then all
						words from the input sentence are retained in the parsed output.
					</PopoverQuestionMark>
				</Flex>
			}
			name="discard_isolated_stop_words"
			onChange={(event) =>
				updateInput({ discard_isolated_stop_words: event.target.checked })
			}
			style={{ width: "100%" }}
		/>
	);

	const stringUnitsInput = (
		<Switch
			defaultChecked
			checked={input.string_units}
			label={
				<Flex gap="xs" justify="flex-start">
					<div>String units</div>
					<PopoverQuestionMark>
						If set to True, the IngredientAmount unit will be the string
						identified from the sentence instead of a data class object.
					</PopoverQuestionMark>
				</Flex>
			}
			name="string_units"
			onChange={(event) => updateInput({ string_units: event.target.checked })}
			style={{ width: "100%" }}
		/>
	);

	const expectNameInput = (
		<Switch
			defaultChecked
			checked={input.expect_name_in_output}
			label={
				<Flex gap="xs" justify="flex-start">
					<div>Expect name in output</div>
					<PopoverQuestionMark>
						Sometimes a name isn’t identified in the ingredient sentence, often
						due to the sentence structure being unusual or the sentence contains
						an ingredient name that is ambiguous. For these cases, attempt to
						find the most likely name even if the words making that name are
						considered more likely to belong to a different field of the
						ParsedIngredient object.
					</PopoverQuestionMark>
				</Flex>
			}
			name="expect_name_in_output"
			onChange={(event) =>
				updateInput({ expect_name_in_output: event.target.checked })
			}
			style={{ width: "100%" }}
		/>
	);

	const imperialUnitsInput = (
		<Switch
			defaultChecked
			checked={input.imperial_units}
			label={
				<Flex gap="xs" justify="flex-start">
					<div>Imperial units</div>
					<PopoverQuestionMark>
						Some units have have multiple definitions versions with the same
						name but representing different quantities, such as fluid ounces,
						cups, pints, quarts or gallons.
					</PopoverQuestionMark>
				</Flex>
			}
			name="imperial_units"
			onChange={(event) =>
				updateInput({ imperial_units: event.target.checked })
			}
			style={{ width: "100%" }}
		/>
	);

	const separateNamesInput = (
		<Group gap="xs">
			<Switch
				checked={input.separate_names}
				label={
					<Flex gap="xs" justify="flex-start">
						<div>Separate names</div>
						<PopoverQuestionMark>
							If the ingredient sentence includes multiple alternative
							ingredient names, return each name separately
						</PopoverQuestionMark>
					</Flex>
				}
				name="separate_names"
				onChange={(event) =>
					updateInput({ separate_names: event.target.checked })
				}
				style={{ width: "100%" }}
			/>
		</Group>
	);

	return (
		<Menu
			shadow="md"
			position="top-end"
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
				<Menu.Item component="div">{foundationFoodsInput}</Menu.Item>
				<Menu.Divider />
				<Menu.Item component="div">{discardIsolatedStopWordsInput}</Menu.Item>
				<Menu.Divider />
				<Menu.Item component="div">{stringUnitsInput}</Menu.Item>
				<Menu.Divider />
				<Menu.Item component="div">{expectNameInput}</Menu.Item>
				<Menu.Divider />
				<Menu.Item component="div">{imperialUnitsInput}</Menu.Item>
				<Menu.Divider />
				<Menu.Item component="div">{separateNamesInput}</Menu.Item>
			</Menu.Dropdown>
		</Menu>
	);
}

function ActionIconHistory(props: ComboboxProps) {
	const { updateInput, history, clearHistory, getParsedApi } =
		useTabParserStore(
			useShallow((state) => ({
				updateInput: state.updateInput,
				history: state.history,
				clearHistory: state.clearHistory,
				getParsedApi: state.getParsedApi,
			})),
		);

	const combobox = useCombobox({
		onDropdownClose: () => combobox.resetSelectedOption(),
	});

	const options = history
		.map((item) => (
			<Combobox.Option
				value={item.timestamp}
				key={`history-item-${item.sentence}`}
			>
				{item.sentence}
			</Combobox.Option>
		))
		.reverse();

	return (
		<Combobox
			store={combobox}
			width={250}
			position="top-end"
			onOptionSubmit={useCallback(
				(val: string) => {
					const match = history.find((item) => item.timestamp === val);
					if (!match) return;
					updateInput({ sentence: match.sentence });
					getParsedApi({ input: match, shouldAddToHistory: false });
				},
				[history],
			)}
			{...props}
		>
			<Combobox.Target>
				<ActionIcon
					disabled={history.length === 0}
					style={{ width: 36, height: 36 }}
					variant="dark"
					onClick={() => combobox.toggleDropdown()}
				>
					<Indicator
						disabled={history.length === 0}
						offset={2}
						color="var(--fg)"
					>
						{combobox.dropdownOpened ? (
							<IconClipboardListFilled size={16} />
						) : (
							<IconClipboardList size={16} />
						)}
					</Indicator>
				</ActionIcon>
			</Combobox.Target>

			<Combobox.Dropdown>
				<Combobox.Options>
					<ScrollArea.Autosize type="scroll" mah={200}>
						{options}
					</ScrollArea.Autosize>
				</Combobox.Options>
				<Combobox.Footer p="xs" style={{ borderTop: "1px solid var(--fg-4)" }}>
					<Button
						leftSection={<IconTrash size={16} />}
						onClick={() => {
							combobox.toggleDropdown();
							clearHistory();
						}}
						variant="light"
						size="sm"
					>
						Clear history
					</Button>
				</Combobox.Footer>
			</Combobox.Dropdown>
		</Combobox>
	);
}

export function InputSubmit(props: TextInputProps) {
	const { sentence, updateInput, getParsedApi } = useTabParserStore(
		useShallow((state) => ({
			sentence: state.input.sentence,
			updateInput: state.updateInput,
			getParsedApi: state.getParsedApi,
		})),
	);

	return (
		<TextInput
			styles={{ input: { height: 50 }, root: { height: 50 } }}
			placeholder="Ingredient sentence, e.g. 1/2 cup of olives"
			value={sentence}
			onChange={(event) => {
				updateInput({ sentence: event.target.value as string });
			}}
			onKeyDown={getHotkeyHandler([
				["mod+Enter", () => getParsedApi({ shouldAddToHistory: true })],
				["Enter", () => getParsedApi({ shouldAddToHistory: true })],
			])}
			rightSection={
				<Group gap="var(--xxsmall-spacing)" mr="var(--xsmall-spacing)">
					<ActionIconClear />
					<ActionIconGroup>
						<ActionIconFilter />
						<ActionIconHistory />
					</ActionIconGroup>
				</Group>
			}
			rightSectionProps={{ style: { backgroundColor: "var(--bg-2)" } }}
			rightSectionWidth="auto"
			{...props}
		/>
	);
}
