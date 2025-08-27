// {{{EXTERNAL}}}
import { Pagination } from "@mantine/core";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useTabLabellerStore } from "../../../domain";
import { SwitchEditMode } from "../SwitchEditMode";

const OFFSET_MULTIPLIER = 250;

export function ActionBarPaginator() {
	const { parsed, parsedSentences, loading, activePage } = useTabLabellerStore(
		useShallow((state) => ({
			parsed: state.parsed,
			parsedSentences: state.parsedSentences,
			loading: state.loading,
			activePage: state.activePage,
		})),
	);

	const onChangePaginatorHandler = (value: number) => {
		const {
			hasUnsavedChanges,
			setUnsavedChangesModalOpen,
			setUnsavedChangesFnCallback,
		} = useTabLabellerStore.getState();
		const fnCallback = () => {
			const { setActivePage, getLabellerSearchApi } =
				useTabLabellerStore.getState();
			setActivePage(value);
			getLabellerSearchApi({ offsetPage: (value - 1) * OFFSET_MULTIPLIER });
		};
		if (hasUnsavedChanges()) {
			setUnsavedChangesFnCallback(fnCallback);
			setUnsavedChangesModalOpen(true);
		} else {
			fnCallback();
		}
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
