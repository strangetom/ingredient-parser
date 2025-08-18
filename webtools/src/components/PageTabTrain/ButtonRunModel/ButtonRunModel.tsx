// {{{EXTERNAL}}}
import {
	ActionIcon,
	Box,
	Button,
	Flex,
	Group,
	Loader,
	Menu,
	MultiSelect,
	NumberInput,
	SegmentedControl,
	Switch,
	Text,
} from "@mantine/core";
// {{{ASSETS}}}
import { IconChevronDown, IconChevronUp } from "@tabler/icons-react";
import { useState } from "react";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useTabLabellerStore, useTabTrainerStore } from "../../../domain";
import { PopoverQuestionMark } from "../../Shared";

function PopoverQuestionMarkWrapper({
	label,
	description,
}: {
	label?: string;
	description?: string;
}) {
	return (
		<Flex gap="xs" justify="flex-start">
			<div>{label}</div>
			<PopoverQuestionMark>{description}</PopoverQuestionMark>
		</Flex>
	);
}

export function ButtonRunModel() {
	const {
		mode,
		connected,
		training,
		onSendTrainRun,
		inputTrainer,
		updateInputTrainer,
	} = useTabTrainerStore(
		useShallow((state) => ({
			mode: state.mode,
			connected: state.connected,
			training: state.training,
			onSendTrainRun: state.onSendTrainRun,
			inputTrainer: state.input,
			updateInputTrainer: state.updateInput,
		})),
	);

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

	const modelRunCategoryInput = (
		<Group gap="xl" w="100%" justify="space-between">
			<SegmentedControl
				value={inputTrainer.runsCategory}
				onChange={(value: string) => {
					updateInputTrainer({ runsCategory: value });
				}}
				data={[
					{ label: "Single", value: "single" },
					{ label: "Multiple", value: "multiple" },
				]}
			/>
			<div>
				<NumberInput
					disabled={inputTrainer.runsCategory === "single"}
					w={120}
					value={inputTrainer.runs}
					onChange={(value) => {
						if (!value) return;
						updateInputTrainer({ runs: parseFloat(value.toString()) });
					}}
					step={1}
					min={2}
				/>
				<Text mt={3} c="var(--fg-4)" size="xs">
					Number of training runs
				</Text>
			</div>
		</Group>
	);

	const labelSourcesInput = fetchingAvailablePublisherSources ? (
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
				updateInputTrainer({ sources: [...values] });
			}}
			comboboxProps={{ withinPortal: false, width: 200, position: "top-start" }}
		/>
	);

	const splitInput = (
		<NumberInput
			w={120}
			value={inputTrainer.split}
			onChange={(value) => {
				if (!value) return;
				updateInputTrainer({ split: parseFloat(value.toString()) });
			}}
			step={0.001}
			min={0.001}
			max={0.999}
			decimalScale={3}
		/>
	);

	const seedInput = (
		<Group gap="xs">
			<NumberInput
				w={120}
				value={inputTrainer.seed}
				onChange={(value) => {
					if (!value) return;
					updateInputTrainer({ seed: parseFloat(value.toString()) });
				}}
				hideControls
			/>
			<Button
				variant="light"
				onClick={() => {
					updateInputTrainer({
						seed: Math.floor(Math.random() * 1_000_000_001),
					});
				}}
			>
				Generate
			</Button>
		</Group>
	);

	const combineLabelsFlagSwitch = (
		<Switch
			label={
				<PopoverQuestionMarkWrapper
					label="Combine NAME labels"
					description="Determines whether to combine all NAME labels into a single NAME label"
				/>
			}
			checked={inputTrainer.combineNameLabels}
			onChange={(event) => {
				updateInputTrainer({ combineNameLabels: event.currentTarget.checked });
			}}
		/>
	);

	const htmlFlagSwitch = (
		<Switch
			label={
				<PopoverQuestionMarkWrapper
					label="HTML results file"
					description="Output an html file listing all the sentences where the model labelled any token incorrectly and what the errors were"
				/>
			}
			checked={inputTrainer.html}
			onChange={(event) => {
				updateInputTrainer({ html: event.currentTarget.checked });
			}}
		/>
	);

	const confusionFlagSwitch = (
		<Switch
			label={
				<PopoverQuestionMarkWrapper
					label="Confusion"
					description="Output a confusion matrix showing the mapping between true label and predicted label"
				/>
			}
			checked={inputTrainer.confusion}
			onChange={(event) => {
				updateInputTrainer({ confusion: event.currentTarget.checked });
			}}
		/>
	);

	const detailedFlagSwitch = (
		<Switch
			label={
				<PopoverQuestionMarkWrapper
					label="Detailed errors"
					description="Output a set of TSV containing information about the types of errors made by the model"
				/>
			}
			checked={inputTrainer.detailed}
			onChange={(event) => {
				updateInputTrainer({ detailed: event.currentTarget.checked });
			}}
		/>
	);

	const debugLevelFlagSwitch = (
		<Switch
			label={
				<PopoverQuestionMarkWrapper
					label="Verbose debugging"
					description="Output verbose logging. Only use for debugging purposes"
				/>
			}
			checked={inputTrainer.debugLevel === 1}
			onChange={(event) => {
				updateInputTrainer({ debugLevel: event.currentTarget.checked ? 1 : 0 });
			}}
		/>
	);

	return connected && mode === "trainer" ? (
		<Group wrap="nowrap" gap={0}>
			<Button
				loading={training}
				style={{
					width: 200,
					height: 50,
					borderTopRightRadius: 0,
					borderBottomRightRadius: 0,
				}}
				variant="dark"
				onClick={() => onSendTrainRun("training")}
			>
				Run train model
			</Button>
			<Menu
				shadow="md"
				keepMounted={false}
				position="bottom-end"
				width={500}
				closeOnItemClick={false}
				offset={8}
				opened={opened}
				onChange={setOpened}
				trigger="click"
			>
				<Menu.Target>
					<ActionIcon
						variant="dark"
						style={{
							borderTopLeftRadius: 0,
							borderBottomLeftRadius: 0,
							borderTop: "none",
							borderBottom: "none",
							borderRight: "none",
						}}
						size={50}
						disabled={training}
					>
						{opened ? (
							<IconChevronUp size={16} />
						) : (
							<IconChevronDown size={16} />
						)}
					</ActionIcon>
				</Menu.Target>
				<Menu.Dropdown>
					<Menu.Label>
						<PopoverQuestionMarkWrapper
							label="Training runs"
							description="The type of training run — multiple runs will take longer"
						/>
					</Menu.Label>
					<Box py="xs" px="sm">
						{modelRunCategoryInput}
					</Box>
					<Menu.Divider />
					<Menu.Label>
						<PopoverQuestionMarkWrapper
							label="Source datasets"
							description="The datasets to use for training"
						/>
					</Menu.Label>
					<Box py="xs" px="sm">
						{labelSourcesInput}
					</Box>
					<Menu.Divider />
					<Menu.Label>
						<PopoverQuestionMarkWrapper
							label="Split value"
							description="Fraction of data to be used for testing"
						/>
					</Menu.Label>
					<Box py="xs" px="sm">
						{splitInput}
					</Box>
					<Menu.Divider />
					<Menu.Label>
						<PopoverQuestionMarkWrapper
							label="Seed value"
							description="Seed value used for train/test split"
						/>
					</Menu.Label>
					<Box py="xs" px="sm">
						{seedInput}
					</Box>
					<Menu.Divider />
					<Box py="xs" px="sm">
						{htmlFlagSwitch}
					</Box>
					<Box py="xs" px="sm">
						{detailedFlagSwitch}
					</Box>
					<Box py="xs" px="sm">
						{confusionFlagSwitch}
					</Box>
					<Box py="xs" px="sm">
						{combineLabelsFlagSwitch}
					</Box>
					<Box py="xs" px="sm">
						{debugLevelFlagSwitch}
					</Box>
				</Menu.Dropdown>
			</Menu>
		</Group>
	) : null;
}
