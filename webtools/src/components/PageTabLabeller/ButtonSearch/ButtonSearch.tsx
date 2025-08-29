// {{{EXTERNAL}}}
import { Button } from "@mantine/core";
import { useShallow } from "zustand/react/shallow";
// {{{INTERNAL}}}
import { useTabLabellerStore } from "../../../domain";

export function ButtonSearch() {
	const { input, loading, setActivePage, getLabellerSearchApi } =
		useTabLabellerStore(
			useShallow((state) => ({
				input: state.input,
				loading: state.loading,
				setActivePage: state.setActivePage,
				getLabellerSearchApi: state.getLabellerSearchApi,
			})),
		);

	const onSearchWrapperHandler = () => {
		const { hasUnsavedChanges, setUnsavedChangesModalOpen } =
			useTabLabellerStore.getState();
		const fnCallback = () => {
			getLabellerSearchApi();
			setActivePage(1);
		};
		if (hasUnsavedChanges()) {
			const { setUnsavedChangesFnCallback } = useTabLabellerStore.getState();
			setUnsavedChangesFnCallback(fnCallback);
			setUnsavedChangesModalOpen(true);
		} else {
			fnCallback();
		}
	};

	return (
		<Button
			variant="dark"
			style={{ width: 150, height: 50 }}
			onClick={() => onSearchWrapperHandler()}
			loading={loading}
			disabled={!input.sentence}
		>
			Search
		</Button>
	);
}
