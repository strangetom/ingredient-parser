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
	Switch,
} from "@mantine/core";
// {{{ASSETS}}}
import { IconChevronDown, IconChevronUp } from "@tabler/icons-react";
import { useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { useTabLabellerStore, useTabTrainerStore } from "../../../domain";
// {{{INTERNAL}}}
import { PopoverQuestionMark } from "../../Shared";
import { ComboBoxAlgos } from "./ComboBoxAlgos";
import { TextAreaAlgosParams } from "./TextAreaAlgosParams";

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

export function ButtonRunModelGridSearch() {
	const {
		mode,
		connected,
		training,
		onSendTrainRun,
		inputGridSearch,
		updateInputGridSearch,
	} = useTabTrainerStore(
		useShallow((state) => ({
			mode: state.mode,
			connected: state.connected,
			training: state.training,
			onSendTrainRun: state.onSendTrainRun,
			inputGridSearch: state.inputGridSearch,
			updateInputGridSearch: state.updateInputGridSearch,
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
				updateInputGridSearch({ sources: [...values] });
			}}
			comboboxProps={{ withinPortal: false, width: 200, position: "top-start" }}
		/>
	);

	const splitInput = (
		<NumberInput
			w={120}
			value={inputGridSearch.split}
			onChange={(value) => {
				if (!value) return;
				updateInputGridSearch({ split: parseFloat(value.toString()) });
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
				value={inputGridSearch.seed}
				onChange={(value) => {
					if (!value) return;
					updateInputGridSearch({ seed: parseFloat(value.toString()) });
				}}
				hideControls
			/>
			<Button
				variant="light"
				onClick={() => {
					updateInputGridSearch({
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
			checked={inputGridSearch.combineNameLabels}
			onChange={(event) => {
				updateInputGridSearch({
					combineNameLabels: event.currentTarget.checked,
				});
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
			checked={inputGridSearch.debugLevel === 1}
			onChange={(event) => {
				updateInputGridSearch({
					debugLevel: event.currentTarget.checked ? 1 : 0,
				});
			}}
		/>
	);

	return connected && mode === "tuner" ? (
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
				onClick={() => onSendTrainRun("gridsearch")}
			>
				Run gridsearch
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
				menuItemTabIndex={0}
				loop={false}
				trapFocus={true}
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
							label="Algorithm(s)"
							description="The CRFSuite training algorithms to use — defaults to lbfgs if none selected"
						/>
					</Menu.Label>
					<Box py="xs" px="sm">
						<ComboBoxAlgos />
					</Box>
					<Menu.Label>
						<PopoverQuestionMarkWrapper
							label="Algorithm parameters"
							description="The hyper-parameters applied to the CRFsuite algorithm — it is recommended to copy & paste your json, editing features here is limited"
						/>
					</Menu.Label>
					<Box py="xs" px="sm">
						<TextAreaAlgosParams />
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
