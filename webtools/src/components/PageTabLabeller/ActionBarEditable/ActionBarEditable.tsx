// {{{EXTERNAL}}}
import { Button } from "@mantine/core";
import { useShallow } from "zustand/react/shallow";
import { useTabLabellerStore } from "../../../domain";

export function ActionBarEditable() {
	const { editing, editLabellerItemsApi } = useTabLabellerStore(
		useShallow((state) => ({
			editing: state.editing,
			editLabellerItemsApi: state.editLabellerItemsApi,
		})),
	);

	const onEditApiHandler = async () => {
		await editLabellerItemsApi();
	};

	return (
		<>
			<div />
			<Button
				variant="light"
				h={50}
				onClick={onEditApiHandler}
				loading={editing}
			>
				Save changes
			</Button>
		</>
	);
}
