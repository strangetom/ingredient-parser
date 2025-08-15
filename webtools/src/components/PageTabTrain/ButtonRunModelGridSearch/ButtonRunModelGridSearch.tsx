// {{{EXTERNAL}}}
import {
	ActionIcon,
	Anchor,
	Box,
	Button,
	Code,
	Flex,
	Group,
	JsonInput,
	Loader,
	LoadingOverlay,
	Menu,
	MultiSelect,
	NumberInput,
	Switch,
	Text,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
// {{{ASSETS}}}
import {
	IconChevronDown,
	IconChevronUp,
	IconCode,
	IconX,
} from "@tabler/icons-react";
import { useState } from "react";
import { useShallow } from "zustand/react/shallow";
import { useTabLabellerStore, useTabTrainerStore } from "../../../domain";
// {{{INTERNAL}}}
import { ActionIconTooltipped, PopoverQuestionMark } from "../../Shared";
import { ComboBoxAlgos } from "./ComboBoxAlgos";

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
	const [jsonError, setHasJsonError] = useState(false);
	const [prettyJsonOpened, { open: openPrettyJson, close: closePrettyJson }] =
		useDisclosure(false);

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
			step={0.1}
			min={0.1}
			max={0.9}
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

	const algosInput = (
		<div>
			<Box style={{ position: "relative" }}>
				<JsonInput
					value={inputGridSearch.algosGlobalParams}
					onChange={(value) => {
						updateInputGridSearch({ algosGlobalParams: value });

						try {
							JSON.parse(value);
							setHasJsonError(false);
						} catch {
							setHasJsonError(true);
						}
					}}
					validationError="Invalid JSON — parameters will be ignored unless corrected"
					rows={4}
				/>
				{!jsonError && (
					<Box
						style={{
							position: "absolute",
							bottom: "var(--xsmall-spacing)",
							right: "var(--xsmall-spacing)",
						}}
					>
						<ActionIconTooltipped
							text="View pretty format"
							iconography={IconCode}
							onClick={openPrettyJson}
						/>
					</Box>
				)}
			</Box>
			<Text fz="xs">
				View CRFSuite's{" "}
				<Anchor
					target="_blank"
					fz="inherit"
					href="https://www.chokkan.org/software/crfsuite/manual.html"
				>
					hyper-parameters documentation
				</Anchor>
			</Text>
		</div>
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
					<LoadingOverlay
						visible={prettyJsonOpened}
						loaderProps={{
							style: {
								position: "relative",
								height: "100%",
								width: "100%",
								padding: "var(--medium-spacing)",
							},
							children: (
								<div
									style={{
										position: "relative",
										height: "100%",
										width: "100%",
									}}
								>
									<Code block style={{ height: "100%", width: "100%" }}>
										{!jsonError &&
											JSON.stringify(
												JSON.parse(inputGridSearch.algosGlobalParams),
												null,
												2,
											)}
									</Code>
									<Box
										style={{
											position: "absolute",
											top: "var(--xsmall-spacing)",
											right: "var(--xsmall-spacing)",
										}}
									>
										<ActionIconTooltipped
											text="Exit"
											iconography={IconX}
											onClick={closePrettyJson}
										/>
									</Box>
								</div>
							),
						}}
						zIndex={99999}
						overlayProps={{
							blur: 0,
							backgroundOpacity: 0.9,
							color: "var(--bg-1)",
							center: false,
						}}
						styles={{
							root: {
								display: "block",
								align: undefined,
								justifyContent: undefined,
							},
						}}
					/>

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
							label="Algorithm global parameters"
							description="The hyper-parameters applied to the CRFsuite algorithm — it is recommended to copy & paste your json, editing features here is limited"
						/>
					</Menu.Label>
					<Box py="xs" px="sm">
						{algosInput}
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
					<Menu.Item component="div">{combineLabelsFlagSwitch}</Menu.Item>
				</Menu.Dropdown>
			</Menu>
		</Group>
	) : null;
}
