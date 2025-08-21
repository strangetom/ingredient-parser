// {{{EXTERNAL}}}
import { Flex, Group, SegmentedControl, Text } from "@mantine/core";
import { useShallow } from "zustand/react/shallow";
import { type TrainerMode, useTabTrainerStore } from "../../../domain";
// {{{INTERNAL}}}
import { PopoverQuestionMark } from "../../Shared";

export function SectionSelectMode() {
	const { training, mode, updateMode } = useTabTrainerStore(
		useShallow((state) => ({
			training: state.training,
			mode: state.mode,
			updateMode: state.updateMode,
		})),
	);

	return (
		<Flex style={{ width: "100%" }} justify="center">
			<Group>
				<Text>Choose mode:</Text>
				<SegmentedControl
					disabled={training}
					value={mode}
					data={[
						{ value: "trainer", label: "Model Trainer" },
						{ value: "tuner", label: "Gridsearch Tuner" },
					]}
					onChange={(value: string) => {
						updateMode(value as TrainerMode);
					}}
				/>
				<PopoverQuestionMark>
					<div>
						<div style={{ marginBottom: "var(--small-spacing)" }}>
							<b>Trainer</b>: Use this to train your models. This uses the
							single and multiple training features.
						</div>
						<div>
							<b>Tuner</b>: Use this to compare and fine tune your models. This
							uses the grid search feature.
						</div>
					</div>
				</PopoverQuestionMark>
			</Group>
		</Flex>
	);
}
