// {{{EXTERNAL}}}

import { FetchAvailableSouceListener } from "./PageTabLabeller";
import {
	ButtonRunModel,
	ColorSwatchIndicator,
	SectionNotes,
	SectionProgressText,
} from "./PageTabTrain";
import { ButtonRunModelGridSearch } from "./PageTabTrain/ButtonRunModelGridSearch";
import { SectionSelectMode } from "./PageTabTrain/SectionSelectMode";
import { TimeElapsedIndicator } from "./PageTabTrain/TimeElapsedIndicator";
// {{{INTERNAL}}}
import { Sectionable } from "./Shared";

export function MainTrainModel() {
	return (
		<Sectionable>
			<FetchAvailableSouceListener />

			<Sectionable.ActionBar position="top">
				<SectionSelectMode />
			</Sectionable.ActionBar>

			<Sectionable.ActionBar position="top">
				<Sectionable.ActionBarSubGrouping>
					<ColorSwatchIndicator />
					<TimeElapsedIndicator />
				</Sectionable.ActionBarSubGrouping>
				<Sectionable.ActionBarSubGrouping>
					<ButtonRunModelGridSearch />
					<ButtonRunModel />
				</Sectionable.ActionBarSubGrouping>
			</Sectionable.ActionBar>

			<Sectionable.Section grow overflowHidden padded full>
				<SectionProgressText />
			</Sectionable.Section>

			<Sectionable.ActionBar position="bottom">
				<SectionNotes />
			</Sectionable.ActionBar>
		</Sectionable>
	);
}
