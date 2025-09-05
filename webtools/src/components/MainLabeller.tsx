// {{{EXTERNAL}}}

import { useShallow } from "zustand/react/shallow";
import { useTabLabellerStore } from "../domain";
import {
	ActionBarEditable,
	ActionBarPaginator,
	ButtonSearch,
	ButtonUpload,
	FetchAvailableSouceListener,
	ListParsedSentences,
	ModalUnsavedChanges,
	TextInputSubmit,
} from "./PageTabLabeller";
// {{{INTERNAL}}}
import { Sectionable } from "./Shared";

export function MainLabeller() {
	const { parsed, parsedSentences, editModeEnabled } = useTabLabellerStore(
		useShallow((state) => ({
			parsed: state.parsed,
			parsedSentences: state.parsedSentences,
			editModeEnabled: state.editModeEnabled,
		})),
	);

	return (
		<Sectionable>
			<FetchAvailableSouceListener />
			<ModalUnsavedChanges />

			<Sectionable.ActionBar position="top">
				<TextInputSubmit style={{ flexBasis: "100%" }} />
				<Sectionable.ActionBarSubGrouping>
					<ButtonSearch />
					<ButtonUpload />
				</Sectionable.ActionBarSubGrouping>
			</Sectionable.ActionBar>

			<Sectionable.ActionBar
				mounted={Boolean(parsed) && parsedSentences.length !== 0}
			>
				<ActionBarPaginator />
			</Sectionable.ActionBar>

			<Sectionable.Section grow>
				<ListParsedSentences />
			</Sectionable.Section>

			<Sectionable.ActionBar
				mounted={
					Boolean(parsed) && editModeEnabled && parsedSentences.length > 0
				}
				position="bottom"
			>
				<ActionBarEditable />
			</Sectionable.ActionBar>
		</Sectionable>
	);
}
