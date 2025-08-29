// {{{EXTERNAL}}}
import { Pagination } from "@mantine/core";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useTabLabellerStore } from "../../../domain";
import { SwitchEditMode } from "../SwitchEditMode";

const OFFSET_MULTIPLIER = 250;

export function ActionBarPaginator() {
	const {
		parsed,
		parsedSentences,
		loading,
		activePage,
		setActivePage,
		getLabellerSearchApi,
	} = useTabLabellerStore(
		useShallow((state) => ({
			parsed: state.parsed,
			parsedSentences: state.parsedSentences,
			loading: state.loading,
			activePage: state.activePage,
			setActivePage: state.setActivePage,
			getLabellerSearchApi: state.getLabellerSearchApi,
		})),
	);

	const onChangePaginatorHandler = (value: number) => {
		setActivePage(value);
		getLabellerSearchApi({ offsetPage: (value - 1) * OFFSET_MULTIPLIER });
	};
	return parsed && parsedSentences.length !== 0 ? (
		<>
			<SwitchEditMode />
			<Pagination
				total={Math.ceil(parsed.total / 250)}
				value={activePage}
				onChange={onChangePaginatorHandler}
				disabled={loading}
			/>
		</>
	) : null;
}
