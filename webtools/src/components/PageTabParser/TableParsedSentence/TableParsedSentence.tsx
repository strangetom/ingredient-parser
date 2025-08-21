// {{{EXTERNAL}}}
import { useShallow } from "zustand/react/shallow";
import {
	type ParsedSentenceEditable,
	useTabParserStore,
} from "../../../domain";
// {{{INTERNAL}}}
import { LabellerSentence } from "../../Shared";

export function TableParsedSentence() {
	const { input, parsed } = useTabParserStore(
		useShallow((state) => ({
			input: state.input,
			parsed: state.parsed,
		})),
	);

	return parsed ? (
		<LabellerSentence
			sentence={
				{
					id: "",
					labels: [],
					tokens: parsed.tokens,
					sentence: input.sentence,
					source: "-",
				} as ParsedSentenceEditable
			}
			labellerProps={{
				marginalsMode: true,
				size: "large",
			}}
		/>
	) : null;
}
