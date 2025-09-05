// {{{EXTERNAL}}}
import { Box, LoadingOverlay } from "@mantine/core";
import { useShallow } from "zustand/react/shallow";
import { type InputTabLabeller, useTabLabellerStore } from "../../../domain";
import { PrefabExamplesLabellerSource } from "../../PageTabLabeller";
// {{{INTERNAL}}}
import { Filler, ScrollableVirtualized } from "../../Shared/";

export function ListParsedSentences() {
	const {
		loading,
		editModeEnabled,
		parsed,
		parsedSentencesOriginal,
		parsedSentencesOriginalHandler,
		parsedSentences,
		parsedSentencesHandler,
	} = useTabLabellerStore(
		useShallow((state) => ({
			loading: state.loading,
			editModeEnabled: state.editModeEnabled,
			parsed: state.parsed,
			parsedSentencesOriginal: state.parsedSentencesOriginal,
			parsedSentencesOriginalHandler: state.parsedSentencesOriginalHandler,
			parsedSentences: state.parsedSentences,
			parsedSentencesHandler: state.parsedSentencesHandler,
		})),
	);

	const onClickPreFabHandler = (abbr: string) => {
		const preFabInput = {
			sentence: "~~",
			settings: {
				sources: [abbr],
				caseSensitive: false,
				labels: [
					"COMMENT",
					"B_NAME_TOK",
					"I_NAME_TOK",
					"NAME_VAR",
					"NAME_MOD",
					"NAME_SEP",
					"PREP",
					"PUNC",
					"PURPOSE",
					"QTY",
					"SIZE",
					"UNIT",
					"OTHER",
				],
				wholeWord: false,
			},
		} as InputTabLabeller;
		const { updateInput, getLabellerSearchApi } =
			useTabLabellerStore.getState();
		updateInput(preFabInput);
		getLabellerSearchApi();
	};

	return (
		<>
			<LoadingOverlay
				visible={loading}
				overlayProps={{ opacity: 0.6, blur: 0, bg: "var(--bg-s)" }}
				loaderProps={{ children: <div /> }}
				zIndex={1}
			/>
			{parsed ? (
				<>
					{editModeEnabled && (
						<ScrollableVirtualized
							style={{ height: "100%", width: "100%" }}
							parsedSentencesProvided={parsedSentences}
							parsedSentencesProvidedHandler={parsedSentencesHandler}
							labellerSentenceProps={{
								tasks: ["copy", "remove", "plain"],
								listable: true,
							}}
							labellerProps={{
								editMode: true,
							}}
						/>
					)}

					{!editModeEnabled && (
						<ScrollableVirtualized
							style={{ height: "100%", width: "100%" }}
							parsedSentencesProvided={parsedSentencesOriginal}
							parsedSentencesProvidedHandler={parsedSentencesOriginalHandler}
							labellerSentenceProps={{
								tasks: ["copy", "plain"],
								listable: true,
							}}
							labellerProps={{
								editMode: false,
							}}
						/>
					)}
				</>
			) : (
				<Filler
					text="Search for and edit ingredient labels or browse all from"
					illustration="sandwich"
				>
					<Box mt="sm">
						<PrefabExamplesLabellerSource onClick={onClickPreFabHandler} />
					</Box>
				</Filler>
			)}
		</>
	);
}
